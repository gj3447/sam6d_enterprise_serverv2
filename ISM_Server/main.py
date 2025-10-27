# ISM_Server/main.py - Phase 2: 모델 로딩 기능 구현
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import sys
import time
import torch
import trimesh
from PIL import Image
import numpy as np
import base64
import io
import json
import logging
from datetime import datetime
from hydra import initialize, initialize_config_dir, compose
from hydra.utils import instantiate
from omegaconf import OmegaConf
from contextlib import asynccontextmanager

# SAM-6D 모듈 import
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sam6d_path = os.path.join(current_dir, '..', 'SAM-6D', 'SAM-6D', 'Instance_Segmentation_Model')
sam6d_path = os.path.abspath(sam6d_path)
sys.path.append(sam6d_path)
from run_inference_custom_function import load_templates_from_files, run_inference_core, batch_input_data_from_params

# 전역 변수
model = None
templates_data = None
templates_masks = None
templates_boxes = None
cad_points = None
device = None

# 로깅 설정
def setup_logging():
    """로깅 설정"""
    log_dir = os.path.join(current_dir, "log")
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일명 (날짜별)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"ism_server_{timestamp}.log")
    
    # 기존 핸들러 제거
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # 콘솔에도 출력
        ],
        force=True  # 기존 설정 강제 덮어쓰기
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Log directory: {log_dir}")
    return logger

# 로거 초기화
logger = setup_logging()

# 로그 파일 직접 쓰기 함수 (백업용)
def write_to_log_file(message):
    """로그 파일에 직접 메시지 쓰기"""
    try:
        log_dir = os.path.join(current_dir, "log")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"ism_server_{timestamp}.log")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
            f.flush()  # 즉시 파일에 쓰기
    except Exception as e:
        print(f"Failed to write to log file: {e}")

# Pydantic 모델 정의
class ServerStatus(BaseModel):
    server: str
    model_loaded: bool
    templates_loaded: bool
    cad_loaded: bool
    device: Optional[str] = None
    num_templates: int = 0
    uptime: float

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: float

# 추론 API용 스키마
class InferenceRequest(BaseModel):
    rgb_image: str          # Base64 인코딩된 RGB 이미지
    depth_image: str        # Base64 인코딩된 깊이 이미지
    cam_params: dict        # 카메라 파라미터 (cam_K, depth_scale)
    template_dir: str       # 템플릿 디렉토리 경로 (필수)
    cad_path: str           # CAD 모델 경로 (필수)
    output_dir: Optional[str] = None  # 결과 저장 경로 (선택사항, None이면 파일 저장 안함)

class InferenceResponse(BaseModel):
    success: bool
    detections: dict  # dict 타입으로 변경
    inference_time: float
    template_dir_used: str
    cad_path_used: str
    output_dir_used: Optional[str] = None  # 사용된 출력 경로
    error_message: Optional[str] = None

# 모델 로딩 함수들
async def load_model():
    """모델 로딩 함수"""
    global model, device
    
    try:
        logger.info("Starting model loading...")
        
        # ISM_Server 디렉토리에서 직접 실행 (상대 경로 사용)
        ism_server_dir = os.path.join(current_dir)
        original_cwd = os.getcwd()
        os.chdir(ism_server_dir)
        
        try:
            logger.debug(f"Current working directory: {os.getcwd()}")
            logger.debug(f"Configs directory exists: {os.path.exists('configs')}")
            
            # Python 경로에 SAM-6D 모듈 추가
            sam6d_dir = os.path.join(current_dir, '..', 'SAM-6D', 'SAM-6D', 'Instance_Segmentation_Model')
            sam6d_dir = os.path.abspath(sam6d_dir)
            if sam6d_dir not in sys.path:
                sys.path.insert(0, sam6d_dir)
            
            # 모델을 직접 import해서 테스트
            try:
                from model.detector import Instance_Segmentation_Model
                logger.debug("Instance_Segmentation_Model class imported successfully")
            except ImportError as e:
                logger.error(f"Instance_Segmentation_Model import failed: {e}")
                return False
            
            # Hydra를 사용한 설정 로드 (ISM_Server 디렉토리에서)
            with initialize_config_dir(version_base=None, config_dir=os.path.join(ism_server_dir, "configs")):
                cfg = compose(config_name='run_inference.yaml')
            
            # SAM 모델 설정
            with initialize_config_dir(version_base=None, config_dir=os.path.join(ism_server_dir, "configs", "model")):
                cfg.model = compose(config_name='ISM_sam.yaml')
                
        finally:
            # 원래 작업 디렉토리로 복원
            os.chdir(original_cwd)
        
        # 모델 인스턴스화
        model = instantiate(cfg.model)
        
        # GPU 설정
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.descriptor_model.model = model.descriptor_model.model.to(device)
        model.descriptor_model.model.device = device
        
        if hasattr(model.segmentor_model, "predictor"):
            model.segmentor_model.predictor.model = model.segmentor_model.predictor.model.to(device)
        else:
            model.segmentor_model.model.setup_model(device=device, verbose=True)
        
        logger.info(f"Model loaded successfully on {device}")
        return True
        
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        return False

