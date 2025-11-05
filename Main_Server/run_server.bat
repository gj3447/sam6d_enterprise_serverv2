@echo off
REM Main_Server 백그라운드 실행 스크립트 (Windows)

setlocal

set "APP_ENV=prod"

echo ========================================
echo Main_Server Starting...
echo ========================================

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

REM config.env 파일 사용 (설정 파일 자동 로드됨)

REM Python 경로 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python이 설치되어 있지 않습니다.
    pause
    exit /b 1
)

REM 의존성 확인
if not exist "requirements.txt" (
    echo ERROR: requirements.txt 파일이 없습니다.
    pause
    exit /b 1
)

echo.
echo 환경 설정:
echo   App Env: %APP_ENV%
echo   Host: %HOST%
echo   Port: %PORT%
echo   Log Level: %LOG_LEVEL%
echo   Reload: %RELOAD%
echo.

REM 백그라운드 실행
echo 서버를 시작합니다...
start "Main_Server" cmd /k python main.py

echo.
echo 서버가 백그라운드에서 실행 중입니다.
echo 로그는 logs 디렉토리에서 확인하실 수 있습니다.
echo.
echo 서버 중지: taskkill /F /FI "WINDOWTITLE eq Main_Server*"
echo.

pause

