import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime  
from dataclasses import dataclass
import argparse

# LLM 라이브러리 import
# pip install google-generativeai
# export GOOGLE_API_KEY="여기에_복사한_API_키를_붙여넣으세요"
import google.generativeai as genai

# --- 데이터 클래스 및 파일 리더 ---

@dataclass
class LogReaderConfig:
    """로그 리더의 설정을 담는 데이터 클래스"""
    file_path: Path
    encoding: str = 'auto'
    candidate_encodings: List[str] = None
    
    def __post_init__(self):
        """객체 생성 후 초기화 메서드"""
        if self.candidate_encodings is None:
            self.candidate_encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin1']

class MissionLogReader:
    """로그 파일을 읽고 기본적인 유효성 검사를 수행하는 클래스"""
    def __init__(self, config: LogReaderConfig):
        self.config = config
        self._setup_logging()
        self.detected_encoding = None

    def _setup_logging(self) -> None:
        """로깅 기본 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _validate_file(self) -> None:
        """파일 존재 여부, 파일/디렉토리 여부, 읽기 권한을 검사합니다."""
        if not self.config.file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {self.config.file_path}")
        if not self.config.file_path.is_file():
            raise ValueError(f"경로가 파일이 아닙니다: {self.config.file_path}")

    def _detect_encoding(self) -> str:
        
        for encoding in self.config.candidate_encodings:
            try:
                with open(self.config.file_path, 'r', encoding=encoding) as f:
                    f.read(1024) # 테스트로 일부만 읽기
                self.logger.info(f"파일 인코딩 감지 성공: {encoding}")
                self.detected_encoding = encoding
                return encoding
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError(f"지원하는 인코딩으로 파일을 디코딩할 수 없습니다: {self.config.file_path}")

    def read_entire_file(self) -> List[str]:
        """파일 전체 내용을 읽어 줄 단위 리스트로 반환합니다."""
        try:
            self._validate_file()
            encoding = self._detect_encoding()
            self._print_header()

            with open(self.config.file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()

            return lines

        except (FileNotFoundError, PermissionError, ValueError, UnicodeDecodeError) as e:
            self.logger.error(e)
            print(f"❌ 에러 발생: {e}", file=sys.stderr)
            return None # 실패 시 None 반환
        except Exception as e:
            self.logger.exception(f"예상치 못한 에러 발생: {e}")
            print(f"❌ 예상치 못한 에러: {e}", file=sys.stderr)
            return None
    
    def _print_header(self) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 현재 시간을 문자열로 변환
        
        header = f"\n{'='*60}\n📄 Log File: {self.config.file_path.name}\n"
        header += f"📅 Read at: {timestamp}\n"
        header += f"📝 Program Name: main.py\n"
        header += f"{'='*60}\n\n"
        print(header)

# --- 로그 데이터 처리 클래스 ---

class LogProcessor:
    """로그 데이터를 파싱, 정렬, 변환 및 저장하는 클래스"""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse_logs(self, log_lines: List[str]) -> List[List[str]]:
        parsed_data = []
        for i, line in enumerate(log_lines):
            line = line.strip()
            if not line:
                continue # 빈 줄은 건너뛰기
            
            parts = line.split(',', 2) 
            if len(parts) == 3:
                timestamp, message = parts[0].strip(), parts[2].strip()
                parsed_data.append([timestamp, message])
            else:
                self.logger.warning(f"{i+1}번째 줄 파싱 실패 (포맷 오류): {line}")
        print("✅ 로그 내용 파싱 완료.")
        return parsed_data

    def sort_logs_desc(self, logs: List[List[str]]) -> List[List[str]]:
        sorted_logs = sorted(logs, key=lambda item: item[0], reverse=True)
        print("✅ 시간 역순으로 정렬 완료.")
        return sorted_logs

    def convert_to_dict(self, logs: List[List[str]]) -> Dict[str, str]:
        """정렬된 로그 리스트를 {시간: 메시지} 형태의 사전으로 변환합니다."""
        log_dict = {timestamp: message for timestamp, message in logs}
        print("✅ 사전(Dict) 객체로 변환 완료.")
        return log_dict

    def save_as_json(self, data: Dict[str, str], output_path: Path) -> None:
        """사전 데이터를 JSON 파일로 저장합니다."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=0)
            print(f"✅ JSON 파일 저장 완료: {output_path}")
        except Exception as e:
            self.logger.error(f"JSON 파일 저장 실패: {e}")
            print(f"❌ JSON 파일 저장 중 에러 발생: {e}", file=sys.stderr)

