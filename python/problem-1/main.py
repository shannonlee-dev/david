import sys        # 시스템 관련 기능 (종료코드, stdin 등)
import os         # 운영체제 관련 기능 (파일권한 확인 등)
import argparse   # 명령줄 옵션 처리 (-n, --help 같은 것들)
import logging    # 로그 기록 (디버깅용)
import json       # JSON 처리
from pathlib import Path                    # 파일경로 쉽게 다루기
from typing import Optional, Union, List, Iterator, Dict  # 타입 힌트 (무슨 타입인지 알려줌)
from datetime import datetime               # 날짜/시간 처리
from dataclasses import dataclass          # 데이터 저장용 클래스 쉽게 만들기

BULLET = "\u2022\u2009"

@dataclass
class LogReaderConfig:
    
    file_path: Union[Path, str]              # 파일 경로 (Path 객체나 문자열)
    encoding: str = 'auto'                   # 인코딩 방식 (기본값: 자동감지)
    show_line_numbers: bool = False          # 줄번호 보여줄지 (기본값: 안보여줌)
    chunk_size: int = 8192                   # 한번에 읽을 데이터 크기 (8KB)
    candidate_encodings: List[str] = None
    parse_csv: bool = False                  # CSV 파싱 옵션
    sort_by_time: bool = False               # 시간 정렬 옵션
    save_json: bool = False                  # JSON 저장 옵션

    def __post_init__(self):
        # __post_init__은 "객체가 만들어진 직후에 실행되는 함수"
        # 추가 설정이나 검증을 할 때 씀
        if self.candidate_encodings is None:
            self.candidate_encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin1']
            # utf-8-sig: BOM이 있는 UTF-8 (윈도우에서 많이 씀)
            # utf-8: 일반 UTF-8 (가장 일반적)
            # cp949, euc-kr: 한글 인코딩
            # latin1: 안전망 인코딩 (거의 모든 바이트를 읽을 수 있음)
        
        if isinstance(self.file_path, str):
            # isinstance(객체, 타입): "이 객체가 이 타입인가?" 확인
            # 만약 file_path가 문자열이면
            self.file_path = Path(self.file_path) if self.file_path != '-' else '-'
            # '-'이 아니면 Path 객체로 변환, '-'면 그대로 (표준입력 의미)


