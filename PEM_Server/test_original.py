#!/usr/bin/env python3
# 원본 SAM-6D 테스트

import sys
import os

# 원본 SAM-6D 경로 추가
original_paths = [
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model',
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/utils',
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/model',
    '/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/provider'
]

for path in original_paths:
    if path not in sys.path:
        sys.path.append(path)

print("=== 원본 SAM-6D 테스트 ===")

try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ CUDA available: {torch.cuda.is_available()}")
except Exception as e:
    print(f"❌ PyTorch import failed: {e}")

try:
    from utils.data_utils import load_im, get_bbox, get_point_cloud_from_depth
    print("✅ 원본 data_utils imported successfully")
except Exception as e:
    print(f"❌ 원본 data_utils import failed: {e}")

try:
    from utils.draw_utils import draw_detections
    print("✅ 원본 draw_utils imported successfully")
except Exception as e:
    print(f"❌ 원본 draw_utils import failed: {e}")

try:
    from utils.model_utils import LayerNorm2d, sample_pts_feats
    print("✅ 원본 model_utils imported successfully")
except Exception as e:
    print(f"❌ 원본 model_utils import failed: {e}")

# PointNet2 테스트
try:
    from pointnet2_modules import PointnetSAModuleMSG
    print("✅ PointNet2 modules imported successfully")
except Exception as e:
    print(f"❌ PointNet2 modules import failed: {e}")

# gorilla 라이브러리 테스트
try:
    import gorilla
    print("✅ gorilla imported successfully")
except Exception as e:
    print(f"❌ gorilla import failed: {e}")

print("\n=== 원본 SAM-6D 테스트 완료 ===")
