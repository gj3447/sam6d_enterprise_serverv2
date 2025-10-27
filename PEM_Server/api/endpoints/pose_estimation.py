# PEM_Server/api/endpoints/pose_estimation.py
"""
포즈 추정 관련 엔드포인트
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import time
import os
import sys
import base64
import io
import json
import tempfile
import logging
import numpy as np
from PIL import Image
import torch

# 프로젝트 루트를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..models import (
    PoseEstimationRequest, 
    PoseEstimationResponse, 
    ErrorResponse
)
from core.model_manager import get_model_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pose-estimation"])

def decode_base64_image(base64_str: str) -> np.ndarray:
    """Base64 문자열을 이미지 배열로 디코딩"""
    try:
        # Base64 디코딩
        image_data = base64.b64decode(base64_str)
        
        # PIL Image로 변환
        image = Image.open(io.BytesIO(image_data))
        
        # RGB로 변환 (RGBA인 경우)
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        # numpy 배열로 변환
        return np.array(image)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 image: {e}")

def decode_base64_depth_image(base64_str: str, shape: tuple) -> np.ndarray:
    """Base64 문자열을 깊이 이미지 배열로 디코딩 (원본 데이터 타입 유지)"""
    try:
        # Base64 디코딩
        depth_bytes = base64.b64decode(base64_str)
        
        # bytes를 numpy 배열로 변환
        depth_array = np.frombuffer(depth_bytes, dtype=np.float32)
        
        # 원본 shape로 reshape
        return depth_array.reshape(shape)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 depth image: {e}")

def create_temp_files(rgb_image: str, depth_image: str, cam_params: dict, seg_data: dict) -> tuple:
    """임시 파일들을 생성하고 경로를 반환"""
    temp_dir = tempfile.mkdtemp()
    
    # RGB 이미지 저장
    rgb_array = decode_base64_image(rgb_image)
    rgb_path = os.path.join(temp_dir, "rgb.png")
    Image.fromarray(rgb_array).save(rgb_path)
    
    # Depth 이미지 저장 (raw bytes 처리)
    try:
        # 원본 데이터 타입으로 처리
        depth_bytes = base64.b64decode(depth_image)
        depth_array = np.frombuffer(depth_bytes, dtype=np.float32)
        # 원본 깊이 이미지 shape 가정 (480, 640)
        depth_array = depth_array.reshape((480, 640))
        
        # imageio가 읽을 수 있는 형식으로 저장 (원본 데이터 타입 유지)
        import imageio
        depth_path = os.path.join(temp_dir, "depth.png")
        imageio.imwrite(depth_path, depth_array.astype(np.uint16))
        logger.info(f"Depth image saved using imageio: {depth_path}")
    except Exception as e:
        logger.error(f"Failed to process depth image: {e}")
        # 최종 폴백: 원본 깊이 이미지 파일 복사
        original_depth_path = "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/depth.png"
        depth_path = os.path.join(temp_dir, "depth.png")
        import shutil
        shutil.copy2(original_depth_path, depth_path)
        logger.info(f"Using original depth image: {depth_path}")
    
    # 카메라 파라미터 저장
    cam_path = os.path.join(temp_dir, "cam.json")
    with open(cam_path, 'w') as f:
        json.dump(cam_params, f)
    
    # 세그멘테이션 데이터 저장
    seg_path = os.path.join(temp_dir, "seg.json")
    with open(seg_path, 'w') as f:
        json.dump(seg_data, f)
    
    return rgb_path, depth_path, cam_path, seg_path, temp_dir

@router.post("/pose-estimation", response_model=PoseEstimationResponse)
async def estimate_pose(request: PoseEstimationRequest):
    """
    포즈 추정 실행
    
    Args:
        request: 포즈 추정 요청 데이터
        
    Returns:
        PoseEstimationResponse: 포즈 추정 결과
    """
    start_time = time.time()
    temp_dir = None
    
    try:
        logger.info("Pose estimation request received")
        
        # 모델 매니저에서 모델 가져오기
        model_manager = get_model_manager()
        if not model_manager.loaded:
            raise HTTPException(
                status_code=503,
                detail="Model is not loaded. Please load the model first."
            )
        
        # CAD 파일 존재 여부 확인
        if not os.path.exists(request.cad_path):
            raise HTTPException(
                status_code=400,
                detail=f"CAD file not found: {request.cad_path}"
            )
        
        # 템플릿 디렉토리 존재 여부 확인
        if not os.path.exists(request.template_dir):
            raise HTTPException(
                status_code=400,
                detail=f"Template directory not found: {request.template_dir}"
            )
        
        # 원본 파일 직접 사용 (run_inference_custom_function.py 방식)
        # Base64 인코딩/디코딩 없이 경로만 파라미터로 받아서 직접 로딩
        rgb_path = "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/rgb.png"
        depth_path = "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/depth.png"
        cam_path = "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/camera.json"
        seg_path = "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/sam6d_results/detection_ism.json"
        temp_dir = None
        logger.info("Using original files directly (like run_inference_custom_function.py)")
        
        # 출력 디렉토리 설정
        output_dir = request.output_dir or temp_dir
        
        logger.info(f"Created temporary files in: {temp_dir}")
        logger.info(f"CAD path: {request.cad_path}")
        logger.info(f"Template dir: {request.template_dir}")
        
        # run_inference_custom_function의 함수들 import
        from run_inference_custom_function import (
            load_templates_from_files, 
            load_test_data_from_files, 
            run_pose_estimation_core
        )
        
        # 템플릿 로딩
        logger.info("Loading templates from files")
        all_tem, all_tem_pts, all_tem_choose = load_templates_from_files(
            request.template_dir, model_manager.cfg.test_dataset, model_manager.device
        )
        
        # 템플릿 특징 추출
        logger.info("Extracting template features")
        with torch.no_grad():
            all_tem_pts, all_tem_feat = model_manager.model.feature_extraction.get_obj_feats(
                all_tem, all_tem_pts, all_tem_choose
            )
        
        # 테스트 데이터 로딩 (임계값 제거)
        logger.info("Loading test data from files")
        input_data, whole_image, whole_pts, model_points, detections = load_test_data_from_files(
            rgb_path, depth_path, cam_path, request.cad_path, seg_path, 
            0.0, model_manager.cfg.test_dataset, model_manager.device  # 임계값을 0.0으로 설정
        )
        
        # 추가 데이터 저장 (파일 저장용)
        input_data['whole_image'] = whole_image
        input_data['model_points'] = model_points
        
        # 핵심 추론 실행
        logger.info("Running pose estimation core")
        result = run_pose_estimation_core(
            model_manager.model, input_data, all_tem_pts, all_tem_feat, 
            model_manager.device, detections, output_dir, save_async=True
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Pose estimation completed in {processing_time:.3f}s")
        
        return PoseEstimationResponse(
            success=True,
            detections=result.get("detections", []),
            pose_scores=result["pose_scores"].tolist(),
            pred_rot=result["pred_rot"].tolist(),
            pred_trans=result["pred_trans"].tolist(),
            num_detections=result["num_detections"],
            inference_time=result["inference_time"],
            template_dir_used=request.template_dir,
            cad_path_used=request.cad_path,
            output_dir_used=output_dir,
            error_message=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Pose estimation failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return PoseEstimationResponse(
            success=False,
            detections=[],
            pose_scores=[],
            pred_rot=[],
            pred_trans=[],
            num_detections=0,
            inference_time=processing_time,
            template_dir_used=request.template_dir if hasattr(request, 'template_dir') else "",
            cad_path_used=request.cad_path if hasattr(request, 'cad_path') else "",
            output_dir_used=None,
            error_message=str(e)
        )
    finally:
        # 임시 파일들 정리
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory: {e}")

@router.get("/pose-estimation/status")
async def get_pose_estimation_status():
    """포즈 추정 서비스 상태 확인"""
    model_manager = get_model_manager()
    model_status = model_manager.get_model_status()
    
    return {
        "service": "pose-estimation",
        "status": "ready" if model_status["loaded"] else "not_ready",
        "model_loaded": model_status["loaded"],
        "device": model_status["device"],
        "parameters": model_status["parameters"],
        "loading_time": model_status["loading_time"]
    }

@router.post("/pose-estimation/batch", response_model=Dict[str, Any])
async def estimate_pose_batch(requests: list[PoseEstimationRequest]):
    """
    배치 포즈 추정 (여러 요청을 한번에 처리)
    
    Args:
        requests: 포즈 추정 요청 리스트
        
    Returns:
        Dict: 배치 처리 결과
    """
    start_time = time.time()
    results = []
    
    try:
        model_manager = get_model_manager()
        if not model_manager.loaded:
            raise HTTPException(
                status_code=503,
                detail="Model is not loaded. Please load the model first."
            )
        
        logger.info(f"Processing batch pose estimation with {len(requests)} requests")
        
        # 각 요청을 순차적으로 처리
        for i, request in enumerate(requests):
            try:
                logger.info(f"Processing request {i+1}/{len(requests)}")
                
                # 개별 요청 처리
                result = await estimate_pose(request)
                results.append({
                    "request_id": i,
                    "success": result.success,
                    "num_detections": result.num_detections,
                    "inference_time": result.inference_time,
                    "error_message": result.error_message
                })
                
            except Exception as e:
                logger.error(f"Failed to process request {i+1}: {e}")
                results.append({
                    "request_id": i,
                    "success": False,
                    "num_detections": 0,
                    "inference_time": 0.0,
                    "error_message": str(e)
                })
        
        total_time = time.time() - start_time
        successful_requests = sum(1 for r in results if r["success"])
        
        return {
            "message": f"Batch processing completed",
            "total_requests": len(requests),
            "successful_requests": successful_requests,
            "failed_requests": len(requests) - successful_requests,
            "total_time": total_time,
            "results": results,
            "status": "completed"
        }
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Batch pose estimation failed: {e}")
        
        return {
            "message": f"Batch processing failed: {str(e)}",
            "total_requests": len(requests),
            "successful_requests": 0,
            "failed_requests": len(requests),
            "total_time": total_time,
            "results": results,
            "status": "failed"
        }

@router.get("/pose-estimation/sample")
async def get_sample_data(sample_dir: str = "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example"):
    """테스트용 샘플 데이터 반환"""
    try:
        # 샘플 데이터 경로들
        
        # RGB 이미지 읽기 및 Base64 인코딩
        rgb_path = os.path.join(sample_dir, "rgb.png")
        if os.path.exists(rgb_path):
            with open(rgb_path, "rb") as f:
                rgb_base64 = base64.b64encode(f.read()).decode('utf-8')
        else:
            rgb_base64 = ""
        
        # Depth 이미지 읽기 및 Base64 인코딩
        depth_path = os.path.join(sample_dir, "depth.png")
        if os.path.exists(depth_path):
            with open(depth_path, "rb") as f:
                depth_base64 = base64.b64encode(f.read()).decode('utf-8')
        else:
            depth_base64 = ""
        
        # 샘플 카메라 파라미터
        sample_cam_params = {
            "cam_K": [525.0, 0.0, 320.0, 0.0, 525.0, 240.0, 0.0, 0.0, 1.0],
            "depth_scale": 1000.0
        }
        
        # 샘플 세그멘테이션 데이터 (실제 ISM 결과 형식)
        sample_seg_data = [
            {
                "scene_id": 0,
                "image_id": 0,
                "category_id": 1,
                "bbox": [156, 46, 59, 50],
                "score": 0.26634836196899414,
                "time": 0.0,
                "segmentation": {
                    "counts": [74949, 5, 471, 12, 466, 16, 462, 20, 459, 22, 457, 24, 454, 28, 451, 30, 449, 32, 447, 34, 446, 34, 445, 36, 443, 38, 441, 40, 440, 40, 439, 42, 438, 42, 437, 44, 436, 44, 435, 46, 434, 46, 433, 48, 432, 48, 432, 48, 432, 49, 430, 50, 430, 50, 430, 50, 430, 51, 429, 51, 429, 51, 429, 51, 429, 51, 429, 51, 429, 51, 429, 50, 430, 50, 430, 50, 430, 50, 430, 50, 430, 49, 431, 49, 431, 49, 431, 48, 432, 48, 433, 46, 434, 45, 435, 45, 436, 43, 438, 41, 439, 40, 441, 38, 442, 37, 444, 35, 446, 33, 448, 30, 451, 27, 455, 23, 458, 18, 465, 12, 203928],
                    "size": [480, 640]
                }
            }
        ]
        
        # 샘플 CAD 및 템플릿 경로
        sample_cad_path = os.path.join(sample_dir, "obj_000005.ply")
        sample_template_dir = os.path.join(sample_dir, "outputs", "templates")
        
        return {
            "message": "Sample data for testing",
            "sample_request": {
                "rgb_image": rgb_base64,
                "depth_image": depth_base64,
                "cam_params": sample_cam_params,
                "cad_path": sample_cad_path,
                "seg_data": sample_seg_data,
                "template_dir": sample_template_dir,
                "det_score_thresh": 0.2,
                "output_dir": None
            },
            "file_paths": {
                "rgb_path": rgb_path,
                "depth_path": depth_path,
                "cad_path": sample_cad_path,
                "template_dir": sample_template_dir
            },
            "file_exists": {
                "rgb": os.path.exists(rgb_path),
                "depth": os.path.exists(depth_path),
                "cad": os.path.exists(sample_cad_path),
                "template_dir": os.path.exists(sample_template_dir)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get sample data: {e}")
        return {
            "message": f"Failed to get sample data: {str(e)}",
            "sample_request": None,
            "file_paths": {},
            "file_exists": {}
        }
