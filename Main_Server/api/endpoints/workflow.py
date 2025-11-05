#!/usr/bin/env python3
"""
워크플로우 오케스트레이션 API 엔드포인트
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, Optional

from ..models import (
    HealthResponse, RenderTemplatesRequest, FullPipelineRequest, WorkflowResponse,
    RenderMissingTemplatesRequest, RenderAllTemplatesRequest, RenderSingleTemplateRequest,
    RssFullPipelineRequest
)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from Main_Server.services.workflow_service import get_workflow_service
from Main_Server.services.scanner import get_scanner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflow", tags=["workflow"])
workflow_service = get_workflow_service()
scanner = get_scanner()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """워크플로우 서비스 헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.post("/render-templates", response_model=WorkflowResponse)
async def render_templates(request: RenderTemplatesRequest):
    """템플릿 생성 워크플로우 시작"""
    try:
        logger.info(f"템플릿 생성 요청: {request.class_name} - {request.object_names}")
        result = await workflow_service.render_templates(
            class_name=request.class_name,
            object_names=request.object_names,
            force_regenerate=request.force_regenerate
        )
        
        logger.info(f"템플릿 생성 완료: {result['successful']}/{result['total']}")
        
        return WorkflowResponse(
            success=result["success"],
            message=f"Processed {result['successful']}/{result['total']} objects",
            results=result
        )
    except Exception as e:
        logger.error(f"템플릿 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/render-templates-missing", response_model=WorkflowResponse)
