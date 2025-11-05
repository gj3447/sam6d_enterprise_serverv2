#!/usr/bin/env python3
"""
API 모델 정의 (Pydantic)
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ============= 공통 모델 =============

class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str = Field(..., description="서버 상태")
    timestamp: str = Field(..., description="체크 시간")


# ============= 객체 관리 모델 =============

class ObjectInfo(BaseModel):
    """객체 정보"""
    name: str = Field(..., description="객체 이름")
    cad_file: str = Field(..., description="CAD 파일명")
    cad_path: str = Field(..., description="CAD 파일 경로")
    template_path: Optional[str] = Field(None, description="템플릿 디렉토리 경로")
    has_template: bool = Field(..., description="템플릿 생성 여부")
    template_files: Dict[str, int] = Field(..., description="템플릿 파일 통계")
    last_updated: Optional[str] = Field(None, description="마지막 업데이트 시간")
    status: str = Field(..., description="상태 (ready, needs_template, unknown)")


class ClassSummary(BaseModel):
    """클래스 요약 정보"""
    name: str = Field(..., description="클래스 이름")
    path: str = Field(..., description="클래스 경로")
    object_count: int = Field(..., description="객체 수")
    template_count: int = Field(..., description="템플릿 생성된 객체 수")
    template_completion_rate: float = Field(..., description="템플릿 완성률 (%)")


class ClassesResponse(BaseModel):
    """클래스 목록 응답"""
    classes: List[ClassSummary] = Field(..., description="클래스 목록")
    total_classes: int = Field(..., description="전체 클래스 수")
    total_objects: int = Field(..., description="전체 객체 수")
    total_templates: int = Field(..., description="전체 템플릿 수")
    overall_completion_rate: float = Field(..., description="전체 완성률 (%)")


class ObjectDetail(BaseModel):
    """객체 상세 정보"""
    name: str = Field(..., description="객체 이름")
    class_name: str = Field(..., description="클래스 이름")
    cad_info: Dict[str, Any] = Field(..., description="CAD 파일 정보")
    template_info: Dict[str, Any] = Field(..., description="템플릿 정보")
    status: str = Field(..., description="상태")


class ClassObjectsResponse(BaseModel):
    """클래스의 객체 목록 응답"""
    class_name: str = Field(..., description="클래스 이름")
    objects: List[ObjectInfo] = Field(..., description="객체 목록")
    object_count: int = Field(..., description="객체 수")
    template_count: int = Field(..., description="템플릿 수")


class ScanRequest(BaseModel):
    """스캔 요청"""
    force: bool = Field(False, description="강제 재스캔 여부")


# ============= 서버 상태 모델 =============

class ServerStatus(BaseModel):
    """서버 상태"""
    url: str = Field(..., description="서버 URL")
    status: str = Field(..., description="상태 (healthy, unhealthy, unknown)")
    response_time_ms: Optional[int] = Field(None, description="응답 시간 (ms)")
    last_check: str = Field(..., description="마지막 체크 시간")
    error_message: Optional[str] = Field(None, description="에러 메시지")


class ServersStatusResponse(BaseModel):
    """서버 상태 목록 응답"""
    servers: Dict[str, ServerStatus] = Field(..., description="서버 상태")
    overall_status: str = Field(..., description="전체 상태")
    healthy_servers: int = Field(..., description="정상 서버 수")
    total_servers: int = Field(..., description="전체 서버 수")


# ============= 워크플로우 모델 =============

class RenderTemplatesRequest(BaseModel):
    """템플릿 생성 요청"""
    class_name: str = Field(..., description="클래스 이름")
    object_names: List[str] = Field(..., description="객체 이름 목록")
    force_regenerate: bool = Field(False, description="강제 재생성 여부")


class RenderMissingTemplatesRequest(BaseModel):
    """템플릿 없는 객체들만 생성 요청"""
    class_name: Optional[str] = Field(None, description="클래스 이름 (None이면 모든 클래스)")


class RenderAllTemplatesRequest(BaseModel):
    """모든 객체 템플릿 생성 요청"""
    class_name: Optional[str] = Field(None, description="클래스 이름 (None이면 모든 클래스)")
    force: bool = Field(False, description="강제 재생성 여부")


class RenderSingleTemplateRequest(BaseModel):
    """특정 객체 템플릿 생성 요청"""
    class_name: str = Field(..., description="클래스 이름")
    object_name: str = Field(..., description="객체 이름")
    force: bool = Field(False, description="강제 재생성 여부")


class FullPipelineRequest(BaseModel):
    """전체 파이프라인 실행 요청"""
    class_name: str = Field(..., description="클래스 이름")
    object_name: str = Field(..., description="객체 이름")
    rgb_image: str = Field(..., description="Base64 인코딩된 RGB 이미지")
    depth_image: str = Field(..., description="Base64 인코딩된 Depth 이미지")
    cam_params: Dict[str, Any] = Field(..., description="카메라 파라미터 (intrinsics)")
    output_dir: Optional[str] = Field(None, description="출력 디렉토리")
    # 카메라 프레임 유추(보정 회전 후보 적용) 사용 여부
    frame_guess: Optional[bool] = Field(False, description="카메라 프레임 유추 보정 활성화")
    save_outputs: Optional[bool] = Field(True, description="결과 파일과 이미지를 저장할지 여부")
    output_mode: Optional[str] = Field(
        None,
        description="출력 전략 (full/results_only/none). 지정하지 않으면 save_outputs 값 기준으로 결정",
    )


class WorkflowResponse(BaseModel):
    """워크플로우 응답"""
    success: bool = Field(..., description="성공 여부")
    job_id: Optional[str] = Field(None, description="작업 ID")
    message: str = Field(..., description="메시지")
    results: Optional[Dict[str, Any]] = Field(None, description="결과")


class RssFullPipelineRequest(BaseModel):
    """RSS 서버에서 직접 이미지를 가져와 전체 파이프라인 실행 요청"""
    class_name: str = Field(..., description="클래스 이름")
    object_name: str = Field(..., description="객체 이름")
    base: Optional[str] = Field(None, description="예: http://192.168.0.197:51000")
    host: Optional[str] = Field(None, description="RSS 서버 호스트")
    port: Optional[int] = Field(None, description="RSS 서버 포트")
    align_color: bool = Field(False, description="컬러 프레임 기준으로 cam_K 선택")
    frame_guess: Optional[bool] = Field(False, description="카메라 프레임 유추 보정 활성화")
    output_dir: Optional[str] = Field(None, description="출력 디렉토리")
    save_outputs: Optional[bool] = Field(True, description="결과 파일과 이미지를 저장할지 여부")
    output_mode: Optional[str] = Field(
        None,
        description="출력 전략 (full/results_only/none). 지정하지 않으면 save_outputs 값 기준으로 결정",
    )


class JobStatus(BaseModel):
    """작업 상태"""
    job_id: str = Field(..., description="작업 ID")
    job_type: str = Field(..., description="작업 타입")
    status: str = Field(..., description="상태 (pending, running, completed, failed)")
    progress: int = Field(..., description="진행률 (%)")
    started_at: Optional[str] = Field(None, description="시작 시간")
    completed_at: Optional[str] = Field(None, description="완료 시간")
    error_message: Optional[str] = Field(None, description="에러 메시지")


