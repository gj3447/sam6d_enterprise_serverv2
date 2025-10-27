# PEM_Server/test_model_loading.py - Phase 2: PEM 모델 로딩 테스트
import os
import sys
import torch
import time

def test_pem_model_loading():
    """PEM 모델 로딩 테스트"""
    print("=== PEM 모델 로딩 테스트 ===")
    
    # PEM 모듈 경로 추가 (PEM_Server의 PointNet2 사용)
    pem_paths = [
        '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model',
        '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/utils',
        '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/model',
        '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/provider',
        '/workspace/Estimation_Server/PEM_Server/model/pointnet2'  # PEM_Server의 PointNet2 사용
    ]
    
    for path in pem_paths:
        if path not in sys.path:
            sys.path.append(path)
    
    try:
        import gorilla
        print("✅ gorilla imported successfully")
    except ImportError as e:
        print(f"❌ gorilla import failed: {e}")
        return False
    
    # 환경 변수에서 경로 가져오기
    config_path = os.getenv('PEM_CONFIG_PATH', '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/config/base.yaml')
    checkpoint_path = os.getenv('PEM_CHECKPOINT_PATH', '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/checkpoints/sam-6d-pem-base.pth')
    
    print(f"Config path: {config_path}")
    print(f"Checkpoint path: {checkpoint_path}")
    
    # 파일 존재 여부 확인
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return False
    
    if not os.path.exists(checkpoint_path):
        print(f"❌ Checkpoint file not found: {checkpoint_path}")
        return False
    
    print("✅ Config and checkpoint files found")
    
    # GPU 설정
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"✅ Using device: {device}")
    
    # 모델 로딩 시도 (원본 SAM-6D 방식)
    try:
        print("Loading PEM model...")
        start_time = time.time()
        
        # 원본 SAM-6D 방식으로 모델 로딩
        import importlib
        from run_inference_custom_function import init_model_and_config
        
        model, cfg = init_model_and_config(
            gpus="0",
            model_name="pose_estimation_model", 
            config_path=config_path,
            iter_num=0
        )
        
        end_time = time.time()
        loading_time = end_time - start_time
        
        print(f"✅ PEM model loaded successfully on cuda")
        print(f"✅ Loading time: {loading_time:.2f} seconds")
        
        # 모델 정보 출력
        if hasattr(model, 'parameters'):
            total_params = sum(p.numel() for p in model.parameters())
            print(f"✅ Total parameters: {total_params:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ PEM model loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pointnet2_cuda():
    """PointNet2 CUDA 확장 모듈 테스트"""
    print("\n=== PointNet2 CUDA 확장 모듈 테스트 ===")
    
    # PEM_Server의 PointNet2 경로 추가
    pointnet2_path = '/workspace/Estimation_Server/PEM_Server/model/pointnet2'
    if pointnet2_path not in sys.path:
        sys.path.append(pointnet2_path)
    
    try:
        from pointnet2_modules import PointnetSAModuleMSG
        print("✅ PointNet2 CUDA modules imported successfully")
        
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

if __name__ == "__main__":
    print("PEM Server 모델 로딩 테스트 시작...\n")
    
    success = True
    success &= test_pointnet2_cuda()
    success &= test_pem_model_loading()
    
    print(f"\n=== 테스트 결과 ===")
    if success:
        print("✅ PEM 모델 로딩 테스트 통과!")
        print("Phase 2 준비 완료 - 다음 단계로 진행 가능")
    else:
        print("❌ PEM 모델 로딩 실패")
        print("Phase 2 실패 - 문제 해결 후 재시도 필요")
