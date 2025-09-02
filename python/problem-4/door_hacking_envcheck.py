#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
door_hacking_envcheck.py

기능:
1) 벤치마크: 내 환경에서 '헤더 조기 검증(prefilter)' 사용/미사용의 시도/초 비교
2) 자동 선택: 더 빠른 모드로 멀티프로세싱 브루트포스 실행
3) 과제 요구 충족: 진행 로그, 예외처리, password.txt/result.txt 저장

사용법 예시:
  python door_hacking_envcheck.py --zip emergency_storage_key.zip --bench
  python door_hacking_envcheck.py --zip emergency_storage_key.zip --run
  python door_hacking_envcheck.py --zip emergency_storage_key.zip --run --procs 6
  python door_hacking_envcheck.py --zip emergency_storage_key.zip --run --force-prefilter on|off
"""

import io
import os
import time
import struct
import string
import zipfile
import zlib
import argparse
import platform
import multiprocessing as mp
from ctypes import c_bool, c_ulonglong, c_char

# =========================
# 공용 유틸
# =========================

def format_hms(seconds: float) -> str:
    s = int(seconds)
    h, r = divmod(s, 3600)
    m, r = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{r:02d}"

def partition_ranges(total: int, parts: int):
    base = total // parts
    ranges = []
    start = 0
    for i in range(parts):
        end = start + base
        if i == parts - 1:
            end = total
        ranges.append((start, end))
        start = end
    return ranges

def dos_time_high_byte(dt_tuple):
    """ZipInfo.date_time -> DOS time 상위 1바이트 계산"""
    hour, minute, second = dt_tuple[3], dt_tuple[4], dt_tuple[5]
    dos_time = ((hour & 0x1F) << 11) | ((minute & 0x3F) << 5) | ((second // 2) & 0x1F)
    return (dos_time >> 8) & 0xFF

def extract_enc_header(zip_bytes: bytes, zi: zipfile.ZipInfo) -> bytes:
    """로컬 파일 헤더에서 12바이트 암호화 헤더 추출 (PKZIP Traditional)"""
    off = zi.header_offset
    if off + 30 > len(zip_bytes):
        raise ValueError("로컬 파일 헤더 범위 오류")
    if zip_bytes[off:off+4] != b'PK\x03\x04':
        raise ValueError("Local File Header signature mismatch")
    fnlen = struct.unpack_from("<H", zip_bytes, off + 26)[0]
    extralen = struct.unpack_from("<H", zip_bytes, off + 28)[0]
    data_start = off + 30 + fnlen + extralen
    if data_start + 12 > len(zip_bytes):
        raise ValueError("암호화 헤더 범위 오류")
    return zip_bytes[data_start:data_start+12]

# =========================
# PKZIP 전통 암호 헤더 조기 검증
# =========================

def keys_init(pw_bytes: bytes):
    """PKZIP 전통 암호 키 초기화(3개의 32-bit key)"""
    k0, k1, k2 = 0x12345678, 0x23456789, 0x34567890
    for b in pw_bytes:
        k0 = zlib.crc32(bytes([b]), k0) & 0xFFFFFFFF
        k1 = (k1 + (k0 & 0xFF)) & 0xFFFFFFFF
        k1 = (k1 * 134775813 + 1) & 0xFFFFFFFF
        k2 = zlib.crc32(bytes([(k1 >> 24) & 0xFF]), k2) & 0xFFFFFFFF
    return [k0, k1, k2]

def decrypt_byte(keys):
    """현재 키 상태에서 1바이트 키스트림 생성"""
    t = (keys[2] | 2) & 0xFFFFFFFF
    return ((t * (t ^ 1)) >> 8) & 0xFF

def update_keys(keys, plain_byte: int):
    """평문 바이트 적용 후 키 갱신"""
    keys[0] = zlib.crc32(bytes([plain_byte]), keys[0]) & 0xFFFFFFFF
    keys[1] = (keys[1] + (keys[0] & 0xFF)) & 0xFFFFFFFF
    keys[1] = (keys[1] * 134775813 + 1) & 0xFFFFFFFF
    keys[2] = zlib.crc32(bytes([(keys[1] >> 24) & 0xFF]), keys[2]) & 0xFFFFFFFF

def verify_header_byte(enc_header: bytes, pw_bytes: bytes, expect_last_byte: int) -> bool:
    """
    암호 후보에 대해 12바이트 암호화 헤더를 복호화하고
    마지막 검증 바이트가 기대값과 일치하는지 확인(조기 필터).
    평균적으로 255/256 후보가 여기서 컷됨.
    """
    keys = keys_init(pw_bytes)
    for i in range(12):
        c = enc_header[i]
        p = c ^ decrypt_byte(keys)      # 복호화된 평문 바이트
        update_keys(keys, p)
        if i == 11:
            return p == expect_last_byte
    return False

# =========================
# 비밀번호 생성(인덱스→base36)
# =========================

def fill_password(buf: bytearray, idx: int, charset: bytes):
    base = len(charset)
    L = len(buf)
    x = idx
    for j in range(L - 1, -1, -1):
        buf[j] = charset[x % base]
        x //= base

# =========================
# 워커 (브루트포스)
# =========================

def worker(zip_bytes: bytes,
           target_file: str,
           enc_header: bytes,
           expect_last_byte: int,
           charset_bytes: bytes,
           pwd_len: int,
           start_index: int,
           end_index: int,
           is_found,
           result_buf,
           attempts_shared,
           print_interval: int,
           t0_wall: float,
           use_prefilter: bool):
    """
    use_prefilter=True  : 헤더 조기 검증 → 통과한 극소수만 실제 zipfile.open() 확인
    use_prefilter=False : 바로 zipfile.open() 확인(실패 시 예외가 매 시도 발생 가능)
    """
    name = mp.current_process().name
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))  # 1회 생성/재사용
    zopen = zf.open

    buf = bytearray(pwd_len)
    ZipErrors = (RuntimeError, zipfile.BadZipFile, zlib.error)

    local_attempts = 0

    for idx in range(start_index, end_index):
        if is_found.value:
            break

        fill_password(buf, idx, charset_bytes)

        try:
            if use_prefilter:
                if not verify_header_byte(enc_header, buf, expect_last_byte):
                    local_attempts += 1
                    if local_attempts % print_interval == 0:
                        with attempts_shared.get_lock():
                            attempts_shared.value += local_attempts
                            total = attempts_shared.value
                            local_attempts = 0
                        elapsed = time.time() - t0_wall
                        rate = int(total / elapsed) if elapsed > 0 else 0
                        print(f"🔍 [{name}] attempts={total:,} | elapsed={format_hms(elapsed)} | ~{rate:,}/s")
                    continue
                # 통과한 소수만 최종 확인
                with zopen(target_file, pwd=bytes(buf)) as f:
                    f.read(1)
            else:
                # 바로 확인(오류/예외가 빈번)
                with zopen(target_file, pwd=bytes(buf)) as f:
                    f.read(1)

            # 성공 처리
            if not is_found.value:
                with is_found.get_lock():
                    if not is_found.value:
                        is_found.value = True
                        result_buf[:pwd_len] = bytes(buf)

                        if local_attempts:
                            with attempts_shared.get_lock():
                                attempts_shared.value += local_attempts
                                local_attempts = 0

                        elapsed = time.time() - t0_wall
                        total = attempts_shared.value
                        pw = bytes(buf).decode('ascii')
                        print(f"\n✅ [{name}] SUCCESS: {pw} | attempts≈{total:,} | elapsed={format_hms(elapsed)}")
            break

        except ZipErrors:
            local_attempts += 1
            if local_attempts % print_interval == 0:
                with attempts_shared.get_lock():
                    attempts_shared.value += local_attempts
                    total = attempts_shared.value
                    local_attempts = 0
                elapsed = time.time() - t0_wall
                rate = int(total / elapsed) if elapsed > 0 else 0
                print(f"🔍 [{name}] attempts={total:,} | elapsed={format_hms(elapsed)} | ~{rate:,}/s")

    if local_attempts:
        with attempts_shared.get_lock():
            attempts_shared.value += local_attempts

# =========================
# 벤치마크 (1프로세스)
# =========================

def bench(zip_path: str,
          seconds: int = 8,
          password_length: int = 6,
          use_prefilter: bool = True) -> float:
    """
    동일 ZIP, 동일 루프에서 use_prefilter on/off 의 시도/초 측정
    반환: attempts_per_sec (float)
    """
    charset = (string.digits + string.ascii_lowercase).encode("ascii")

    if not os.path.exists(zip_path):
        print(f"❌ ZIP 파일이 없습니다: {zip_path}")
        return 0.0

    try:
        with open(zip_path, "rb") as f:
            zip_bytes = f.read()
    except Exception as e:
        print(f"❌ ZIP 파일 읽기 오류: {e}")
        return 0.0

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            names = z.namelist()
            if not names:
                print("❌ ZIP 내부에 파일이 없습니다.")
                return 0.0
            target_file = names[0]
            zi = z.getinfo(target_file)
            if (zi.flag_bits & 0x08) != 0:
                expect_last = dos_time_high_byte(zi.date_time)
            else:
                expect_last = (zi.CRC >> 24) & 0xFF
            enc_header = extract_enc_header(zip_bytes, zi)
    except Exception as e:
        print(f"❌ ZIP 구조 분석 실패: {e}")
        return 0.0

    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    zopen = zf.open
    ZipErrors = (RuntimeError, zipfile.BadZipFile, zlib.error)

    buf = bytearray(password_length)
    attempts = 0
    t0 = time.perf_counter()

    # 연속 인덱스 생성 (키스페이스 균일 샘플)
    idx = 0
    base = len(charset)
    total_space = base ** password_length

    print(f"⏱️ 벤치마크 시작: mode={'prefilter' if use_prefilter else 'direct'} | duration={seconds}s")

    while time.perf_counter() - t0 < seconds:
        # 안전: 키스페이스 순환
        if idx >= total_space:
            idx = 0

        fill_password(buf, idx, charset)
        try:
            if use_prefilter:
                if not verify_header_byte(enc_header, buf, expect_last):
                    attempts += 1
                    idx += 1
                    continue
                with zopen(target_file, pwd=bytes(buf)) as f:
                    f.read(1)
            else:
                with zopen(target_file, pwd=bytes(buf)) as f:
                    f.read(1)
        except ZipErrors:
            pass

        attempts += 1
        idx += 1

    dt = time.perf_counter() - t0
    aps = attempts / dt if dt > 0 else 0.0
    print(f"📊 결과: attempts={attempts:,} | time={dt:.2f}s | {aps:,.0f}회/초")
    return aps

# =========================
# 브루트포스 실행
# =========================

def unlock_zip(zip_path: str,
               password_length: int = 6,
               process_count: int | None = None,
               print_interval: int = 500_000,
               force_prefilter: str | None = None) -> str | None:
    """
    성공 시 password.txt / result.txt 저장
    force_prefilter: "on" / "off" / None(auto; 벤치 후 선택)
    """
    charset = (string.digits + string.ascii_lowercase).encode("ascii")
    t0 = time.time()
    start_human = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0))

    if not os.path.exists(zip_path):
        print(f"❌ ZIP 파일이 없습니다: {zip_path}")
        return None
    try:
        with open(zip_path, "rb") as f:
            zip_bytes = f.read()
    except Exception as e:
        print(f"❌ ZIP 파일 읽기 오류: {e}")
        return None

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            names = z.namelist()
            if not names:
                print("❌ ZIP 내부에 파일이 없습니다.")
                return None
            target_file = names[0]
            zi = z.getinfo(target_file)
            encrypted = bool(zi.flag_bits & 0x1)
            if (zi.flag_bits & 0x08) != 0:
                expect_last = dos_time_high_byte(zi.date_time)
            else:
                expect_last = (zi.CRC >> 24) & 0xFF
            enc_header = extract_enc_header(zip_bytes, zi)
    except Exception as e:
        print(f"❌ ZIP 구조 분석 실패: {e}")
        return None

    base = len(charset)
    total = base ** password_length
    process_count = process_count or (mp.cpu_count() or 4)

    # 모드 결정
    if force_prefilter is None:
        print("🔬 자동 선택을 위해 1프로세스 벤치마크를 수행합니다...")
        aps_on = bench(zip_path, seconds=6, password_length=password_length, use_prefilter=True)
        aps_off = bench(zip_path, seconds=6, password_length=password_length, use_prefilter=False)
        use_prefilter = aps_on >= aps_off
        print(f"✅ 선택: {'prefilter' if use_prefilter else 'direct'} (on={aps_on:,.0f}/s, off={aps_off:,.0f}/s)")
    else:
        use_prefilter = (force_prefilter.lower() == "on")
        print(f"⚙️  강제 설정: use_prefilter={use_prefilter}")

    print("=" * 72)
    print("🚀 ZIP Password Cracker (env-checked)")
    print(f"📁 ZIP Path     : {zip_path}")
    print(f"📄 Target File  : {target_file}")
    print(f"🔐 Encrypted    : {encrypted}")
    print(f"🕒 Start Time   : {start_human}")
    print(f"🧮 Keyspace     : {total:,} (36^{password_length})")
    print(f"🧵 Processes    : {process_count}")
    print(f"🧰 Mode         : {'prefilter' if use_prefilter else 'direct'}")
    print("=" * 72)

    is_found = mp.Value(c_bool, False)
    attempts_shared = mp.Value(c_ulonglong, 0)
    result_buf = mp.Array(c_char, password_length)

    ranges = partition_ranges(total, process_count)
    procs: list[mp.Process] = []

    try:
        for i, (s, e) in enumerate(ranges, start=1):
            p = mp.Process(
                target=worker,
                name=f"W{i}",
                args=(
                    zip_bytes,
                    target_file,
                    enc_header,
                    expect_last,
                    charset,
                    password_length,
                    s, e,
                    is_found,
                    result_buf,
                    attempts_shared,
                    print_interval,
                    t0,
                    use_prefilter,
                ),
                daemon=False,
            )
            p.start()
            procs.append(p)
            print(f"▶️  [W{i}] range={s:,} ~ {e:,}  (size={e - s:,})")
    except Exception as e:
        print(f"❌ 프로세스 시작 실패: {e}")
        for p in procs:
            if p.is_alive():
                p.terminate()
        return None

    try:
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        print("\n🛑 사용자 중단: 종료 중...")
        is_found.value = True
        for p in procs:
            if p.is_alive():
                p.terminate()
                p.join()

    elapsed = time.time() - t0
    total_attempts = attempts_shared.value
    rate = int(total_attempts / elapsed) if elapsed > 0 else 0

    if is_found.value:
        password = bytes(result_buf[:]).decode("ascii", errors="ignore")
        print("=" * 72)
        print(f"✅ DONE: password={password} | attempts≈{total_attempts:,} | elapsed={format_hms(elapsed)} | ~{rate:,}/s")
        print("=" * 72)
        for outname in ("password.txt", "result.txt"):
            try:
                with open(outname, "w", encoding="utf-8") as f:
                    f.write(password)
                print(f"💾 saved -> {outname}")
            except Exception as e:
                print(f"❌ {outname} 저장 실패: {e}")
        return password
    else:
        print("=" * 72)
        print(f"😞 실패: 암호를 찾지 못했습니다. attempts≈{total_attempts:,} | elapsed={format_hms(elapsed)} | ~{rate:,}/s")
        print("=" * 72)
        return None

# =========================
# 엔트리포인트
# =========================

def main():
    if hasattr(mp, "set_start_method"):
        try:
            mp.set_start_method("fork")
        except Exception:
            pass  # Windows/macOS는 spawn 기본

    parser = argparse.ArgumentParser(description="ZIP Password Cracker (env-check + auto mode)")
    parser.add_argument("--zip", dest="zip_path", default="emergency_storage_key.zip", help="ZIP 파일 경로")
    parser.add_argument("--bench", action="store_true", help="벤치마크만 실행")
    parser.add_argument("--run", action="store_true", help="브루트포스 실행")
    parser.add_argument("--seconds", type=int, default=8, help="벤치마크 시간(초)")
    parser.add_argument("--procs", type=int, default=0, help="프로세스 수(0이면 자동)")
    parser.add_argument("--print-interval", type=int, default=500_000, help="진행 로그 주기(시도 수)")
    parser.add_argument("--force-prefilter", choices=["on", "off"], default=None, help="헤더 조기 검증 강제 on/off (기본: 자동)")

    args = parser.parse_args()

    print(f"🖥️  환경: Python {platform.python_version()} | OS={platform.system()} {platform.release()} | CPU={mp.cpu_count()}")

    if args.bench:
        print("=== BENCH (prefilter=ON) ===")
        bench(args.zip_path, seconds=args.seconds, password_length=6, use_prefilter=True)
        print("=== BENCH (prefilter=OFF) ===")
        bench(args.zip_path, seconds=args.seconds, password_length=6, use_prefilter=False)

    if args.run:
        procs = args.procs if args.procs and args.procs > 0 else None
        unlock_zip(
            zip_path=args.zip_path,
            password_length=6,
            process_count=procs,
            print_interval=args.print_interval,
            force_prefilter=args.force_prefilter,
        )

if __name__ == "__main__":
    main()
