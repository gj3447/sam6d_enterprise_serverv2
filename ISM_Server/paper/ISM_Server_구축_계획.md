# ISM_Server 구축 계획

## 개요
SAM-6D Instance Segmentation Model을 사용하여 실시간 객체 인스턴스 세그멘테이션을 제공하는 서버를 구축합니다. 서버 시작 시 모델을 로딩하고, 들어오는 요청에 따라 추론을 수행하여 결과를 반환합니다.

## 1. 서버 아키텍처

### 1.1 기술 스택
- **웹 프레임워크**: FastAPI (비동기 처리 지원)
- **모델 프레임워크**: PyTorch
- **이미지 처리**: OpenCV, PIL
- **데이터 직렬화**: JSON, Base64
- **컨테이너화**: Docker + Docker Compose

### 1.2 서버 구조 (정말 최소 단위)
```
Estimation_Server/                    # 전체 프로젝트 루트
├── ISM_Server/                       # 새로 추가될 ISM 서버
│   ├── main.py                       # FastAPI 애플리케이션 (모든 기능 포함)
│   ├── requirements.txt              # 추가 Python 의존성
│   └── README.md                    # 서버 사용법
├── SAM-6D/                          # 기존 SAM-6D 프로젝트
│   └── SAM-6D/
│       ├── Instance_Segmentation_Model/
│       │   ├── run_inference_custom_function.py  # 기존 추론 함수
│       │   ├── checkpoints/         # 모델 체크포인트
│       │   ├── configs/             # 설정 파일들
│       │   └── templates/           # 템플릿 데이터
│       └── Data/
│           └── Example/
│               ├── obj_000005.ply   # CAD 모델
│               └── outputs/
│                   └── templates/   # 렌더링된 템플릿들
├── PEM_Server/                      # 기존 PEM 서버
├── Render_Server/                   # 기존 렌더 서버
├── docker-compose.sam6d.yml         # 기존 Docker Compose 설정
├── Dockerfile.sam6d                 # 기존 Dockerfile
└── static/output/                   # 출력 디렉토리
```

## 2. 핵심 컴포넌트 설계 (정말 최소 단위)

### 2.1 단일 파일 구조 (main.py)
```python
# ISM_Server/main.py - 모든 기능을 하나의 파일에
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import sys
import base64
import io
from PIL import Image
import numpy as np

# 기존 추론 함수 임포트
sys.path.append('/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model')
from run_inference_custom_function import run_inference_core, load_templates_from_files

app = FastAPI(title="ISM Server", version="1.0.0")

# 전역 변수로 모델과 템플릿 데이터 저장
model = None
templates_data = None
templates_masks = None
templates_boxes = None
cad_points = None
device = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로딩"""
    global model, templates_data, templates_masks, templates_boxes, cad_points, device
    # 모델 로딩 로직
    # 템플릿 로딩 로직
    # CAD 모델 로딩 로직

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/inference")
async def inference(request: InferenceRequest):
    # 추론 로직
    pass

class InferenceRequest(BaseModel):
    rgb_image: str
    depth_image: str
    cam_params: dict
    template_dir: Optional[str] = None
    cad_path: Optional[str] = None

class InferenceResponse(BaseModel):
    success: bool
    detections: list
    inference_time: float
    error_message: Optional[str] = None
```

## 3. 구현 단계 (정말 최소 단위)

### 3.1 Phase 1: 단일 파일 서버 구현
1. **main.py 파일 생성**
   - FastAPI 앱 생성
   - 모델 로딩 (startup 이벤트)
   - 헬스체크 API
   - 추론 API

2. **requirements.txt 생성**
   - 최소 의존성만 포함

### 3.2 Phase 2: 테스트 및 배포
1. **로컬 테스트**
   - 단일 파일로 서버 실행 테스트

2. **Docker 통합**
   - 기존 docker-compose.sam6d.yml에 ism-server 추가

## 4. API 사용 예시

### 4.1 추론 요청 (템플릿 경로 지원)
```bash
# ISM 서버는 포트 8002에서 실행
curl -X POST "http://localhost:8002/api/v1/inference" \
  -H "Content-Type: application/json" \
  -d '{
    "rgb_image": "base64_encoded_rgb_image",
    "depth_image": "base64_encoded_depth_image", 
    "cam_params": {
      "cam_K": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
      "depth_scale": 1000.0
    },
    "segmentor_model": "sam",
    "stability_score_thresh": 0.97,
    "template_dir": "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/templates",
    "cad_path": "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply"
  }'
```

