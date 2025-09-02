#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZIP 파일 암호 해독 및 카이사르 암호 해독 프로그램
PEP 8 스타일 가이드를 준수하여 작성
"""

import zipfile
import time
import itertools
import string
import os


def unlock_zip():
    """
    emergency_storage_key.zip 파일의 암호를 해독하는 함수
    6자리 숫자와 소문자 알파벳으로 구성된 암호를 브루트포스로 찾음
    """
    zip_filename = 'emergency_storage_key.zip'
    
    # ZIP 파일 존재 확인
    try:
        if not os.path.exists(zip_filename):
            print(f'오류: {zip_filename} 파일을 찾을 수 없습니다.')
            return None
    except Exception as e:
        print(f'파일 확인 중 오류 발생: {e}')
        return None
    
    # 가능한 문자들 (숫자 + 소문자 알파벳)
    chars = string.digits + string.ascii_lowercase
    password_length = 6
    
    print(f'ZIP 파일 암호 해독 시작: {zip_filename}')
    print(f'암호 길이: {password_length}자리')
    print(f'사용 가능한 문자: {chars}')
    print(f'총 가능한 조합 수: {len(chars)**password_length:,}개')
    print('-' * 50)
    
    start_time = time.time()
    attempt_count = 0
    
    try:
        # 모든 가능한 조합을 시도
        for password_tuple in itertools.product(chars, repeat=password_length):
            password = ''.join(password_tuple)
            attempt_count += 1
            
            # 진행 상황 출력 (1000번마다)
            if attempt_count % 1000 == 0:
                elapsed_time = time.time() - start_time
                print(f'시도 횟수: {attempt_count:,}, 현재 암호: {password}, '
                      f'경과 시간: {elapsed_time:.2f}초')
            
            try:
                with zipfile.ZipFile(zip_filename, 'r') as zip_file:
                    # 암호로 ZIP 파일 테스트
                    zip_file.testzip()
                    zip_file.setpassword(password.encode('utf-8'))
                    
                    # 첫 번째 파일을 읽어보기 시도
                    file_list = zip_file.namelist()
                    if file_list:
                        zip_file.read(file_list[0])
                        
                        # 성공시 결과 출력 및 저장
                        end_time = time.time()
                        total_time = end_time - start_time
                        
                        print('\n' + '=' * 50)
                        print('암호 해독 성공!')
                        print(f'찾은 암호: {password}')
                        print(f'총 시도 횟수: {attempt_count:,}')
                        print(f'총 소요 시간: {total_time:.2f}초')
                        print('=' * 50)
                        
                        # 암호를 password.txt 파일로 저장
                        try:
                            with open('password.txt', 'w', encoding='utf-8') as f:
                                f.write(password)
                            print('암호가 password.txt 파일에 저장되었습니다.')
                        except Exception as e:
                            print(f'password.txt 저장 중 오류: {e}')
                        
                        return password
                        
            except (zipfile.BadZipFile, RuntimeError):
                # 잘못된 암호인 경우 계속 진행
                continue
            except Exception as e:
                print(f'ZIP 파일 처리 중 오류: {e}')
                continue
                
    except KeyboardInterrupt:
        print('\n사용자에 의해 중단되었습니다.')
        return None
    except Exception as e:
        print(f'암호 해독 중 오류 발생: {e}')
        return None
    
    print('\n암호를 찾지 못했습니다.')
    return None


def caesar_cipher_decode(target_text):
    """
    카이사르 암호를 해독하는 함수
    
    Args:
        target_text (str): 해독할 텍스트
    """
    print(f'카이사르 암호 해독 시작: "{target_text}"')
    print('-' * 50)
    
    # 알파벳 26개 자리수로 시도
    for shift in range(26):
        decoded_text = ''
        
        for char in target_text:
            if char.isalpha():
                # 대문자 처리
                if char.isupper():
                    decoded_char = chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
                # 소문자 처리
                else:
                    decoded_char = chr((ord(char) - ord('a') + shift) % 26 + ord('a'))
                decoded_text += decoded_char
            else:
                # 알파벳이 아닌 문자는 그대로 유지
                decoded_text += char
        
        print(f'자리수 {shift:2d}: {decoded_text}')
    
    print('-' * 50)
    
    # 사용자가 올바른 해독 결과를 선택할 수 있도록 함
    while True:
        try:
            choice = input('올바른 해독 결과의 자리수를 입력하세요 (0-25): ')
            shift_num = int(choice)
            
            if 0 <= shift_num <= 25:
                # 선택된 자리수로 최종 해독
                final_decoded = ''
                for char in target_text:
                    if char.isalpha():
                        if char.isupper():
                            decoded_char = chr((ord(char) - ord('A') + shift_num) % 26 + ord('A'))
                        else:
                            decoded_char = chr((ord(char) - ord('a') + shift_num) % 26 + ord('a'))
                        final_decoded += decoded_char
                    else:
                        final_decoded += char
                
                print(f'\n선택된 해독 결과: {final_decoded}')
                
                # result.txt에 저장
                try:
                    with open('result.txt', 'w', encoding='utf-8') as f:
                        f.write(final_decoded)
                    print('해독 결과가 result.txt 파일에 저장되었습니다.')
                except Exception as e:
                    print(f'result.txt 저장 중 오류: {e}')
                
                return final_decoded
            else:
                print('0부터 25 사이의 숫자를 입력해주세요.')
        except ValueError:
            print('올바른 숫자를 입력해주세요.')
        except KeyboardInterrupt:
            print('\n프로그램을 종료합니다.')
            return None


def main():
    """메인 함수"""
    print('=' * 60)
    print('비밀번호 해독 및 카이사르 암호 해독 프로그램')
    print('=' * 60)
    
    # 1단계: ZIP 파일 암호 해독
    print('\n[1단계] ZIP 파일 암호 해독')
    password = unlock_zip()
    
    if password is None:
        print('ZIP 파일 암호 해독에 실패했습니다.')
        return
    
    # 2단계: password.txt 파일 읽기 및 카이사르 암호 해독ㄴ
    print('\n[2단계] 카이사르 암호 해독')
    try:
        with open('password.txt', 'r', encoding='utf-8') as f:
            password_text = f.read().strip()
        
        print(f'password.txt에서 읽은 내용: {password_text}')
        caesar_cipher_decode(password_text)
        
    except FileNotFoundError:
        print('password.txt 파일을 찾을 수 없습니다.')
    except Exception as e:
        print(f'password.txt 읽기 중 오류: {e}')


if __name__ == '__main__':
    main()