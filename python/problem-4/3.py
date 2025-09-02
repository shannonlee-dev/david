import io
import zipfile
import time
import zlib
from itertools import product
from multiprocessing import Process, Value, Lock, Array, current_process
import os


def try_passwords(zip_binary, target_file, charset, length, prefix_group, is_found, result_holder, lock):
    """
    각 프로세스에서 비밀번호 조합을 시도해보는 함수입니다.
    prefix_group에 해당하는 접두어들만 담당하며, 멀티프로세싱 환경에서 작동합니다.
    """
    zip_data = io.BytesIO(zip_binary)
    zip_obj = zipfile.ZipFile(zip_data)
    start_time = time.time()
    attempts = 0

    for prefix in prefix_group:
        if is_found.value:
            return  # 다른 프로세스에서 이미 찾았으면 종료

        # prefix 이후 뒷자리를 조합해서 전체 비밀번호 구성
        for tail in product(charset, repeat=length - 1):
            if is_found.value:
                return  # 중간에라도 다른 프로세스가 찾았으면 바로 중단

            password = prefix + ''.join(tail)
            attempts += 1

            try:
                # 전체 압축을 푸는 대신, 파일 일부만 읽어서 비밀번호 확인
                data = zip_obj.open(target_file, pwd=password.encode('utf-8')).read(1)
                if data:
                    with lock:
                        # 다시 확인한 후 비밀번호 저장
                        if not is_found.value:
                            is_found.value = True
                            result_holder.value = password.encode('utf-8')
                            elapsed = time.time() - start_time
                            print(f'\n✅ [성공] 비밀번호: {password}')
                            print(f'⏱️ 경과 시간: {elapsed:.2f}초')
                    return
            except (RuntimeError, zipfile.BadZipFile, zlib.error):
                # 비밀번호가 틀렸거나 압축이 깨졌을 경우 그냥 넘어감
                pass

            # 진행 상황 출력 (10만 회마다)
            if attempts % 100000 == 0:
                elapsed = time.time() - start_time
                print(f'[{current_process().name}] {attempts}회 시도 중... {elapsed:.1f}s 경과')


def unlock_zip_password(zip_path: str, length: int = 6, process_count: int = 4) -> str | None:
    """
    여러 프로세스를 사용해 ZIP 파일의 비밀번호를 브루트포스로 찾아내는 함수입니다.
    """
    charset = 'abcdefghijklmnopqrstuvwxyz0123456789'  # 소문자 + 숫자 조합

    # zip 파일 전체를 메모리에 올려서 빠르게 접근할 수 있도록 처리
    with open(zip_path, 'rb') as f:
        zip_bytes = f.read()

    # 테스트할 파일은 압축 파일 내 첫 번째 파일로 지정
    zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))
    file_to_test = zip_file.namelist()[0]

    # 접두어를 나눠서 각 프로세스가 맡을 부분 정함
    prefixes = list(charset)
    step = len(prefixes) // process_count
    chunks = [prefixes[i * step: (i + 1) * step] for i in range(process_count - 1)]
    chunks.append(prefixes[(process_count - 1) * step:])  # 마지막은 남은 문자 전부

    # 공통 데이터 구조 (공유 변수, 락)
    is_found = Value('b', False)          # 비밀번호를 찾았는지 여부
    result_holder = Array('c', 7)         # 비밀번호 저장용 배열 (최대 6자리 + null)
    lock = Lock()                         # 동기화용 락

    # 각 프로세스 실행
    processes = []
    for i in range(process_count):
        p = Process(
            target=try_passwords,
            args=(zip_bytes, file_to_test, charset, length, chunks[i], is_found, result_holder, lock),
            name=f"P{i + 1}"
        )
        processes.append(p)
        p.start()

    # 모든 프로세스가 종료될 때까지 대기
    for p in processes:
        p.join()

    # 결과 반환
    if is_found.value:
        return result_holder.value.decode('utf-8')
    else:
        print('❌ 비밀번호를 찾지 못했습니다.')
        return None


if __name__ == '__main__':
    # ZIP 파일 경로 설정 (과제 기준 파일명)
    zip_path = './emergency_storage_key.zip'

    # CPU 코어 수에 따라 병렬 프로세스 수 결정
    password = unlock_zip_password(zip_path, process_count=os.cpu_count() or 4)

    if password:
        # 찾은 비밀번호를 파일로 저장
        with open('password.txt', 'w') as f:
            f.write(password)