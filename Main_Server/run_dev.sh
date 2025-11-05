#!/bin/bash
# Main_Server 개발 환경 실행 스크립트 (Linux)

echo "========================================"
echo "Main_Server Development Mode Starting..."
echo "========================================"

# 로그 디렉토리 생성
mkdir -p logs

# 개발 환경 변수 설정
export APP_ENV=dev
export HOST=0.0.0.0
export PORT=8001
export LOG_LEVEL=DEBUG
export RELOAD=true

# Python 경로 확인
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3가 설치되어 있지 않습니다."
    exit 1
fi

echo ""
echo "개발 환경 설정:"
echo "  App Env: $APP_ENV"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Log Level: $LOG_LEVEL"
echo "  Reload: $RELOAD"
echo ""

echo "서버를 개발 모드로 시작합니다..."
echo "(코드 변경 시 자동 재시작됩니다)"
echo ""
echo "종료: Ctrl+C"
echo ""

# 개발 모드 실행 (자동 재시작 활성화)
python3 main.py

