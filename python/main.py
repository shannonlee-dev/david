#!/usr/bin/env python3
# 이 줄은 "이 파일을 실행할 때 python3를 사용해라"라는 뜻
# Linux/Mac에서 ./파일명 으로 바로 실행할 수 있게 해줌

"""
Mission Computer Log Reader
A professional-grade utility for reading and displaying log files with proper error handling.
"""
# 위 3개 따옴표는 파일 전체 설명 (docstring)
# 이 파일이 뭘 하는지 설명해주는 부분

# === 필요한 도구들을 가져오는 부분 (import) ===
import sys        # 시스템 관련 기능 (종료코드, stdin 등)
import os         # 운영체제 관련 기능 (파일권한 확인 등)
import argparse   # 명령줄 옵션 처리 (-n, --help 같은 것들)
import logging    # 로그 기록 (디버깅용)
from pathlib import Path                    # 파일경로 쉽게 다루기
from typing import Optional, Union, List, Iterator  # 타입 힌트 (무슨 타입인지 알려줌)
from datetime import datetime               # 날짜/시간 처리
from enum import Enum                      # 상수 그룹 만들기
from dataclasses import dataclass          # 데이터 저장용 클래스 쉽게 만들기


# === 로그 레벨을 정의하는 부분 ===
class LogLevel(Enum):
    """Log level enumeration for output formatting."""
    # Enum은 "미리 정해진 값들의 집합"이라고 생각하면 됨
    # 마치 "빨강, 파랑, 초록"처럼 정해진 선택지
    INFO = "INFO"        # 정보성 메시지
    WARNING = "WARNING"  # 경고 메시지  
    ERROR = "ERROR"      # 에러 메시지
    DEBUG = "DEBUG"      # 디버그 메시지


# === 설정을 저장하는 클래스 ===
@dataclass  # 이 데코레이터는 "데이터만 저장하는 클래스 쉽게 만들어줘"
class LogReaderConfig:
    """Configuration for the log reader."""
    # 이 클래스는 "설정 정보들을 한 곳에 모아두는 상자" 역할
    
    file_path: Union[Path, str]              # 파일 경로 (Path 객체나 문자열)
    encoding: str = 'auto'                   # 인코딩 방식 (기본값: 자동감지)
    show_line_numbers: bool = False          # 줄번호 보여줄지 (기본값: 안보여줌)
    show_timestamp: bool = True              # 시간 정보 보여줄지 (기본값: 보여줌)
    chunk_size: int = 8192                   # 한번에 읽을 데이터 크기 (8KB)
    candidate_encodings: List[str] = None    # 시도해볼 인코딩 목록
    
    def __post_init__(self):
        # __post_init__은 "객체가 만들어진 직후에 실행되는 함수"
        # 추가 설정이나 검증을 할 때 씀
        
        if self.candidate_encodings is None:
            # 만약 인코딩 목록이 비어있으면 기본값 설정
            self.candidate_encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin1']
            # utf-8-sig: BOM이 있는 UTF-8 (윈도우에서 많이 씀)
            # utf-8: 일반 UTF-8 (가장 일반적)
            # cp949, euc-kr: 한글 인코딩
            # latin1: 서구권 인코딩 (거의 모든 바이트를 읽을 수 있음)
        
        if isinstance(self.file_path, str):
            # isinstance(객체, 타입): "이 객체가 이 타입인가?" 확인
            # 만약 file_path가 문자열이면
            self.file_path = Path(self.file_path) if self.file_path != '-' else '-'
            # '-'이 아니면 Path 객체로 변환, '-'면 그대로 (표준입력 의미)


