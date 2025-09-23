#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
#  door_hacking_clean.py — ZIP 브루트포스 + 카이사르 암호 해독
# ============================================================

import io
import multiprocessing as mp
import os
import string
import struct
import time
import zipfile
from dataclasses import dataclass
from typing import Optional, List, Tuple
from multiprocessing import shared_memory

ALPHABET = string.ascii_lowercase + string.digits
DEFAULT_ZIP = "emergency_storage_key.zip"


def hms(sec: float) -> str:
    sec = int(sec)
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def log(msg: str) -> None:
    print(msg, flush=True)


# -------------------------------
# 카이사르 암호
# -------------------------------
def caesar_cipher_decode(target_text: str) -> None:
    for shift in range(26):
        decoded = ''.join(
            chr((ord(ch) - ord('A' if ch.isupper() else 'a') + shift) % 26 + ord('A' if ch.isupper() else 'a'))
            if ch.isalpha() else ch
            for ch in target_text
        )
        print(f"{shift+1:2d}. {decoded}")


def choose_answer(target_text: str) -> str:
    while True:
        try:
            idx = int(input("줄 번호를 입력하시면, 암호해독결과가 저장됩니다 (1-26): ").strip()) - 1
            if 0 <= idx < 26:
                result = ''.join(
                    chr((ord(ch) - ord('A' if ch.isupper() else 'a') + idx) % 26 + ord('A' if ch.isupper() else 'a'))
                    if ch.isalpha() else ch
                    for ch in target_text
                )
                print(f"\n선택된 해독 결과: {result}")
                return result
            print("1부터 26 사이의 번호를 입력하세요.")
        except ValueError:
            print("올바른 숫자를 입력하세요.")
        except KeyboardInterrupt:
            print("\n사용자 중단.")
            return ""


