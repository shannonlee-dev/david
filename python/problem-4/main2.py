#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
문제 1. 비밀번호 찾기 (보너스 포함)
- emergency_storage_key.zip 의 암호(숫자+소문자, 6자리)를 브루트포스로 해제
- 진행 상황(시작 시간, 시도 횟수, 경과 시간)을 지속 출력
- 성공 시 암호를 password.txt, result.txt 에 저장
- 표준 라이브러리만 사용(압축은 zipfile 사용 허용)
"""

import io
import os
import time
import string
import zipfile
import zlib
import multiprocessing as mp
from ctypes import c_bool, c_ulonglong, c_char


# -----------------------------
# 내부 유틸
# -----------------------------
def _format_hms(seconds: float) -> str:
    s = int(seconds)
    h, r = divmod(s, 3600)
    m, r = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{r:02d}"


def _partition_ranges(total: int, parts: int):
    """총 total 개의 인덱스를 parts개 구간으로 균등 분할"""
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


# -----------------------------
# 워커(보너스: 순수 속도 최적화 적용)
#  - ZipFile, BytesIO는 프로세스 시작 시 1회 생성 후 재사용
#  - 비밀번호는 bytearray 버퍼에 직접 구성
#  - 시도/초당 출력 최소화를 위해 print_interval 사용
# -----------------------------
def _worker(zip_bytes,
            filename: str,
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
    zip_bytes      : ZIP 파일 원본 바이트
    filename       : ZIP 내 대상 파일명 (첫 번째 파일)
    charset_bytes  : b'0123456789abcdefghijklmnopqrstuvwxyz'
    pwd_len        : 6
    start_index    : 시작 키 인덱스(포함)
    end_index      : 끝 키 인덱스(제외)
    is_found       : multiprocessing.Value(c_bool)
    result_buf     : multiprocessing.Array(c_char, pwd_len)
    attempts_shared: multiprocessing.Value(c_ulonglong) - 전체 누적 시도
    print_interval : 진행 출력 주기(시도 수)
    t0_wall        : 전체 시작 시간(epoch)
    """
    name = mp.current_process().name

    # 프로세스 로컬 준비(재사용)
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    zopen = zf.open
    base = len(charset_bytes)
    buf = bytearray(pwd_len)
    ZipErrors = (RuntimeError, zipfile.BadZipFile, zlib.error)

    local_attempts = 0

    for idx in range(start_index, end_index):
        if is_found.value:
            break

        # idx → base-N → buf 채우기 (오른쪽 자릿수부터)
        x = idx
        for j in range(pwd_len - 1, -1, -1):
            buf[j] = charset_bytes[x % base]
            x //= base

        try:
            # 최소 바이트만 읽어서 빠르게 검증
            with zopen(filename, pwd=bytes(buf)) as f:
                f.read(1)

            # 성공 처리(경쟁 방지)
            if not is_found.value:
                with is_found.get_lock():
                    if not is_found.value:
                        is_found.value = True
                        result_buf[:pwd_len] = bytes(buf)

                        # 남은 로컬 시도 누적 반영
                        if local_attempts:
                            with attempts_shared.get_lock():
                                attempts_shared.value += local_attempts
                                local_attempts = 0

                        elapsed = time.time() - t0_wall
                        total_attempts = attempts_shared.value
                        pw = bytes(buf).decode('ascii')
                        print(f"\n✅ [{name}] SUCCESS: password={pw} | attempts≈{total_attempts:,} | elapsed={_format_hms(elapsed)}")
            break

        except ZipErrors:
            pass

        local_attempts += 1

        # 진행 상황 출력(간헐적으로만)
        if local_attempts % print_interval == 0:
            with attempts_shared.get_lock():
                attempts_shared.value += local_attempts
                total_attempts = attempts_shared.value
                local_attempts = 0

            elapsed = time.time() - t0_wall
            rate = int(total_attempts / elapsed) if elapsed > 0 else 0
            sample = bytes(buf).decode('ascii')
            print(f"🔍 [{name}] last={sample} | attempts={total_attempts:,} | elapsed={_format_hms(elapsed)} | ~{rate:,}/s")

    # 루프 종료 시 남은 로컬 시도 반영
    if local_attempts:
        with attempts_shared.get_lock():
            attempts_shared.value += local_attempts


