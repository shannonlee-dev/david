import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional, Union, List, Iterator
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class LogLevel(Enum):
    """Log level enumeration for output formatting."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


@dataclass
class LogReaderConfig:
    """Configuration for the log reader."""
    file_path: Union[Path, str]
    encoding: str = 'auto'
    show_line_numbers: bool = False
    show_timestamp: bool = True
    chunk_size: int = 8192  # 8KB chunks for streaming
    candidate_encodings: List[str] = None
    
    def __post_init__(self):
        if self.candidate_encodings is None:
            self.candidate_encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin1']
        
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path) if self.file_path != '-' else '-'


class MissionLogReader:
    """Professional log file reader with comprehensive error handling."""
    
    def __init__(self, config: LogReaderConfig):
        """
        Initialize the log reader with configuration.
        
        Args:
            config: LogReaderConfig instance with reader settings
        """
        self.config = config
        self._setup_logging()
        self._detected_encoding = None
    
    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def read_and_display(self) -> bool:
        """
        Read and display the log file contents using streaming approach.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.config.file_path == '-':
                self._display_stdin()
            else:
                self._validate_file()
                encoding = self._detect_encoding()
                self._stream_file_content(encoding)
            return True
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {self.config.file_path}")
            print(f"❌ Error: The file '{self.config.file_path}' does not exist.", file=sys.stderr)
            return False
            
        except PermissionError:
            self.logger.error(f"Permission denied: {self.config.file_path}")
            print(f"❌ Error: Permission denied to read '{self.config.file_path}'.", file=sys.stderr)
            return False
            
        except ValueError as e:
            self.logger.error(f"Invalid file path: {e}")
            print(f"❌ Error: {e}", file=sys.stderr)
            return False
            
        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error: {e}")
            print(f"❌ Error: Unable to decode file with any supported encoding.", file=sys.stderr)
            return False
            
        except Exception as e:
            self.logger.exception(f"Unexpected error: {e}")
            print(f"❌ Unexpected error: {e}", file=sys.stderr)
            return False
    
    def _validate_file(self) -> None:
        """
        Validate that the file exists and is readable.
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file isn't readable
            ValueError: If the path is not a file
        """
        file_path = self.config.file_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Cross-platform readable check
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"File is not readable: {file_path}")
    
    def _detect_encoding(self) -> str:
        """
        Detect file encoding by trying candidate encodings.
        
        Returns:
            str: The detected encoding
            
        Raises:
            UnicodeDecodeError: If no encoding works
        """
        if self.config.encoding != 'auto':
            return self.config.encoding
            
        file_path = self.config.file_path
        
        for encoding in self.config.candidate_encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Try to read first chunk to validate encoding
                    f.read(1024)
                self.logger.info(f"Detected encoding: {encoding}")
                return encoding
            except UnicodeDecodeError:
                continue
        
        raise UnicodeDecodeError("Unable to detect encoding", str(file_path), 0, 1, "All candidate encodings failed")
    
    def _stream_file_content(self, encoding: str) -> None:
        """
        Stream file content in chunks for memory efficiency.
        
        Args:
            encoding: The file encoding to use
        """
        file_path = self.config.file_path
        
        if self.config.show_timestamp:
            self._print_header()
        
        line_number = 1
        
        with open(file_path, 'r', encoding=encoding, buffering=self.config.chunk_size) as f:
            if self.config.show_line_numbers:
                # For line numbers, we need to process line by line
                for line in f:
                    print(f"{line_number:>6} | {line}", end='')
                    line_number += 1
            else:
                # Stream in chunks for better performance
                while True:
                    chunk = f.read(self.config.chunk_size)
                    if not chunk:
                        break
                    print(chunk, end='')
        
        if self.config.show_timestamp:
            self._print_footer()
    
    def _display_stdin(self) -> None:
        """Display content from standard input."""
        if self.config.show_timestamp:
            self._print_header()
        
        line_number = 1
        
        if self.config.show_line_numbers:
            for line in sys.stdin:
                print(f"{line_number:>6} | {line}", end='')
                line_number += 1
        else:
            # Stream stdin directly
            for chunk in iter(lambda: sys.stdin.read(self.config.chunk_size), ''):
                print(chunk, end='')
        
        if self.config.show_timestamp:
            self._print_footer()
    
    def _print_header(self) -> None:
        """Print formatted header with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.config.file_path == '-':
            header = f"\n{'='*60}\n📄 Reading from: STDIN\n"
        else:
            header = f"\n{'='*60}\n📄 Log File: {self.config.file_path.name}\n"
        header += f"📅 Read at: {timestamp}\n{'='*60}\n"
        print(header)
    
    def _print_footer(self) -> None:
        """Print formatted footer."""
        print(f"\n{'='*60}\n✅ End of log file\n{'='*60}")


class LogFileAnalyzer:
    """Advanced analyzer for log file statistics."""
    
    @staticmethod
    def analyze(file_path: Path, encoding: str = 'utf-8') -> dict:
        """
        Analyze log file and return statistics using streaming approach.
        
        Args:
            file_path: Path to the log file
            encoding: File encoding to use
            
        Returns:
            dict: Statistics about the log file
        """
        stats = {
            'file_size': file_path.stat().st_size,
            'line_count': 0,
            'word_count': 0,
            'char_count': 0,
            'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime)
        }
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                for line in f:
                    stats['line_count'] += 1
                    stats['word_count'] += len(line.split())
                    stats['char_count'] += len(line)
        except Exception as e:
            # If we can't read the file, return partial stats
            logging.warning(f"Could not analyze file content: {e}")
        
        return stats


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Mission Computer Log Reader - Professional log file viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s mission_computer_main.log          # Read log file
  %(prog)s -n mission_computer_main.log       # Show line numbers
  %(prog)s -e cp949 korean_log.txt           # Specify encoding
  cat logfile | %(prog)s -                   # Read from stdin
  %(prog)s --no-timestamp -n - < input.log   # Minimal output from stdin
        """
    )
    
    parser.add_argument(
        'file', 
        help='Log file path (use "-" for stdin)'
    )
    
    parser.add_argument(
        '-n', '--line-numbers', 
        action='store_true',
        help='Show line numbers'
    )
    
    parser.add_argument(
        '-e', '--encoding',
        default='auto',
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
        type=int,
        default=8192,
        help='Chunk size for reading (default: 8192)'
    )
    
    return parser


def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Create configuration from CLI arguments
    config = LogReaderConfig(
        file_path=args.file,
        encoding=args.encoding,
        show_line_numbers=args.line_numbers,
        show_timestamp=not args.no_timestamp,
        chunk_size=args.chunk_size
    )
    
    # Create reader and execute
    reader = MissionLogReader(config)
    
    # Read and display the log
    success = reader.read_and_display()
    
    # Optional: Display statistics for files (not stdin)
    if success and not args.no_stats and config.file_path != '-' and Path(config.file_path).exists():
        print("\n📊 File Statistics:")
        try:
            encoding = reader._detected_encoding or config.encoding
            if encoding == 'auto':
                encoding = 'utf-8'
            stats = LogFileAnalyzer.analyze(Path(config.file_path), encoding)
            print(f"  • Size: {stats['file_size']:,} bytes")
            print(f"  • Lines: {stats['line_count']:,}")
            print(f"  • Words: {stats['word_count']:,}")
            print(f"  • Characters: {stats['char_count']:,}")
            print(f"  • Last Modified: {stats['last_modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logging.warning(f"Could not generate statistics: {e}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())