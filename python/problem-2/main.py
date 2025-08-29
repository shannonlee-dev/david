import csv
from pathlib import Path
from typing import List, Dict
import sys

def read_mars_inventory(csv_path: Path)->List:
    """Mars_Base_Inventory_List.csv를 읽어서 리스트로 변환"""
    inventory_list = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            # CSV 내용 출력
            print(f"{'='*50}\n Mars_Base_Inventory_List.csv 내용\n{'='*50}\n")

            for line in f:
                print(line.strip())
            
            # Mars_Base_Inventory_List.csv의 내용을 읽어서 화면에 출력한다.
            f.seek(0)

            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                row['Flammability'] = float(row['Flammability'])
                inventory_list.append(row)

            print(f"list 객체 저장 완료: 총 {len(inventory_list)}개 항목")

    except FileNotFoundError:
        print("Mars_Base_Inventory_List.csv 파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {e}")
        return []
    
    return inventory_list

def sort_by_flammability(inventory_list):
    return sorted(inventory_list, key=lambda x: x['Flammability'], reverse=True)

def filter_dangerous_items(inventory_list):
    dangerous_items = [item for item in inventory_list if item['Flammability'] >= 0.7]
    
    print("\n=== 인화성 지수 0.7 이상인 위험 항목들 ===")
    for item in dangerous_items:
        print(f"물질: {item['Substance']}, 인화성 지수: {item['Flammability']}")
    
    return dangerous_items

def save_dangerous_items_csv(dangerous_items):
    if not dangerous_items:
        print("저장할 위험 항목이 없습니다.")
        return
    
    try:
        with open('Mars_Base_Inventory_danger.csv', 'w', newline='', encoding='utf-8') as file:
            fieldnames = dangerous_items[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(dangerous_items)
            
        print(f"\n위험 항목 {len(dangerous_items)}개가 Mars_Base_Inventory_danger.csv에 저장되었습니다.")
        
    except Exception as e:
        print(f"CSV 파일 저장 중 오류 발생: {e}")

def main():
    # 1. CSV 파일 읽기 및 리스트로 변환
    csv_path = Path('./mars_base/Mars_Base_Inventory_List.csv')
    inventory_list = read_mars_inventory(csv_path)
    
    if not inventory_list:
        return 1
    
    print(f"\n총 {len(inventory_list)}개의 항목을 읽었습니다.")
    
    # 2. 인화성 지수 기준으로 내림차순 정렬
    sorted_list = sort_by_flammability(inventory_list)
    print(f'{"="*60}\n인화성 지수 기준 내림차순 정렬 완료\n{"="*60}')
    
    # 3. 인화성 지수 0.7 이상인 항목 필터링
    dangerous_items = filter_dangerous_items(sorted_list)
    
    # 4. 위험 항목들을 CSV로 저장
    save_dangerous_items_csv(dangerous_items)

    return 0

if __name__ == "__main__":
    sys.exit(main())