class LLMReportGenerator:
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = None
        try:
            # 환경 변수에서 API 키를 안전하게 불러옵니다.
            key = os.getenv("GOOGLE_API_KEY")
            if not key:
                raise ValueError("환경 변수에서 'GOOGLE_API_KEY'를 찾을 수 없습니다. API 키를 설정해주세요.")
            
            genai.configure(api_key=key)

            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("Gemini 모델이 성공적으로 초기화되었습니다.")

        except Exception as e:
            self.logger.error(f"Gemini 모델 초기화 실패: {e}")
            print(f"❌ LLM 리포트 생성기 초기화 실패: {e}", file=sys.stderr)

    def _create_prompt(self, logs: List[List[str]]) -> str:

        # 로그 데이터를 LLM이 이해하기 쉬운 문자열 형태로 변환합니다.
        log_str = "\n".join([f"{ts}, {msg}" for ts, msg in logs]) # 시간순으로 제공

        # LLM에게 역할, 작업, 데이터, 출력 형식을 구체적으로 지시합니다.
        prompt = f"""
        ### 역할: 당신은 최고의 우주선 시스템 사고 분석 전문가입니다. 주어진 임무 컴퓨터 로그 데이터를 바탕으로, 전문적이고 체계적인 '사고 원인 분석 보고서'를 작성해 주십시오.

        ### 분석할 로그 데이터:
        ```
        {log_str}
        ```

        ### 보고서에 반드시 포함되어야 할 항목:
        1.  **개요**: 보고서의 목적을 간략히 서술합니다.
        2.  **사고 타임라인 분석**: 로그에 나타난 주요 경고(WARNING), 오류(ERROR), 그리고 치명적(CRITICAL/FATAL) 이벤트를 시간순으로 요약하여 재구성합니다.
        3.  **사고 원인 추론**: 타임라인을 바탕으로 이벤트 간의 인과 관계를 분석하여, 사고의 가장 핵심적인 원인(Root Cause)을 논리적으로 추론합니다.
        4.  **권고 사항**: 추론된 원인을 바탕으로, 향후 동일한 사고의 재발을 방지하기 위한 구체적이고 실질적인 대책을 3가지 제시합니다.

        ### 출력 형식:
        - 반드시 Markdown을 사용해야 합니다.
        - 제목은 `🚀 사고 원인 분석 보고서` 로 시작해 주세요.
        - 한국어로 작성해 주세요.
        """
        return prompt

    def generate_analysis_report(self, logs: List[List[str]], output_path: Path) -> bool:

        if not self.model:
            print("❌ 모델이 초기화되지 않아 보고서를 생성할 수 없습니다.", file=sys.stderr)
            return False

        print("\n🤖 LLM을 사용하여 사고 원인 분석 보고서를 생성합니다. 잠시 기다려 주세요...")
        
        try:
            prompt = self._create_prompt(logs)
            response = self.model.generate_content(prompt)
            
            # LLM이 생성한 텍스트를 파일에 저장합니다.
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"✅ LLM 기반 분석 보고서 저장 완료: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"LLM 보고서 생성 실패: {e}")
            print(f"❌ LLM 보고서 생성 중 에러 발생: {e}", file=sys.stderr)
            return False

# --- 메인 실행 함수 ---

def main() -> int:
    """스크립트의 메인 로직을 실행합니다."""
    
    # 1. 설정 및 객체 생성
    log_file = Path("mission_computer_main.log")
    json_output_file = Path("mission_computer_main.json")
    report_file = Path("log_analysis.md")

    config = LogReaderConfig(file_path=log_file)
    reader = MissionLogReader(config)
    processor = LogProcessor()
    reporter = LLMReportGenerator()

    # 2. 로그 파일 읽기
    log_lines = reader.read_entire_file()
    if log_lines is None:
        return 1
    print("\n--- [ 원본 로그 파일 내용 ] ---")
    for line in log_lines:
        print(line, end='')
    print(f"\n{'='*60}\n✅ End of log file\n{'='*60}")

    # 3. 로그 파싱
    parsed_logs = processor.parse_logs(log_lines)
    if not parsed_logs:
        return 1
    print("\n--- [ 파싱된 리스트 객체 ] ---")
    for log in parsed_logs:
        print(f'{log}')
    print(f"{'='*60}\n✅ End of parsed logs\n{'='*60}")

    # 4. 시간 역순 정렬
    sorted_logs = processor.sort_logs_desc(parsed_logs)
    if not sorted_logs:
        return 1
    print("\n--- [ 시간 역순으로 정렬된 리스트 ] ---")
    for log in sorted_logs:
        print(log)
    print(f"{'='*60}\n✅ End of sorted logs\n{'='*60}")

    # 5. 사전 객체로 변환
    log_dict = processor.convert_to_dict(sorted_logs)
    if not log_dict:
        return 1

    # 6. JSON 파일로 저장
    result = processor.save_as_json(log_dict, json_output_file)
    if result is False:
        return 1

    # 7. 사고 원인 분석 보고서 작성
    report_result = reporter.generate_analysis_report(parsed_logs, report_file)
    if report_result is False:
        return 1

    print("\n🎉 모든 작업이 성공적으로 완료되었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