async def render_missing_templates(request: RenderMissingTemplatesRequest):
    """템플릿이 없는 객체들만 템플릿 생성
    
    Args:
        request: 요청 데이터
    """
    class_name = request.class_name
    try:
        # 클래스 정보 수집
        if class_name:
            class_info = scanner.scan_class(class_name)
            if not class_info:
                raise HTTPException(status_code=404, detail=f"Class not found: {class_name}")
            classes = [class_info]
        else:
            classes = scanner.scan_all_classes()
        
        # 템플릿이 없는 객체들 찾기
        objects_to_render = []
        for class_info in classes:
            for obj in class_info["objects"]:
                if not obj["has_template"]:
                    objects_to_render.append({
                        "class_name": class_info["name"],
                        "object_name": obj["name"]
                    })
        
        if not objects_to_render:
            return WorkflowResponse(
                success=True,
                message="No missing templates found",
                results={"processed": 0, "skipped": 0}
            )
        
        # 템플릿 생성
        results = []
        for obj_info in objects_to_render:
            result = await workflow_service.render_templates(
                class_name=obj_info["class_name"],
                object_names=[obj_info["object_name"]],
                force_regenerate=False
            )
            results.append(result)
        
        # 결과 집계
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        return WorkflowResponse(
            success=successful > 0,
            message=f"Generated templates for {successful}/{total} objects",
            results={
                "total": total,
                "successful": successful,
                "objects": objects_to_render
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/render-templates-all", response_model=WorkflowResponse)
async def render_all_templates(request: RenderAllTemplatesRequest):
    """모든 객체 템플릿 생성 (강제 재생성 가능)
    
    Args:
        request: 요청 데이터
    """
    class_name = request.class_name
    force = request.force
    try:
        # 클래스 정보 수집
        if class_name:
            class_info = scanner.scan_class(class_name)
            if not class_info:
                raise HTTPException(status_code=404, detail=f"Class not found: {class_name}")
            classes = [class_info]
        else:
            classes = scanner.scan_all_classes()
        
        # 모든 객체 수집
        objects_to_render = []
        for class_info in classes:
            for obj in class_info["objects"]:
                if force or not obj["has_template"]:
                    objects_to_render.append({
                        "class_name": class_info["name"],
                        "object_name": obj["name"]
                    })
        
        if not objects_to_render:
            return WorkflowResponse(
                success=True,
                message="No objects found",
                results={"processed": 0}
            )
        
        # 템플릿 생성
        results = []
        for obj_info in objects_to_render:
            result = await workflow_service.render_templates(
                class_name=obj_info["class_name"],
                object_names=[obj_info["object_name"]],
                force_regenerate=force
            )
            results.append(result)
        
        # 결과 집계
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        return WorkflowResponse(
            success=successful > 0,
            message=f"Generated templates for {successful}/{total} objects",
            results={
                "total": total,
                "successful": successful,
                "force_regenerate": force,
                "objects": objects_to_render
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/render-template-single", response_model=WorkflowResponse)
async def render_single_template(request: RenderSingleTemplateRequest):
    """특정 객체 템플릿 생성
    
    Args:
        request: 요청 데이터
    """
    class_name = request.class_name
    object_name = request.object_name
    force = request.force
    try:
        result = await workflow_service.render_templates(
            class_name=class_name,
            object_names=[object_name],
            force_regenerate=force
        )
        
        return WorkflowResponse(
            success=result["success"],
            message=f"Template generation for {class_name}/{object_name}",
            results=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/full-pipeline", response_model=WorkflowResponse)
async def execute_full_pipeline(request: FullPipelineRequest):
    """전체 파이프라인 실행 (Render → ISM → PEM)"""
    try:
        logger.info(f"파이프라인 실행 요청: {request.class_name}/{request.object_name}")
        mode = request.output_mode
        if mode is None:
            if request.save_outputs is None:
                mode = "full"
            else:
                mode = "full" if request.save_outputs else "none"
        mode = mode.lower()
        if mode not in {"full", "results_only", "none"}:
            mode = "full"

        result = await workflow_service.execute_full_pipeline(
            class_name=request.class_name,
            object_name=request.object_name,
            rgb_image=request.rgb_image,
            depth_image=request.depth_image,
            cam_params=request.cam_params,
            output_dir=request.output_dir,
            frame_guess=request.frame_guess or False,
            request_tag="api-full-pipeline",
            output_mode=mode,
        )
        summary = {
            "pose_results": result.get("pose_results", []),
            "num_poses": result.get("num_poses", 0),
            "output_dir": result.get("output_dir"),
            "request_tag": result.get("request_tag"),
        }
        if not result.get("success"):
            summary["error"] = result.get("error")
            logger.error(f"파이프라인 실행 실패: {result.get('error')}")
        else:
            logger.info(f"파이프라인 실행 성공: {result.get('output_dir')}")
        
        return WorkflowResponse(
            success=result.get("success", False),
            message="Pipeline execution completed" if result.get("success") else "Pipeline execution failed",
            results=summary
        )
    except Exception as e:
        logger.error(f"파이프라인 실행 중 에러: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/full-pipeline-from-rss", response_model=WorkflowResponse)
async def execute_full_pipeline_from_rss(request: RssFullPipelineRequest):
    """RSS 서버에서 직접 프레임을 받아 전체 파이프라인 실행"""
    try:
        mode = request.output_mode
        if mode is None:
            if request.save_outputs is None:
                mode = "full"
            else:
                mode = "full" if request.save_outputs else "none"
        mode = mode.lower()
        if mode not in {"full", "results_only", "none"}:
            mode = "full"

        result = await workflow_service.execute_full_pipeline_from_rss(
            class_name=request.class_name,
            object_name=request.object_name,
            base=request.base,
            host=request.host,
            port=request.port,
            align_color=request.align_color,
            output_dir=request.output_dir,
            frame_guess=request.frame_guess or False,
            request_tag="api-full-pipeline-from-rss",
            output_mode=mode,
        )
        summary = {
            "pose_results": result.get("pose_results", []),
            "num_poses": result.get("num_poses", 0),
            "output_dir": result.get("output_dir"),
            "request_tag": result.get("request_tag"),
        }
        if not result.get("success"):
            summary["error"] = result.get("error")
        return WorkflowResponse(
            success=result.get("success", False),
            message="Pipeline execution completed" if result.get("success") else "Pipeline execution failed",
            results=summary,
        )
    except Exception as e:
        logger.error(f"RSS 파이프라인 실행 중 에러: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