def save_text(path: str, text: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{path} 에 저장했습니다.")
    except Exception as e:
        print(f"{path} 저장 실패: {e}")


# -------------------------------
# ZIP 해제
# -------------------------------
@dataclass
class ZipTargetInfo:
    name: str
    size: int
    method: int
    flag_bits: int

def _pick_encrypted_member(zf):
    candidates = [info for info in zf.infolist() if (info.flag_bits & 0x1) and (info.file_size > 0)]
    if not candidates:
        return None
    target = min(candidates, key=lambda i: i.file_size)
    return ZipTargetInfo(target.filename, target.file_size, target.compress_type, target.flag_bits)



def _extract_enc_header_and_expected(zip_path: str) -> Tuple:
    
    
    try:
        with open(zip_path, "rb") as f:
            data = f.read()
            actual_offset = data.find(b'PK\x03\x04')
            if actual_offset == -1 or actual_offset + 30 > len(data):
                return None, None
                
            f.seek(actual_offset)
            local_hdr = f.read(30)
            sig, version, flag_bits, method, mtime, mdate, crc32, comp_size, uncomp_size, fnlen, exlen = struct.unpack("<IHHHHHLLLHH", local_hdr)
            
            if sig != 0x04034B50:
                return None, None
                
            enc_off = actual_offset + 30 + fnlen + exlen
            if enc_off + 12 > len(data):
                return None, None
                
            f.seek(enc_off)
            enc12 = f.read(12)
            expected = (mtime >> 8) & 0xFF if flag_bits & 0x0008 else (crc32 >> 24) & 0xFF
            return enc12, expected
    except Exception:
        return None, None


def _crc32_table() -> List[int]:
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = 0xEDB88320 ^ (c >> 1) if c & 1 else c >> 1
        table.append(c)
    return table

_CRC32_TAB = _crc32_table()

def _crc32_update(crc: int, b: int) -> int:
    return ((crc >> 8) ^ _CRC32_TAB[(crc ^ b) & 0xFF]) & 0xFFFFFFFF

def _keys_init():
    return 0x12345678, 0x23456789, 0x34567890

def _keys_update(k0: int, k1: int, k2: int, c: int):
    k0 = _crc32_update(k0, c)
    k1 = (k1 + (k0 & 0xFF)) & 0xFFFFFFFF
    k1 = (k1 * 134775813 + 1) & 0xFFFFFFFF
    k2 = _crc32_update(k2, (k1 >> 24) & 0xFF)
    return k0, k1, k2

def _decrypt_byte(k2: int) -> int:
    temp = (k2 | 3) & 0xFFFFFFFF
    return ((temp * (temp ^ 1)) >> 8) & 0xFF

def _header_prefilter(pwd: str, enc12: bytes, expected_check: int) -> bool:
    k0, k1, k2 = _keys_init()
    for ch in pwd.encode('utf-8'):
        k0, k1, k2 = _keys_update(k0, k1, k2, ch)
    for c in enc12:
        kb = _decrypt_byte(k2)
        p = c ^ kb
        k0, k1, k2 = _keys_update(k0, k1, k2, p)
        last_plain = p
    return last_plain == expected_check


def _worker_try_passwords(worker_id: int, total_workers: int, length: int, alphabet: str,
                          shm_name: Optional[str], enc_header_12: Optional[bytes], expected_check: Optional[int],
                          start_time: float, found_event, result_queue, member_name: Optional[str]) -> None:
    zf, shm = None, None
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
        zf = zipfile.ZipFile(io.BytesIO(shm.buf), 'r')
    
        if member_name is None:
            result_queue.put("")
            found_event.set()
            return

        attempt_local, base, number_cases = 0, len(alphabet), len(alphabet) ** length
        idx = worker_id
        
        while idx < number_cases and not found_event.is_set():
            x, chars = idx, []
            for _ in range(length):
                x, r = divmod(x, base)
                chars.append(alphabet[r])
            pwd = ''.join(reversed(chars))
            attempt_local += 1

            if attempt_local % 100000 == 0:  # 여기서 출력 회수 조정
                elapsed = time.time() - start_time
                log(f"[워커 {worker_id}] 시도: {attempt_local:,}개 | 현재 암호: {pwd} | 경과: {hms(elapsed)}")

            try:
                if enc_header_12 is not None and expected_check is not None:
                    if not _header_prefilter(pwd, enc_header_12, expected_check):
                        idx += total_workers
                        continue

                zf.setpassword(pwd.encode('utf-8')) # 비밀번호을 기어코 찾아냈다면 이 줄이 실행.
                with zf.open(member_name, 'r') as f:
                    _ = f.read(1)
                result_queue.put(pwd)
                found_event.set()
                return
            except Exception:
                pass
            idx += total_workers
    finally:
        if zf: zf.close()
        if shm: shm.close()


def unlock_zip(zip_path: str, length: int, alphabet: str, processes: int):
    start = time.time()
    
    print('=' * 60)
    print(f" zip 해제 시작: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"ZIP: {zip_path}")
    print(f"길이: {length}, (경우의 수: {len(alphabet) ** length:,})")
    print(f"옵션 - 프로세스: {processes}")
    print('=' * 60)

    if not os.path.exists(zip_path):
        print(f"오류: ZIP 파일을 찾을 수 없습니다: {zip_path}")
        return None

    shm_obj = None
    use_shared_memory = True

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf0:
            info = _pick_encrypted_member(zf0)
            if info is None:
                print("암호화된 멤버가 없습니다.")
                return ""
            
            print(f"검증 타겟 멤버: '{info.name}' (size={info.size}, method={info.method}, flag=0x{info.flag_bits:04x})")
            
            if info.method == 99:  # AES(WinZip AES 등)**은 전통 ZipCrypto와 구조가 달라서, 여기 프리필터(12바이트) 기법을 적용할 수 없다.
                return None
            
            enc12, expected = _extract_enc_header_and_expected(zip_path)
            
            print(f"헤더-프리필터 적용 (체크 바이트: 0x{expected:02x})")

        if use_shared_memory:
            with open(zip_path, "rb") as f:
                zbytes = f.read()
            shm_obj = shared_memory.SharedMemory(create=True, size=len(zbytes))
            shm_obj.buf[:len(zbytes)] = zbytes
            print(f"공유 메모리 사용: name={shm_obj.name}, size={len(zbytes):,} bytes")

        found_event, result_queue = mp.Event(), mp.Queue()

        workers = []
        for id in range(processes):
            p = mp.Process(target=_worker_try_passwords,
                          args=(id, processes, length, alphabet, shm_obj.name,
                                enc12 , expected,start, found_event, result_queue, info.name))
            p.daemon = True
            p.start()
            workers.append(p)

        password = None

        while any(p.is_alive() for p in workers):
            try:
                password = result_queue.get(timeout=0.5)
                if password is not None:
                    break
            except Exception:
                pass

        found_event.set()

        for p in workers:
            p.join(timeout=1.0)

        elapsed = time.time() - start

        if password is None:
            print("암호를 찾지 못했습니다.")
            return None

        print('\n' + '=' * 60)
        print("암호 해독 성공!")
        print(f"암호: {password}")
        print(f"총 경과 시간: {hms(elapsed)}")
        print('=' * 60)

        with open("password.txt", "w", encoding="utf-8") as f:
            f.write(password)
        print("암호를 password.txt 파일에 저장했습니다.")
        return password

    finally:
        if shm_obj:
            shm_obj.close()
            shm_obj.unlink()


def run_caesar(zip_path: str = DEFAULT_ZIP, recovered_password: Optional[str] = None) -> None:
    target_text = None

    if os.path.exists("password.txt"):
        try:
            with open("password.txt", "r", encoding="utf-8") as f:
                target_text = f.read().strip()
            print("로컬 password.txt 를 읽었습니다.")
        except Exception as e:
            print(f"로컬 password.txt 읽기 실패: {e}")

    if target_text is None and recovered_password is not None:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.setpassword(recovered_password.encode('utf-8'))
                try:
                    data = zf.read('password.txt')
                    target_text = data.decode('utf-8', errors='replace').strip()
                    print("ZIP 내부의 password.txt 를 읽었습니다.")
                except KeyError:
                    print("ZIP 내부에 password.txt 가 없습니다.")
        except Exception as e:
            print(f"ZIP password.txt 읽기 실패: {e}")

    if target_text is None:
        print("카이사르 해독 대상 텍스트를 찾지 못했습니다.")
        return

    print("\n" + "=" * 60)
    print("카이사르 암호 해독 단계")
    print("=" * 60)
    caesar_cipher_decode(target_text)
    print("출력된 문자열 중 올바른 문장을 찾으세요.")
    chosen = choose_answer(target_text)
    if chosen:
        save_text("result.txt", chosen)


def main():
    recovered = unlock_zip(zip_path=DEFAULT_ZIP, length=6, alphabet=ALPHABET,
                          processes=os.cpu_count())
    run_caesar(DEFAULT_ZIP, recovered)


if __name__ == "__main__":
    mp.freeze_support()
    main()