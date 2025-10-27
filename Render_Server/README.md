# Render Server

Render Server는 CAD 모델로부터 템플릿을 생성하는 FastAPI 서버입니다.

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [시스템 요구사항](#시스템-요구사항)
- [설치 및 실행](#설치-및-실행)
- [API 사용법](#api-사용법)
- [테스트](#테스트)
- [문제 해결](#문제-해결)
- [개발자 가이드](#개발자-가이드)

## 🎯 개요

Render_Server는 BlenderProc을 사용하여 CAD 모델로부터 다양한 시점의 템플릿 이미지를 생성하는 서버입니다. SAM-6D 모델에서 사용할 수 있는 RGB, 마스크, NOCS 좌표 템플릿을 생성합니다.

### 주요 특징

- **FastAPI 기반**: 고성능 비동기 웹 서버
- **BlenderProc 통합**: 고품질 3D 렌더링
- **다양한 시점**: 42개의 카메라 포즈에서 템플릿 생성
- **RESTful API**: 표준 HTTP API 인터페이스
- **로깅 시스템**: 상세한 로그 기록 및 파일 저장
- **Docker 지원**: 컨테이너화된 환경에서 실행

## 🚀 주요 기능

### 1. 템플릿 생성 API
- CAD 모델 파일 입력
- 다양한 렌더링 옵션 설정
- RGB, 마스크, NOCS 좌표 템플릿 생성
- 배치 템플릿 생성 지원

### 2. 렌더링 옵션
- 모델 정규화 설정
- 컬러링 옵션
- 카메라 포즈 커스터마이징
- 출력 품질 설정

### 3. 헬스 체크
- 서버 상태 모니터링
- 렌더링 작업 상태 확인
- 시스템 리소스 정보

## 💻 시스템 요구사항

### 하드웨어
- **CPU**: 멀티코어 프로세서 (렌더링 집약적)
- **메모리**: 최소 8GB RAM
- **저장공간**: 최소 5GB 여유 공간
- **GPU**: 선택사항 (BlenderProc GPU 가속)

### 소프트웨어
- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **Blender**: 3.0 이상 (BlenderProc 요구사항)

### Python 환경
- **Python**: 3.8 이상
- **BlenderProc**: 3D 렌더링 라이브러리
- **FastAPI**: 웹 서버 프레임워크
- **OpenCV**: 이미지 처리

## 🛠 설치 및 실행

### 1. Docker 환경 설정

```bash
# Render_Server 디렉토리로 이동
cd Render_Server

# Docker Compose로 서버 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f render-server
```

### 2. 서버 상태 확인(헬스)

```bash
# 헬스 체크
curl http://localhost:8004/health
```

### 3. 서버 중지

```bash
# 서버 중지
docker-compose down
```

## 📡 API 사용법

### 기본 정보

- **서버 URL**: `http://localhost:8004`
- **API 문서**: `http://localhost:8004/docs` (Swagger UI)
- **API 버전**: v1

### 간단 서버 API (현재 구현)

#### 1) 템플릿 생성(동기/비동기)

```bash
POST /render/templates?wait=<true|false>&wait_timeout_sec=<초>

# 요청(JSON)
{
  "cad_path": "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply",
  "output_dir": "/workspace/Estimation_Server/Render_Server/test",
  "colorize": false,
  "base_color": 0.05
}

# 비동기(기본)
curl -X POST "http://localhost:8004/render/templates" \
  -H "Content-Type: application/json" \
  -d '{
        "cad_path":"/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply",
        "output_dir":"/workspace/Estimation_Server/Render_Server/test",
        "colorize":false,
        "base_color":0.05
      }'

# 동기(완료까지 대기)
curl -X POST "http://localhost:8004/render/templates?wait=true&wait_timeout_sec=3600" \
  -H "Content-Type: application/json" \
  -d '{
        "cad_path":"/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply",
        "output_dir":"/workspace/Estimation_Server/Render_Server/test",
        "colorize":false,
        "base_color":0.05
      }'
```

응답:
- 비동기: `{ "job_id": "...", "status": "queued" }`
- 동기: `{ status: succeeded|failed|timeout, log_path, returncode, elapsed_sec, ... }`

로그 위치: `Render_Server/logs/<job_id>.log`

#### 2) 작업 상태 조회(비동기 흐름용)

```bash
GET /jobs/{job_id}

curl http://localhost:8004/jobs/<job_id>
```

응답:
`{ status, cad_path, output_dir, started_at, ended_at, elapsed_sec, log_path, returncode? }`

### 주요 엔드포인트

#### 1. 헬스 체크

```bash
GET /health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "message": "Render Server is running",
  "timestamp": 1234567890.123
}
```

#### 2. 서버 상태

```bash
GET /api/v1/status
```

**응답 예시:**
```json
{
  "server": "running",
  "renderer_ready": true,
  "uptime": 1234567890.123,
  "version": "1.0.0"
}
```

#### 3. 템플릿 생성

```bash
POST /api/v1/render-templates
```

**요청 형식:**
```json
{
  "cad_path": "/path/to/cad/model.ply",
  "output_dir": "/path/to/output",
  "normalize": true,
  "colorize": false,
  "base_color": 0.05,
  "camera_poses_path": "/path/to/camera_poses.npy"
}
```

**응답 예시:**
```json
{
  "success": true,
  "total_poses": 42,
  "rendered_count": 42,
  "output_dir": "/path/to/output/templates",
  "cad_path": "/path/to/cad/model.ply",
  "normalize": true,
  "colorize": false,
  "base_color": 0.05,
  "rendering_time": 120.5
}
```

#### 4. 배치 템플릿 생성

```bash
POST /api/v1/render-templates-batch
```

여러 CAD 모델에 대해 배치로 템플릿을 생성합니다.

## 🧪 테스트

### 1. 템플릿 생성 테스트

```bash
# Docker 컨테이너 내에서 실행
docker-compose exec render-server bash -c "source /opt/conda/bin/activate sam6d && cd /workspace/Estimation_Server/Render_Server && python test_render_api.py"
```

### 2. 테스트 결과 예시

```
[INFO] Render Server 템플릿 생성 API 테스트 시작
==================================================
[INFO] 서버 상태 확인 중...
[SUCCESS] 서버 상태: {'server': 'running', 'renderer_ready': True}

==================================================
[INFO] 템플릿 생성 테스트 시작...
[SUCCESS] 템플릿 생성 성공!
   - 성공 여부: True
   - 렌더링 시간: 120.5초
   - 생성된 템플릿 수: 42/42
   - 출력 디렉토리: /path/to/output/templates

[SUCCESS] 모든 테스트가 완료되었습니다!
```

### 3. 성능 지표

- **렌더링 시간**: ~2분 (42개 템플릿)
- **메모리 사용량**: ~2GB RAM
- **생성 파일**: RGB, 마스크, NOCS 좌표
- **템플릿 품질**: 고해상도 렌더링

## 🔧 문제 해결

### 일반적인 문제

#### 1. BlenderProc 초기화 실패

**증상:**
```
Failed to initialize BlenderProc
```

**해결방법:**
1. Blender 설치 확인
2. DISPLAY 환경변수 설정
3. 서버 재시작

```bash
docker-compose restart render-server
```

#### 2. CAD 파일 로드 실패

**증상:**
```
CAD file not found or invalid format
```

**해결방법:**
1. CAD 파일 경로 확인
2. 파일 형식 확인 (.ply, .obj, .stl 지원)
3. 파일 권한 확인

#### 3. 메모리 부족

**증상:**
```
Out of memory during rendering
```

**해결방법:**
1. 시스템 메모리 확인
2. 동시 렌더링 작업 수 제한
3. Docker 메모리 제한 설정

### 로그 확인

```bash
# 실시간 로그 확인
docker-compose logs -f render-server

# 로그 파일 위치
Render_Server/logs/<job_id>.log
```

## 👨‍💻 개발자 가이드

### 프로젝트 구조

```
Render_Server/
├── main.py                    # FastAPI 애플리케이션
├── render_custom_templates.py  # 템플릿 생성 함수
├── test_render_api.py         # API 테스트 스크립트
├── requirements.txt           # Python 의존성
├── docker-compose.yml         # Docker Compose 설정
├── Dockerfile                 # Docker 이미지 정의
├── log/                       # 로그 파일 디렉토리
└── README.md                  # 이 파일
```

### 주요 컴포넌트

#### 1. 템플릿 생성 함수
- BlenderProc 기반 렌더링
- 다중 카메라 포즈 지원
- RGB, 마스크, NOCS 좌표 생성

#### 2. API 엔드포인트
- 템플릿 생성 요청 처리
- 배치 처리 지원
- 진행 상황 모니터링

#### 3. 로깅 시스템
- 파일 기반 로깅
- 렌더링 과정 상세 기록
- 에러 추적

### 환경 변수

- `RENDER_SERVER_HOST`: 서버 호스트 (기본값: 0.0.0.0)
- `RENDER_SERVER_PORT`: 서버 포트 (기본값: 8004)
- `RENDER_LOG_LEVEL`: 로그 레벨 (기본값: INFO)
- `BLENDER_PROC_SAMPLES`: 렌더링 샘플 수 (기본값: 50)

### 볼륨 마운트

- `..:/workspace/Estimation_Server`: Estimation_Server 전체 마운트
- `.:/workspace/Render_Server`: Render_Server 코드 마운트 (개발용)

### 포트

- `8004`: Render 서버 API 포트

### 개발 환경 설정

```bash
# 개발용 컨테이너 실행
docker-compose up -d

# 컨테이너 접속
docker exec -it render-server bash

# 컨테이너 내부에서 작업
conda activate sam6d
cd /workspace/Estimation_Server/Render_Server
```

### 코드 스타일

- **Python**: PEP 8 준수
- **API**: RESTful 설계 원칙
- **로깅**: 구조화된 로그 메시지
- **에러 처리**: 명확한 에러 메시지

## 📊 성능 지표

### 일반적인 성능

- **렌더링 시간**: ~2분 (42개 템플릿)
- **메모리 사용량**: ~2GB RAM
- **CPU 사용률**: 높음 (렌더링 집약적)
- **생성 파일 크기**: ~50MB (42개 템플릿)

### 최적화 팁

1. **병렬 처리**: 여러 CAD 모델 동시 처리
2. **캐싱**: 동일한 CAD 모델 재사용
3. **품질 조절**: 샘플 수 조정으로 속도 향상
4. **리소스 관리**: 메모리 사용량 모니터링

## 🔄 다른 서버와의 연동

Render_Server는 다른 서버들과 함께 사용됩니다:

1. **Render_Server**: CAD 모델로부터 템플릿 생성
2. **ISM_Server**: 템플릿을 사용한 인스턴스 세그멘테이션
3. **PEM_Server**: 세그멘테이션 결과를 기반으로 포즈 추정

### 연동 워크플로우

```
CAD 모델 → Render_Server → 템플릿 → ISM_Server → PEM_Server → 최종 결과
```

## 📝 라이선스

이 프로젝트는 BlenderProc과 SAM-6D 모델을 기반으로 하며, 해당 라이선스를 따릅니다.

## 🤝 기여

버그 리포트나 기능 요청은 이슈 트래커를 통해 제출해 주세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 로그 파일과 함께 문의해 주세요.

---

**Render Server v1.0.0** - BlenderProc 기반 템플릿 생성 서버