# === 메인 로그 읽기 클래스 ===
class MissionLogReader:
    """Professional log file reader with comprehensive error handling."""
    # 실제로 로그 파일을 읽고 처리하는 핵심 클래스
    
    def __init__(self, config: LogReaderConfig):
        # __init__은 "생성자" - 객체가 만들어질 때 실행됨
        # config: LogReaderConfig 타입의 매개변수를 받음
        """
        Initialize the log reader with configuration.
        
        Args:
            config: LogReaderConfig instance with reader settings
        """
        self.config = config              # 받은 설정을 내 속성으로 저장
        self._setup_logging()             # 로깅 설정 함수 호출
        self._detected_encoding = None    # 감지된 인코딩 저장할 변수 (처음엔 None)
    
    def _setup_logging(self) -> None:
        # 함수명 앞의 _는 "내부에서만 쓰는 함수"라는 의미 (private)
        # -> None은 "이 함수는 아무것도 리턴하지 않음"이라는 의미
        """Configure logging for the application."""
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
        """
        Read and display the log file contents using streaming approach.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # try: "이 부분에서 에러가 날 수도 있으니 조심해서 실행해"
            
            if self.config.file_path == '-':
                # 만약 파일 경로가 '-'면 (표준입력 의미)
                self._display_stdin()      # 표준입력에서 읽기
            else:
                # 일반 파일이면
                self._validate_file()      # 파일이 유효한지 검사
                encoding = self._detect_encoding()  # 인코딩 자동 감지
                self._stream_file_content(encoding) # 파일 내용을 스트리밍으로 출력
            return True                    # 성공하면 True 리턴
            
        # 예상 가능한 에러들을 각각 처리
        except FileNotFoundError:
            # 파일이 없을 때
            self.logger.error(f"File not found: {self.config.file_path}")
            print(f"❌ Error: The file '{self.config.file_path}' does not exist.", file=sys.stderr)
            # file=sys.stderr: 에러는 에러 출력으로 (일반 출력과 구분)
            return False
            
        except PermissionError:
            # 파일 읽기 권한이 없을 때
            self.logger.error(f"Permission denied: {self.config.file_path}")
            print(f"❌ Error: Permission denied to read '{self.config.file_path}'.", file=sys.stderr)
            return False
            
        except ValueError as e:
            # 값이 잘못되었을 때 (파일이 아닌 디렉토리 등)
            self.logger.error(f"Invalid file path: {e}")
            print(f"❌ Error: {e}", file=sys.stderr)
            return False
            
        except UnicodeDecodeError as e:
            # 인코딩 문제로 파일을 읽을 수 없을 때
            self.logger.error(f"Encoding error: {e}")
            print(f"❌ Error: Unable to decode file with any supported encoding.", file=sys.stderr)
            return False
            
        except Exception as e:
            # 위에서 처리하지 못한 모든 에러
            self.logger.exception(f"Unexpected error: {e}")
            print(f"❌ Unexpected error: {e}", file=sys.stderr)
            return False
    
    def _validate_file(self) -> None:
        # 파일이 존재하고 읽을 수 있는지 검사
        """
        Validate that the file exists and is readable.
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file isn't readable
            ValueError: If the path is not a file
        """
        file_path = self.config.file_path  # 설정에서 파일 경로 가져오기
        
        if not file_path.exists():
            # exists(): 파일/폴더가 존재하는지 확인
            raise FileNotFoundError(f"File not found: {file_path}")
            # raise: 에러를 강제로 발생시킴
        
        if not file_path.is_file():
            # is_file(): 일반 파일인지 확인 (폴더가 아닌)
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Cross-platform readable check (운영체제 상관없이 읽기 권한 확인)
        if not os.access(file_path, os.R_OK):
            # os.access(경로, 권한): 해당 권한이 있는지 확인
            # os.R_OK: 읽기 권한 확인 상수
            raise PermissionError(f"File is not readable: {file_path}")
    
    def _detect_encoding(self) -> str:
        # 파일의 인코딩을 자동으로 감지
        """
        Detect file encoding by trying candidate encodings.
        
        Returns:
            str: The detected encoding
            
        Raises:
            UnicodeDecodeError: If no encoding works
        """
        if self.config.encoding != 'auto':
            # 사용자가 특정 인코딩을 지정했으면 그대로 사용
            return self.config.encoding
            
        file_path = self.config.file_path
        
        # 여러 인코딩을 시도해봄
        for encoding in self.config.candidate_encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # with문: 파일을 안전하게 열고 자동으로 닫아줌
                    # Try to read first chunk to validate encoding
                    f.read(1024)  # 첫 1KB만 읽어서 인코딩이 맞는지 테스트
                self.logger.info(f"Detected encoding: {encoding}")
                return encoding  # 성공하면 이 인코딩 사용
            except UnicodeDecodeError:
                continue  # 실패하면 다음 인코딩 시도
        
        # 모든 인코딩이 실패하면 에러 발생
        raise UnicodeDecodeError("Unable to detect encoding", str(file_path), 0, 1, "All candidate encodings failed")
    
    def _stream_file_content(self, encoding: str) -> None:
        # 파일을 스트리밍 방식으로 읽어서 출력
        # 스트리밍: 전체를 메모리에 올리지 않고 조금씩 읽어서 바로 출력
        """
        Stream file content in chunks for memory efficiency.
        
        Args:
            encoding: The file encoding to use
        """
        file_path = self.config.file_path
        
        if self.config.show_timestamp:
            # 타임스탬프를 보여주는 설정이면 헤더 출력
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
        
        if self.config.show_timestamp:
            # 타임스탬프 설정이면 푸터도 출력
            self._print_footer()
    
    def _display_stdin(self) -> None:
        # 표준입력(키보드나 파이프)에서 내용을 읽어서 출력
        """Display content from standard input."""
        if self.config.show_timestamp:
            self._print_header()
        
        line_number = 1
        
        if self.config.show_line_numbers:
            for line in sys.stdin:
                # sys.stdin: 표준입력 (키보드나 파이프로 들어오는 데이터)
                print(f"{line_number:>6} | {line}", end='')
                line_number += 1
        else:
            # Stream stdin directly (표준입력을 바로 스트리밍)
            for chunk in iter(lambda: sys.stdin.read(self.config.chunk_size), ''):
                # iter(함수, 끝값): 함수를 반복 호출하다가 끝값이 나오면 중단
                # lambda: 간단한 익명 함수
                print(chunk, end='')
        
        if self.config.show_timestamp:
            self._print_footer()
    
    def _print_header(self) -> None:
        # 예쁜 헤더 출력
        """Print formatted header with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 현재 시간을 문자열로 변환
        
        if self.config.file_path == '-':
            header = f"\n{'='*60}\n📄 Reading from: STDIN\n"
            # '='*60: =을 60개 반복
        else:
            header = f"\n{'='*60}\n📄 Log File: {self.config.file_path.name}\n"
            # .name: 파일명만 (경로 제외)
        header += f"📅 Read at: {timestamp}\n{'='*60}\n"
        print(header)
    
    def _print_footer(self) -> None:
        # 예쁜 푸터 출력
        """Print formatted footer."""
        print(f"\n{'='*60}\n✅ End of log file\n{'='*60}")


