# ISM Server

ISM (Instance Segmentation Model) Server는 SAM-6D 기반의 인스턴스 세그멘테이션 모델을 FastAPI로 구현한 서버입니다.

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

ISM_Server는 SAM-6D 모델을 활용하여 RGB-D 이미지에서 객체 인스턴스를 세그멘테이션하는 서버입니다. SAM (Segment Anything Model)과 DINOv2를 결합하여 정확한 객체 분할을 수행합니다.

### 주요 특징

- **FastAPI 기반**: 고성능 비동기 웹 서버
- **자동 모델 로딩**: 서버 시작 시 SAM-6D 모델 자동 로드
- **CUDA 지원**: GPU 가속을 통한 빠른 추론
- **RESTful API**: 표준 HTTP API 인터페이스
- **로깅 시스템**: 상세한 로그 기록 및 파일 저장
- **템플릿 기반**: 클라이언트가 제공하는 템플릿과 CAD 모델 활용

## 🚀 주요 기능

### 1. 인스턴스 세그멘테이션 API
- RGB-D 이미지 입력
- 템플릿과 CAD 모델 기반 세그멘테이션
- 객체 마스크 및 바운딩 박스 생성
- 검출 신뢰도 점수 제공

### 2. 모델 관리
- SAM 모델 자동 로딩
- DINOv2 특징 추출기 로딩
- GPU 메모리 관리

### 3. 헬스 체크
- 서버 상태 모니터링
- 모델 로딩 상태 확인
- 시스템 리소스 정보

## 💻 시스템 요구사항

### 하드웨어
- **GPU**: NVIDIA GPU (CUDA 지원)
- **메모리**: 최소 8GB RAM
- **저장공간**: 최소 10GB 여유 공간

### 소프트웨어
- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **NVIDIA Container Toolkit**: GPU 지원용

### Python 환경
- **Python**: 3.8 이상
- **PyTorch**: CUDA 지원 버전
- **FastAPI**: 웹 서버 프레임워크
- **SAM-6D**: 인스턴스 세그멘테이션 모델

## 🛠 설치 및 실행

### 1. Docker 환경 설정

```bash
# ISM_Server 디렉토리로 이동
cd ISM_Server

# Docker Compose로 서버 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f ism-server
```

### 2. 서버 상태 확인

```bash
# 헬스 체크
curl http://localhost:8002/health

# 서버 상태 확인
curl http://localhost:8002/api/v1/status
```

### 3. 서버 중지

```bash
# 서버 중지
docker-compose down
```

## 📡 API 사용법

### 기본 정보

- **서버 URL**: `http://localhost:8002`
- **API 문서**: `http://localhost:8002/docs` (Swagger UI)
- **API 버전**: v1

### 주요 엔드포인트

#### 1. 헬스 체크

```bash
GET /health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "message": "Server is running",
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
  "model_loaded": true,
  "templates_loaded": false,
  "cad_loaded": false,
  "device": "cuda",
  "num_templates": 0,
  "uptime": 1234567890.123
}
```

#### 3. 인스턴스 세그멘테이션

```bash
POST /api/v1/inference
```

**요청 형식:**
```json
{
  "rgb_image": "base64_encoded_rgb_image",
  "depth_image": "base64_encoded_depth_image",
  "cam_params": {
    "cam_K": [572.4114, 0.0, 325.2611, 0.0, 573.57043, 242.04899, 0.0, 0.0, 1.0],
    "depth_scale": 1.0
  },
  "template_dir": "/path/to/templates",
  "cad_path": "/path/to/cad/model.ply",
  "output_dir": "/path/to/output"
}
```

**응답 예시:**
```json
{
  "success": true,
  "inference_time": 10.253,
  "num_detections": 4,
  "template_dir_used": "/path/to/templates",
  "cad_path_used": "/path/to/cad/model.ply",
  "output_dir_used": "/path/to/output"
}
```

#### 4. 샘플 데이터

```bash
GET /test/sample
```

샘플 RGB-D 이미지와 카메라 파라미터를 제공합니다.

## 🧪 테스트

### 1. 추론 API 테스트

```bash
# Docker 컨테이너 내에서 실행
docker-compose exec ism-server bash -c "source /opt/conda/bin/activate sam6d && cd /workspace/Estimation_Server/ISM_Server && python test_inference_api.py"
```

### 2. 테스트 결과 예시

```
[INFO] ISM Server 추론 API 테스트 시작
==================================================
[INFO] 서버 상태 확인 중...
[SUCCESS] 서버 상태: {'server': 'running', 'model_loaded': True, 'device': 'cuda'}

==================================================
[INFO] 샘플 데이터 가져오는 중...
[SUCCESS] 샘플 데이터 가져오기 성공
   - RGB 이미지 크기: 620680 bytes
   - Depth 이미지 크기: 110764 bytes

==================================================
[INFO] 추론 API 테스트 시작...
[SUCCESS] 추론 성공!
   - 성공 여부: True
   - 추론 시간: 10.253초
   - 감지 결과 수: 4

[SUCCESS] 모든 테스트가 완료되었습니다!
```

### 3. 성능 지표