### 4.2 응답 예시 (템플릿 경로 정보 포함)
```json
{
  "success": true,
  "detections": [
    {
      "category_id": 1,
      "score": 0.95,
      "segmentation": "rle_encoded_mask",
      "bbox": [x, y, width, height]
    }
  ],
  "scores": [0.95],
  "inference_time": 1.234,
  "visualization": "base64_encoded_visualization_image",
  "template_dir_used": "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/templates",
  "cad_path_used": "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply"
}
```

## 5. 설정 및 환경

### 5.1 환경 변수 (Estimation_Server 전체 마운트 기준)
```bash
# 모델 설정
ISM_MODEL_TYPE=sam                    # sam 또는 fastsam
ISM_STABILITY_THRESHOLD=0.97
ISM_TEMPLATE_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/templates
ISM_CAD_MODEL_PATH=/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply
ISM_CONFIG_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/configs
ISM_CHECKPOINTS_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/checkpoints

# 서버 설정
ISM_SERVER_HOST=0.0.0.0
ISM_SERVER_PORT=8002                 # ISM 서버 전용 포트
ISM_LOG_LEVEL=INFO

# GPU 설정
CUDA_VISIBLE_DEVICES=0
```

### 5.2 기존 Docker 환경 활용 설정

#### 5.2.1 기존 docker-compose.sam6d.yml 수정 (Estimation_Server 전체 마운트)
```yaml
version: '3.8'

services:
  sam6d-server:
    image: ai_server-server:latest
    container_name: sam6d-server
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    volumes:
      - .:/workspace/Estimation_Server  # Estimation_Server 전체 마운트
    ports:
      - "8000:8000"
    working_dir: /workspace/Estimation_Server/SAM-6D/SAM-6D
    command: conda run -n sam6d bash
    stdin_open: true
    tty: true

  # 기존 sam6d-api 서비스는 유지하거나 제거
  sam6d-api:
    image: ai_server-server:latest
    container_name: sam6d-api
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    volumes:
      - .:/workspace/Estimation_Server  # Estimation_Server 전체 마운트
    ports:
      - "8001:8001"
    working_dir: /workspace/Estimation_Server/SAM-6D/SAM-6D
    command: conda run -n sam6d python /workspace/Estimation_Server/api_server.py
    depends_on:
      - sam6d-server

  # 새로운 ISM 서버 추가
  ism-server:
    image: ai_server-server:latest
    container_name: ism-server
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
      - ISM_MODEL_TYPE=sam
      - ISM_STABILITY_THRESHOLD=0.97
      - ISM_TEMPLATE_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/templates
      - ISM_CAD_MODEL_PATH=/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply
      - ISM_CONFIG_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/configs
      - ISM_CHECKPOINTS_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/checkpoints
      - ISM_SERVER_HOST=0.0.0.0
      - ISM_SERVER_PORT=8002
      - ISM_LOG_LEVEL=INFO
    volumes:
      - .:/workspace/Estimation_Server  # Estimation_Server 전체 마운트
    ports:
      - "8002:8002"  # ISM 서버 전용 포트
    working_dir: /workspace/Estimation_Server/ISM_Server
    command: conda run -n sam6d python -m app.main
    depends_on:
      - sam6d-server
```

#### 5.2.2 기존 Dockerfile.sam6d 활용
기존 `Dockerfile.sam6d`는 그대로 사용하고, ISM_Server는 별도로 추가합니다:

```dockerfile
# 기존 Dockerfile.sam6d는 수정하지 않음
# ISM_Server는 기존 컨테이너 환경에서 실행
```

#### 5.2.3 ISM_Server requirements.txt (정말 최소)
```txt
# 정말 필요한 것만
fastapi
uvicorn[standard]
pydantic
python-multipart
```

#### 5.2.4 서비스 실행 방법
```bash
# 전체 서비스 실행
docker-compose -f docker-compose.sam6d.yml up -d

# ISM 서버만 실행
docker-compose -f docker-compose.sam6d.yml up -d ism-server

# 로그 확인
docker-compose -f docker-compose.sam6d.yml logs -f ism-server
```

## 6. 성능 고려사항

