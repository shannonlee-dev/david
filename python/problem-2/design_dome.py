import math
import sys
from typing import Tuple
from scipy.constants import g

# 전역 변수들
material_name = ""
diameter_value = 0
thickness_value = 0
area_value = 0
weight_value = 0

# 재질별 밀도 (g/cm³)
MATERIAL_DENSITY = {
    '유리': 2.4,
    'glass': 2.4,
    '알루미늄': 2.7,
    'aluminum': 2.7,
    '탄소강': 7.85,
    'carbon_steel': 7.85
}

MARS_GRAVITY = 0.38

def sphere_area(diameter, material, thickness=1):

    global material_name, diameter_value, thickness_value, area_value, weight_value
            

    # 반구체 표면적 계산 (m²) - 1/2 * 4πr² = π/2 * d²
    surface_area = 1/2 * math.pi * diameter**2
    
    # 부피 계산 (m³) - (2/3)π(R³ - r³)
    thickness_m = thickness / 100  # cm를 m로 변환
    volume = 2/3 * math.pi * ((diameter/2)**3 - (diameter/2 - thickness_m)**3)

    # 부피를 cm³로 변환
    volume_cm3 = volume * (100 ** 3)
    
    # 질량 계산 (g)
    weight_g = volume_cm3 * MATERIAL_DENSITY[material]
    
    # g을 kg으로 변환
    weight_kg = weight_g / 1000
    
    # 지구에서의 무게 계산
    earth_weight_kg = weight_kg * g

    # 화성 중력 적용
    mars_weight_kg = earth_weight_kg * MARS_GRAVITY
    
    # 전역 변수에 저장
    material_name = material
    diameter_value = diameter
    thickness_value = thickness
    area_value = surface_area
    weight_value = mars_weight_kg


def get_user_input()-> Tuple[float, str]:
    while True:
        try:
            diameter = float(input("돔의 지름을 입력하세요 (m): ").strip())
            
            if diameter <= 0:
                print("지름은 0보다 큰 수여야 합니다.")
                continue
            
            # 재질 입력
            material_input = input("재질을 입력하세요 (유리/glass, 알루미늄/aluminum, 탄소강/carbon_steel): ").strip()

            material_lower = material_input.lower()
            valid_materials = ['유리', 'glass', '알루미늄', 'aluminum', '탄소강', 'carbon_steel']
            
            if material_input.lower() not in valid_materials:
                print("올바른 재질을 입력하세요. (유리, 알루미늄, 탄소강)\n입력된 지름이 초기화 됐습니다.")
                continue
            
            return diameter, material_input
            
        except ValueError:
            print("올바른 숫자를 입력하세요.")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            return None, None

def print_result():
    print(f'재질 ⇒ {material_name}, 지름 ⇒ {diameter_value}, 두께 ⇒ {thickness_value}, 면적 ⇒ {area_value:.3f}, 무게 ⇒ {weight_value:.3f} N')

def main():
    print('''=== Mars 돔 구조물 설계 프로그램 ===
지원 재질: 유리(glass), 알루미늄(aluminum), 탄소강(carbon_steel)
종료하려면 Ctrl+C를 누르세요.''')
    
    while True:
        try:
            diameter, material = get_user_input()
            if diameter is None or material is None:
                break
            sphere_area(diameter, material, thickness=1)
            # 결과 출력
            print('\n=== 계산 결과 ===')
            print_result()

            continue_choice = input('다른 돔을 계산하시겠습니까? (y/n): ').strip().lower()
            if continue_choice not in ['y', 'yes', 'ㅇ', 'yup']:
                break
                
        except ValueError as e:
            print(f"입력 오류: {e}")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"예상치 못한 오류가 발생했습니다: {e}")
    
    print("프로그램이 종료되었습니다.")

if __name__ == "__main__":
    main()