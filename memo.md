__pycache__ 란?
생성 이유: 파이썬은 실행 속도를 높이기 위해 우리가 작성한 .py 소스 코드를 **바이트코드(bytecode)**라는 중간 형태로 미리 변환(컴파일)합니다. __pycache__는 이 바이트코드 파일(.pyc)을 저장하는 캐시(cache) 폴더입니다.

작동 방식: 파이썬 프로그램을 다시 실행할 때, 소스 코드가 변경되지 않았다면 파이썬 인터프리터는 컴파일 과정을 건너뛰고 __pycache__ 폴더에 있는 .pyc 파일을 바로 실행합니다. 이 덕분에 프로그램의 시작 속도가 빨라집니다.



주요 항목 그룹:

바이트코드 및 캐시 파일: __pycache__/, *.py[cod], .mypy_cache/ 등

가상환경 폴더: .venv/, venv/, ENV/ 등

패키징 및 배포 파일: build/, dist/, *.egg-info/, wheels/ 등

테스트 및 커버리지 리포트: .tox/, .coverage, htmlcov/, .pytest_cache/ 등

에디터 및 IDE 설정 파일: .vscode/, .idea/ (PyCharm), .spyderproject 등

OS 생성 파일: Thumbs.db (Windows), .DS_Store (macOS)

보안 정보 파일: .env (환경 변수 파일)

기타 로그 및 임시 파일: *.log, pip-log.txt 등



# # # Flask 프로젝트에 특화된 추가 항목 # # #

# Flask-specific
instance/     
Flask 애플리케이션의 인스턴스 폴더입니다. 데이터베이스 파일이나 설정 파일과 같이, 버전 관리 시스템에 포함되어서는 안 되는 민감한 정보를 저장하는 데 주로 사용됩니다.

.webassets-cache
웹 에셋(CSS, JS)의 캐시 폴더입니다.

# Database files
*.sqlite3
*.db

개발용으로 사용하는 SQLite 데이터베이스 파일입니다. 실제 데이터는 저장소에 올리지 않는 것이 원칙입니다.