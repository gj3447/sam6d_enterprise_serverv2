# 서버 무한 루프 문제 해결 (2025-10-30)

## 🔍 문제 발생

서버가 실행 중에 멈추는 현상이 발생했습니다.

## 📊 원인 분석

### 증상
- `watchfiles`가 로그 파일 변경을 계속 감지
- 무한 루프로 인한 CPU 100% 사용
- 서버 응답 불가

### 로그 예시
```
2025-10-30 15:21:27 - watchfiles.main - DEBUG - [main.py:306] - 1 change detected: {(<Change.modified: 2>, 'C:\\CD\\PROJECT\\BINPICKING\\Estimation_Server\\Main_Server\\logs\\main_server_20251030.log')}
...
(무한 반복)
```

## ✅ 해결 방법

### 1. 개발 모드 (`run_dev.bat`)
- `RELOAD=true`로 설정됨
- uvicorn의 `--reload` 옵션 사용
- `watchfiles`가 로그 파일 변경을 감지해 무한 루프 발생

### 2. 프로덕션 모드 (`run_server.bat`)
- `RELOAD=false`로 설정됨
- reload 옵션 없이 안정적으로 실행
- 무한 루프 문제 없음

## 🎯 권장 사용법

### 개발 시
```bash
# 서버를 백그라운드로 실행하지 말고 포그라운드에서 실행
cd Main_Server
python main.py
```

### 프로덕션 환경
```bash
# 프로덕션 모드로 실행 (안정적)
cd Main_Server
.\run_server.bat
```

## ⚠️ 주의사항

1. **로그 파일 경로를 제외**
   - `watchfiles`는 기본적으로 모든 파일을 감시
   - 로그 파일이 자주 변경되어 무한 루프 발생 가능

2. **개발 시 수동 실행 권장**
   - 백그라운드 실행보다 포그라운드 실행 권장
   - 문제 발생 시 즉시 확인 가능

3. **프로덕션 환경은 안정 모드 사용**
   - `RELOAD=false`로 실행
   - 안정성 확보

## 📝 참고

- `config.env`: RELOAD=false (기본)
- `config_dev.env`: RELOAD=true (개발용, 하지만 문제 있음)
- `config_prod.env`: RELOAD=false (프로덕션용)

## 🔧 추가 개선 사항 (향후)

1. `watchfiles` ignore 패턴 설정
2. 로그 디렉토리 제외
3. 개발 모드 개선






