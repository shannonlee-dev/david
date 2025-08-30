import numpy as np
import csv
from pathlib import Path
import sys
from typing import Tuple

def read_csv_to_numpy(filename:Path) -> np.ndarray:
    """CSV 파일을 읽어서 구조화된 NumPy 배열로 변환"""
    try:
        # 구조화된 배열로 읽기 (첫 번째 열은 문자열, 나머지는 숫자)
        data = np.genfromtxt(filename, delimiter = ',', skip_header = 1 , 
                           dtype = [('parts', 'U10'), ('strength', 'i4')] , encoding = 'utf-8')
        
        print(f"{filename} 읽기 완료: {len(data)}행")
        
        # 샘플 데이터 출력
        if len(data) > 0:
            print(f"열 이름: {data.dtype.names}")
            print(f"샘플 데이터: {data[:3] if len(data) >= 3 else data}")
        
        return data
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {filename}")
        return None
    except Exception as e:
        print(f"{filename} 읽기 중 오류 발생: {e}")


def merge_structured_arrays(arr1, arr2, arr3):

    if arr1 is None or arr2 is None or arr3 is None:
        print("일부 배열이 None입니다. 병합할 수 없습니다.")
        return None
    
    try:
        merged = np.concatenate((arr1, arr2, arr3), axis=0)
        print(f"배열 병합 완료: {len(merged)}행")
        return merged
    
    except Exception as e:
        print(f"배열 병합 중 오류 발생: {e}")
        return None

def calculate_item_averages(integrated_csv:np.ndarray)->Tuple:
    """각 부품 항목별 평균 강도값 계산"""
    if integrated_csv is None:
        return None
    
    try:
        # 부품명과 강도값 추출
        part_names = integrated_csv['parts']
        strength_values = integrated_csv['strength']

        unique_part_names = np.unique(part_names)

        item_averages = []
        
        print(f"\n=== 항목별 평균값 계산 ===")
        for part in unique_part_names:

            mask = part_names == part
            part_strengths = strength_values[mask]
            avg_strength = np.mean(part_strengths)
            
            item_averages.append((part, avg_strength))
            print(f"{part}: {avg_strength:.2f} (샘플 수: {len(part_strengths)})")
        
        # 부품명과 평균값을 각각 배열로 반환
        part_names_avg = np.array([x[0] for x in item_averages])
        mean_strengths = np.array([x[1] for x in item_averages])
        return part_names_avg, mean_strengths
        
    except Exception as e:
        print(f"항목별 평균값 계산 중 오류 발생: {e}")
        return None

def filter_low_average_items(part_names_avg,mean_strengths):

    if part_names_avg is None or mean_strengths is None:
        return None
    
    mask = mean_strengths < 50

    filtered_parts = part_names_avg[mask]

    filtered_strengths = mean_strengths[mask]

    print(f"\n=== 평균 강도 50보다 작은 항목 필터링 결과 ===")
    print(f"필터링된 항목 수: {len(filtered_parts)}")

    return filtered_parts, np.round(filtered_strengths,3)
    
def save_structured_array_to_csv(data, filename):

    if data is None or len(data) == 0:
        print("저장할 데이터가 없습니다.")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            headers = list(data.dtype.names)
            writer.writerow(headers)

            for r in data:
                row = [str(field) for field in r]
                writer.writerow(row)
        
        print(f"\n데이터가 {filename}에 저장되었습니다. ({len(data)}행)")
        return True
        
    except Exception as e:
        print(f"CSV 파일 저장 중 오류 발생: {e}")
        return False

def main():
    print("=== Mars 부품 데이터 통합 분석 ===")
    
    # 1. 세 개의 CSV 파일을 구조화된 NumPy 배열로 읽기
    print("\n1단계: CSV 파일들을 구조화된 NumPy 배열로 읽기")
    arr1 = read_csv_to_numpy(Path('./mars_base/mars_base_main_parts-001.csv'))
    arr2 = read_csv_to_numpy(Path('./mars_base/mars_base_main_parts-002.csv'))
    arr3 = read_csv_to_numpy(Path('./mars_base/mars_base_main_parts-003.csv'))
    
    # 2. 세 배열을 병합하여 parts 배열 생성
    print("\n2단계: 배열들을 병합하여 parts 배열 생성")
    parts = merge_structured_arrays(arr1, arr2, arr3)
    
    if parts is None:
        print("배열 병합에 실패했습니다. 프로그램을 종료합니다.")
        return 1

    # 3. 강도값(두 번째 열)의 통계 계산
    print("\n3단계: 강도값 통계 계산")
    part_names_avg, mean_strengths = calculate_item_averages(parts)

    # 4. 평균값이 50보다 작은 항목만 필터링
    print("\n4단계: 강도 50보다 작은 항목 필터링")
    filtered_parts, filtered_strengths = filter_low_average_items(part_names_avg, mean_strengths)

    if filtered_parts is None:
        print("필터링 중 오류가 발생했습니다.")
        return 1

    if len(filtered_parts) == 0:
        print("필터링할 항목이 없습니다.")
        return 0

    # 5. 필터링된 데이터를 CSV로 저장 (예외 처리 포함)
    print("\n5단계: parts_to_work_on.csv로 저장")

    save_array = np.array(list(zip(filtered_parts, filtered_strengths)), dtype=[('parts', 'U50'), ('avg_strength', 'f8')])
    success = save_structured_array_to_csv(save_array, 'parts_to_work_on.csv')

    if success:
        print("Mars 부품 데이터 분석이 완료되었습니다!")
        return 0
    else:
        print("파일 저장에 실패했습니다.")
        return 1

if __name__ == "__main__":
    sys.exit(main())