# === 메인 로그 읽기 클래스 ===
class MissionLogReader:
    # 실제로 로그 파일을 읽고 처리하는 핵심 클래스
    
    def __init__(self, config: LogReaderConfig):
        self.config = config
        self._setup_logging()             # 로깅 설정 함수 호출
        self._detected_encoding = None    # 감지된 인코딩 저장할 변수 (처음엔 None)
    
    def _setup_logging(self) -> None:
        # 함수명 앞의 _는 "내부에서만 쓰는 함수"라는 의미 (private)
        logging.basicConfig(
            # 로깅 기본 설정
            level=logging.INFO,           # INFO 레벨 이상만 보여줘
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            # 로그 형식: 시간 - 클래스명 - 레벨 - 메시지
            datefmt='%Y-%m-%d %H:%M:%S'  # 날짜 형식: 2024-08-27 15:30:45
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        # 이 클래스 이름으로 로거 생성 (MissionLogReader라는 이름으로)
    
    def read_and_display(self) -> bool:
        # 메인 기능 함수 - 파일을 읽고 화면에 출력
        # -> bool: 성공하면 True, 실패하면 False 리턴   
        try:            
            if self.config.file_path == '-':
                self._display_stdin()      # 표준입력에서 읽기
            else:
                # 일반 파일이면
                self._validate_file()      # 파일이 유효한지 검사
                encoding = self._detect_encoding()  # 인코딩 자동 감지
                
                # CSV 파싱 옵션이 활성화된 경우
                if self.config.parse_csv:
                    log_data = self._parse_csv_content(encoding)
                    self._display_parsed_data(log_data)
                    
                    if self.config.sort_by_time:
                        sorted_data = self._sort_by_time(log_data)
                        self._display_sorted_data(sorted_data)
                        
                        if self.config.save_json:
                            dict_data = self._convert_to_dict(sorted_data)
                            self._save_to_json(dict_data)
                else:
                    self._stream_file_content(encoding) # 파일 내용을 스트리밍으로 출력
            return True                    # 성공하면 True 리턴
            
        # 예상 가능한 에러들을 각각 처리
        except FileNotFoundError:
            # 파일이 없을 때
            self.logger.error(f"File not found: {self.config.file_path}")
            print(f"Error: The file '{self.config.file_path}' does not exist.", file=sys.stderr)
            return False
            
        except PermissionError:
            # 파일 읽기 권한이 없을 때
            self.logger.error(f"Permission denied: {self.config.file_path}")
            print(f"Error: Permission denied to read '{self.config.file_path}'.", file=sys.stderr)
            return False
            
        except ValueError as e:
            # 값이 잘못되었을 때 (파일이 아닌 디렉토리 등)
            self.logger.error(f"Invalid file path: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return False
            
        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error: {e}")
            print(f"Error: Unable to decode file with any supported encoding.", file=sys.stderr)
            return False
            
        except Exception as e:
            # 위에서 처리하지 못한 모든 에러
            self.logger.exception(f"Unexpected error: {e}")
            print(f"Unexpected error: {e}", file=sys.stderr)
            return False
    
    def _parse_csv_content(self, encoding: str) -> List[Dict[str, str]]:
        """CSV 형태의 로그를 파싱하여 리스트로 변환"""
        log_data = []
        file_path = self.config.file_path
        
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()
            
            # 첫 번째 줄이 헤더인지 확인 (timestamp, event, message)
            start_index = 0
            if lines and lines[0].strip().lower().startswith('timestamp'):
                start_index = 1  # 헤더 건너뛰기
            
            for line_num, line in enumerate(lines[start_index:], start_index + 1):
                line = line.strip()
                if not line:
                    continue
                    
                # 콤마로 분리 (3개 컬럼: timestamp, event, message)
                parts = line.split(',', 2)  # 최대 3개로 분리
                
                if len(parts) >= 3:
                    timestamp = parts[0].strip()
                    event = parts[1].strip()
                    message = parts[2].strip()
                    log_data.append({
                        'timestamp': timestamp,
                        'event': event,
                        'message': message,
                        'line_number': line_num
                    })
                elif len(parts) == 2:
                    # 2개 컬럼만 있는 경우 (기존 방식과 호환)
                    timestamp = parts[0].strip()
                    message = parts[1].strip()
                    log_data.append({
                        'timestamp': timestamp,
                        'event': '',
                        'message': message,
                        'line_number': line_num
                    })
                else:
                    # 콤마가 없는 경우 전체를 메시지로 처리
                    log_data.append({
                        'timestamp': '',
                        'event': '',
                        'message': line,
                        'line_number': line_num
                    })
        
        return log_data
    
    def _display_parsed_data(self, log_data: List[Dict[str, str]]) -> None:
        """파싱된 데이터를 화면에 출력"""
        self._print_header()
        print("Parsed Log Data (List format):")
        print(f"{'='*80}")
        
        for i, entry in enumerate(log_data):
            print(f"[{i}] Timestamp: {entry['timestamp']}")
            if entry['event']:
                print(f"    Event: {entry['event']}")
            print(f"    Message: {entry['message']}")
            print(f"    Line: {entry['line_number']}")
            print()
        
        print(f"Total entries: {len(log_data)}")
        print(f"{'='*80}")
    
    def _sort_by_time(self, log_data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """시간 역순으로 정렬"""
        def parse_datetime(timestamp_str: str) -> datetime:
            """다양한 날짜 형식을 파싱"""
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y/%m/%d %H:%M',
                '%m/%d/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # 파싱 실패시 현재 시간 반환
            return datetime.now()
        
        # 시간 역순 정렬 (최신이 먼저)
        return sorted(log_data, key=lambda x: parse_datetime(x['timestamp']), reverse=True)
    
    def _display_sorted_data(self, sorted_data: List[Dict[str, str]]) -> None:
        """정렬된 데이터를 화면에 출력"""
        print("\nTime-Sorted Log Data (Reverse Chronological Order):")
        print(f"{'='*80}")
        
        for i, entry in enumerate(sorted_data):
            print(f"[{i}] Timestamp: {entry['timestamp']}")
            if entry['event']:
                print(f"    Event: {entry['event']}")
            print(f"    Message: {entry['message']}")
            print(f"    Original Line: {entry['line_number']}")
            print()
        
        print(f"Total sorted entries: {len(sorted_data)}")
        print(f"{'='*80}")
    
    def _convert_to_dict(self, log_data: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """리스트를 딕셔너리로 변환"""
        result_dict = {}
        
        for i, entry in enumerate(log_data):
            key = f"entry_{i:04d}"  # entry_0001, entry_0002 형태
            result_dict[key] = {
                'timestamp': entry['timestamp'],
                'event': entry['event'],
                'message': entry['message'],
                'original_line_number': entry['line_number'],
                'sorted_index': i
            }
        
        return result_dict
    
    def _save_to_json(self, dict_data: Dict[str, Dict[str, str]]) -> None:
        """딕셔너리를 JSON 파일로 저장"""
        output_file = "mission_computer_main.json"
        
        # 메타데이터 추가
        json_output = {
            'metadata': {
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source_file': str(self.config.file_path),
                'total_entries': len(dict_data),
                'sorted_by': 'timestamp_reverse',
                'encoding': self._detected_encoding,
                'format': 'CSV with timestamp,event,message columns'
            },
            'log_entries': dict_data
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_output, f, ensure_ascii=False, indent=2)
            
            print(f"\nJSON file saved: {output_file}")
            print(f"   Entries: {len(dict_data)}")
            print(f"   Encoding: UTF-8")
            
        except Exception as e:
            self.logger.error(f"Failed to save JSON file: {e}")
            print(f"Error saving JSON file: {e}", file=sys.stderr)
    
    def _validate_file(self) -> None:
        # 파일이 존재하고 읽을 수 있는지 검사
        file_path = self.config.file_path  # 설정에서 파일 경로 가져오기
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Cross-platform readable check (운영체제 상관없이 읽기 권한 확인)
        if not os.access(file_path, os.R_OK):
            # os.access(경로, 권한): 해당 권한이 있는지 확인
            # os.R_OK: 읽기 권한 확인 상수
            raise PermissionError(f"File is not readable: {file_path}")
    
    def _detect_encoding(self) -> str:
        # 파일의 인코딩을 자동으로 감지
        file_path = self.config.file_path
        
        # 여러 인코딩을 시도해봄
        for encoding in self.config.candidate_encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 첫 1KB만 읽어서 인코딩이 맞는지 테스트
                self.logger.info(f"Detected encoding: {encoding}")
                self._detected_encoding = encoding  # 저장
                return encoding  # 성공하면 이 인코딩 사용
            except UnicodeDecodeError:
                continue  # 실패하면 다음 인코딩 시도
        # 모든 인코딩이 실패하면 에러 발생
        raise Exception("Unable to detect encoding for file: " + str(file_path))
    
    def _stream_file_content(self, encoding: str) -> None:
        # 파일을 스트리밍 방식으로 읽어서 출력
        # 스트리밍: 전체를 메모리에 올리지 않고 조금씩 읽어서 바로 출력
        file_path = self.config.file_path
        
        self._print_header()
        
        line_number = 1  # 줄번호 카운터
        
        with open(file_path, 'r', encoding=encoding, buffering=self.config.chunk_size) as f:
            # buffering: 한번에 읽을 버퍼 크기 지정
            
            if self.config.show_line_numbers:
                # 줄번호를 보여주는 설정이면
                for line in f:
                    # 파일을 한 줄씩 읽음
                    print(f"{line_number:>6} | {line}", end='')
                    # {:>6}: 오른쪽 정렬로 6자리 확보
                    # end='': 줄바꿈을 추가하지 않음 (line에 이미 있음)
                    line_number += 1  # 줄번호 증가
            else:
                # 줄번호 없이 그냥 출력
                while True:
                    chunk = f.read(self.config.chunk_size)  # 지정된 크기만큼 읽기
                    if not chunk:
                        # 더 이상 읽을 내용이 없으면
                        break  # 루프 종료
                    print(chunk, end='')  # 읽은 내용 바로 출력
        
        self._print_footer()
    
    def _display_stdin(self) -> None:
        # 표준입력(키보드나 파이프)에서 내용을 읽어서 출력
        self._print_header()
        
        line_number = 1
        
        if self.config.show_line_numbers:
            for line in sys.stdin:
                print(f"{line_number:>6} | {line}", end='')
                line_number += 1
        else:
            for chunk in iter(lambda: sys.stdin.read(self.config.chunk_size), ''):
                # iter(함수, 끝값): 함수를 반복 호출하다가 끝값이 나오면 중단
                print(chunk, end='')
        
        self._print_footer()
    
    def _print_header(self) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 현재 시간을 문자열로 변환
        
        if self.config.file_path == '-':
            header = f"\n{'='*60}\n Reading from: STDIN\n"
        else:
            header = f"\n{'='*60}\n Log File: {self.config.file_path.name}\n"
        header += f" Read at: {timestamp}\n"
        header += f" Program Name: main.py\n"
        header += f"{'='*60}\n\n"
        print(header)
    
    def _print_footer(self) -> None:
        print(f"\n{'='*60}\n End of log file\n{'='*60}")


class LogFileAnalyzer:
    
    @staticmethod  # 정적 메서드: 클래스 인스턴스 없이도 호출 가능
    def analyze(file_path: Path, encoding: str) -> dict:
        # 파일을 분석해서 통계 정보를 딕셔너리로 리턴
        stats = {
            # 통계 정보를 저장할 딕셔너리
            'file_size' : file_path.stat().st_size,  # 파일 크기 (바이트)
            'line_count' : 0,     # 줄 개수
            'word_count' : 0,     # 단어 개수
            'char_count' : 0,     # 문자 개수
            'last_modified' : datetime.fromtimestamp(file_path.stat().st_mtime),
            'created' : datetime.fromtimestamp(file_path.stat().st_ctime)
        }

        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                # errors='replace': 인코딩 에러가 나면 대체 문자로 변경하고 계속
                for line in f:
                    stats['line_count'] += 1              # 줄 개수 증가
                    stats['word_count'] += len(line.split())  # 단어 개수 증가
                    stats['char_count'] += len(line)      # 문자 개수 증가
        except Exception as e:
            # 파일을 읽을 수 없으면 부분 통계만 리턴
            logging.warning(f"Could not analyze file content: {e}")
            print(f"Warning: Could not analyze file content: {e}", file=sys.stderr)

        return stats

def create_parser() -> argparse.ArgumentParser:
    # 명령줄 옵션(-n, --help 등)을 처리하는 파서 생성
    parser = argparse.ArgumentParser()
    
    # 필수 인자
    parser.add_argument(
        'file', 
        help='Log file path (use "-" for stdin)'
    )
    # 선택 인자
    parser.add_argument(
        '-l', '--line-numbers',
        action='store_true',
        help='Show line numbers'
    )
    
    parser.add_argument(
        '-s', '--stats',
        action='store_true',
        help='Show file statistics'
    )
    
    # 새로운 CSV 관련 옵션들
    parser.add_argument(
        '-p',
        '--parse-csv',
        action='store_true',
        help='Parse log file as CSV format (comma-separated timestamp, event, message)'
    )
    
    parser.add_argument(
        '-t',
        '--sort-time',
        action='store_true',
        help='Sort parsed data by time in reverse chronological order'
    )
    
    parser.add_argument(
        '-j',
        '--save-json',
        action='store_true',
        help='Save processed data as JSON file (mission_computer_main.json)'
    )
    
    return parser

def main() -> int:
    parser = create_parser()        # 명령줄 파서 생성
    args = parser.parse_args()      # 실제 명령줄 인자 분석

    config = LogReaderConfig(       # 각종 인스턴스 속성 설정
        file_path=args.file,
        show_line_numbers=args.line_numbers,
        parse_csv=args.parse_csv,        # 추가된 옵션들
        sort_by_time=args.sort_time,
        save_json=args.save_json,
    )
    
    reader = MissionLogReader(config)   # 로그 리더 객체 생성
    success = reader.read_and_display()  # 실제 로그 읽기 및 출력
    
    if success and args.stats and config.file_path != '-' and Path(config.file_path).exists():
        print("\nFile Statistics:")
        try:
            # 감지된 인코딩이 있으면 사용, 없으면 설정값 사용
            encoding = reader._detected_encoding
            stats = LogFileAnalyzer.analyze(Path(config.file_path), encoding)
            
            # 통계 정보를 예쁘게 출력
            print(f"  {BULLET}Size: {stats['file_size']:,} bytes")      # :,는 천단위 구분자
            print(f"  {BULLET}Lines: {stats['line_count']:,}")
            print(f"  {BULLET}Words: {stats['word_count']:,}")
            print(f"  {BULLET}Characters: {stats['char_count']:,}")
            print(f"  {BULLET}Last Modified: {stats['last_modified'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  {BULLET}Created: {stats['created'].strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logging.warning(f"Could not generate statistics: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())