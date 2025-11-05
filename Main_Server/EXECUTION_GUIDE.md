# Main_Server 실행 가이드

## 🎯 실행 모드 비교

| 모드 | 자동 재시작 | 로그 레벨 | 용도 | 스크립트 |
|------|------------|----------|------|---------|
| **개발** | ✅ Yes | DEBUG | 개발/테스트 | `run_dev.bat/sh` |
| **프로덕션** | ❌ No | INFO | 실제 운영 | `run_server.bat/sh` |

## 🚀 빠른 실행

### 1. 개발 모드 (추천 - 코드 변경 시 자동 재시작)

**Windows:**
```cmd
cd Main_Server
run_dev.bat
```

**특징:**
- LOG_LEVEL=DEBUG (상세 로그)
- RELOAD=true (파일 변경 시 자동 재시작)
- 포그라운드 실행 (로그 확인)

### 2. 프로덕션 모드 (백그라운드 실행)

**Windows:**
```cmd
cd Main_Server
run_server.bat
```

**특징:**
- LOG_LEVEL=INFO (일반 로그)
- RELOAD=false (안정적 실행)
- 백그라운드 실행

## 📋 환경 변수

모든 스크립트는 다음 환경 변수를 지원합니다:

```bash
HOST=0.0.0.0           # 서버 호스트 (기본값)
PORT=8001              # 서버 포트 (기본값)
LOG_LEVEL=INFO         # 로그 레벨: DEBUG, INFO, WARNING, ERROR
RELOAD=false           # 자동 재시작: true/false
```

## 🔍 서버 실행 확인

### 1. 헬스 체크
```bash
curl http://localhost:8001/health
```

### 2. API 문서 확인
```bash
# 브라우저에서 열기
http://localhost:8001/docs
```

### 3. 서버 상태 확인
```bash
curl http://localhost:8001/api/v1/servers/status
```

## 📝 로그 확인

### 로그 파일 위치
```
Main_Server/
└── logs/
    └── main_server_YYYYMMDD.log
```

### 실시간 로그 확인
```bash
# Windows PowerShell
Get-Content logs\main_server_*.log -Wait -Tail 50

# Linux/Mac
tail -f logs/main_server_*.log

# 또는 모든 로그 파일
tail -f logs/*.log
```

## 🛑 서버 중지

### Windows (개발 모드)
```cmd
# 포그라운드에서 실행 중인 경우
Ctrl+C
```

### Windows (프로덕션 모드)
```cmd
# PID 찾기
netstat -ano | findstr :8001

# 프로세스 종료
taskkill /F /PID <PID>
```

### Linux
```bash
# 스크립트 사용
./stop_server.sh

# 또는 직접
kill $(cat logs/server.pid)
```

## ⚠️ 문제 해결

### 1. 포트가 이미 사용 중
```bash
# 포트 확인 (Windows)
netstat -ano | findstr :8001

# 포트 확인 (Linux)
lsof -i :8001
```

### 2. 로그 파일이 생성되지 않음
```bash
# logs 디렉토리 생성
mkdir logs
```

### 3. 모듈 import 에러
```bash
# 프로젝트 루트에서 실행
cd C:\CD\PROJECT\BINPICKING\Estimation_Server\Main_Server

# 의존성 재설치
pip install -r requirements.txt
鵬

## 📊 추천 설정

### 개발 초기 단계
```cmd
run_dev.bat  # 자동 재시작 + DEBUG 로그
```

### 테스트 단계
```cmd
# 환경 변수로 설정
set LOG_LEVEL=INFO
set RELOAD=true
python main.py
```

### 운영 환경
```cmd
run_server.bat  # 안정적 실행 + INFO 로그
```

