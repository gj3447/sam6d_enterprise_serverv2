# PEM Server 구축 계획 문서

## 📋 목차
1. [PEM Server 개요](#1-pem-server-개요)
2. [기술적 요구사항](#2-기술적-요구사항)
3. [아키텍처 설계](#3-아키텍처-설계)
4. [구현 계획](#4-구현-계획)
5. [API 설계](#5-api-설계)
6. [Docker 환경 구성](#6-docker-환경-구성)
7. [테스트 전략](#7-테스트-전략)
8. [배포 및 운영](#8-배포-및-운영)

---

## 1. PEM Server 개요

### 🎯 목적
PEM (Pose Estimation Model) Server는 SAM-6D의 포즈 추정 모델을 마이크로서비스로 제공하는 서버입니다. ISM Server에서 생성된 객체 검출 결과를 입력으로 받아 6D 포즈를 추정합니다.

### 🔄 ISM Server와의 연동
```
ISM Server → PEM Server → 최종 결과
    ↓            ↓
 객체 검출    포즈 추정
 (마스크)     (회전/이동)
```

### 📊 주요 기능
- **6D 포즈 추정**: 객체의 3D 회전(Rotation)과 3D 이동(Translation) 추정
- **Point Cloud 처리**: 깊이 이미지에서 포인트 클라우드 생성 및 처리
- **CAD 모델 매칭**: 검출된 객체와 CAD 모델 간의 기하학적 매칭
- **Transformer 기반**: 최신 Transformer 아키텍처 활용

---

## 2. 기술적 요구사항

### 🧠 모델 아키텍처
- **Base Model**: SAM-6D PEM (Pose Estimation Model)
- **Backbone**: Vision Transformer + PointNet2
- **Input**: RGB 이미지, 깊이 이미지, 객체 마스크, CAD 모델
- **Output**: 6D 포즈 (3D 회전 + 3D 이동)

### 📦 의존성
```python
# 핵심 라이브러리
torch>=2.0.0
torchvision
numpy
opencv-python
PIL
trimesh
pycocotools

# SAM-6D PEM 특화
pointnet2  # CUDA 확장 모듈
transformer
```

### 🖥️ 시스템 요구사항
- **GPU**: CUDA 11.3+ 지원 GPU (권장: RTX 3090Ti 이상)
- **메모리**: 최소 8GB GPU 메모리
- **Python**: 3.9.6
- **OS**: Linux (Docker 환경)

---

## 3. 아키텍처 설계

### 🏗️ 시스템 구조
```
PEM_Server/
├── main.py                    # FastAPI 서버 메인
├── docker-compose.yml         # Docker 오케스트레이션
├── Dockerfile                 # 컨테이너 빌드 설정
├── config/                    # 모델 설정 파일
├── checkpoints/               # 사전 훈련된 모델
├── model/                     # PEM 모델 구현
│   ├── pose_estimation_model.py
│   ├── transformer.py
│   └── pointnet2/            # PointNet2 CUDA 확장
├── utils/                     # 유틸리티 함수
├── provider/                  # 데이터 제공자
└── test_inference_api.py      # API 테스트 스크립트
```

### 🔄 데이터 플로우
```
클라이언트 → PEM Server → PEM 모델 → 포즈 추정 결과
    ↓              ↓              ↓
  RGB/Depth     모델 로딩       포인트 클라우드
  마스크        GPU 설정        기하학적 매칭
  CAD 모델      API 서비스      포즈 반환
```

### 🎯 설계 원칙
- **클라이언트 중심**: 모든 데이터를 클라이언트가 제공
- **ISM 연동**: ISM Server 결과와 완벽 호환
- **마이크로서비스**: 포즈 추정 전용 서비스
- **확장성**: 다중 객체 동시 처리

---

## 4. 구현 계획

### 📅 Phase 1: 기본 서버 구축 (1주)
1. **FastAPI 서버 기본 구조**
   - 기본 엔드포인트 구현
   - Pydantic 스키마 정의
   - 로깅 시스템 구축

2. **PEM 모델 로딩**
   - `pose_estimation_model.py` 통합
   - 체크포인트 로딩 (`sam-6d-pem-base.pth`)
   - GPU 메모리 관리

3. **Docker 환경 구성**
   - Dockerfile 작성
   - docker-compose.yml 설정
   - Conda 환경 통합

### 📅 Phase 2: 핵심 기능 구현 (1주)
1. **포즈 추론 API**
   - `run_inference_custom_function.py` 통합
   - 포인트 클라우드 처리
   - CAD 모델 매칭

2. **이미지 처리 파이프라인**
   - RGB/Depth 이미지 전처리
   - 마스크 기반 객체 분할
   - 포인트 클라우드 생성

3. **결과 후처리**
   - 포즈 결과 검증
   - 시각화 이미지 생성
   - JSON/NPZ 형식 출력

### 📅 Phase 3: 통합 및 최적화 (1주)
1. **ISM Server 연동**
   - ISM 결과 형식 호환성
   - 파이프라인 통합 테스트
   - 성능 최적화

2. **에러 처리 및 로깅**
   - 포괄적 에러 핸들링
   - 상세한 로깅 시스템
   - 모니터링 기능

3. **테스트 및 문서화**
   - 단위 테스트 작성
   - 통합 테스트 구현
   - API 문서화

---

## 5. API 설계

### 📡 REST API 엔드포인트

#### 1. 상태 확인 엔드포인트
```python
@app.get("/api/v1/status", response_model=ServerStatus)
async def get_status():
    return ServerStatus(
        server="running",
        model_loaded=model is not None,
        device=str(device) if device else None,
        uptime=time.time()
    )
```

#### 2. 포즈 추정 엔드포인트
```python
@app.post("/api/v1/pose_estimation", response_model=PoseEstimationResponse)
async def estimate_pose(request: PoseEstimationRequest):
    """포즈 추정 API - ISM 결과를 입력으로 받아 6D 포즈 추정"""
```

#### 3. 통합 추론 엔드포인트
```python
@app.post("/api/v1/full_pipeline", response_model=FullPipelineResponse)
async def full_pipeline(request: FullPipelineRequest):
    """ISM + PEM 통합 파이프라인"""
```

### 📋 Pydantic 데이터 스키마

#### 요청 스키마 (`PoseEstimationRequest`)
```python
class PoseEstimationRequest(BaseModel):
    rgb_image: str              # Base64 인코딩된 RGB 이미지
    depth_image: str            # Base64 인코딩된 깊이 이미지
    cam_params: dict            # 카메라 파라미터 (cam_K, depth_scale)
    detections: dict            # ISM Server 검출 결과
    cad_path: str               # CAD 모델 경로
    output_dir: Optional[str] = None  # 결과 저장 경로
```

#### 응답 스키마 (`PoseEstimationResponse`)
```python
class PoseEstimationResponse(BaseModel):
    success: bool
    poses: List[dict]           # 6D 포즈 결과 리스트
    inference_time: float       # 추론 소요 시간
    cad_path_used: str         # 사용된 CAD 모델 경로
    output_dir_used: Optional[str] = None
    error_message: Optional[str] = None
```

#### 포즈 데이터 구조
```python
class PoseResult(BaseModel):
    object_id: int              # 객체 ID
    rotation: List[List[float]] # 3x3 회전 행렬
    translation: List[float]   # 3D 이동 벡터
    confidence: float           # 신뢰도 점수
    bbox: List[int]             # 바운딩 박스 [x, y, w, h]
```

### 🔄 포즈 추정 처리 플로우

```python
# 1. 이미지 변환
rgb_image = base64_to_image(request.rgb_image)
depth_image = base64_to_image(request.depth_image)
rgb_array = image_to_numpy(rgb_image)
depth_array = depth_image_to_numpy(depth_image)

# 2. 포인트 클라우드 생성
point_cloud = get_point_cloud_from_depth(depth_array, cam_params)

# 3. 객체별 포즈 추정
poses = []
for detection in request.detections['masks']:
    # 객체 마스크 추출
    mask = extract_mask(detection)
    
    # 포인트 클라우드 크롭
    cropped_points = crop_point_cloud(point_cloud, mask)
    
    # PEM 모델 추론
    pose_result = pem_model.inference(
        rgb_array, cropped_points, cad_model
    )
    
    poses.append(pose_result)

# 4. 결과 후처리 및 반환
return PoseEstimationResponse(
    success=True,
    poses=poses,
    inference_time=inference_time,
    cad_path_used=cad_path
)
```

---

## 6. Docker 환경 구성

### 🐳 Dockerfile 구성

```dockerfile
FROM ai_server-server:latest

WORKDIR /workspace/Estimation_Server

# PEM Server 파일들 복사
COPY requirements.txt main.py /workspace/Estimation_Server/PEM_Server/
COPY config/ /workspace/Estimation_Server/PEM_Server/config/
COPY checkpoints/ /workspace/Estimation_Server/PEM_Server/checkpoints/
COPY model/ /workspace/Estimation_Server/PEM_Server/model/
COPY utils/ /workspace/Estimation_Server/PEM_Server/utils/
COPY provider/ /workspace/Estimation_Server/PEM_Server/provider/

# PointNet2 CUDA 확장 빌드
RUN cd /workspace/Estimation_Server/PEM_Server/model/pointnet2 && \
    python setup.py build_ext --inplace

# 환경 변수 설정
ENV PYTHONPATH=/workspace/Estimation_Server/PEM_Server:$PYTHONPATH

# 포트 노출
EXPOSE 8003

# 서버 실행 명령
CMD ["bash", "-c", "source /opt/conda/bin/activate sam6d && cd /workspace/Estimation_Server/PEM_Server && python main.py"]
```

### 🚀 Docker Compose 설정

```yaml
version: '3.8'
services:
  pem-server:
    build: .
    ports:
      - "8003:8003"
    volumes:
      - ../:/workspace/Estimation_Server
    command: bash -c "source /opt/conda/bin/activate sam6d && cd /workspace/Estimation_Server/PEM_Server && python main.py"
    environment:
      - CUDA_VISIBLE_DEVICES=0
    depends_on:
      - ism-server  # ISM Server와 연동
```

### 🔧 환경 설정 관리

```python
# 로깅 설정
def setup_logging():
    """로깅 설정"""
    log_dir = os.path.join(current_dir, "log")
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"pem_server_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
```

---

## 7. 테스트 전략

### 🧪 테스트 계층

#### 1. 단위 테스트
```python
def test_point_cloud_generation():
    """포인트 클라우드 생성 테스트"""
    depth_array = np.random.randint(0, 1000, (480, 640))
    cam_params = {"cam_K": [...], "depth_scale": 1.0}
    
    point_cloud = get_point_cloud_from_depth(depth_array, cam_params)
    assert point_cloud.shape[1] == 3  # x, y, z 좌표

def test_pose_estimation():
    """포즈 추정 모델 테스트"""
    model = load_pem_model()
    rgb_tensor = torch.randn(1, 3, 224, 224)
    points_tensor = torch.randn(1, 1024, 3)
    
    pose = model.inference(rgb_tensor, points_tensor)
    assert pose['rotation'].shape == (3, 3)
    assert pose['translation'].shape == (3,)
```

#### 2. 통합 테스트
```python
def test_ism_pem_pipeline():
    """ISM + PEM 통합 파이프라인 테스트"""
    # ISM Server에서 검출 결과 가져오기
    ism_result = call_ism_server(sample_data)
    
    # PEM Server로 포즈 추정 요청
    pem_request = {
        "rgb_image": sample_data["rgb_image"],
        "depth_image": sample_data["depth_image"],
        "cam_params": sample_data["cam_params"],
        "detections": ism_result["detections"],
        "cad_path": sample_data["cad_path"]
    }
    
    pem_result = call_pem_server(pem_request)
    
    # 결과 검증
    assert pem_result["success"] == True
    assert len(pem_result["poses"]) == len(ism_result["detections"]["masks"])
```

#### 3. 성능 테스트
```python
def test_performance_benchmark():
    """성능 벤치마크 테스트"""
    start_time = time.time()
    
    # 다중 요청 동시 처리 테스트
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(call_pem_server, request)
            for request in test_requests
        ]
        
        results = [future.result() for future in futures]
    
    end_time = time.time()
    avg_time = (end_time - start_time) / len(test_requests)
    
    assert avg_time < 5.0  # 평균 5초 이내
```

### 📊 테스트 데이터

#### 샘플 데이터셋
```python
SAMPLE_DATA = {
    "rgb_image": "base64_encoded_rgb",
    "depth_image": "base64_encoded_depth", 
    "cam_params": {
        "cam_K": [572.4114, 0.0, 325.2611, 0.0, 573.57043, 242.04899, 0.0, 0.0, 1.0],
        "depth_scale": 1.0
    },
    "detections": {
        "masks": [...],  # ISM 검출 결과
        "boxes": [...],
        "scores": [...]
    },
    "cad_path": "/path/to/cad_model.ply"
}
```

---

## 8. 배포 및 운영

### 🚀 배포 명령어

```bash
# PEM Server 단독 배포
cd PEM_Server
docker-compose up -d --build

# ISM + PEM 통합 배포
cd ..
docker-compose -f docker-compose.full.yml up -d --build

# 서버 상태 확인
docker ps
curl http://localhost:8003/api/v1/status
```

### 📊 모니터링

#### 로그 모니터링
```bash
# 실시간 로그 확인
docker logs -f pem-server

# 로그 파일 확인
tail -f PEM_Server/log/pem_server_*.log
```

#### 성능 모니터링
```python
# GPU 사용률 모니터링
nvidia-smi -l 1

# 메모리 사용량 확인
docker stats pem-server
```

### 🔧 운영 가이드

#### 서버 재시작
```bash
# 서버 재시작
docker-compose restart pem-server

# 완전 재빌드
docker-compose down
docker-compose up -d --build
```

#### 모델 업데이트
```bash
# 새 모델 체크포인트 교체
cp new_model.pth PEM_Server/checkpoints/sam-6d-pem-base.pth
docker-compose restart pem-server
```

---

## 📈 예상 성과

### ✨ 기술적 성과
1. **완전한 SAM-6D 파이프라인**: ISM + PEM 통합 서비스
2. **실시간 포즈 추정**: 평균 3-5초 내 6D 포즈 추정
3. **확장 가능한 아키텍처**: 다중 객체 동시 처리
4. **프로덕션 준비**: 완전한 Docker화 및 모니터링

### 📊 성능 지표 목표
- **추론 시간**: 평균 3-5초 (단일 객체)
- **정확도**: BOP 벤치마크 기준 90% 이상
- **처리량**: 동시 4개 요청 처리 가능
- **가용성**: 99.9% 업타임

### 🎯 비즈니스 가치
- **자동화**: 수동 포즈 추정 작업 자동화
- **정확성**: 높은 정밀도의 6D 포즈 추정
- **확장성**: 다양한 산업 분야 적용 가능
- **통합성**: 기존 시스템과 쉬운 연동

---

## 📞 다음 단계

### 🔄 구현 우선순위
1. **Phase 1**: 기본 서버 구축 (1주)
2. **Phase 2**: 핵심 기능 구현 (1주)  
3. **Phase 3**: 통합 및 최적화 (1주)

### 📋 체크리스트
- [ ] PEM 모델 로딩 시스템 구현
- [ ] 포즈 추정 API 엔드포인트 개발
- [ ] ISM Server 연동 테스트
- [ ] Docker 환경 구성
- [ ] 성능 최적화 및 벤치마크
- [ ] 문서화 및 배포 가이드

### 🎯 성공 기준
- ISM Server와 완벽한 연동
- BOP 벤치마크 기준 성능 달성
- 프로덕션 환경에서 안정적 운영
- 완전한 문서화 및 테스트 커버리지

---

**문서 작성일**: 2025년 10월 24일  
**버전**: 1.0.0  
**상태**: 계획 단계 📋
