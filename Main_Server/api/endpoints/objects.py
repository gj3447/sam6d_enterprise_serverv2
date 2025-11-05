#!/usr/bin/env python3
"""
객체 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..models import (
    HealthResponse, ClassesResponse, ClassSummary,
    ObjectInfo, ClassObjectsResponse, ObjectDetail,
    ScanRequest
)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from Main_Server.services.scanner import get_scanner

router = APIRouter(prefix="/api/v1/objects", tags=["objects"])
scanner = get_scanner()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """객체 서비스 헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/classes", response_model=ClassesResponse)
async def get_classes():
    """모든 클래스 목록 반환"""
    classes = scanner.scan_all_classes()
    
    # 클래스 요약 생성
    class_summaries = []
    total_objects = 0
    total_templates = 0
    
    for class_info in classes:
        class_summaries.append(ClassSummary(
            name=class_info["name"],
            path=class_info["path"],
            object_count=class_info["object_count"],
            template_count=class_info["template_count"],
            template_completion_rate=class_info["template_completion_rate"]
        ))
        
        total_objects += class_info["object_count"]
        total_templates += class_info["template_count"]
    
    # 전체 통계 계산
    overall_completion_rate = (
        (total_templates / total_objects * 100) 
        if total_objects > 0 else 0.0
    )
    
    return ClassesResponse(
        classes=class_summaries,
        total_classes=len(class_summaries),
        total_objects=total_objects,
        total_templates=total_templates,
        overall_completion_rate=overall_completion_rate
    )


@router.get("/classes/{class_name}", response_model=ClassObjectsResponse)
async def get_class_objects(class_name: str):
    """특정 클래스의 객체 목록 반환"""
    class_info = scanner.scan_class(class_name)
    
    if not class_info:
        raise HTTPException(status_code=404, detail=f"Class not found: {class_name}")
    
    # 객체 정보 변환
    objects = []
    for obj in class_info["objects"]:
        objects.append(ObjectInfo(
            name=obj["name"],
            cad_file=obj["cad_file"],
            cad_path=obj["cad_path"],
            template_path=obj.get("template_path"),
            has_template=obj["has_template"],
            template_files=obj["template_files"],
            last_updated=obj.get("cad_last_modified"),
            status=obj["status"]
        ))
    
    return ClassObjectsResponse(
        class_name=class_name,
        objects=objects,
        object_count=len(objects),
        template_count=sum(1 for o in objects if o.has_template)
    )


@router.get("/{class_name}/{object_name}", response_model=ObjectDetail)
async def get_object_detail(class_name: str, object_name: str):
    """특정 객체의 상세 정보 반환"""
    obj_info = scanner.scan_object(class_name, object_name)
    
    if not obj_info:
        raise HTTPException(
            status_code=404, 
            detail=f"Object not found: {class_name}/{object_name}"
        )
    
    return ObjectDetail(
        name=object_name,
        class_name=class_name,
        cad_info={
            "file": obj_info["cad_file"],
            "path": obj_info["cad_path"],
            "size_bytes": obj_info["cad_size_bytes"],
            "last_modified": obj_info["cad_last_modified"]
        },
        template_info={
            "has_template": obj_info["has_template"],
            "path": obj_info.get("template_path"),
            "files": obj_info["template_files"],
            "last_generated": obj_info.get("template_last_updated")
        },
        status=obj_info["status"]
    )


@router.post("/scan", response_model=dict)
async def scan_objects(request: ScanRequest):
    """객체 디렉토리 재스캔"""
    # 강제 스캔은 현재 구현에서 항상 실시간 스캔을 하므로
    # 별도의 캐시 갱신이 필요 없음
    
    stats = scanner.get_statistics()
    
    return {
        "success": True,
        "message": "Scan completed",
        "statistics": stats
    }