# === 파일 분석 클래스 ===
class LogFileAnalyzer:
    # 로그 파일의 통계 정보를 분석하는 클래스
    """Advanced analyzer for log file statistics."""
    
    @staticmethod  # 정적 메서드: 클래스 인스턴스 없이도 호출 가능
    def analyze(file_path: Path, encoding: str = 'utf-8') -> dict:
        # 파일을 분석해서 통계 정보를 딕셔너리로 리턴
        """
        Analyze log file and return statistics using streaming approach.
        
        Args:
            file_path: Path to the log file
            encoding: File encoding to use
            
        Returns:
            dict: Statistics about the log file
        """
        stats = {
            # 통계 정보를 저장할 딕셔너리
            'file_size': file_path.stat().st_size,  # 파일 크기 (바이트)
            'line_count': 0,     # 줄 개수
            'word_count': 0,     # 단어 개수
            'char_count': 0,     # 문자 개수
            'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime)
            # 마지막 수정 시간
        }
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                # errors='ignore': 인코딩 에러가 나도 무시하고 계속
                for line in f:
                    stats['line_count'] += 1              # 줄 개수 증가
                    stats['word_count'] += len(line.split())  # 단어 개수 증가
                    # line.split(): 공백으로 나누어서 단어 리스트 만듦
                    stats['char_count'] += len(line)      # 문자 개수 증가
        except Exception as e:
            # 파일을 읽을 수 없으면 부분 통계만 리턴
            logging.warning(f"Could not analyze file content: {e}")
        
        return stats


# === 명령줄 옵션 처리 ===
def create_parser() -> argparse.ArgumentParser:
    # 명령줄 옵션(-n, --help 등)을 처리하는 파서 생성
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Mission Computer Log Reader - Professional log file viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,  # 설명 형식 유지
        epilog="""
Examples:
  %(prog)s mission_computer_main.log          # Read log file
  %(prog)s -n mission_computer_main.log       # Show line numbers
  %(prog)s -e cp949 korean_log.txt           # Specify encoding
  cat logfile | %(prog)s -                   # Read from stdin
  %(prog)s --no-timestamp -n - < input.log   # Minimal output from stdin
        """
        # %(prog)s: 프로그램 이름으로 자동 치환
    )
    
    # 필수 인자: 파일명
    parser.add_argument(
        'file', 
        help='Log file path (use "-" for stdin)'  # 도움말
    )
    
    # 선택 인자들
    parser.add_argument(
        '-n', '--line-numbers',   # 짧은 이름, 긴 이름
        action='store_true',      # 플래그 옵션 (True/False)
        help='Show line numbers'
    )
    
    parser.add_argument(
        '-e', '--encoding',
        default='auto',           # 기본값
        help='File encoding (default: auto-detect)'
    )
    
    parser.add_argument(
        '--no-timestamp',
        action='store_true',
        help='Hide timestamp headers'
    )
    
    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='Hide file statistics'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,                 # 정수 타입으로 변환
        default=8192,
        help='Chunk size for reading (default: 8192)'
    )
    
    return parser


# === 메인 함수 ===
def main() -> int:
    # 프로그램의 시작점
    """
    Main entry point for the application.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = create_parser()        # 명령줄 파서 생성
    args = parser.parse_args()      # 실제 명령줄 인자 분석
    
    # Create configuration from CLI arguments
    # 명령줄 인자로부터 설정 객체 생성
    config = LogReaderConfig(
        file_path=args.file,
        encoding=args.encoding,
        show_line_numbers=args.line_numbers,
        show_timestamp=not args.no_timestamp,  # not: 반대로
        chunk_size=args.chunk_size
    )
    
    # Create reader and execute
    reader = MissionLogReader(config)   # 로그 리더 객체 생성
    
    # Read and display the log
    success = reader.read_and_display()  # 실제 로그 읽