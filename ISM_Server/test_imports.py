#!/usr/bin/env python3
"""
Phase 0 테스트: Docker 환경 및 라이브러리 Import 테스트
"""

import sys
import os

# SAM-6D 경로 추가
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sam6d_path = os.path.join(current_dir, '..', 'SAM-6D', 'SAM-6D', 'Instance_Segmentation_Model')
sam6d_path = os.path.abspath(sam6d_path)
sys.path.append(sam6d_path)

print("=== Python 환경 확인 ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

print("\n=== 작업 디렉토리 확인 ===")
workspace_dir = os.path.join(current_dir, '..')
workspace_dir = os.path.abspath(workspace_dir)
print(f"Workspace contents: {os.listdir(workspace_dir)}")

print("\n=== SAM-6D 디렉토리 확인 ===")
ism_dir = os.path.join(current_dir, '..', 'SAM-6D', 'SAM-6D', 'Instance_Segmentation_Model')
ism_dir = os.path.abspath(ism_dir)
if os.path.exists(ism_dir):
    print(f"SAM-6D ISM directory exists: {ism_dir}")
    print(f"Contents: {os.listdir(ism_dir)}")
else:
    print(f"SAM-6D ISM directory NOT found: {ism_dir}")

print("\n=== 기본 라이브러리 Import 테스트 ===")
try:
    import numpy as np
    print(f"✓ NumPy version: {np.__version__}")
except ImportError as e:
    print(f"✗ NumPy import failed: {e}")

try:
    import cv2
    print(f"✓ OpenCV version: {cv2.__version__}")
except ImportError as e:
    print(f"✗ OpenCV import failed: {e}")

try:
    from PIL import Image
    print("✓ PIL (Pillow) imported successfully")
except ImportError as e:
    print(f"✗ PIL import failed: {e}")

print("\n=== PyTorch Import 테스트 ===")
try:
    import torch
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ CUDA device count: {torch.cuda.device_count()}")
except ImportError as e:
    print(f"✗ PyTorch import failed: {e}")

print("\n=== SAM-6D 관련 라이브러리 Import 테스트 ===")
try:
    from run_inference_custom_function import run_inference_core, load_templates_from_files
    print("✓ run_inference_custom_function imported successfully")
except ImportError as e:
    print(f"✗ run_inference_custom_function import failed: {e}")

try:
    from model.detector import Detector
    print("✓ Detector model imported successfully")
except ImportError as e:
    print(f"✗ Detector model import failed: {e}")

try:
    from model.sam import SAM
    print("✓ SAM model imported successfully")
except ImportError as e:
    print(f"✗ SAM model import failed: {e}")

print("\n=== FastAPI Import 테스트 ===")
try:
    import fastapi
    print(f"✓ FastAPI version: {fastapi.__version__}")
except ImportError as e:
    print(f"✗ FastAPI import failed: {e}")

try:
    import uvicorn
    print(f"✓ Uvicorn version: {uvicorn.__version__}")
except ImportError as e:
    print(f"✗ Uvicorn import failed: {e}")

print("\n=== Phase 0 테스트 완료 ===")
