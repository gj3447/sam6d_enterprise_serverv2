# PEM_Server/api/models.py
"""
PEM Server API 데이터 모델 정의
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class StatusEnum(str, Enum):
    """서버 상태 열거형"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    LOADING = "loading"

class DeviceEnum(str, Enum):
    """디바이스 타입 열거형"""
    CUDA = "cuda"
    CPU = "cpu"

class ModelStatus(BaseModel):
    """모델 상태 정보"""
    loaded: bool
    device: Optional[DeviceEnum] = None
    parameters: Optional[int] = None
    loading_time: Optional[float] = None

class ServerStatus(BaseModel):
    """서버 상태 정보"""
    status: StatusEnum
    message: str
    uptime: float
    model: Optional[ModelStatus] = None

class PoseEstimationRequest(BaseModel):
    """포즈 추정 요청 모델"""
    rgb_image: str          # Base64 인코딩된 RGB 이미지
    depth_image: str        # Base64 인코딩된 깊이 이미지
    cam_params: dict        # 카메라 파라미터 (cam_K, depth_scale)
    cad_path: str           # CAD 모델 경로 (필수)
    seg_data: List[Dict[str, Any]]  # ISM 세그멘테이션 결과 데이터
    template_dir: str       # 템플릿 디렉토리 경로 (필수)
    det_score_thresh: float = 0.2  # 검출 점수 임계값
    output_dir: Optional[str] = None  # 결과 저장 경로 (선택사항)

class PoseEstimationResponse(BaseModel):
    """포즈 추정 응답 모델"""
    success: bool
    detections: List[Dict[str, Any]]  # 검출 결과 리스트
    pose_scores: List[float]          # 포즈 점수
    pred_rot: List[List[List[float]]]  # 회전 행렬
    pred_trans: List[List[float]]     # 변위 벡터
    num_detections: int               # 검출된 객체 수
    inference_time: float             # 추론 시간
    template_dir_used: str           # 사용된 템플릿 디렉토리
    cad_path_used: str               # 사용된 CAD 경로
    output_dir_used: Optional[str] = None  # 사용된 출력 경로
    error_message: Optional[str] = None

class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    timestamp: float