### 6.1 메모리 관리
- 모델 로딩 시 GPU 메모리 최적화
- 템플릿 데이터 캐싱
- 배치 처리 시 메모리 사용량 모니터링

### 6.2 응답 시간 최적화
- 모델 추론 비동기 처리
- 결과 캐싱 (선택사항)
- 이미지 전처리 최적화

### 6.3 확장성
- 다중 GPU 지원
- 로드 밸런싱
- 수평 확장 가능한 아키텍처

## 7. 테스트 계획

### 7.1 단위 테스트
- 모델 로딩 테스트
- 이미지 처리 유틸리티 테스트
- API 엔드포인트 테스트

### 7.2 통합 테스트
- 전체 추론 파이프라인 테스트
- 다양한 입력 데이터 테스트
- 에러 상황 테스트

### 7.3 성능 테스트
- 응답 시간 측정
- 동시 요청 처리 테스트
- 메모리 사용량 모니터링

## 8. 배포 및 운영

### 8.1 배포 전략
- Docker 컨테이너 기반 배포
- Kubernetes 배포 (선택사항)
- CI/CD 파이프라인 구축

### 8.2 모니터링
- 서버 상태 모니터링
- API 응답 시간 모니터링
- 에러율 모니터링

### 8.3 로그 관리
- 구조화된 로그 포맷
- 로그 레벨 관리
- 로그 로테이션

## 9. 향후 개선 사항

### 9.1 기능 확장
- 다중 객체 모델 지원
- 실시간 스트리밍 처리
- 웹소켓 기반 실시간 통신

### 9.2 성능 개선
- 모델 양자화
- TensorRT 최적화
- 배치 추론 지원

### 9.3 사용자 경험
- API 문서 자동 생성
- 웹 기반 테스트 인터페이스
- 결과 시각화 개선

## 10. 기존 Docker 환경과의 통합

### 10.1 기존 환경 활용 장점
- **이미 구축된 환경**: `ai_server-server:latest` 이미지와 `sam6d` conda 환경 활용
- **GPU 지원**: NVIDIA runtime과 CUDA 환경이 이미 설정됨
- **모델 체크포인트**: 기존 SAM-6D 모델들이 이미 로딩되어 있음
- **템플릿 데이터**: 기존 렌더링된 템플릿들을 재사용 가능

### 10.2 포트 구성
```
- 8000: sam6d-server (기존 개발/디버깅용)
- 8001: sam6d-api (기존 API 서버)
- 8002: ism-server (새로운 ISM 서버) ← 새로 추가
```

### 10.3 볼륨 마운트 구조 (Estimation_Server 전체 마운트)
```yaml
volumes:
  - .:/workspace/Estimation_Server  # Estimation_Server 전체 마운트
```

**컨테이너 내부 경로 구조:**
```
/workspace/Estimation_Server/
├── ISM_Server/                    # 새로운 ISM 서버
├── SAM-6D/                        # 기존 SAM-6D 프로젝트
│   └── SAM-6D/
│       ├── Instance_Segmentation_Model/
│       │   ├── run_inference_custom_function.py
│       │   ├── checkpoints/       # 모델 체크포인트
│       │   ├── configs/          # 설정 파일들
│       │   └── templates/        # 템플릿 데이터
│       └── Data/
│           └── Example/
│               ├── obj_000005.ply # CAD 모델
│               └── outputs/
│                   └── templates/ # 렌더링된 템플릿들
├── PEM_Server/                    # 기존 PEM 서버
├── Render_Server/                # 기존 렌더 서버
├── static/output/                # 공통 출력 디렉토리
├── docker-compose.sam6d.yml       # Docker Compose 설정
└── Dockerfile.sam6d              # Dockerfile
```

### 10.4 기존 코드와의 연동 (Estimation_Server 전체 마운트 기준)
- `run_inference_custom_function.py`의 `run_inference_core` 함수를 직접 활용
- **기존 템플릿 데이터 경로**: `/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/templates`
- **기존 CAD 모델 경로**: `/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply`
- **기존 설정 파일들**: `/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/configs/`
- **기존 체크포인트**: `/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/checkpoints/`
- **ISM 서버 코드**: `/workspace/Estimation_Server/ISM_Server/`

### 10.5 개발 워크플로우
1. **기존 환경 유지**: `sam6d-server`는 개발/디버깅용으로 유지
2. **새 서버 추가**: `ism-server`는 프로덕션 API 서버로 활용
3. **점진적 마이그레이션**: 기존 `sam6d-api`에서 `ism-server`로 점진적 전환 가능

