# PEM Server

PEM (Pose Estimation Model) Server는 SAM-6D 기반의 포즈 추정 모델을 FastAPI로 구현한 서버입니다.

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

PEM_Server는 SAM-6D 모델을 활용하여 RGB-D 이미지에서 객체의 6D 포즈를 추정하는 서버입니다. ISM (Instance Segmentation Model) 결과를 입력으로 받아 객체의 위치와 방향을 정확하게 추정합니다.

### 주요 특징

- **FastAPI 기반**: 고성능 비동기 웹 서버
- **자동 모델 로딩**: 서버 시작 시 SAM-6D 모델 자동 로드
- **CUDA 지원**: GPU 가속을 통한 빠른 추론
- **RESTful API**: 표준 HTTP API 인터페이스
- **로깅 시스템**: 상세한 로그 기록 및 파일 저장

## 🚀 주요 기능

### 1. 포즈 추정 API
- RGB-D 이미지 입력
- ISM 세그멘테이션 결과 처리
- 6D 포즈 (회전 + 변위) 추정
- 검출 신뢰도 점수 제공

### 2. 모델 관리
- 모델 상태 확인
- 동적 모델 로딩/언로딩
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

## 🛠 설치 및 실행

### 1. Docker 환경 설정

```bash
# Docker Compose로 서버 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f pem-server
```

### 2. 서버 상태 확인

```bash
# 헬스 체크
curl http://localhost:8003/api/v1/health

# 모델 상태 확인
curl http://localhost:8003/api/v1/model/status
```

### 3. 서버 중지

```bash
# 서버 중지
docker-compose down
```

## 📡 API 사용법

### 기본 정보

- **서버 URL**: `http://localhost:8003`
- **API 문서**: `http://localhost:8003/docs` (Swagger UI)
- **API 버전**: v1

### 주요 엔드포인트

#### 1. 헬스 체크

```bash
GET /api/v1/health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "message": "Server is running",
  "uptime": 1234.56,
  "model": {
    "loaded": true,
    "device": "cuda",
    "parameters": 107939560,
    "loading_time": 45.2
  }
}
```

#### 2. 포즈 추정

```bash
POST /api/v1/pose-estimation
```

**요청 형식:**
```json
{
  "rgb_image": "base64_encoded_rgb_image",
  "depth_image": "base64_encoded_depth_image",
  "cam_params": {
    "cam_K": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
    "depth_scale": 1000.0
  },
  "cad_path": "/path/to/cad/model.ply",
  "seg_data": [
    {
      "scene_id": 1,
      "image_id": 1,
      "category_id": 1,
      "bbox": [x, y, w, h],
      "score": 0.9,
      "segmentation": {
        "size": [height, width],
        "counts": "encoded_mask"
      }
    }
  ],
  "template_dir": "/path/to/templates",
  "det_score_thresh": 0.2,
  "output_dir": "/path/to/output"
}
```

**응답 예시:**
```json
{
  "success": true,
  "detections": [...],
  "pose_scores": [0.95, 0.87, 0.92],
  "pred_rot": [[[r11, r12, r13], [r21, r22, r23], [r31, r32, r33]], ...],
  "pred_trans": [[x, y, z], ...],
  "num_detections": 3,
  "inference_time": 2.45,
  "template_dir_used": "/path/to/templates",
  "cad_path_used": "/path/to/cad/model.ply",
  "output_dir_used": "/path/to/output"
}
```

#### 3. 샘플 데이터

```bash
GET /api/v1/pose-estimation/sample?sample_dir=/path/to/example
```

#### 4. 모델 관리

```bash
# 모델 상태 확인
GET /api/v1/model/status

# 모델 로딩
POST /api/v1/model/load

# 모델 언로딩
POST /api/v1/model/unload
```

## 🧪 테스트

### 1. 기본 API 테스트

