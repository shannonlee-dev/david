import random
import json
import time
import platform
import psutil
import threading
import multiprocessing
import sys
from datetime import datetime

def wait_for_quit():
    global stop_flag
    while not stop_flag:
        user_input = input()
        if user_input.lower() == 'q':
            stop_flag = True
            print("System stoped….")
            break


class DummySensor:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': 0,
            'mars_base_external_temperature': 0,
            'mars_base_internal_humidity': 0,
            'mars_base_external_illuminance': 0,
            'mars_base_internal_co2': 0,
            'mars_base_internal_oxygen': 0
        }
    
    def set_env(self):
        self.env_values['mars_base_internal_temperature'] = random.uniform(18, 30)
        self.env_values['mars_base_external_temperature'] = random.uniform(0, 21)
        self.env_values['mars_base_internal_humidity'] = random.uniform(50, 60)
        self.env_values['mars_base_external_illuminance'] = random.uniform(500, 715)
        self.env_values['mars_base_internal_co2'] = random.uniform(0.02, 0.1)
        self.env_values['mars_base_internal_oxygen'] = random.uniform(4, 7)
    
    def get_env(self):
        return self.env_values

class MissionComputer:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': 0,
            'mars_base_external_temperature': 0,
            'mars_base_internal_humidity': 0,
            'mars_base_external_illuminance': 0,
            'mars_base_internal_co2': 0,
            'mars_base_internal_oxygen': 0
        }
        self.ds = DummySensor()
    
    def get_sensor_data(self, use_multiprocessing=False)->None:

        if use_multiprocessing:
            while True:
                try:
                    self.ds.set_env()
                    sensor_data = self.ds.get_env()
                    self.env_values.update(sensor_data)
                    print( '=' * 60)
                    print(json.dumps(self.env_values, indent=0, ensure_ascii=False))
                    print(f"업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n종료하려면 Ctrl+C를 입력하세요.")
                    print( '=' * 60)
                    time.sleep(5)
                except KeyboardInterrupt:
                    print("센서 데이터 프로세스 종료")
                    break
        else:
            while not stop_flag: 
                self.ds.set_env()
                sensor_data = self.ds.get_env()
                self.env_values.update(sensor_data)
                print( '=' * 60)
                print(json.dumps(self.env_values, indent=0, ensure_ascii=False))
                print(f"업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n종료하려면 'q'를 입력하세요.")
                print( '=' * 60)
                time.sleep(5)

    
    def get_mission_computer_info(self, use_multiprocessing=False):
        if use_multiprocessing:
            while True:
                try:
                    system_info = {
                        '운영체계': platform.system(),
                        '운영체계_버전': platform.version(),
                        'CPU_타입': platform.processor() or platform.machine(),
                        'CPU_코어수': psutil.cpu_count(logical=False),
                        '메모리_크기_GB': round(psutil.virtual_memory().total / (1024**3), 2)
                    }
                    
                    print("=== 미션 컴퓨터 시스템 정보 ===")
                    print(json.dumps(system_info, indent=2, ensure_ascii=False))
                    print(f"업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n종료하려면 Ctrl+C를 입력하세요.")
                    print("-" * 50)
                    
                    time.sleep(20)
                except KeyboardInterrupt:
                    print("시스템 정보 프로세스 종료")
                    break
        else:
            while not stop_flag:
                system_info = {
                    '운영체계': platform.system(),
                    '운영체계_버전': platform.version(),
                    'CPU_타입': platform.processor() or platform.machine(),
                    'CPU_코어수': psutil.cpu_count(logical=False),
                    '메모리_크기_GB': round(psutil.virtual_memory().total / (1024**3), 2)
                }
                
                print("=== 미션 컴퓨터 시스템 정보 ===")
                print(json.dumps(system_info, indent=2, ensure_ascii=False))
                print(f"업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n종료하려면 'q or ctrl + C'를 입력하세요.")
                print("-" * 50)
                
                time.sleep(20)
    
    def get_mission_computer_load(self, use_multiprocessing=False):
        if use_multiprocessing:
            while True:
                try:
                    load_info = {
                        'CPU_사용량_%': round(psutil.cpu_percent(interval=1), 2),
                        '메모리_사용량_%': round(psutil.virtual_memory().percent, 2),
                    }
                    
                    print("=== 미션 컴퓨터 부하 정보 ===")
                    print(json.dumps(load_info, indent=2, ensure_ascii=False))
                    print(f"업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n종료하려면 Ctrl+C를 입력하세요.")
                    print('=' * 60)
                    
                    time.sleep(20)
                except KeyboardInterrupt:
                    print("부하 정보 프로세스 종료")
                    break
        else:
            while not stop_flag:
                load_info = {
                    'CPU_사용량_%': round(psutil.cpu_percent(interval=1), 2),
                    '메모리_사용량_%': round(psutil.virtual_memory().percent, 2),
                }
                
                print("=== 미션 컴퓨터 부하 정보 ===")
                print(json.dumps(load_info, indent=2, ensure_ascii=False))
                print(f"업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n종료하려면 'q or ctrl + C'를 입력하세요.")
                print('=' * 60)
                
                time.sleep(20)