### 10.6 환경 변수 설정 (Estimation_Server 전체 마운트 기준)
```bash
# 기존 환경 변수들은 그대로 유지하고 추가
ISM_MODEL_TYPE=sam
ISM_STABILITY_THRESHOLD=0.97
ISM_TEMPLATE_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/templates
ISM_CAD_MODEL_PATH=/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply
ISM_CONFIG_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/configs
ISM_CHECKPOINTS_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/checkpoints
ISM_SERVER_HOST=0.0.0.0
ISM_SERVER_PORT=8002
ISM_LOG_LEVEL=INFO
```

### 10.7 경로 설정 주의사항 및 템플릿 로딩 방식
**중요**: Estimation_Server 전체가 마운트되므로 모든 경로는 `/workspace/Estimation_Server/`로 시작해야 합니다.

**현재 템플릿 로딩 방식:**
```python
# load_templates_from_files 함수에서 사용하는 파일 구조:
# - rgb_0.png, rgb_1.png, ... (RGB 템플릿 이미지)
# - mask_0.png, mask_1.png, ... (마스크 이미지)  
# - xyz_0.npy, xyz_1.npy, ... (3D 좌표 데이터, 현재는 사용하지 않음)

def load_templates_from_files(template_dir, device):
    """파일에서 템플릿 데이터 로딩"""
    num_templates = len(glob.glob(f"{template_dir}/*.npy"))  # .npy 파일 개수로 템플릿 수 결정
    boxes, masks, templates = [], [], []
    
    for idx in range(num_templates):
        image = Image.open(os.path.join(template_dir, 'rgb_'+str(idx)+'.png'))
        mask = Image.open(os.path.join(template_dir, 'mask_'+str(idx)+'.png'))
        boxes.append(mask.getbbox())
        # ... 템플릿 처리 로직
```

**모델 로딩 시 사용할 경로들:**
```python
import os
import sys

# 환경 변수에서 가져올 경로들
TEMPLATE_DIR = os.getenv('ISM_TEMPLATE_DIR', '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/templates')
CAD_MODEL_PATH = os.getenv('ISM_CAD_MODEL_PATH', '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply')
CONFIG_DIR = os.getenv('ISM_CONFIG_DIR', '/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/configs')
CHECKPOINTS_DIR = os.getenv('ISM_CHECKPOINTS_DIR', '/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/checkpoints')

# run_inference_custom_function.py 임포트 시 경로
sys.path.append('/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model')

# 템플릿 경로 동적 처리
def resolve_template_path(template_dir=None):
    """템플릿 경로를 동적으로 해결"""
    if template_dir is None:
        template_dir = os.getenv('ISM_TEMPLATE_DIR', '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/templates')
    
    # 상대 경로인 경우 workspace 기준으로 절대 경로로 변환
    if not os.path.isabs(template_dir):
        template_dir = os.path.join('/workspace/Estimation_Server', template_dir)
    
    return template_dir
```

**템플릿 파일 검증:**
```python
import os
import glob

def validate_template_directory(template_dir):
    """템플릿 디렉토리 유효성 검사"""
    if not os.path.exists(template_dir):
        raise FileNotFoundError(f"Template directory not found: {template_dir}")
    
    # 필요한 파일들이 있는지 확인
    npy_files = glob.glob(f"{template_dir}/*.npy")
    if not npy_files:
        raise ValueError(f"No .npy files found in template directory: {template_dir}")
    
    num_templates = len(npy_files)
    
    # 각 템플릿에 대해 rgb와 mask 파일이 있는지 확인
    for idx in range(num_templates):
        rgb_file = os.path.join(template_dir, f'rgb_{idx}.png')
        mask_file = os.path.join(template_dir, f'mask_{idx}.png')
        
        if not os.path.exists(rgb_file):
            raise FileNotFoundError(f"RGB template file not found: {rgb_file}")
        if not os.path.exists(mask_file):
            raise FileNotFoundError(f"Mask template file not found: {mask_file}")
    
    return num_templates
```

---

이 계획을 바탕으로 기존 Docker 환경을 활용하여 단계별로 ISM_Server를 구축하여 안정적이고 확장 가능한 객체 인스턴스 세그멘테이션 서비스를 제공할 수 있습니다.
