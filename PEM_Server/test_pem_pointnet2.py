#!/usr/bin/env python3
# PEM_Server의 PointNet2 모듈 사용 테스트

import sys
import os

# PEM_Server의 PointNet2 경로 추가
pem_server_paths = [
    '/workspace/Estimation_Server/PEM_Server',
    '/workspace/Estimation_Server/PEM_Server/utils',
    '/workspace/Estimation_Server/PEM_Server/model',
    '/workspace/Estimation_Server/PEM_Server/model/pointnet2',  # PEM_Server의 PointNet2
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model',
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/utils',
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/model',
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/provider'
]

for path in pem_server_paths:
    if path not in sys.path:
        sys.path.append(path)

print("=== PEM_Server PointNet2 모듈 테스트 ===")

try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ CUDA available: {torch.cuda.is_available()}")
except Exception as e:
    print(f"❌ PyTorch import failed: {e}")

# PEM_Server의 PointNet2 utils 테스트
try:
    from pointnet2_utils import gather_operation, furthest_point_sample
    print("✅ PEM_Server pointnet2_utils imported successfully")
except Exception as e:
    print(f"❌ PEM_Server pointnet2_utils import failed: {e}")

# PEM_Server의 PointNet2 modules 테스트
try:
    from pointnet2_modules import PointnetSAModuleMSG
    print("✅ PEM_Server pointnet2_modules imported successfully")
except Exception as e:
    print(f"❌ PEM_Server pointnet2_modules import failed: {e}")

# 원본 SAM-6D의 utils 테스트
try:
    from utils.data_utils import load_im, get_bbox, get_point_cloud_from_depth
    print("✅ SAM-6D data_utils imported successfully")
except Exception as e:
    print(f"❌ SAM-6D data_utils import failed: {e}")

try:
    from utils.draw_utils import draw_detections
    print("✅ SAM-6D draw_utils imported successfully")
except Exception as e:
    print(f"❌ SAM-6D draw_utils import failed: {e}")

# 원본 SAM-6D의 model_utils 테스트 (이제 PointNet2 의존성 해결됨)
try:
    from utils.model_utils import LayerNorm2d, sample_pts_feats
    print("✅ SAM-6D model_utils imported successfully")
except Exception as e:
    print(f"❌ SAM-6D model_utils import failed: {e}")

# gorilla 테스트
try:
    import gorilla
    print("✅ gorilla imported successfully")
except Exception as e:
    print(f"❌ gorilla import failed: {e}")

print("\n=== PEM_Server PointNet2 모듈 테스트 완료 ===")
