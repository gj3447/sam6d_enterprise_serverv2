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

# --- Start of Caching Implementation ---
from threading import Lock
from lru_cache import LRUCache

# 스레드 안전성을 위한 Lock 객체
CACHE_LOCK = Lock()

# 최대 캐시 크기 설정 (환경 변수에서 읽어오기, 기본값 20)
MAX_CACHE_SIZE = int(os.getenv("ISM_MAX_CACHE_SIZE", 20))

# 템플릿과 CAD 모델을 위한 LRU 캐시
TEMPLATE_CACHE = LRUCache(capacity=MAX_CACHE_SIZE)
CAD_CACHE = LRUCache(capacity=MAX_CACHE_SIZE)
# --- End of Caching Implementation ---

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
    
    # 모델 로딩
    model_loaded = await load_model()
    if not model_loaded:
        logger.error("Model loading failed")
        yield
        return

    # --- Start of Pre-loading Logic ---
    # 환경 변수에서 PRELOAD_ALL_TEMPLATES 값을 읽어옴
    # 이 값을 true로 설정하면 서버 시작 시 모든 템플릿을 미리 로드합니다.
    should_preload = os.getenv("ISM_PRELOAD_TEMPLATES", "false").lower() == "true"
    
    if should_preload:
        logger.info(f"PRELOAD_ALL_TEMPLATES is true. Starting pre-loading of all templates and CAD models up to a capacity of {MAX_CACHE_SIZE}...")
        
        # ../static/templates 와 ../static/meshes 경로 설정
        project_root = os.path.abspath(os.path.join(current_dir, '..'))
        templates_base_dir = os.path.join(project_root, 'static', 'templates')
        meshes_base_dir = os.path.join(project_root, 'static', 'meshes')
        
        if not os.path.exists(templates_base_dir):
            logger.warning(f"Templates base directory not found, skipping preload: {templates_base_dir}")
        else:
            # 클래스 디렉토리 순회 (e.g., ycb)
            for class_name in os.listdir(templates_base_dir):
                if class_name.lower() != "ycb":
                    continue
                if len(TEMPLATE_CACHE) >= MAX_CACHE_SIZE:
                    break
                class_template_dir = os.path.join(templates_base_dir, class_name)
                class_mesh_dir = os.path.join(meshes_base_dir, class_name)
                
                if not os.path.isdir(class_template_dir) or not os.path.exists(class_mesh_dir):
                    continue

                # 객체 디렉토리 순회
                for object_name in os.listdir(class_template_dir):
                    if len(TEMPLATE_CACHE) >= MAX_CACHE_SIZE:
                        logger.info(f"Cache is full (capacity: {MAX_CACHE_SIZE}). Stopping pre-loading.")
                        break

                    template_dir = os.path.join(class_template_dir, object_name)
                    if not os.path.isdir(template_dir):
                        continue

                    logger.info(f"Pre-loading data for object: {class_name}/{object_name}")
                    
                    # Find corresponding CAD model
                    cad_path = None
                    for ext in ['.ply', '.obj', '.stl']:
                        potential_cad_path = os.path.join(class_mesh_dir, f"{object_name}{ext}")
                        if os.path.exists(potential_cad_path):
                            cad_path = potential_cad_path
                            break
                    
                    if not cad_path:
                        logger.warning(f"Could not find CAD model for {object_name}, skipping.")
                        continue

                    # Load and cache data
                    try:
                        with CACHE_LOCK:
                            if template_dir not in TEMPLATE_CACHE:
                                t_data, t_masks, t_boxes = load_templates_from_files(template_dir, device)
                                TEMPLATE_CACHE.put(template_dir, (t_data, t_masks, t_boxes))
                                logger.info(f"Successfully cached templates for {template_dir}")

                            if cad_path not in CAD_CACHE:
                                mesh = trimesh.load_mesh(cad_path)
                                c_points = mesh.sample(2048).astype(np.float32) / 1000.0
                                CAD_CACHE.put(cad_path, c_points)
                                logger.info(f"Successfully cached CAD model for {cad_path}")
                    except Exception as e:
                        logger.error(f"Failed to preload data for {object_name}: {e}")
                if len(TEMPLATE_CACHE) >= MAX_CACHE_SIZE:
                    break
        
        logger.info(f"Finished pre-loading data. Cache size: {len(TEMPLATE_CACHE)}/{MAX_CACHE_SIZE}")
    else:
        logger.info("PRELOAD_ALL_TEMPLATES is false. Templates will be cached on-demand.")
    # --- End of Pre-loading Logic ---

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
        import io
        image_data = base64.b64decode(base64_string)
        logger.info(f"Decoded image data (first 10 bytes): {image_data[:10]}")
        image = Image.open(io.BytesIO(image_data))
        # BytesIO 객체를 닫아서 메모리 해제
        # (Image.open은 BytesIO를 자동으로 close하지 않으므로)
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
            with CACHE_LOCK:
                # --- Template Caching ---
                cached_templates = TEMPLATE_CACHE.get(template_dir)
                if cached_templates:
                    logger.info("Found templates in cache.")
                    client_templates_data, client_templates_masks, client_templates_boxes = cached_templates
                else:
                    logger.info("Templates not in cache, loading from files...")
                    client_templates_data, client_templates_masks, client_templates_boxes = load_templates_from_files(template_dir, device)
                    TEMPLATE_CACHE.put(template_dir, (client_templates_data, client_templates_masks, client_templates_boxes))
                    logger.info(f"Cached templates for: {template_dir}")

                # --- CAD Model Caching ---
                cached_cad = CAD_CACHE.get(cad_path)
                if cached_cad is not None:
                    logger.info("Found CAD model in cache.")
                    client_cad_points = cached_cad
                else:
                    logger.info("CAD model not in cache, loading from file...")
                    mesh = trimesh.load_mesh(cad_path)
                    client_cad_points = mesh.sample(2048).astype(np.float32) / 1000.0
                    CAD_CACHE.put(cad_path, client_cad_points)
                    logger.info(f"Cached CAD model for: {cad_path}")

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
            conversion_start = time.time()
            
            if hasattr(detections, 'to_dict'):
                detections = detections.to_dict()
            elif hasattr(detections, 'masks'):
                # Detections 객체를 딕셔너리로 변환
                # 마스크는 COCO RLE 형식으로 변환하거나, 파일 경로만 전달하는 것이 효율적
                num_objects = len(detections.masks) if hasattr(detections.masks, '__len__') else 0
                logger.info(f"Converting {num_objects} detections to response format...")
                
                # 마스크는 이미지 파일로 저장되어 있으므로, 큰 배열 변환을 피함
                # COCO RLE 형식이나 파일 경로만 전달하는 것이 좋지만,
                # 호환성을 위해 최소한의 변환만 수행
                try:
                    # 마스크가 COCO RLE 형식인지 확인
                    if isinstance(detections.masks, list) and len(detections.masks) > 0:
                        # 이미 리스트 형식이거나 COCO RLE 형식인 경우
                        masks_data = detections.masks
                    elif hasattr(detections.masks, 'tolist'):
                        # 큰 배열인 경우 - 상위 10개만 전송하거나 RLE 변환 고려
                        if num_objects > 10:
                            logger.warning(f"Too many detections ({num_objects}). Converting top 10 only.")
                            masks_data = detections.masks[:10].tolist() if hasattr(detections.masks, '__getitem__') else detections.masks.tolist()[:10]
                        else:
                            masks_data = detections.masks.tolist()
                    else:
                        masks_data = detections.masks
                except Exception as mask_err:
                    logger.warning(f"Mask conversion error: {mask_err}. Using original format.")
                    masks_data = detections.masks
                
                # 상위 10개만 전송 (점수 순으로 정렬된 경우)
                max_objects = min(10, num_objects)
                detections = {
                    "masks": masks_data[:max_objects] if isinstance(masks_data, list) and len(masks_data) > max_objects else masks_data,
                    "boxes": (detections.boxes[:max_objects].tolist() if hasattr(detections.boxes, '__getitem__') else detections.boxes.tolist()[:max_objects]) if hasattr(detections.boxes, 'tolist') else (detections.boxes[:max_objects] if hasattr(detections.boxes, '__getitem__') else detections.boxes),
                    "scores": (detections.scores[:max_objects].tolist() if hasattr(detections.scores, '__getitem__') else detections.scores.tolist()[:max_objects]) if hasattr(detections.scores, 'tolist') else (detections.scores[:max_objects] if hasattr(detections.scores, '__getitem__') else detections.scores),
                    "object_ids": (detections.object_ids[:max_objects].tolist() if hasattr(detections.object_ids, '__getitem__') else detections.object_ids.tolist()[:max_objects]) if hasattr(detections.object_ids, 'tolist') else (detections.object_ids[:max_objects] if hasattr(detections.object_ids, '__getitem__') else detections.object_ids)
                }
                logger.info(f"Sending top {max_objects} detections (out of {num_objects} total)")
            
            conversion_time = time.time() - conversion_start
            logger.info(f"SAM-6D inference completed successfully")
            logger.info(f"Detected {len(detections.get('masks', []))} objects")
            if conversion_time > 1.0:
                logger.warning(f"Data conversion took {conversion_time:.2f}s (consider optimizing mask format)")
            
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