# -----------------------------
# 공개 API
# -----------------------------
def unlock_zip(zip_path: str = "emergency_storage_key.zip",
               password_length: int = 6,
               process_count: int | None = None,
               print_interval: int = 500_000) -> str | None:
    """
    ZIP(전통 암호)을 브루트포스로 해제.
    - 암호는 숫자+소문자 6자리 가정
    - 진행 상황을 주기적으로 출력
    - 성공 시 password.txt, result.txt 저장
    """
    t0_wall = time.time()
    start_human = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0_wall))
    charset = (string.digits + string.ascii_lowercase).encode("ascii")

    # 1) ZIP 로드 및 대상 파일 파악
    if not os.path.exists(zip_path):
        print(f"❌ ZIP 파일을 찾을 수 없습니다: {zip_path}")
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
            # 암호화 여부 간단 안내
            info = z.getinfo(target_file)
            encrypted = bool(info.flag_bits & 0x1)
    except Exception as e:
        print(f"❌ ZIP 구조 분석 실패: {e}")
        return None

    base = len(charset)  # 36
    total = base ** password_length

    # 2) 실행 환경 안내
    process_count = process_count or mp.cpu_count() or 4
    print("=" * 72)
    print("🚀 ZIP Password Cracker (digits+lowercase, length=6)")
    print(f"📁 ZIP Path     : {zip_path}")
    print(f"📄 Target File  : {target_file}")
    print(f"🔐 Encrypted    : {encrypted}")
    print(f"🕒 Start Time   : {start_human}")
    print(f"🧮 Keyspace     : {total:,} (36^{password_length})")
    print(f"🧵 Processes    : {process_count}")
    print("=" * 72)

    # 3) 멀티프로세싱 공유 객체
    is_found = mp.Value(c_bool, False)
    attempts_shared = mp.Value(c_ulonglong, 0)
    result_buf = mp.Array(c_char, password_length)  # 정확히 6바이트만 저장

    # 4) 인덱스 범위 분할
    ranges = _partition_ranges(total, process_count)

    # 5) 워커 시작
    procs: list[mp.Process] = []
    try:
        for i, (s, e) in enumerate(ranges, start=1):
            p = mp.Process(
                target=_worker,
                name=f"W{i}",
                args=(
                    zip_bytes,
                    target_file,
                    charset,
                    password_length,
                    s,
                    e,
                    is_found,
                    result_buf,
                    attempts_shared,
                    print_interval,
                    t0_wall,
                ),
                daemon=False,
            )
            p.start()
            procs.append(p)
            print(f"▶️  [W{i}] range={s:,} ~ {e:,}  (size={e - s:,})")
    except Exception as e:
        print(f"❌ 프로세스 시작 실패: {e}")
        # 안전 종료
        for p in procs:
            if p.is_alive():
                p.terminate()
        return None

    # 6) 완료 대기
    try:
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        print("\n🛑 사용자 중단 요청: 작업을 종료합니다.")
        is_found.value = True
        for p in procs:
            if p.is_alive():
                p.terminate()
                p.join()

    # 7) 결과 처리
    elapsed = time.time() - t0_wall
    total_attempts = attempts_shared.value
    rate = int(total_attempts / elapsed) if elapsed > 0 else 0

    if is_found.value:
        password = bytes(result_buf[:]).decode("ascii", errors="ignore")
        print("=" * 72)
        print(f"✅ DONE: password={password} | attempts≈{total_attempts:,} | elapsed={_format_hms(elapsed)} | ~{rate:,}/s")
        print("=" * 72)

        # 파일 저장(요구사항: password.txt, result.txt)
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


# -----------------------------
# 스크립트 엔트리포인트
# -----------------------------
def _main():
    # Linux/Unix에선 fork가 메모리 효율적(COW). Windows/Mac은 기본 spawn.
    if hasattr(mp, "set_start_method"):
        try:
            mp.set_start_method("fork")
        except Exception:
            # Windows/macOS(파이썬 최신)에서는 fork가 없거나 제한될 수 있음 → 무시
            pass

    # 환경변수로 프로세스 수 조정 가능 (예: PROCESS_COUNT=6)
    pc_env = os.environ.get("PROCESS_COUNT")
    try:
        pc = int(pc_env) if pc_env else None
    except Exception:
        pc = None

    # 기본 실행(과제의 기본 파일명/길이 요구사항 준수)
    unlock_zip(
        zip_path="emergency_storage_key.zip",
        password_length=6,
        process_count=pc,
        print_interval=500_000,  # 필요 시 100k~1M 사이로 조정 가능
    )


if __name__ == "__main__":
    _main()
