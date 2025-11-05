# Main_Server 백그라운드 실행 가이드

## 📋 개요

Main_Server는 백그라운드에서 실행될 수 있도록 다음 기능들이 추가되었습니다:

- ✅ **로깅 설정**: 일자별 로그 파일 자동 생성
- ✅ **환경 변수 지원**: HOST, PORT, LOG_LEVEL 설정 가능
- ✅ **백그라운드 실행 스크립트**: Windows/Linux 지원
- ✅ **에러 핸들링 강화**: 상세한 에러 로깅
- ✅ **서버 상태 모니터링**: 헬스 체크 및 서버 상태 확인

空中️ 실행 방법

### 개발 모드 (권장)

**Windows:**
```cmd
run_dev.bat  # 코드 변경 시 자동 재시작
```

**Linux/Mac:**
```bash
chmod +x run_dev.sh
./run_dev.sh  # 코드 변경 시 자동 재시작
```

### 백그라운드 실행 (프로덕션)

**Windows:**
```cmd
run_server.bat
```

**Linux/Mac:**
```bash
chmod +x run_server.sh
./run_server.sh
```

### 직접 실행

**개발 환경:**
```bash
set RELOAD=true
set LOG_LEVEL=DEBUG
python main.py
```

**프로덕션 환경:**
```bash
set RELOAD=false
set LOG_LEVEL=INFO
python main.py
```

### Linux 환경

```bash
# 1. 실행 권한 부여
chmod +x run_server.sh stop_server.sh

# 2. 백그라운드 실행
./run_server.sh

# 3. 서버 중지
./stop_server.sh

# 4. 또는 직접 실행
python3 main.py
```

## 📂 로그 파일

### 로그 디렉토리
```
Main_Server/
└── logs/
    ├── main_server_20250128.log  # 오늘 날짜 로그
    ├── main_server_20250127.log  # 어제 날짜 로그
    └── server.pid                 # 서버 PID (Linux)
```

### 로그 레벨
- `DEBUG`: 상세한 디버깅 정보
- `INFO`: 일반 정보 (기본값)
- `WARNING`: 경고 메시지
- `ERROR`: 에러 메시지
- `CRITICAL`: 치명적 에러

## ⚙️ 환경 변수 설정

### config.env 파일 사용

```bash
# 환경 변수 로드 (Linux)
source config.env

# 서버 실행
python3 main.py
```

### 직접 설정

```bash
# Windows (CMD)
set HOST=0.0.0.0
set PORT=8001
set LOG_LEVEL=INFO
set RELOAD=false

# Linux/Mac
export HOST=0.0.0.0
export PORT=8001
export LOG_LEVEL=INFO
export RELOAD=false
```

## 📊 서버 모니터링

### 헬스 체크

```bash
# 서버 상태 확인
curl http://localhost:8001/health

# API 문서 확인
curl http://localhost:8001/docs
```

### 로그 확인

```bash
# Windows
type logs\main_server_*.log

# Linux (실시간 로그 확인)
tail -f logs/server.log

# 또는 일자별 로그
tail -f logs/main_server_20250128.log
```

## 🔍 서버 중지

### Windows

```cmd
# 프로세스 이름으로 중지
taskkill /F /FI "WINDOWTITLE eq Main_Server*"

# 또는 PID로 중지
taskkill /F /PID <PID>
```

### Linux

```bash
# 스크립트 사용
./stop_server.sh

# 또는 직접 중지
kill $(cat logs/server.pid)

# 강제 중지
kill -9 $(cat logs/server.pid)
```

## 🐳 Docker 사용 시 주의사항

Main_Server는 다른 서버들(ISM, PEM, Render)을 오케스트레이션하는 역할을 하므로 **호스트에서 실행하는 것을 권장**합니다.

### 이유

1. **Localhost 통신**: 다른 서버들과 `localhost:8002/8003/8004`로 통신
2. **파일 시스템 접근**: `static` 폴더를 직접 스캔하고 결과 파일 생성
3. **워크플로우 오케스트레이션**: 서버 간 파일 전달 및 조율

### 대안 (모두 Docker로 실행할 경우)

```yaml
# docker-compose.yml 예시
services:
  main-server:
    build: ./Main_Server
    ports:
      - "8001:8001"
    volumes:
      - ../static:/workspace/Estimation_Server/static
    network_mode: host  # 호스트 네트워크 사용
    environment:
      - ISM_SERVER_URL=http://localhost:8002
      - PEM_SERVER_URL=http://localhost:8003
      - RENDER_SERVER_URL=http://localhost:8004
```

## 📝 주요 변경사항

### 1. 로깅 설정 추가

- `utils/logging_config.py`: 로깅 유틸리티
- 일자별 로그 파일 자동 생성
- 콘솔/파일 로그 동시 지원

### 2. main.py 업데이트

- 로깅 통합
- 환경 변수 지원
- 에러 핸들링 강화

### 3. 실행 스크립트

- `run_server.bat`: Windows 백그라운드 실행
- `run_server.sh`: Linux 백그라운드 실행
- `stop_server.sh`: 서버 중지 스크립트

### 4. 설정 파일

- `config.env`: 환경 변수 관리

## 🎯 체크리스트

백그라운드 실행 전 확인:

- [ ] `logs` 디렉토리 존재 확인
- [ ] Python 의존성 설치 완료
- [ ] 환경 변수 설정 확인
- [ ] 다른 서버들(ISM, PEM, Render) 실행 여부 확인
- [ ] 포트 8001 사용 가능 여부 확인

## 🆘 트러블슈팅

### 문제: 로그 파일이 생성되지 않음

```bash
# 해결: logs 디렉토리 수동 생성
mkdir logs
```

### 문제: 서버가 시작되지 않음

```bash
# 해결: 포트 확인
netstat -ano | findstr :8001  # Windows
lsof -i :8001                 # Linux
```

### 드러블: 로그에 에러가 보임

```bash
# 로그 확인
tail -100 logs/main_server_*.log

# 또는 DEBUG 레벨로 실행
export LOG_LEVEL=DEBUG
python3 main.py
```

