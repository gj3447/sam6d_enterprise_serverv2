#!/usr/bin/env python3
"""
서버 상태 모니터링 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import Dict

from ..models import HealthResponse, ServerStatus, ServersStatusResponse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from Main_Server.services.server_monitor import get_monitor

router = APIRouter(prefix="/api/v1/servers", tags=["servers"])
monitor = get_monitor()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 상태 모니터링 헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/status", response_model=ServersStatusResponse)
async def get_all_servers_status():
    """모든 서버의 상태 확인"""
    try:
        result = await monitor.check_all_servers()
        
        # ServerStatus 객체로 변환
        server_statuses = {}
        for name, status in result["servers"].items():
            server_statuses[name] = ServerStatus(
                url=status["url"],
                status=status["status"],
                response_time_ms=status["response_time_ms"],
                last_check=status["last_check"],
                error_message=status.get("error_message")
            )
        
        return ServersStatusResponse(
            servers=server_statuses,
            overall_status=result["overall_status"],
            healthy_servers=result["healthy_servers"],
            total_servers=result["total_servers"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{server_name}", response_model=ServerStatus)
async def get_server_status(server_name: str):
    """특정 서버의 상태 확인"""
    if server_name not in monitor.SERVERS:
        raise HTTPException(
            status_code=404, 
            detail=f"Server not found: {server_name}"
        )
    
    url = monitor.SERVERS[server_name]
    status = await monitor.check_server_health(server_name, url)
    
    return ServerStatus(
        url=status["url"],
        status=status["status"],
        response_time_ms=status["response_time_ms"],
        last_check=status["last_check"],
        error_message=status.get("error_message")
    )


