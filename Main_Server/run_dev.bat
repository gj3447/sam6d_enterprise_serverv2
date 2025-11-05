@echo off
REM Main_Server 개발 환경 실행 스크립트 (Windows)

setlocal

set "APP_ENV=dev"

echo ========================================
echo Main_Server Development Mode Starting...
echo ========================================

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

REM config_dev.env 파일 사용 (설정 파일 자동 로드됨)

REM Python 경로 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python이 설치되어 있지 않습니다.
    pause
    exit /b 1
)

echo.
echo 개발 환경 설정:
echo   App Env: %APP_ENV%
echo   Host: %HOST%
echo   Port: %PORT%
echo   Log Level: %LOG_LEVEL%
echo   Reload: %RELOAD%
echo.

echo 서버를 개발 모드로 시작합니다...
echo (코드 변경 시 자동 재시작됩니다)
echo.
echo 종료: Ctrl+C
echo.

REM 개발 모드 실행 (자동 재시작 활성화)
python main.py

pause

