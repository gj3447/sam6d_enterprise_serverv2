# PEM_Server/test_imports.py - Phase 0: 라이브러리 Import 테스트
import sys
import os

def test_basic_imports():
    """기본 라이브러리 import 테스트"""
    print("=== 기본 라이브러리 Import 테스트 ===")
    
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ PIL imported successfully")
    except ImportError as e:
        print(f"❌ PIL import failed: {e}")
        return False
    
    try:
        import trimesh
        print("✅ Trimesh imported successfully")
    except ImportError as e:
        print(f"❌ Trimesh import failed: {e}")
        return False
    
    try:
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import pycocotools.mask as cocomask
        print("✅ pycocotools imported successfully")
    except ImportError as e:
        print(f"❌ pycocotools import failed: {e}")
        return False
    
    return True

def test_pem_imports():
    """PEM 관련 라이브러리 import 테스트"""
    print("\n=== PEM 관련 라이브러리 Import 테스트 ===")
    
    # PEM 모듈 경로 추가 (PEM_Server의 PointNet2 사용)
    pem_paths = [
        '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model',
        '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/utils',
        '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/model',
        '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/provider',
        '/workspace/Estimation_Server/PEM_Server/model/pointnet2'  # PEM_Server의 PointNet2 사용
    ]
    
    import sys
    for path in pem_paths:
        if path not in sys.path:
            sys.path.append(path)
    
    try:
        from utils.data_utils import load_im, get_bbox, get_point_cloud_from_depth
        print("✅ PEM data utils imported successfully")
    except ImportError as e:
        print(f"❌ PEM data utils import failed: {e}")
        return False
    
    try:
        from utils.draw_utils import draw_detections
        print("✅ PEM draw utils imported successfully")
    except ImportError as e:
        print(f"❌ PEM draw utils import failed: {e}")
        return False
    
    try:
        # 원본 SAM-6D에는 load_model 함수가 없음 - gorilla.solver.load_checkpoint 사용
        import gorilla
        print("✅ gorilla imported successfully")
    except ImportError as e:
        print(f"❌ gorilla import failed: {e}")
        return False
    
    try:
        from run_inference_custom_function import run_pose_estimation_core
        print("✅ PEM run_inference_custom_function imported successfully")
    except ImportError as e:
        print(f"❌ PEM run_inference_custom_function import failed: {e}")
        return False
    
    return True

def test_pointnet2_cuda():
    """PointNet2 CUDA 확장 모듈 테스트"""
    print("\n=== PointNet2 CUDA 확장 모듈 테스트 ===")
    
    # PEM_Server의 PointNet2 경로 추가
    pointnet2_path = '/workspace/Estimation_Server/PEM_Server/model/pointnet2'
    if pointnet2_path not in sys.path:
        sys.path.append(pointnet2_path)
    
    try:
        import torch
        # PointNet2 CUDA 확장 모듈 테스트
        import pointnet2._ext
        print("✅ PointNet2 CUDA extension module imported successfully")
        
        # PointNet2 모듈 테스트
        from pointnet2_modules import PointnetSAModuleMSG
        print("✅ PointNet2 modules imported successfully")
        
        # 간단한 테스트
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"✅ Using device: {device}")
        
        # PointNet2 모듈 초기화 테스트
        sa_module = PointnetSAModuleMSG(
            npoint=512,
            radii=[0.1, 0.2, 0.4],
            nsamples=[16, 32, 128],
            mlps=[[32, 32, 64], [64, 64, 128], [64, 96, 128]],
            use_xyz=True
        ).to(device)
        print("✅ PointNet2 module initialized successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ PointNet2 CUDA modules import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ PointNet2 module initialization failed: {e}")
        return False

def test_fastapi_imports():
    """FastAPI 관련 라이브러리 import 테스트"""
    print("\n=== FastAPI 관련 라이브러리 Import 테스트 ===")
    
    try:
        import fastapi
        print(f"✅ FastAPI version: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported successfully")
    except ImportError as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import pydantic
        print(f"✅ Pydantic version: {pydantic.__version__}")
    except ImportError as e:
        print(f"❌ Pydantic import failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("PEM Server 라이브러리 Import 테스트 시작...\n")
    
    success = True
    success &= test_basic_imports()
    success &= test_pem_imports()
    success &= test_pointnet2_cuda()
    success &= test_fastapi_imports()
    
    print(f"\n=== 테스트 결과 ===")
    if success:
        print("✅ 모든 라이브러리 import 테스트 통과!")
        print("Phase 0 완료 - 다음 단계로 진행 가능")
    else:
        print("❌ 일부 라이브러리 import 실패")
        print("Phase 0 실패 - 문제 해결 후 재시도 필요")
