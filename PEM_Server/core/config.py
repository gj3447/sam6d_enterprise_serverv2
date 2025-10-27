# PEM_Server/core/config.py
"""
PEM Server 설정 관리
"""
import os
from typing import Optional
from pydantic import BaseModel

class Settings(BaseModel):
    """서버 설정"""
    
    # 서버 설정
    app_name: str = "PEM Server"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API 설정
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8003
    
    # 모델 설정
    model_name: str = "pose_estimation_model"
    config_path: str = "/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/config/base.yaml"
    checkpoint_path: str = "/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/checkpoints/sam-6d-pem-base.pth"
    device: str = "cuda"  # GPU 사용
    
    # 파일 경로 설정
    workspace_root: str = "/workspace/Estimation_Server"
    sam6d_root: str = "/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model"
    pem_server_root: str = "/workspace/Estimation_Server/PEM_Server"
    
    # 로깅 설정
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 전역 설정 인스턴스
settings = Settings()

def get_settings() -> Settings:
    """설정 인스턴스 반환"""
    return settings
