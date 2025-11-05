# PEM_Server/core/model_manager.py
"""
PEM 모델 관리자
"""
import os
import sys
import time
import torch
import logging
from typing import Optional, Dict, Any, Tuple
from threading import Lock

import trimesh

from .config import get_settings
from .cache import LRUCache

logger = logging.getLogger(__name__)

class ModelManager:
    """PEM 모델 관리자"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.cfg = None
        self.device = None
        self.loaded = False
        self.loading_time = None
        self.parameters = None
        self.cache_lock = Lock()
        self.template_cache = LRUCache(self.settings.template_cache_capacity)
        self.cad_cache = LRUCache(self.settings.cad_cache_capacity)
        
        # 경로 설정
        self._setup_paths()
    
    def _setup_paths(self):
        """필요한 경로들을 sys.path에 추가"""
        paths = [
            self.settings.sam6d_root,
            os.path.join(self.settings.sam6d_root, 'utils'),
            os.path.join(self.settings.sam6d_root, 'model'),
            os.path.join(self.settings.sam6d_root, 'provider'),
            os.path.join(self.settings.pem_server_root, 'model', 'pointnet2')
        ]
        
        for path in paths:
            if path not in sys.path:
                sys.path.append(path)
        
        logger.info(f"Added paths to sys.path: {paths}")
    
    def load_model(
        self, 
        config_path: Optional[str] = None,
        checkpoint_path: Optional[str] = None,
        device: Optional[str] = None
    ) -> bool:
        """
        모델 로딩
        
        Args:
            config_path: 설정 파일 경로
            checkpoint_path: 체크포인트 파일 경로
            device: 사용할 디바이스
            
        Returns:
            bool: 로딩 성공 여부
        """
        try:
            start_time = time.time()
            
            # 설정 파일 경로 결정
            config_path = config_path or self.settings.config_path
            checkpoint_path = checkpoint_path or self.settings.checkpoint_path
            device = device or self.settings.device
            
            logger.info(f"Loading model with config: {config_path}")
            logger.info(f"Checkpoint: {checkpoint_path}")
            logger.info(f"Device: {device}")
            
            # 파일 존재 여부 확인
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            if not os.path.exists(checkpoint_path):
                raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")
            
            # 실제 모델 로딩 로직 구현
            import gorilla
            from run_inference_custom_function import init_model_and_config

            # GPU 설정 확인
            if device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available, falling back to CPU")
                device = "cpu"

            # CUDA 디바이스 설정 (gorilla가 CUDA를 인식할 수 있도록)
            if device == "cuda":
                gorilla.utils.set_cuda_visible_devices("0")
                logger.info("Set CUDA visible devices to 0")

            # 모델 초기화 및 로딩
            self.model, self.cfg = init_model_and_config(
                gpus="0" if device == "cuda" else "0",  # gorilla는 GPU ID를 문자열로 받음
                model_name=self.settings.model_name,
                config_path=config_path,
                iter_num=0
            )
            
            # 모델 상태 설정
            self.device = device
            self.loaded = True
            self.loading_time = time.time() - start_time
            
            # 모델 파라미터 수 계산
            if self.model is not None:
                self.parameters = sum(p.numel() for p in self.model.parameters())
            else:
                self.parameters = 107939560  # 기본값
            
            logger.info(f"Model loaded successfully in {self.loading_time:.2f} seconds")
            logger.info(f"Device: {self.device}")
            logger.info(f"Parameters: {self.parameters:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.loaded = False
            return False
    
    def unload_model(self) -> bool:
        """모델 언로드"""
        try:
            # 실제 모델 언로드 로직 구현
            if self.model is not None:
                del self.model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            self.model = None
            self.cfg = None
            self.loaded = False
            self.loading_time = None
            self.parameters = None
            
            logger.info("Model unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Model unloading failed: {e}")
            return False
    
    def get_model_status(self) -> Dict[str, Any]:
        """모델 상태 반환"""
        return {
            "loaded": self.loaded,
            "device": self.device,
            "parameters": self.parameters,
            "loading_time": self.loading_time,
            "model_name": self.settings.model_name,
            "config_path": self.settings.config_path,
            "checkpoint_path": self.settings.checkpoint_path
        }
    
    def predict(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        포즈 추정 실행
        
        Args:
            request_data: 요청 데이터
            
        Returns:
            Dict: 추정 결과
        """
        if not self.loaded:
            raise RuntimeError("Model is not loaded")
        
        try:
            # TODO: 실제 추론 로직 구현
            # from run_inference_custom_function import run_pose_estimation_core
            # 
            # result = run_pose_estimation_core(
            #     model=self.model,
            #     input_data=input_data,
            #     all_tem_pts=all_tem_pts,
            #     all_tem_feat=all_tem_feat,
            #     device=self.device,
            #     detections=detections,
            #     output_dir=output_dir
            # )
            
            # 임시 응답
            return {
                "success": True,
                "message": "Pose estimation completed (placeholder)",
                "detections": [],
                "processing_time": 0.0
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

    # ------------------------------------------------------------------
    # 캐시 유틸리티
    # ------------------------------------------------------------------
    def get_template_bundle(self, template_dir: str) -> Tuple[Any, Any, Any, Any]:
        """템플릿 관련 데이터를 캐시에서 가져오거나 새로 로드"""
        if not self.loaded:
            raise RuntimeError("Model must be loaded before accessing templates")

        template_dir = os.path.abspath(template_dir)

        with self.cache_lock:
            cached = self.template_cache.get(template_dir)
        if cached is not None:
            return cached

        from run_inference_custom_function import load_templates_from_files

        all_tem, all_tem_pts, all_tem_choose = load_templates_from_files(
            template_dir, self.cfg.test_dataset, self.device
        )

        with torch.no_grad():
            all_tem_pts, all_tem_feat = self.model.feature_extraction.get_obj_feats(
                all_tem, all_tem_pts, all_tem_choose
            )

        bundle = (all_tem, all_tem_pts, all_tem_choose, all_tem_feat)
        with self.cache_lock:
            self.template_cache.put(template_dir, bundle)

        return bundle

    def get_cad_points(self, cad_path: str) -> Any:
        """CAD 모델 포인트를 캐시에서 가져오거나 새로 로드"""
        cad_path = os.path.abspath(cad_path)

        with self.cache_lock:
            cached = self.cad_cache.get(cad_path)
        if cached is not None:
            return cached

        mesh = trimesh.load_mesh(cad_path)
        cad_points = mesh.sample(2048).astype("float32") / 1000.0

        with self.cache_lock:
            self.cad_cache.put(cad_path, cad_points)

        return cad_points

    def preload_assets(self):
        """템플릿과 CAD 자산을 미리 로드"""
        templates_root = os.path.join(self.settings.workspace_root, "static", "templates")
        meshes_root = os.path.join(self.settings.workspace_root, "static", "meshes")

        if not os.path.exists(templates_root):
            logger.warning(f"Templates root not found, skipping preload: {templates_root}")
            return

        logger.info(
            "Preloading PEM assets (templates & CAD). Capacity: %s templates, %s CAD",
            self.template_cache.capacity,
            self.cad_cache.capacity,
        )

        for class_name in sorted(os.listdir(templates_root)):
            if class_name.lower() != "ycb":
                continue
            class_template_dir = os.path.join(templates_root, class_name)
            class_mesh_dir = os.path.join(meshes_root, class_name)

            if not os.path.isdir(class_template_dir) or not os.path.isdir(class_mesh_dir):
                continue

            for object_name in sorted(os.listdir(class_template_dir)):
                template_dir = os.path.join(class_template_dir, object_name)
                if not os.path.isdir(template_dir):
                    continue

                cad_path = None
                for ext in (".ply", ".obj", ".stl"):
                    candidate = os.path.join(class_mesh_dir, f"{object_name}{ext}")
                    if os.path.exists(candidate):
                        cad_path = candidate
                        break

                if cad_path is None:
                    continue

                try:
                    self.get_template_bundle(template_dir)
                    self.get_cad_points(cad_path)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("Failed to preload %s/%s: %s", class_name, object_name, exc)

                with self.cache_lock:
                    template_full = len(self.template_cache) >= self.template_cache.capacity
                    cad_full = len(self.cad_cache) >= self.cad_cache.capacity
                if template_full and cad_full:
                    logger.info("Reached cache capacity during preload")
                    logger.info(
                        "Preload finished: template_cache=%s/%s, cad_cache=%s/%s",
                        len(self.template_cache),
                        self.template_cache.capacity,
                        len(self.cad_cache),
                        self.cad_cache.capacity,
                    )
                    return

        logger.info(
            "Preload finished: template_cache=%s/%s, cad_cache=%s/%s",
            len(self.template_cache),
            self.template_cache.capacity,
            len(self.cad_cache),
            self.cad_cache.capacity,
        )

# 전역 모델 매니저 인스턴스
model_manager = ModelManager()

def get_model_manager() -> ModelManager:
    """모델 매니저 인스턴스 반환"""
    return model_manager
