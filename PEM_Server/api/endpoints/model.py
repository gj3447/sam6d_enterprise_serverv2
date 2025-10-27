# PEM_Server/api/endpoints/model.py
"""
모델 관리 관련 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import time
import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..models import ModelStatus, DeviceEnum
from core.model_manager import get_model_manager

router = APIRouter(prefix="/api/v1", tags=["model"])

# 모델 매니저 인스턴스 가져오기
model_manager = get_model_manager()

@router.get("/model/status", response_model=ModelStatus)
async def get_model_status():
    """모델 상태 확인"""
    status = model_manager.get_model_status()
    return ModelStatus(
        loaded=status["loaded"],
        device=DeviceEnum(status["device"]) if status["device"] else None,
        parameters=status["parameters"],
        loading_time=status["loading_time"]
    )

@router.post("/model/load")
async def load_model(
    config_path: Optional[str] = None,
    checkpoint_path: Optional[str] = None,
    device: Optional[str] = "cuda"
):
    """
    모델 로딩
    
    Args:
        config_path: 설정 파일 경로
        checkpoint_path: 체크포인트 파일 경로
        device: 사용할 디바이스 (cuda/cpu)
        
    Returns:
        Dict: 로딩 결과
    """
    try:
        # 실제 모델 로딩 실행
        success = model_manager.load_model(config_path, checkpoint_path, device)
        
        if success:
            status = model_manager.get_model_status()
            return {
                "success": True,
                "message": "Model loaded successfully",
                "loading_time": status["loading_time"],
                "device": status["device"],
                "parameters": status["parameters"]
            }
        else:
            return {
                "success": False,
                "message": "Model loading failed",
                "loading_time": None
            }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Model loading failed: {str(e)}",
            "loading_time": None
        }

@router.post("/model/unload")
async def unload_model():
    """모델 언로드"""
    try:
        # 실제 모델 언로드 실행
        success = model_manager.unload_model()
        
        if success:
            return {
                "success": True,
                "message": "Model unloaded successfully"
            }
        else:
            return {
                "success": False,
                "message": "Model unloading failed"
            }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Model unloading failed: {str(e)}"
        }

@router.get("/model/info")
async def get_model_info():
    """모델 정보 조회"""
    return {
        "model_name": "SAM-6D PEM",
        "version": "1.0.0",
        "description": "Pose Estimation Model based on SAM-6D",
        "architecture": "Vision Transformer + PointNet2",
        "input_format": {
            "rgb": "RGB image",
            "depth": "Depth image", 
            "camera": "Camera parameters",
            "cad": "CAD model",
            "segmentation": "Segmentation mask"
        },
        "output_format": {
            "pose": "6D pose (rotation + translation)",
            "confidence": "Detection confidence score"
        }
    }
