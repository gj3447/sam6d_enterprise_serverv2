# PEM_Server/api/endpoints/health.py
"""
헬스 체크 및 상태 관련 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..models import ServerStatus, StatusEnum, ModelStatus, DeviceEnum
from core.model_manager import get_model_manager

router = APIRouter(prefix="/api/v1", tags=["health"])

# 서버 시작 시간
SERVER_START_TIME = time.time()

# 모델 매니저 인스턴스 가져오기
model_manager = get_model_manager()

@router.get("/health", response_model=ServerStatus)
async def health_check():
    """서버 헬스 체크"""
    uptime = time.time() - SERVER_START_TIME
    
    # 실제 모델 상태 가져오기
    model_status = model_manager.get_model_status()
    
    return ServerStatus(
        status=StatusEnum.HEALTHY,
        message="Server is running",
        uptime=uptime,
        model=ModelStatus(
            loaded=model_status["loaded"],
            device=DeviceEnum(model_status["device"]) if model_status["device"] else None,
            parameters=model_status["parameters"],
            loading_time=model_status["loading_time"]
        )
    )

@router.get("/status", response_model=Dict[str, Any])
async def get_status():
    """서버 상태 정보"""
    uptime = time.time() - SERVER_START_TIME
    
    # 실제 모델 상태 가져오기
    model_status = model_manager.get_model_status()
    
    return {
        "server": "running",
        "model_loaded": model_status["loaded"],
        "device": model_status["device"],
        "uptime": uptime,
        "version": "1.0.0"
    }

@router.get("/ping")
async def ping():
    """간단한 ping 테스트"""
    return {"message": "pong", "timestamp": time.time()}
