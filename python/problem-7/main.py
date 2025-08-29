import os
import zipfile
import cv2
import numpy as np
from pathlib import Path
import time
import json
from typing import List, Tuple, Optional
import torch

# YOLOv10 (최고 성능 딥러닝 모델)
from ultralytics import YOLO


class YOLOPersonDetector:
    """YOLOv10 기반 고성능 사람 감지 클래스"""
    
    def __init__(self, model_size='s', confidence_threshold=0.5):
        """
        model_size 옵션:
        - 'n': nano (가장 빠름, 200+ FPS)
        - 's': small (균형잡힌 성능, 권장)
        - 'm': medium (높은 정확도)
        - 'l': large (매우 높은 정확도)
        - 'x': extra large (최고 정확도, 느림)
        """
        self.model_size = model_size
        self.confidence_threshold = confidence_threshold
        self.device = self._setup_device()
        self.model = None
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        print(f"YOLOv10{model_size} 모델 로딩 중...")
        self.load_model()
        print("모델 로딩 완료!")
    
    def _setup_device(self):
        """최적 디바이스 자동 선택"""
        if torch.cuda.is_available():
            device = 'cuda'
            print(f"GPU 사용: {torch.cuda.get_device_name(0)}")
        else:
            device = 'cpu'
            print("CPU 사용")
        return device
    
    def load_model(self):
        """YOLOv10 모델 로드"""
        model_file = f'yolov10{self.model_size}.pt'
        self.model = YOLO(model_file)
        
        if self.device == 'cuda':
            self.model.to(self.device)
    
    def detect_people(self, image: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        이미지에서 사람 감지
        Returns: [(x1, y1, x2, y2, confidence), ...]
        """
        if self.model is None:
            return []
        
        try:
            # YOLOv10으로 사람만 감지 (class 0 = person)
            results = self.model(image, conf=self.confidence_threshold, classes=[0], verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        confidence = float(box.conf[0].cpu().numpy())
                        detections.append((x1, y1, x2, y2, confidence))
            
            return detections
            
        except Exception as e:
            print(f"감지 중 오류: {e}")
            return []
    
    def draw_detections(self, image: np.ndarray, detections: List[Tuple[int, int, int, int, float]]) -> np.ndarray:
        """감지 결과를 이미지에 표시"""
        result_image = image.copy()
        
        for x1, y1, x2, y2, conf in detections:
            # 초록색 박스
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 3)
            
            # 신뢰도 표시
            label = f'Person {conf:.2f}'
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(result_image, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            cv2.putText(result_image, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        return result_image


class CCTVSystem:
    """CCTV 사람 감지 시스템"""
    
    def __init__(self, model_size='s', confidence_threshold=0.5):
        self.detector = YOLOPersonDetector(model_size, confidence_threshold)
        self.detection_history = []
    
    def extract_zip(self, zip_path: str, extract_path: str = '.') -> bool:
        """ZIP 파일 압축 해제"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            print(f'CCTV.zip 압축 해제 완료 → {extract_path}/CCTV/')
            return True
        except Exception as e:
            print(f'압축 해제 실패: {e}')
            return False
    
    def get_image_files(self, folder_path: str) -> List[str]:
        """이미지 파일 목록 가져오기"""
        image_files = []
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            print(f'❌ {folder_path} 폴더가 없습니다.')
            return image_files
        
        # 이미지 파일만 필터링
        for file_path in folder_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.detector.supported_formats:
                image_files.append(str(file_path))
        
        image_files.sort()
        print(f'📁 총 {len(image_files)}개 이미지 파일 발견')
        return image_files
    
    def process_single_image(self, image_path: str, show_result: bool = True) -> Tuple[bool, int]:
        """단일 이미지 처리"""
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                print(f'❌ 이미지 로드 실패: {image_path}')
                return False, 0
            
            # 사람 감지
            start_time = time.time()
            detections = self.detector.detect_people(image)
            inference_time = time.time() - start_time
            
            # 결과 처리
            if detections:
                result_image = self.detector.draw_detections(image, detections)
                people_count = len(detections)
                
                print(f'👤 {people_count}명 감지 - {os.path.basename(image_path)} ({inference_time:.3f}초)')
                
                # 감지 기록 저장
                self.detection_history.append({
                    'image_path': image_path,
                    'people_count': people_count,
                    'confidence_scores': [det[4] for det in detections],
                    'inference_time': inference_time
                })
                
                if show_result:
                    self._display_image(result_image, f'감지 결과 - {os.path.basename(image_path)}')
                
                return True, people_count
            
            return False, 0
            
        except Exception as e:
            print(f'❌ 처리 중 오류: {e}')
            return False, 0
    
    def auto_search(self, image_files: List[str]):
        """자동 사람 검색 (문제 2 해결)"""
        print('🔍 자동 사람 검색 시작...')
        print('사용법: Enter - 다음 검색, ESC - 종료')
        
        found_count = 0
        
        for i, image_path in enumerate(image_files, 1):
            print(f'\n검색 중... {i}/{len(image_files)} - {os.path.basename(image_path)}')
            
            has_people, people_count = self.process_single_image(image_path, show_result=False)
            
            if has_people:
                found_count += 1
                
                # 감지된 이미지 표시
                image = cv2.imread(image_path)
                detections = self.detector.detect_people(image)
                result_image = self.detector.draw_detections(image, detections)
                
                print(f'✅ 사람 발견! {people_count}명')
                key = self._display_image(result_image, f'🚨 사람 감지됨 - {os.path.basename(image_path)}')
                
                if key == 27:  # ESC
                    print('검색 중단됨')
                    break
        
        print(f'\n🎯 검색 완료!')
        print(f'📊 총 {found_count}개 이미지에서 사람 발견')
        cv2.destroyAllWindows()
    
    def batch_process(self, image_files: List[str], save_results: bool = False):
        """배치 처리"""
        if save_results:
            os.makedirs('detection_results', exist_ok=True)
        
        print(f'⚡ 배치 처리 시작: {len(image_files)}개 이미지')
        
        total_people = 0
        found_images = 0
        total_time = 0
        
        for i, image_path in enumerate(image_files, 1):
            if i % 10 == 0:  # 10개마다 진행률 표시
                print(f'진행률: {i}/{len(image_files)} ({100*i/len(image_files):.1f}%)')
            
            start_time = time.time()
            has_people, people_count = self.process_single_image(image_path, show_result=False)
            process_time = time.time() - start_time
            
            total_time += process_time
            
            if has_people:
                found_images += 1
                total_people += people_count
                
                # 결과 저장
                if save_results:
                    image = cv2.imread(image_path)
                    detections = self.detector.detect_people(image)
                    result_image = self.detector.draw_detections(image, detections)
                    output_path = f'detection_results/detected_{os.path.basename(image_path)}'
                    cv2.imwrite(output_path, result_image)
        
        # 결과 요약
        avg_time = total_time / len(image_files)
        fps = 1.0 / avg_time
        
        print(f'\n📈 배치 처리 완료!')
        print(f'📊 사람 감지된 이미지: {found_images}/{len(image_files)} ({100*found_images/len(image_files):.1f}%)')
        print(f'👥 총 감지된 사람 수: {total_people}명')
        print(f'⚡ 평균 처리 속도: {fps:.1f} FPS')
        print(f'⏱️ 총 소요 시간: {total_time:.1f}초')
        
        if save_results:
            print(f'💾 결과 이미지 저장됨: detection_results/ 폴더')
    
    def browse_images(self, image_files: List[str]):
        """이미지 브라우징 (문제 1 해결)"""
        if not image_files:
            print('표시할 이미지가 없습니다.')
            return
        
        current_index = 0
        print('🖼️ 이미지 브라우저')
        print('사용법: ← → 방향키로 이동, ESC 종료')
        
        while True:
            image_path = image_files[current_index]
            image = cv2.imread(image_path)
            
            if image is not None:
                print(f'표시 중: {os.path.basename(image_path)} ({current_index + 1}/{len(image_files)})')
                key = self._display_image(image, f'이미지 브라우저 - {os.path.basename(image_path)}')
                
                if key == 27:  # ESC
                    break
                elif key in [83, 2555904, ord('d')]:  # 오른쪽 화살표 또는 D
                    current_index = (current_index + 1) % len(image_files)
                elif key in [81, 2424832, ord('a')]:  # 왼쪽 화살표 또는 A
                    current_index = (current_index - 1) % len(image_files)
            else:
                current_index = (current_index + 1) % len(image_files)
        
        cv2.destroyAllWindows()
    
    def _display_image(self, image: np.ndarray, window_name: str = 'Image', wait_key: bool = True):
        """이미지 표시"""
        # 화면 크기에 맞게 조정
        height, width = image.shape[:2]
        if width > 1400 or height > 900:
            scale = min(1400/width, 900/height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))
        
        cv2.imshow(window_name, image)
        
        if wait_key:
            key = cv2.waitKey(0)
            cv2.destroyAllWindows()
            return key
        return None
    
    def save_report(self, filename: str = 'detection_report.json'):
        """감지 결과 리포트 저장"""
        if not self.detection_history:
            print('저장할 데이터가 없습니다.')
            return
        
        report = {
            'model': f'YOLOv10{self.detector.model_size}',
            'confidence_threshold': self.detector.confidence_threshold,
            'total_processed': len(self.detection_history),
            'total_people_detected': sum(record['people_count'] for record in self.detection_history),
            'average_confidence': np.mean([np.mean(record['confidence_scores']) for record in self.detection_history if record['confidence_scores']]),
            'average_fps': 1.0 / np.mean([record['inference_time'] for record in self.detection_history]),
            'detection_details': self.detection_history
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f'📋 리포트 저장완료: {filename}')


