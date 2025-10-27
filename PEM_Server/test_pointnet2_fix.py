#!/usr/bin/env python3
# PointNet2 경로 수정 테스트

import sys
import os

# 올바른 경로들 추가
correct_paths = [
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model',
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/utils',
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/model',
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/provider',
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/model/pointnet2',  # PointNet2 경로 추가
    '/workspace/Estimation_Server/git/SAM-6D/SAM-6D/Pose_Estimation_Model/model/pointnet2'  # git 버전도 추가
]

for path in correct_paths:
    if path not in sys.path:
        sys.path.append(path)

print("=== PointNet2 경로 수정 테스트 ===")

try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ CUDA available: {torch.cuda.is_available()}")
except Exception as e:
    print(f"❌ PyTorch import failed: {e}")

# PointNet2 utils 테스트
try:
    from pointnet2_utils import gather_operation, furthest_point_sample
    print("✅ pointnet2_utils imported successfully")
except Exception as e:
    print(f"❌ pointnet2_utils import failed: {e}")

# PointNet2 modules 테스트
try:
    from pointnet2_modules import PointnetSAModuleMSG
    print("✅ pointnet2_modules imported successfully")
except Exception as e:
    print(f"❌ pointnet2_modules import failed: {e}")

# 원본 model_utils 테스트 (PointNet2 의존성 해결 후)
try:
    from utils.model_utils import LayerNorm2d, sample_pts_feats
    print("✅ 원본 model_utils imported successfully")
except Exception as e:
    print(f"❌ 원본 model_utils import failed: {e}")

# gorilla 테스트
try:
    import gorilla
    print("✅ gorilla imported successfully")
except Exception as e:
    print(f"❌ gorilla import failed: {e}")

print("\n=== PointNet2 경로 수정 테스트 완료 ===")
