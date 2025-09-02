#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
문제 1. 비밀번호 찾기 — 최종(휴리스틱 2: 계산/검증 최적화, '찍기' 없음)
- emergency_storage_key.zip: 숫자+소문자 6자리 전수 탐색
- 진행 상황(시작 시간, 시도 횟수, 경과 시간, 처리속도) 주기 출력
- 성공 시 password.txt, result.txt 저장
- 표준 라이브러리만 사용(zipfile, zlib, multiprocessing)
"""

import io
import os
import time
import struct
import string
import zipfile
import zlib
import multiprocessing as mp
from ctypes import c_bool, c_ulonglong, c_char

# =========================
# 공용 유틸
# =========================

def _format_hms(seconds: float) -> str:
    s = int(seconds)
    h, r = divmod(s, 3600)
    m, r = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{r:02d}"

def _partition_ranges(total: int, parts: int):
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

def _dos_time_high_byte(dt_tuple):
    """ZipInfo.date_time -> DOS time 상위 1바이트 계산"""
    # DOS time(2 bytes): bits 15-11 hour, 10-5 minute, 4-0 second/2
    hour, minute, second = dt_tuple[3], dt_tuple[4], dt_tuple[5]
    dos_time = ((hour & 0x1F) << 11) | ((minute & 0x3F) << 5) | ((second // 2) & 0x1F)
    return (dos_time >> 8) & 0xFF

def _extract_enc_header(zip_bytes: bytes, zi: zipfile.ZipInfo):
    """로컬 파일 헤더에서 12바이트 암호화 헤더 추출"""
    off = zi.header_offset
    if off + 30 > len(zip_bytes):
        raise ValueError("로컬 파일 헤더 범위 오류")
    # Local File Header(30 bytes fixed)
    # sig(4) ver(2) flag(2) comp(2) time(2) date(2) crc(4) csize(4) usize(4) fnlen(2) extralen(2)
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

def _keys_init(pw_bytes: bytes):
    """PKZIP 전통 암호 키 초기화(3개의 32-bit key)"""
    k0, k1, k2 = 0x12345678, 0x23456789, 0x34567890
    for b in pw_bytes:
        # k0 = crc32(k0, b)
        k0 = zlib.crc32(bytes([b]), k0) & 0xFFFFFFFF
        # k1 = ((k1 + (k0 & 0xFF)) * 134775813 + 1) mod 2^32
        k1 = (k1 + (k0 & 0xFF)) & 0xFFFFFFFF
        k1 = (k1 * 134775813 + 1) & 0xFFFFFFFF
        # k2 = crc32(k2, k1 >> 24)
        k2 = zlib.crc32(bytes([(k1 >> 24) & 0xFF]), k2) & 0xFFFFFFFF
    return [k0, k1, k2]

def _decrypt_byte(keys):
    """현재 키 상태에서 1바이트 키스트림 생성"""
    t = (keys[2] | 2) & 0xFFFFFFFF
    return ((t * (t ^ 1)) >> 8) & 0xFF

def _update_keys(keys, plain_byte: int):
    """평문 바이트 적용 후 키 갱신"""
    keys[0] = zlib.crc32(bytes([plain_byte]), keys[0]) & 0xFFFFFFFF
    keys[1] = (keys[1] + (keys[0] & 0xFF)) & 0xFFFFFFFF
    keys[1] = (keys[1] * 134775813 + 1) & 0xFFFFFFFF
    keys[2] = zlib.crc32(bytes([(keys[1] >> 24) & 0xFF]), keys[2]) & 0xFFFFFFFF

def _verify_header_byte(enc_header: bytes, pw_bytes: bytes, expect_last_byte: int) -> bool:
    """
    암호 후보에 대해 12바이트 암호화 헤더를 복호화하고
    마지막 검증 바이트가 기대값과 일치하는지 확인(조기 필터).
    """
    keys = _keys_init(pw_bytes)
    for i in range(12):
        c = enc_header[i]
        p = c ^ _decrypt_byte(keys)      # 복호화된 평문 바이트
        _update_keys(keys, p)
        if i == 11:
            return p == expect_last_byte
    return False

# =========================
# 워커(전수 탐색)
# =========================

def _worker(zip_bytes: bytes,
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
            t0_wall: float):
    """
    - 비번 생성: base-36 인덱스 → bytearray
    - 조기 필터: 12B 헤더 검증(대부분 탈락)
    - 확정 검증: zf.open(...).read(1)  (필터 통과한 극소수만)
    """
    name = mp.current_process().name
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))  # 1회 생성/재사용
    zopen = zf.open

    base = len(charset_bytes)  # 36
    buf = bytearray(pwd_len)
    ZipErrors = (RuntimeError, zipfile.BadZipFile, zlib.error)

    local_attempts = 0

    for idx in range(start_index, end_index):
        if is_found.value:
            break

        # idx → base-36 → buf(비밀번호)
        x = idx
        for j in range(pwd_len - 1, -1, -1):
            buf[j] = charset_bytes[x % base]
            x //= base

        # ---- 조기 필터 (헤더 검증) ----
        if not _verify_header_byte(enc_header, buf, expect_last_byte):
            local_attempts += 1
            if local_attempts % print_interval == 0:
                with attempts_shared.get_lock():
                    attempts_shared.value += local_attempts
                    total = attempts_shared.value
                    local_attempts = 0
                elapsed = time.time() - t0_wall
                rate = int(total / elapsed) if elapsed > 0 else 0
                print(f"🔍 [{name}] attempts={total:,} | elapsed={_format_hms(elapsed)} | ~{rate:,}/s")
            continue

        # ---- 최종 확인(1바이트 읽기) ----
        try:
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
                        print(f"\n✅ [{name}] SUCCESS: {pw} | attempts≈{total:,} | elapsed={_format_hms(elapsed)}")
            break
        except ZipErrors:
            # 이 경우는 헤더 필터가 우연히 통과(1/256)했지만 진짜 암호가 아님
            local_attempts += 1
            continue

    if local_attempts:
        with attempts_shared.get_lock():
            attempts_shared.value += local_attempts

# =========================
# 공개 API
# =========================

def unlock_zip(zip_path: str = "emergency_storage_key.zip",
               password_length: int = 6,
               process_count: int | None = None,
               print_interval: int = 500_000) -> str | None:
    """
    전수 탐색(찍기 X) + 헤더 조기 필터 적용.
    성공 시 password.txt / result.txt 저장.
    """
    t0 = time.time()
    start_human = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0))
    charset = (string.digits + string.ascii_lowercase).encode("ascii")

    # 1) ZIP 로드
    if not os.path.exists(zip_path):
        print(f"❌ ZIP 파일이 없습니다: {zip_path}")
        return None
    try:
        with open(zip_path, "rb") as f:
            zip_bytes = f.read()
    except Exception as e:
        print(f"❌ ZIP 파일 읽기 오류: {e}")
        return None

    # 2) 구조 파악 및 12B 헤더/검증 바이트 준비
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            names = z.namelist()
            if not names:
                print("❌ ZIP 내부에 파일이 없습니다.")
                return None
            target_file = names[0]
            zi = z.getinfo(target_file)
            encrypted = bool(zi.flag_bits & 0x1)
            # 기대 검증 바이트(데이터 디스크립터 bit=0x08 여부에 따라 CRC 또는 DOS time)
            if (zi.flag_bits & 0x08) != 0:
                expect_last = _dos_time_high_byte(zi.date_time)
            else:
                expect_last = (zi.CRC >> 24) & 0xFF
    except Exception as e:
        print(f"❌ ZIP 구조 분석 실패: {e}")
        return None

    try:
        enc_header = _extract_enc_header(zip_bytes, zi)
    except Exception as e:
        print(f"❌ 암호화 헤더 추출 실패: {e}")
        return None

    # 3) 실행 환경 안내
    base = len(charset)  # 36
    total = base ** password_length
    process_count = process_count or mp.cpu_count() or 4
    print("=" * 72)
    print("🚀 ZIP Password Cracker (계산/검증 최적화, 찍기 없음)")
    print(f"📁 ZIP Path     : {zip_path}")
    print(f"📄 Target File  : {target_file}")
    print(f"🔐 Encrypted    : {encrypted}")
    print(f"🕒 Start Time   : {start_human}")
    print(f"🧮 Keyspace     : {total:,} (36^{password_length})")
    print(f"🧵 Processes    : {process_count}")
    print("=" * 72)

    # 4) 공유 상태
    is_found = mp.Value(c_bool, False)
    attempts_shared = mp.Value(c_ulonglong, 0)
    result_buf = mp.Array(c_char, password_length)

    # 5) 분할 후 워커 실행
    ranges = _partition_ranges(total, process_count)
    procs: list[mp.Process] = []
    try:
        for i, (s, e) in enumerate(ranges, start=1):
            p = mp.Process(
                target=_worker,
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

    # 6) 완료 대기
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

    # 7) 결과 처리
    elapsed = time.time() - t0
    total_attempts = attempts_shared.value
    rate = int(total_attempts / elapsed) if elapsed > 0 else 0

    if is_found.value:
        password = bytes(result_buf[:]).decode("ascii", errors="ignore")
        print("=" * 72)
        print(f"✅ DONE: password={password} | attempts≈{total_attempts:,} | elapsed={_format_hms(elapsed)} | ~{rate:,}/s")
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
        print(f"😞 실패: 암호를 찾지 못했습니다. attempts≈{total_attempts:,} | elapsed={_format_hms(elapsed)} | ~{rate:,}/s")
        print("=" * 72)
        return None

# =========================
# 엔트리포인트
# =========================

def _main():
    if hasattr(mp, "set_start_method"):
        try:
            mp.set_start_method("fork")
        except Exception:
            pass  # Windows/macOS는 spawn 기본

    pc_env = os.environ.get("PROCESS_COUNT")
    try:
        pc = int(pc_env) if pc_env else None
    except Exception:
        pc = None

    unlock_zip(
        zip_path="emergency_storage_key.zip",
        password_length=6,
        process_count=pc,
        print_interval=500_000,
    )

if __name__ == "__main__":
    _main()
