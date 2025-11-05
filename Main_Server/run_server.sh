#!/bin/bash
# Main_Server 백그라운드 실행 스크립트 (Linux)

echo "========================================"
echo "Main_Server Starting..."
echo "========================================"

# 로그 디렉토리 생성
mkdir -p logs

# 환경 변수 설정
export APP_ENV=prod
export HOST=0.0.0.0
export PORT=8001
export LOG_LEVEL=INFO
export RELOAD=false

# Python 경로 확인
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3가 설치되어 있지 않습니다."
    exit 1
fi

# 의존성 확인
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt 파일이 없습니다."
    exit 1
fi

echo ""
echo "환경 설정:"
echo "  App Env: $APP_ENV"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Log Level: $LOG_LEVEL"
echo "  Reload: $RELOAD"
echo ""

# 백그라운드 실행
echo "서버를 시작합니다..."
nohup python3 main.py > logs/server.log 2>&1 &

# PID 저장
echo $! > logs/server.pid

echo ""
echo "서버가 백그라운드에서 실행 중입니다. (PID: $(cat logs/server.pid))"
echo "로그는 logs/server.log 파일에서 확인하실 수 있습니다."
echo ""
echo "서버 상태 확인: ps -p $(cat logs/server.pid)"
echo "서버 로그 확인: tail -f logs/server.log"
echo "서버 중지: kill $(cat logs/server.pid)"
echo ""

