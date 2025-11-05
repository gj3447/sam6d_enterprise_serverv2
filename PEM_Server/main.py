# PEM_Server/main.py - FastAPI 서버 메인 파일
import logging
import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 프로젝트 루트를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import get_settings
from core.model_manager import get_model_manager
from core.logging_config import setup_logging
from api.endpoints import health, pose_estimation, model

# 설정 로드
settings = get_settings()

# 로깅 시스템 초기화
logger = setup_logging(
    log_dir="log",
    log_level=settings.log_level,
    log_format=settings.log_format
)

# 모델 매니저 초기화
model_manager = get_model_manager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("Starting PEM Server...")
    
    # 자동 모델 로딩
    logger.info("Loading model automatically...")
    try:
        success = model_manager.load_model()
        if success:
            logger.info("✅ Model loaded successfully on startup")
            if settings.preload_templates:
                logger.info(
                    "Preloading templates and CAD assets (capacity: template=%s, cad=%s)",
                    settings.template_cache_capacity,
                    settings.cad_cache_capacity,
                )
                model_manager.preload_assets()
        else:
            logger.error("❌ Failed to load model on startup")
    except Exception as e:
        logger.error(f"❌ Model loading error on startup: {e}")
    
    yield
    
    # 종료 시 실행
    logger.info("Shutting down PEM Server...")
    model_manager.unload_model()

# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="PEM (Pose Estimation Model) Server based on SAM-6D",
    lifespan=lifespan
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router)
app.include_router(pose_estimation.router)
app.include_router(model.router)

# 루트 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health"
    }

# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": time.time()
    }
    )

if __name__ == "__main__":
    import time
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Server will run on {settings.host}:{settings.port}")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
