#!/usr/bin/env python3
"""
Main_Server - 중앙 관리 서버 (포트 8001)
"""
import sys
import os
import logging
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import requests

# 실행 환경에 따라 환경 변수 파일 로드
env_mode = os.getenv("APP_ENV", "prod").lower()
env_filename = "config_dev.env" if env_mode == "dev" else "config.env"
env_file = Path(__file__).parent / env_filename

if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    print(f"[Main_Server] 경고: {env_filename} 파일을 찾을 수 없어 기본 OS 환경 변수만 사용합니다.")

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parents[1]  # Estimation_Server
estimation_root = project_root  # Estimation_Server (도커 컴포즈 파일들이 여기에 있음)

for path in [project_root, estimation_root]:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from api.endpoints import objects_router, servers_router, workflow_router
from api.models import HealthResponse
from utils.logging_config import setup_logging

# 로깅 설정
logger = setup_logging(
    log_dir=Path(__file__).parent / "logs",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_to_file=True,
    log_to_console=True
)


def check_docker_container_status(container_name: str) -> Tuple[Optional[bool], str]:
    """도커 컨테이너 상태 확인
    
    Returns:
        (is_running, status): 컨테이너가 실행 중인지 여부와 상태 문자열
    """
    try:
        cmd = ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Status}}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
        if result.returncode != 0:
            # Docker API 버전 오류는 무시하고 계속 진행
            if "500 Internal Server Error" in result.stderr or "API route and version" in result.stderr:
                logger.debug(f"Docker API version error (ignored): {result.stderr[:200]}")
                # Health check로 대체 확인
                return None, "docker api error (checking via health endpoint)"
            return False, f"docker command failed: {result.stderr[:100]}"
        
        output = result.stdout.strip()
        if not output:
            return False, "container not found"
        
        is_running = "Up" in output
        return is_running, output
    except FileNotFoundError:
        return False, "docker not found"
    except subprocess.TimeoutExpired:
        return False, "docker command timeout"
    except Exception as e:
        # Docker API 오류는 무시
        if "500 Internal Server Error" in str(e) or "API route and version" in str(e):
            logger.debug(f"Docker API version error (ignored): {str(e)[:200]}")
            return None, "docker api error (checking via health endpoint)"
        return False, f"error: {str(e)[:100]}"