```bash
# Docker 컨테이너 내에서 실행
docker-compose exec pem-server bash -c "source /opt/conda/bin/activate sam6d && cd PEM_Server && python test_basic_api.py"
```

### 2. 포즈 추정 API 테스트

```bash
# 전체 포즈 추정 테스트
docker-compose exec pem-server bash -c "source /opt/conda/bin/activate sam6d && cd PEM_Server && python test_pose_estimation_api.py"
```

### 3. 테스트 결과 예시

```
🚀 PEM Server API 테스트 시작
서버 URL: http://localhost:8003

==================================================
테스트: 서버 헬스 체크
==================================================
✅ 서버 상태: healthy
✅ 모델 로드됨: True
✅ 디바이스: cuda
✅ 파라미터 수: 107,939,560

==================================================
테스트: 포즈 추정 서비스 상태
==================================================
✅ 서비스 상태: ready
✅ 모델 로드됨: True
✅ 디바이스: cuda

==================================================
테스트: 샘플 데이터 포즈 추정
==================================================
✅ 포즈 추정 성공!
✅ 요청 처리 시간: 11.762s
✅ 추론 시간: 8.485s
✅ 검출된 객체 수: 16

🎉 모든 테스트가 성공했습니다!
```

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
docker-compose restart pem-server
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
docker-compose logs -f pem-server

# 로그 파일 위치
PEM_Server/log/pem_server_YYYYMMDD_HHMMSS.log
```

## 👨‍💻 개발자 가이드

### 프로젝트 구조

```
PEM_Server/
├── api/                    # API 엔드포인트
│   ├── endpoints/          # 각 기능별 엔드포인트
│   └── models.py          # Pydantic 모델 정의
├── core/                  # 핵심 기능
│   ├── config.py          # 설정 관리
│   ├── model_manager.py   # 모델 관리
│   └── logging_config.py  # 로깅 설정
├── model/                 # 모델 관련 파일
├── utils/                 # 유틸리티 함수
├── main.py               # FastAPI 애플리케이션 진입점
├── requirements.txt      # Python 의존성
├── docker-compose.yml    # Docker 설정
└── Dockerfile           # Docker 이미지 정의
```

### 주요 컴포넌트

#### 1. ModelManager
- 모델 로딩/언로딩 관리
- GPU 메모리 관리
- 모델 상태 추적

#### 2. PoseEstimationEndpoint
- 포즈 추정 API 구현
- 입력 데이터 검증
- 결과 포맷팅

#### 3. LoggingConfig
- 파일 기반 로깅
- 로그 레벨 관리
- 타임스탬프 포함

### 개발 환경 설정

```bash
# 개발용 컨테이너 실행
docker-compose -f docker-compose.dev.yml up -d

# 코드 변경 시 자동 재시작
docker-compose -f docker-compose.dev.yml up --build
```

### 코드 스타일

- **Python**: PEP 8 준수
- **API**: RESTful 설계 원칙
- **로깅**: 구조화된 로그 메시지
- **에러 처리**: 명확한 에러 메시지

## 📊 성능 지표

### 일반적인 성능

- **모델 로딩 시간**: ~45초
- **추론 시간**: ~8-9초 (16개 객체)
- **메모리 사용량**: ~4GB GPU 메모리
- **검출 정확도**: 16개 객체 검출 성공

### 최적화 팁

1. **GPU 메모리 관리**: 불필요한 모델 언로딩
2. **배치 처리**: 여러 요청 동시 처리
3. **캐싱**: 템플릿 데이터 캐싱
4. **비동기 처리**: FastAPI 비동기 기능 활용

## 📝 라이선스

이 프로젝트는 SAM-6D 모델을 기반으로 하며, 해당 라이선스를 따릅니다.

## 🤝 기여

버그 리포트나 기능 요청은 이슈 트래커를 통해 제출해 주세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 로그 파일과 함께 문의해 주세요.

---

**PEM Server v1.0.0** - SAM-6D 기반 포즈 추정 서버