- **모델 로딩 시간**: ~20초
- **추론 시간**: ~8-10초 (4개 객체)
- **메모리 사용량**: ~4GB GPU 메모리
- **검출 정확도**: 4개 객체 검출 성공

## 🔧 문제 해결

### 일반적인 문제

#### 1. CUDA 사용 불가

**증상:**
```
RuntimeError: No CUDA GPUs are available
```

**해결방법:**
1. NVIDIA Container Toolkit 설치 확인
2. Docker Compose의 GPU 설정 확인
3. 서버 재시작

```bash
docker-compose restart ism-server
```

#### 2. 모델 로딩 실패

**증상:**
```
Model loading failed: FileNotFoundError
```

**해결방법:**
1. 모델 파일 경로 확인
2. 권한 설정 확인
3. Docker 볼륨 마운트 확인

#### 3. 메모리 부족

**증상:**
```
CUDA out of memory
```

**해결방법:**
1. GPU 메모리 정리
2. 배치 크기 감소
3. 모델 언로딩 후 재로딩

### 로그 확인

```bash
# 실시간 로그 확인
docker-compose logs -f ism-server

# 로그 파일 위치
ISM_Server/log/ism_server_YYYYMMDD_HHMMSS.log
```

## 👨‍💻 개발자 가이드

### 프로젝트 구조

```
ISM_Server/
├── main.py                 # FastAPI 애플리케이션 (모든 기능 포함)
├── test_inference_api.py   # 추론 API 테스트 스크립트
├── test_phase0.sh          # Phase 0 테스트 스크립트
├── requirements.txt        # Python 의존성
├── docker-compose.yml      # Docker Compose 설정
├── Dockerfile             # Docker 이미지 정의
├── log/                   # 로그 파일 디렉토리
└── README.md              # 이 파일
```

### 주요 컴포넌트

#### 1. 모델 로딩
- SAM 모델 자동 로딩
- DINOv2 특징 추출기 초기화
- CNOS 모델 통합

#### 2. 추론 엔드포인트
- RGB-D 이미지 처리
- 템플릿과 CAD 모델 로딩
- SAM-6D 추론 실행
- 결과 저장 및 반환

#### 3. 로깅 시스템
- 파일 기반 로깅
- 타임스탬프 포함
- 상세한 추론 과정 기록

### 환경 변수

- `ISM_MODEL_TYPE`: 모델 타입 (기본값: sam)
- `ISM_STABILITY_THRESHOLD`: SAM 안정성 임계값 (기본값: 0.97)
- `ISM_TEMPLATE_DIR`: 템플릿 디렉토리 경로
- `ISM_CAD_MODEL_PATH`: CAD 모델 파일 경로
- `ISM_CONFIG_DIR`: 설정 파일 디렉토리 경로
- `ISM_CHECKPOINTS_DIR`: 체크포인트 디렉토리 경로
- `ISM_SERVER_HOST`: 서버 호스트 (기본값: 0.0.0.0)
- `ISM_SERVER_PORT`: 서버 포트 (기본값: 8002)
- `ISM_LOG_LEVEL`: 로그 레벨 (기본값: INFO)

### 볼륨 마운트

- `..:/workspace/Estimation_Server`: Estimation_Server 전체 마운트
- `.:/workspace/ISM_Server`: ISM_Server 코드 마운트 (개발용)

### 포트

- `8002`: ISM 서버 API 포트

### 개발 환경 설정

```bash
# 개발용 컨테이너 실행
docker-compose up -d

# 컨테이너 접속
docker exec -it ism-server bash

# 컨테이너 내부에서 작업
conda activate sam6d
cd /workspace/Estimation_Server/ISM_Server
```

### 코드 스타일

- **Python**: PEP 8 준수
- **API**: RESTful 설계 원칙
- **로깅**: 구조화된 로그 메시지
- **에러 처리**: 명확한 에러 메시지

## 📊 성능 지표

### 일반적인 성능

- **모델 로딩 시간**: ~20초
- **추론 시간**: ~8-10초 (4개 객체)
- **메모리 사용량**: ~4GB GPU 메모리
- **검출 정확도**: 4개 객체 검출 성공

### 최적화 팁

1. **GPU 메모리 관리**: 불필요한 모델 언로딩
2. **배치 처리**: 여러 요청 동시 처리
3. **캐싱**: 템플릿 데이터 캐싱
4. **비동기 처리**: FastAPI 비동기 기능 활용

## 🔄 PEM_Server와의 연동

ISM_Server는 PEM_Server와 함께 사용됩니다:

1. **ISM_Server**: 객체 인스턴스 세그멘테이션 수행
2. **PEM_Server**: 세그멘테이션 결과를 기반으로 6D 포즈 추정

### 연동 워크플로우

```
RGB-D 이미지 → ISM_Server → 세그멘테이션 결과 → PEM_Server → 6D 포즈
```

## 📝 라이선스

이 프로젝트는 SAM-6D 모델을 기반으로 하며, 해당 라이선스를 따릅니다.

## 🤝 기여

버그 리포트나 기능 요청은 이슈 트래커를 통해 제출해 주세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 로그 파일과 함께 문의해 주세요.

---

**ISM Server v1.0.0** - SAM-6D 기반 인스턴스 세그멘테이션 서버
