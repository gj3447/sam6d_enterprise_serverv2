#!/bin/bash
# Main_Server 중지 스크립트 (Linux)

PID_FILE="logs/server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "ERROR: 서버가 실행 중이지 않습니다. (PID 파일 없음)"
    exit 1
fi

PID=$(cat $PID_FILE)

if ! ps -p $PID > /dev/null 2>&1; then
    echo "ERROR: 서버가 실행 중이지 않습니다. (PID: $PID)"
    rm -f $PID_FILE
    exit 1
fi

echo "서버를 중지합니다... (PID: $PID)"
kill $PID

# 프로세스 종료 대기
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "서버가 정상적으로 중지되었습니다."
        rm -f $PID_FILE
        exit 0
    fi
    sleep 1
done

# 강제 종료
echo "강제 종료합니다..."
kill -9 $PID
rm -f $PID_FILE
echo "서버가 강제 종료되었습니다."