def run_sensor_data(computer):
    computer.get_sensor_data(use_multiprocessing=True)

def run_system_info(computer):
    computer.get_mission_computer_info(use_multiprocessing=True)

def run_load_info(computer):
    computer.get_mission_computer_load(use_multiprocessing=True)

def main():
    print("mars_mission_computer.py 실행")
    print("=" * 60)

    print("\n문제 1: DummySensor 테스트")
    ds = DummySensor()
    ds.set_env()
    sensor_values = ds.get_env()
    for k,v in sensor_values.items():
        print(f'{k} : {v:.2f}')
   
    print("=" * 60)

    print("\n문제 2: MissionComputer 단일 실행 테스트")
    RunComputer = MissionComputer()
    
    global stop_flag
    stop_flag = False
    
    sensor_thread = threading.Thread(target=RunComputer.get_sensor_data)
    quit_thread = threading.Thread(target=wait_for_quit)
    
    sensor_thread.daemon = True
    quit_thread.daemon = True
    
    sensor_thread.start()
    quit_thread.start()
    

    while not stop_flag:
        time.sleep(0.1)
    
    print("문제 2 완료.") 
    
    runComputer = MissionComputer()


    print("\n문제 3,4: 멀티쓰레딩 및 멀티프로세싱 실행")
    print("다음 옵션 중 선택하세요:")
    print("1. 멀티쓰레딩 실행")
    print("2. 멀티프로세싱 실행") 
    print("3. 종료")
    
    choice = input("선택 : ")
    
    if choice == "1":
        print("멀티쓰레딩으로 실행 중...")
        print("종료하려면 'q'를 입력하세요.")
        runComputer = MissionComputer()
        
        stop_flag = False
        
        thread1 = threading.Thread(target=runComputer.get_sensor_data)
        thread2 = threading.Thread(target=runComputer.get_mission_computer_info)
        thread3 = threading.Thread(target=runComputer.get_mission_computer_load)
        quit_thread = threading.Thread(target=wait_for_quit)
        
        thread1.daemon = True
        thread2.daemon = True
        thread3.daemon = True
        quit_thread.daemon = True
        
        thread1.start()
        thread2.start()
        thread3.start()
        quit_thread.start()

        while not stop_flag:
            time.sleep(0.1)
    
    elif choice == "2":
        print("멀티프로세싱으로 실행 중...")
        print("종료하려면 Ctrl+C를 누르세요.")
        
        runComputer1 = MissionComputer()
        runComputer2 = MissionComputer()
        runComputer3 = MissionComputer()

        process1 = multiprocessing.Process(target=run_sensor_data, args=(runComputer1,))
        process2 = multiprocessing.Process(target=run_system_info, args=(runComputer2,))
        process3 = multiprocessing.Process(target=run_load_info, args=(runComputer3,))
        
        process1.start()
        process2.start()
        process3.start()

        try:
            process1.join()
            process2.join()
            process3.join()

        except KeyboardInterrupt:
            print("\n시스템을 종료합니다...")
            process1.terminate()
            process2.terminate()
            process3.terminate()
    
    else:
        print("시스템을 종료합니다...")

    return 0

if __name__ == "__main__":
    sys.exit(main())
    