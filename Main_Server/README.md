# Main Server

## 🎯 개요

Main_Server는 포트 8001에서 실행되는 중앙 관리 서버로, 전체 시스템의 객체 데이터베이스 관리와 서버 오케스트레이션을 담당합니다.

## ✨ 주요 기능

- ✅ Static 폴더 스캔 및 객체 정보 제공
- ✅ 서버 상태 모니터링 (ISM, PEM, Render)
- ✅ 전체 파이프라인 자동 실행 (Render → ISM → PEM)
- ✅ 백그라운드 실행 지원
- ✅ 자동 로깅 (일자별 로그 파일)

## 🚀 빠른 시작

### 개발 모드 실행 (코드 자동 재시작)

**Windows:**
```cmd
run_dev.bat
```

**Linux/Mac:**
```bash
chmod +x run_dev.sh
./run_dev.sh
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

### 일반 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python main.py
```

## 📚 상세 문서

- **[README_BACKGROUND.md](./README_BACKGROUND.md)** - 백그라운드 실행 가이드
- **[DESIGN.md](./DESIGN.md)** - 설계 문서
- **[EXECUTION_GUIDE.md](./EXECUTION_GUIDE.md)** - 실행 가이드
- **[docs/](./docs/)** - 추가 문서들

## 🧪 테스트 스크립트

- `test_api_full_pipeline.py` - API 전체 파이프라인 테스트
- `test_rss_api_call.py` - RSS 기반 API 테스트
- `test_ycb_full_pipeline.py` - YCB 객체 파이프라인 테스트
- `create_ycb_template.py` - YCB 템플릿 생성 스크립트

## 📊 API 문서

서버 실행 후 브라우저에서 확인:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🔍 현재 상태

- 코드 구현: 완료 ✅
- 로깅 시스템: 추가됨 ✅
- 백그라운드 실행: 지원 ✅
- 에러 핸들링: 강화됨 ✅

## ⚙️ 환경 설정

```bash
# config.env 파일 수정 또는 환경 변수 설정
export HOST=0.0.0.0
export PORT=8001
export LOG_LEVEL=INFO
export RELOAD=false
```

## 📝 로그 확인

```bash
# 로그 파일 위치
logs/main_server_YYYYMMDD.log

# 실시간 로그 확인 (Linux)
tail -f logs/server.log
```

## 🆘 트러블슈팅

1. **로그 파일 확인**: `logs/` 디렉토리
2. **서버 상태 확인**: `http://localhost:8001/health`
3. **다른 서버 연결 확인**: `http://localhost:8001/api/v1/servers/status`

## 📦 폴더 정리

- 과거 파일들은 `archive/` 폴더에 보관되어 있습니다
- 상세한 정리 내용은 [docs/CLEANUP_SUMMARY.md](./docs/CLEANUP_SUMMARY.md)를 참조하세요
- 핵심 기능은 루트 폴더의 파일들로 사용 가능합니다
