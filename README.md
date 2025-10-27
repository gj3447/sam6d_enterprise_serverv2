# SAM-6D Enterprise Server

SAM-6D 기반의 엔터프라이즈급 객체 인식 및 포즈 추정 서버 시스템입니다.

## 📋 목차

- [개요](#개요)
- [시스템 구조](#시스템-구조)
- [주요 기능](#주요-기능)
- [요구사항](#요구사항)
- [빠른 시작](#량
- [서버 설명](#서버-설명)
- [API 사용법](#api-사용법)
- [개발 환경 설정](#개발-환경-설정)
- [문제 해결](#문제-해결)

## 🎯 개요

이 프로젝트는 SAM-6D 모델을 기반으로 한 분산형 마이크로서비스 아키텍처로, 객체 인식과 6D 포즈 추정을 수행합니다. 각 서버는 독립적으로 운영되며, RESTful API를 통해 통신합니다.

### 주요 특징

- **마이크로서비스 아키텍처**: 독립적인 서버 구성으로 확장성 확보
- **Docker 기반**: 일관된 환경에서 실행
- **GPU 가속**: CUDA 지원으로 고성능 추론
- **RESTful API**: 표준 HTTP API 인터페이스
- **로깅 시스템**: 상세한 로그 기록 및 모니터링

## 🏗 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Server (8001)                       │
│              중앙 오케스트레이션 서버                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
┌───────▼──────┐ ┌▼───────▼──┐ ┌──────▼────────┐
│   ISM_Server │  │PEM_Server │  │ Render_Server │
│   (8002)     │  │  (8003)   │  │    (8004)     │
│              │  │           │  │               │
│ 인스턴스     │  │ 포즈 추정  │  │ 템플릿 렌더링 │
│세그멘테이션  │  │            │  │               │
└──────────────┘ └───────────┘ └────────────────┘
```

### 서버 구성

| 서버 | 포트 | 기능 | 설명 |
|------|------|------|------|
| **Main_Server** | 8001 | 오케스트레이션 | 전체 워크플로우 조율 |
| **ISM_Server** | 8002 | 인스턴스 세그멘테이션 | 객체 분할 |
| **PEM_Server** | 8003 | 포즈 추정 | 6D 포즈 계산 |
| **Render_Server** | 8004 | 템플릿 렌더링 | CAD 모델 렌더링 |

## 🚀 주요 기능

### 1. 객체 인식 (ISM_Server)
- RGB-D 이미지에서 객체 인스턴스 세그멘테이션
- SAM 모델 기반 정확한 마스크 생성
- DINOv2 특징 추출기 활용

### 2. 포즈 추정 (PEM_Server)
- 세그멘테이션 결과 기반 6D 포즈 추정
- 회전(rotation) 및 변위(translation) 계산
- 신뢰도 점수 제공

### 3. 템플릿 렌더링 (Render_Server)
- CAD 모델 기반 템플릿 생성
- 다양한 시점의 렌더링 지원
- BOP, GSO, ShapeNet 형식 지원

## 💻 요구사항

### 하드웨어
- **GPU**: NVIDIA GPU (CUDA 11.8+ 지원)
- **메모리**: 최소 16GB RAM (32GB 권장)
- **저장공간**: 최소 50GB 여유 공간

### 소프트웨어
- **OS**: Linux (Ubuntu 20.04+ 권장) 또는 Windows with WSL2
- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **NVIDIA Container Toolkit**: GPU 지원용

### Python 환경
- **Python**: 3.8 이상
- **PyTorch**: 2.0+ (CUDA 지원)
- **FastAPI**: 웹 프레임워크
- 기타 의존성: 각 서버의 `requirements.txt` 참조

## 🏃 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/gj3447/sam6d_enterprise_serverv2.git
cd sam6d_enterprise_serverv2
```

### 2. Docker 환경으로 전체 시스템 실행

```bash
# 모든 서버 한번에 실행
docker-compose -f docker-compose.sam6d.yml up -d

# 로그 확인
docker-compose -f docker-compose.sam6d.yml logs -f
```

### 3. 개별 서버 실행

```bash
# ISM Server
cd ISM_Server
docker-compose up -d

# PEM Server
cd PEM_Server
docker-compose up -d

# Render Server
cd Render_Server
docker-compose up -ادر
```

### 4. 서버 상태 확인

```bash
# Main Server
curl http://localhost:8001/health

# ISM Server
curl http://localhost:8002/health

# PEM Server
curl http://localhost:8003/api/v1/health

# Render Server
curl http://localhost:8004/health
```

## 📖 서버 설명

### ISM_Server (Instance Segmentation Model Server)

**포트**: 8002  
**기능**: 객체 인스턴스 세그멘테이션

**주요 특징**:
- SAM 모델 기반 객체 분할
- DINOv2 특징 추출
- 템플릿 기반 매칭

[자세한 문서 보기](ISM_Server/README.md)

### PEM_Server (Pose Estimation Model Server)

**포트**: 8003  
**기능**: 6D 포즈 추정

**주요 특징**:
- PointNet2 기반 특징 추출
- Coarse-to-fine 매칭
- Transformer 기반 포즈 추정

[자세한 문서 보기](PEM_Server/README.md)

### Render_Server

**포트**: 8004  
**기능**: 템플릿 렌더링

**주요 특징**:
- 다중 시점 렌더링
- RGB, Depth, Mask 생성
- 다양한 데이터셋 형식 지원

[자세한 문서 보기](Render_Server/README.md)

## 📡 API 사용법

### 기본 워크플로우

```python
# 1. RGB-D 이미지와 CAD 모델 준비
rgb_image = load_image("path/to/rgb.png")
depth_image = load_image("path/to/depth.png")
cad_model = "path/to/model.ply"

# 2. 템플릿 생성 (Render_Server)
templates = render_templates(cad_model)

# 3. 객체 세그멘테이션 (ISM_Server)
segmentation_result = segment_objects(
    rgb_image, depth_image, templates, cad_model
)

# 4. 포즈 추정 (PEM_Server)
poses = estimate_pose(
    rgb_image, depth_image, cad_model,
    segmentation_result
)

# 5. 결과 사용
for pose in poses:
    print(f"Rotation: {pose['rotation']}")
    print(f"Translation: {pose['translation']}")
    print(f"Score: {pose['score']}")
```

### API 문서

각 서버의 Swagger UI 문서:
- Main Server: http://localhost:8001/docs
- ISM Server: http://localhost:8002/docs
- PEM Server: http://localhost:8003/docs
- Render Server: http://localhost:8004/docs

자세한 API 사용법은 [how_to_api.md](how_to_api.md)를 참조하세요.

## 🛠 개발 환경 설정

### 로컬 개발

```bash
# 1. Conda 환경 생성
conda env create -f Main_Server/environment.yaml
conda activate sam6d

# 2. 의존성 설치
pip install -r ISM_Server/requirements.txt
pip install -r PEM_Server/requirements.txt
pip install -r Render_Server/requirements.txt

# 3. 모델 체크포인트 다운로드
# ISM_Server
cd ISM_Server
python download_sam.py
python download_dinov2.py

# PEM_Server
cd PEM_Server
python download_sam6d-pem.py
```

### 개발 모드로 실행

```bash
# ISM Server
cd ISM_Server
uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# PEM Server
cd PEM_Server
uvicorn main:app --host 0.0.0.0 --port 8003 --reload

# Render Server
cd Render_Server
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. CUDA 사용 불가
```bash
# NVIDIA Container Toolkit 설치 확인
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu20.04 nvidia-smi
```

#### 2. 메모리 부족
- 배치 크기 감소
- 모델 언로딩
- GPU 메모리 모니터링

#### 3. 포트 충돌
`.env` 파일에서 포트 번호 변경

### 로그 확인

```bash
# Docker 로그
docker-compose logs -f <service-name>

# 로컬 로그 파일
tail -f ISM_Server/log/*.log
tail -f PEM_Server/log/*.log
```

## 📊 성능 지표

| 서버 | 모델 로딩 | 추론 시간 | 메모리 사용 |
|------|----------|----------|------------|
| ISM_Server | ~20초 | ~8-10초 (4개 객체) | ~4GB GPU |
| PEM_Server | ~45초 | ~8-9초 (16개 객체) | ~4GB GPU |
| Render_Server | - | ~1초/템플릿 | ~1GB GPU |

## 📝 라이선스

이 프로젝트는 SAM-6D 모델을 기반으로 하며, 해당 라이선스를 따릅니다.

## 🤝 기여

버그 리포트나 기능 요청은 [Issues](https://github.com/gj3447/sam6d_enterprise_serverv2/issues)를 통해 제출해 주세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 로그 파일과 함께 이슈를 생성해 주세요.

## 📚 참고 자료

- [SAM-6D 공식 문서](https://github.com/microsoft/SAM-6D)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Docker 문서](https://docs.docker.com/)

---

**SAM-6D Enterprise Server v1.0.0** - 엔터프라이즈급 객체 인식 시스템