async def load_templates():
    """템플릿 로딩 함수"""
    global templates_data, templates_masks, templates_boxes
    
    try:
        logger.info("Starting template loading...")
        
        template_dir = os.getenv('ISM_TEMPLATE_DIR', os.path.join(current_dir, '..', 'SAM-6D', 'SAM-6D', 'Data', 'Example', 'outputs', 'templates'))
        template_dir = os.path.abspath(template_dir)
        
        if not os.path.exists(template_dir):
            logger.error(f"Template directory not found: {template_dir}")
            return False
        
        # 템플릿 로딩 시에도 ISM_Server 디렉토리에서 실행
        ism_server_dir = os.path.join(current_dir)
        original_cwd = os.getcwd()
        os.chdir(ism_server_dir)
        
        try:
            templates_data, templates_masks, templates_boxes = load_templates_from_files(template_dir, device)
        finally:
            os.chdir(original_cwd)
            
        logger.info(f"Templates loaded successfully: {len(templates_data)} templates")
        return True
        
    except Exception as e:
        logger.error(f"Template loading failed: {e}")
        return False

async def load_cad_model():
    """CAD 모델 로딩 함수"""
    global cad_points
    
    try:
        logger.info("Starting CAD model loading...")
        
        cad_path = os.getenv('ISM_CAD_MODEL_PATH', os.path.join(current_dir, '..', 'SAM-6D', 'SAM-6D', 'Data', 'Example', 'obj_000005.ply'))
        cad_path = os.path.abspath(cad_path)
        
        if not os.path.exists(cad_path):
            logger.error(f"CAD model not found: {cad_path}")
            return False
        
        mesh = trimesh.load_mesh(cad_path)
        cad_points = mesh.sample(2048).astype(np.float32) / 1000.0
        logger.info(f"CAD model loaded successfully: {cad_points.shape}")
        return True
        
    except Exception as e:
        logger.error(f"CAD model loading failed: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 실행되는 lifespan 관리자"""
    logger.info("Starting ISM Server...")
    write_to_log_file("Starting ISM Server...")
    
    # 모델만 로딩 (템플릿과 CAD는 클라이언트가 제공)
    model_loaded = await load_model()
    if not model_loaded:
        logger.error("Model loading failed")
        yield
        return
    
    logger.info("Model loaded successfully! Ready to accept inference requests.")
    write_to_log_file("Model loaded successfully! Ready to accept inference requests.")
    
    # 서버 실행 중
    yield
    
    # 서버 종료 시 정리 작업
    logger.info("Shutting down server...")

# FastAPI 앱 생성
app = FastAPI(title="ISM Server", version="1.0.0", lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"message": "ISM Server is running!", "version": "1.0.0"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="Server is running",
        timestamp=time.time()
    )

@app.get("/api/v1/status", response_model=ServerStatus)
async def get_status():
    return ServerStatus(
        server="running",
        model_loaded=model is not None,
        templates_loaded=False,  # 템플릿은 클라이언트가 제공
        cad_loaded=False,        # CAD는 클라이언트가 제공
        device=str(device) if device else None,
        num_templates=0,         # 템플릿은 클라이언트가 제공
        uptime=time.time()
    )

# 이미지 처리 함수들
def base64_to_image(base64_string):
    """Base64 문자열을 PIL Image로 변환"""
    try:
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        return image
    except Exception as e:
        raise ValueError(f"Invalid base64 image: {e}")

def image_to_numpy(image):
    """PIL Image를 numpy array로 변환"""
    return np.array(image.convert("RGB"))

def depth_image_to_numpy(image):
    """깊이 이미지를 numpy array로 변환"""
    return np.array(image.convert("L"))

# 추론 API
@app.post("/api/v1/inference", response_model=InferenceResponse)
async def inference(request: InferenceRequest):
    """추론 API"""
    logger.info("Inference request received")
    start_time = time.time()
    
    try:
        if not model:
            return InferenceResponse(
                success=False,
                detections={},
                inference_time=0,
                template_dir_used="",
                cad_path_used="",
                output_dir_used=None,
                error_message="Model not loaded"
            )
        
        # 이미지 변환
        rgb_image = base64_to_image(request.rgb_image)
        depth_image = base64_to_image(request.depth_image)
        
        rgb_array = image_to_numpy(rgb_image)
        depth_array = depth_image_to_numpy(depth_image)
        
        # 카메라 파라미터 처리
        cam_params = request.cam_params
        
        # 깊이 데이터를 배치 형태로 변환
        depth_batch = batch_input_data_from_params(depth_array, cam_params, device)
        
        # 클라이언트가 제공한 경로 사용
        template_dir = request.template_dir
        cad_path = request.cad_path
        output_dir = request.output_dir
        
        # 경로 유효성 검사
        if not os.path.exists(template_dir):
            return InferenceResponse(
                success=False,
                detections={},
                inference_time=0,
                template_dir_used=template_dir,
                cad_path_used=cad_path,
                output_dir_used=output_dir,
                error_message=f"Template directory not found: {template_dir}"
            )
        
        if not os.path.exists(cad_path):
            return InferenceResponse(
                success=False,
                detections={},
                inference_time=0,
                template_dir_used=template_dir,
                cad_path_used=cad_path,
                output_dir_used=output_dir,
                error_message=f"CAD model not found: {cad_path}"
            )
        
        # 클라이언트가 제공한 템플릿과 CAD 모델 로딩
        logger.info(f"Loading templates from: {template_dir}")
        logger.info(f"Loading CAD model from: {cad_path}")
        
        try:
            # 템플릿 로딩
            client_templates_data, client_templates_masks, client_templates_boxes = load_templates_from_files(template_dir, device)
            
            # CAD 모델 로딩
            mesh = trimesh.load_mesh(cad_path)
            client_cad_points = mesh.sample(2048).astype(np.float32) / 1000.0
            
            logger.info(f"Loaded {len(client_templates_data)} templates and CAD model with {client_cad_points.shape[0]} points")
            
        except Exception as load_error:
            logger.error(f"Failed to load client data: {load_error}")
            return InferenceResponse(
                success=False,
                detections={},
                inference_time=0,
                template_dir_used=template_dir,
                cad_path_used=cad_path,
                output_dir_used=output_dir,
                error_message=f"Failed to load client data: {load_error}"
            )
        
        # 실제 SAM-6D 추론 실행
        logger.info("Starting SAM-6D inference...")
        try:
            result = run_inference_core(
                model=model,
                rgb_array=rgb_array,
                depth_batch=depth_batch,
                cad_points=client_cad_points,
                templates_data=client_templates_data,
                templates_masks=client_templates_masks,
                templates_boxes=client_templates_boxes,
                device=device,
                output_dir=output_dir,  # 클라이언트가 제공한 출력 경로 사용
                save_async=False
            )
            
            # 결과 처리
            detections = result.get("detections", [])
            if hasattr(detections, 'to_dict'):
                detections = detections.to_dict()
            elif hasattr(detections, 'masks'):
                # Detections 객체를 딕셔너리로 변환
                detections = {
                    "masks": detections.masks.tolist() if hasattr(detections.masks, 'tolist') else detections.masks,
                    "boxes": detections.boxes.tolist() if hasattr(detections.boxes, 'tolist') else detections.boxes,
                    "scores": detections.scores.tolist() if hasattr(detections.scores, 'tolist') else detections.scores,
                    "object_ids": detections.object_ids.tolist() if hasattr(detections.object_ids, 'tolist') else detections.object_ids
                }
            
            logger.info(f"SAM-6D inference completed successfully")
            logger.info(f"Detected {len(detections.get('masks', []))} objects")
            
        except Exception as inference_error:
            logger.error(f"SAM-6D inference failed: {inference_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # 에러 발생 시 빈 결과 반환
            detections = {
                "masks": [],
                "boxes": [],
                "scores": [],
                "object_ids": [],
                "error": str(inference_error)
            }
        
        inference_time = time.time() - start_time
        logger.info(f"Inference completed in {inference_time:.3f}s")
        
        return InferenceResponse(
            success=True,
            detections=detections,
            inference_time=inference_time,
            template_dir_used=template_dir,
            cad_path_used=cad_path,
            output_dir_used=output_dir,
            error_message=None
        )
        
    except Exception as e:
        inference_time = time.time() - start_time
        logger.error(f"Inference failed: {e}")
        
        return InferenceResponse(
            success=False,
            detections={},
            inference_time=inference_time,
            template_dir_used="",
            cad_path_used="",
            output_dir_used=None,
            error_message=str(e)
        )

# 테스트용 샘플 데이터 엔드포인트
@app.get("/test/sample")
async def get_sample_data():
    """테스트용 샘플 데이터 반환"""
    # 기존 예제 데이터 사용
    rgb_path = os.path.join(current_dir, "..", "SAM-6D", "SAM-6D", "Data", "Example", "rgb.png")
    depth_path = os.path.join(current_dir, "..", "SAM-6D", "SAM-6D", "Data", "Example", "depth.png")
    cam_path = os.path.join(current_dir, "..", "SAM-6D", "SAM-6D", "Data", "Example", "camera.json")
    
    try:
        # 이미지를 Base64로 변환
        with open(rgb_path, "rb") as f:
            rgb_base64 = base64.b64encode(f.read()).decode()
        
        with open(depth_path, "rb") as f:
            depth_base64 = base64.b64encode(f.read()).decode()
        
        # 카메라 파라미터 로딩
        with open(cam_path, "r") as f:
            cam_params = json.load(f)
        
        return {
            "rgb_image": rgb_base64,
            "depth_image": depth_base64,
            "cam_params": cam_params
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)