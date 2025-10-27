#!/usr/bin/env python3
"""깊이 이미지 디버깅 스크립트"""

import os
import sys
import numpy as np
from PIL import Image

# SAM-6D 경로 추가
sys.path.append('/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model')

def debug_depth_image():
    """깊이 이미지 정보 확인"""
    depth_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/depth.png'
    
    print("=== 원본 깊이 이미지 분석 ===")
    
    # PIL로 로딩
    img = Image.open(depth_path)
    arr = np.array(img)
    
    print(f"PIL 로딩 - Shape: {arr.shape}, Type: {arr.dtype}")
    print(f"Min: {arr.min()}, Max: {arr.max()}")
    print(f"Unique values: {len(np.unique(arr))}")
    
    # data_utils의 load_im으로 로딩
    try:
        from data_utils import load_im
        depth_loaded = load_im(depth_path)
        print(f"\ndata_utils.load_im - Shape: {depth_loaded.shape}, Type: {depth_loaded.dtype}")
        print(f"Min: {depth_loaded.min()}, Max: {depth_loaded.max()}")
    except Exception as e:
        print(f"data_utils.load_im 실패: {e}")
    
    # 카메라 파라미터 확인
    cam_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/camera.json'
    import json
    with open(cam_path, 'r') as f:
        cam_info = json.load(f)
    
    print(f"\n카메라 파라미터:")
    print(f"cam_K: {cam_info['cam_K']}")
    print(f"depth_scale: {cam_info['depth_scale']}")
    
    # 깊이 스케일링 후 확인
    depth_scaled = arr.astype(np.float32) * cam_info['depth_scale'] / 1000.0
    print(f"\n스케일링 후 - Min: {depth_scaled.min()}, Max: {depth_scaled.max()}")
    print(f"0보다 큰 픽셀 수: {np.sum(depth_scaled > 0)}")

if __name__ == "__main__":
    debug_depth_image()