def ensure_service_running(name: str, health_url: str, compose_dir: Path, container_name: str = None, retries: int = 3, wait_seconds: int = 3) -> None:
    """Ensure required service container is running by health check and optional docker compose up."""
    health_url = health_url.strip()
    if not health_url:
        logger.debug(f"{name}: health URL not provided; skipping auto-check.")
        return

    # 먼저 health check로 서버가 정상 동작하는지 확인
    try:
        resp = requests.get(health_url, timeout=3)
        if resp.status_code == 200:
            logger.info(f"{name}: healthy (status {resp.status_code}).")
            return
        logger.warning(f"{name}: health check returned {resp.status_code}, attempting to start container.")
    except Exception as exc:
        logger.warning(f"{name}: health check failed ({exc}), attempting to start container.")

    # docker-compose.yml 파일 경로 확인
    compose_dir = compose_dir.resolve()
    compose_file = compose_dir / "docker-compose.yml"
    if not compose_file.exists():
        logger.error(f"{name}: docker-compose.yml not found at {compose_file}")
        return

    # 컨테이너 이름이 제공된 경우 상태 확인
    if container_name:
        is_running, status = check_docker_container_status(container_name)
        if is_running is None:
            # Docker API 오류로 상태 확인 불가 - Health check로만 판단
            logger.debug(f"{name}: container status check skipped (Docker API error), using health check only")
        elif is_running:
            logger.info(f"{name}: container '{container_name}' is running but health check failed. Status: {status}")
        else:
            logger.info(f"{name}: container '{container_name}' is not running. Status: {status}")

    # docker compose up 실행 (Windows에서는 docker-compose 또는 docker compose 모두 지원)
    # 먼저 docker compose 시도, 실패하면 docker-compose 시도
    cmd = None
    for docker_cmd in [["docker", "compose", "up", "-d"], ["docker-compose", "up", "-d"]]:
        try:
            test_result = subprocess.run(
                [docker_cmd[0], "--version"] if docker_cmd[0] == "docker-compose" else ["docker", "compose", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if test_result.returncode == 0:
                cmd = docker_cmd
                break
        except:
            continue
    
    if cmd is None:
        logger.error(f"{name}: docker compose command not found. Please install Docker.")
        return
    
    try:
        logger.info(f"{name}: starting docker container from {compose_dir}...")
        logger.debug(f"{name}: executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=str(compose_dir), capture_output=True, text=True, check=False, timeout=60)
        if result.returncode != 0:
            logger.error(f"{name}: docker compose failed (code {result.returncode}).")
            if result.stdout:
                logger.error(f"  stdout: {result.stdout.strip()}")
            if result.stderr:
                logger.error(f"  stderr: {result.stderr.strip()}")
            return
        
        output = result.stdout.strip()
        if output:
            logger.info(f"{name}: docker compose output: {output}")
        else:
            logger.info(f"{name}: docker compose started successfully.")
    except FileNotFoundError:
        logger.error(f"{name}: docker command not found. Please install Docker or start the container manually.")
        return
    except subprocess.TimeoutExpired:
        logger.error(f"{name}: docker compose command timed out.")
        return
    except Exception as e:
        logger.error(f"{name}: unexpected error during docker compose: {e}")
        return

    # 컨테이너가 시작될 때까지 대기하고 health check 재시도
    logger.info(f"{name}: waiting for service to become healthy...")
    for attempt in range(1, retries + 1):
        time.sleep(wait_seconds)
        try:
            resp = requests.get(health_url, timeout=3)
            if resp.status_code == 200:
                logger.info(f"{name}: healthy after start (attempt {attempt}/{retries}).")
                return
            logger.warning(f"{name}: health check returned {resp.status_code} on attempt {attempt}/{retries}.")
        except Exception as exc:
            logger.warning(f"{name}: health check failed on attempt {attempt}/{retries}: {exc}")

    logger.error(f"{name}: failed to become healthy after {retries} attempts. Please investigate manually.")


# 환경 변수 로드 후 AUTO_START_DEPENDENCIES 확인
AUTO_START_DEPENDENCIES = os.getenv("AUTO_START_DEPENDENCIES", "true").lower() == "true"
logger.debug(f"AUTO_START_DEPENDENCIES={AUTO_START_DEPENDENCIES} (from env: {os.getenv('AUTO_START_DEPENDENCIES', 'not set')})")
REQUIRED_SERVICES = [
    {
        "name": "ISM Server",
        "health_url": os.getenv("ISM_HEALTH_URL", "http://localhost:8002/health"),
        "compose_dir": estimation_root / "ISM_Server",
        "container_name": "ism-server",
    },
    {
        "name": "PEM Server",
        "health_url": os.getenv("PEM_HEALTH_URL", "http://localhost:8003/api/v1/health"),
        "compose_dir": estimation_root / "PEM_Server",
        "container_name": "pem-server",
    },
    {
        "name": "Render Server",
        "health_url": os.getenv("RENDER_HEALTH_URL", "http://localhost:8004/health"),
        "compose_dir": estimation_root / "Render_Server",
        "container_name": "render-server",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("=" * 50)
    logger.info("Main Server starting...")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Port: 8001")
    logger.info("=" * 50)

    if AUTO_START_DEPENDENCIES:
        logger.info("Checking required service containers...")
        logger.info(f"AUTO_START_DEPENDENCIES is enabled. Checking {len(REQUIRED_SERVICES)} services...")
        for service in REQUIRED_SERVICES:
            logger.info(f"Checking {service['name']} at {service['compose_dir']}...")
            ensure_service_running(
                name=service["name"],
                health_url=service["health_url"],
                compose_dir=service["compose_dir"],
                container_name=service.get("container_name"),
            )
    else:
        logger.info("AUTO_START_DEPENDENCIES is disabled. Skipping container auto-start.")
    
    # 서버 상태 초기화
    try:
        from services.scanner import get_scanner
        scanner = get_scanner()
        stats = scanner.get_statistics()
        logger.info(f"스캔된 객체 수: {stats['total_objects']}")
        logger.info(f"템플릿 생성률: {stats['overall_completion_rate']:.1f}%")
    except Exception as e:
        logger.warning(f"초기 스캔 실패: {e}")
    
    yield
    
    # 종료 시 실행
    logger.info("=" * 50)
    logger.info("Main Server shutting down...")
    logger.info("=" * 50)


# FastAPI 앱 생성
app = FastAPI(
    title="Main Server",
    description="중앙 관리 서버 - 객체 데이터베이스 관리 및 워크플로우 오케스트레이션",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(objects_router)
app.include_router(servers_router)
app.include_router(workflow_router)


@app.get("/", response_model=HealthResponse)
async def root():
    """루트 엔드포인트"""
    logger.info("Root endpoint accessed")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """헬스 체크"""
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # 환경 변수에서 설정 읽기
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8001))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        reload_includes=["*.py"],
        reload_excludes=[
            "logs/*",
            "**/*.log",
            "static/output/*",
            "RSSServer_connector/output/*"
        ]
    )


