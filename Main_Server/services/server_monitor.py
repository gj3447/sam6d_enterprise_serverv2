#!/usr/bin/env python3
"""
서버 상태 모니터링 서비스
"""
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Optional
try:
    from ..utils.path_utils import get_static_paths
except ImportError:
    from utils.path_utils import get_static_paths


class ServerMonitor:
    """다른 서버들의 상태를 모니터링하는 클래스"""
    
    SERVERS = {
        "ism": "http://localhost:8002",
        "pem": "http://localhost:8003",
        "render": "http://localhost:8004"
    }
    
    TIMEOUT_SECONDS = 5
    
    async def check_server_health(self, name: str, url: str) -> Dict:
        """서버 상태 확인
        
        Args:
            name: 서버 이름
            url: 서버 URL
            
        Returns:
            Dict: 서버 상태 정보
        """
        start_time = datetime.now()
        
        # PEM 서버는 /api/v1/health, 다른 서버는 /health 사용
        health_endpoint = "/api/v1/health" if name == "pem" else "/health"
        
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                # /health 엔드포인트 확인
                try:
                    response = await client.get(f"{url}{health_endpoint}")
                    end_time = datetime.now()
                    
                    if response.status_code == 200:
                        response_time = int((end_time - start_time).total_seconds() * 1000)
                        return {
                            "url": url,
                            "status": "healthy",
                            "response_time_ms": response_time,
                            "last_check": start_time.isoformat(),
                            "error_message": None
                        }
                    else:
                        return {
                            "url": url,
                            "status": "unhealthy",
                            "response_time_ms": None,
                            "last_check": start_time.isoformat(),
                            "error_message": f"HTTP {response.status_code}"
                        }
                except httpx.TimeoutException:
                    return {
                        "url": url,
                        "status": "unhealthy",
                        "response_time_ms": None,
                        "last_check": start_time.isoformat(),
                        "error_message": "Connection timeout"
                    }
                except Exception as e:
                    return {
                        "url": url,
                        "status": "unhealthy",
                        "response_time_ms": None,
                        "last_check": start_time.isoformat(),
                        "error_message": str(e)
                    }
        except Exception as e:
            return {
                "url": url,
                "status": "unhealthy",
                "response_time_ms": None,
                "last_check": start_time.isoformat(),
                "error_message": str(e)
            }
    
    async def check_all_servers(self) -> Dict:
        """모든 서버 상태 확인
        
        Returns:
            Dict: 모든 서버 상태 정보
        """
        tasks = [
            self.check_server_health(name, url)
            for name, url in self.SERVERS.items()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 결과를 딕셔너리로 변환
        server_statuses = {}
        for i, (name, _) in enumerate(self.SERVERS.items()):
            server_statuses[name] = results[i]
        
        # 전체 상태 계산
        healthy_servers = sum(1 for s in results if s["status"] == "healthy")
        total_servers = len(results)
        
        if healthy_servers == total_servers:
            overall_status = "healthy"
        elif healthy_servers > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "servers": server_statuses,
            "overall_status": overall_status,
            "healthy_servers": healthy_servers,
            "total_servers": total_servers
        }


# 전역 모니터 인스턴스
_monitor = None

def get_monitor() -> ServerMonitor:
    """모니터 인스턴스 반환 (싱글톤)"""
    global _monitor
    if _monitor is None:
        _monitor = ServerMonitor()
    return _monitor