def main():
    print('🎯 YOLOv10 기반 CCTV 사람 감지 시스템')
    print('=' * 50)
    
    # 모델 크기 선택
    print('모델 크기 선택:')
    print('n - nano (가장 빠름, 200+ FPS)')
    print('s - small (균형잡힌 성능, 권장) ⭐')
    print('m - medium (높은 정확도)')
    print('l - large (매우 높은 정확도)')
    print('x - extra large (최고 정확도, 느림)')
    
    model_size = input('모델 크기 (기본값: s): ').strip().lower() or 's'
    if model_size not in ['n', 's', 'm', 'l', 'x']:
        model_size = 's'
    
    # 신뢰도 설정
    try:
        confidence = float(input('신뢰도 임계값 (0.1-0.9, 기본값: 0.5): ') or '0.5')
        confidence = max(0.1, min(0.9, confidence))
    except ValueError:
        confidence = 0.5
    
    # 시스템 초기화
    print('\n🚀 시스템 초기화 중...')
    cctv = CCTVSystem(model_size, confidence)
    
    # ZIP 파일 처리
    zip_path = 'CCTV.zip'
    cctv_folder = 'CCTV'
    
    if os.path.exists(zip_path) and not os.path.exists(cctv_folder):
        print('📦 CCTV.zip 압축 해제 중...')
        cctv.extract_zip(zip_path)
    
    # 이미지 파일 검색
    image_files = cctv.get_image_files(cctv_folder)
    
    if not image_files:
        print('❌ 이미지 파일을 찾을 수 없습니다.')
        print('CCTV.zip 파일이 있는지 또는 CCTV 폴더에 이미지가 있는지 확인하세요.')
        return
    
    # 메인 메뉴
    while True:
        print('\n' + '='*50)
        print('🎯 메뉴 선택')
        print('1. 📸 이미지 브라우징 (문제 1)')
        print('2. 🔍 자동 사람 검색 (문제 2)')
        print('3. ⚡ 배치 처리 (전체 분석)')
        print('4. 📊 성능 테스트')
        print('5. 💾 결과 리포트 저장')
        print('6. ❌ 종료')
        
        choice = input('\n선택하세요 (1-6): ').strip()
        
        try:
            if choice == '1':
                cctv.browse_images(image_files)
                
            elif choice == '2':
                cctv.auto_search(image_files)
                
            elif choice == '3':
                save_results = input('결과 이미지를 저장하시겠습니까? (y/n): ').lower().startswith('y')
                cctv.batch_process(image_files, save_results)
                
            elif choice == '4':
                # 성능 테스트 (처음 10개 이미지로)
                test_files = image_files[:min(10, len(image_files))]
                print(f'🧪 {len(test_files)}개 이미지로 성능 테스트...')
                
                start_time = time.time()
                cctv.batch_process(test_files, save_results=False)
                total_time = time.time() - start_time
                
                print(f'⚡ 총 처리 시간: {total_time:.2f}초')
                print(f'🚀 평균 FPS: {len(test_files)/total_time:.1f}')
                
            elif choice == '5':
                filename = input('리포트 파일명 (기본값: detection_report.json): ').strip()
                if not filename:
                    filename = 'detection_report.json'
                cctv.save_report(filename)
                
            elif choice == '6':
                print('👋 프로그램 종료')
                break
                
            else:
                print('❌ 잘못된 선택입니다.')
                
        except KeyboardInterrupt:
            print('\n👋 프로그램 종료')
            break
        except Exception as e:
            print(f'❌ 오류 발생: {e}')


if __name__ == '__main__':
    try:
        # 시스템 정보 출력
        print('💻 시스템 정보:')
        if torch.cuda.is_available():
            print(f'🎮 GPU: {torch.cuda.get_device_name(0)}')
            print(f'💾 VRAM: {torch.cuda.get_device_properties(0).total_memory // 1024**2}MB')
        else:
            print('🖥️ CPU 모드')
        
        main()
        
    except Exception as e:
        print(f'❌ 치명적 오류: {e}')
        print('필수 라이브러리 설치: pip install ultralytics opencv-python')