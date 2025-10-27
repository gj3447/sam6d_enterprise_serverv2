#!/usr/bin/env python3
"""PEM_Server vs 원본 코드 차이점 분석"""

import os
import sys
import numpy as np
import json
import base64
import tempfile
from PIL import Image
import imageio

# SAM-6D 경로 추가
sys.path.append('/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model')

def analyze_differences():
    """두 방식의 차이점 분석"""
    
    print("=== PEM_Server vs 원본 코드 차이점 분석 ===")
    
    # 원본 파일들
    rgb_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/rgb.png'
    depth_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/depth.png'
    cam_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/camera.json'
    
    # 1. 원본 방식 (run_inference_custom_function.py)
    print("\n1. 원본 방식:")
    try:
        from data_utils import load_im
        
        # RGB 로딩
        rgb_original = load_im(rgb_path).astype(np.uint8)
        print(f"RGB - Shape: {rgb_original.shape}, Type: {rgb_original.dtype}")
        
        # 깊이 로딩
        depth_original = load_im(depth_path).astype(np.float32)
        print(f"Depth 원본 - Shape: {depth_original.shape}, Type: {depth_original.dtype}")
        print(f"Depth 원본 - Min: {depth_original.min()}, Max: {depth_original.max()}")
        
        # 카메라 파라미터
        cam_info = json.load(open(cam_path))
        depth_scaled = depth_original * cam_info['depth_scale'] / 1000.0
        print(f"Depth 스케일링 후 - Min: {depth_scaled.min()}, Max: {depth_scaled.max()}")
        print(f"Depth 스케일링 후 - 0보다 큰 픽셀: {np.sum(depth_scaled > 0)}")
        
    except Exception as e:
        print(f"원본 방식 실패: {e}")
    
    # 2. PEM_Server 방식 시뮬레이션
    print("\n2. PEM_Server 방식:")
    try:
        # Base64 인코딩 (테스트 코드 시뮬레이션)
        with open(rgb_path, "rb") as f:
            rgb_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        depth_image = Image.open(depth_path)
        depth_array = np.array(depth_image).astype(np.float32)
        depth_bytes = depth_array.tobytes()
        depth_base64 = base64.b64encode(depth_bytes).decode('utf-8')
        
        print(f"RGB Base64 길이: {len(rgb_base64)}")
        print(f"Depth Base64 길이: {len(depth_base64)}")
        
        # Base64 디코딩 (PEM_Server 시뮬레이션)
        rgb_data = base64.b64decode(rgb_base64)
        rgb_image = Image.open(io.BytesIO(rgb_data))
        rgb_decoded = np.array(rgb_image)
        
        depth_bytes_decoded = base64.b64decode(depth_base64)
        depth_decoded = np.frombuffer(depth_bytes_decoded, dtype=np.float32)
        depth_decoded = depth_decoded.reshape(depth_array.shape)
        
        print(f"RGB 디코딩 후 - Shape: {rgb_decoded.shape}, Type: {rgb_decoded.dtype}")
        print(f"Depth 디코딩 후 - Shape: {depth_decoded.shape}, Type: {depth_decoded.dtype}")
        print(f"Depth 디코딩 후 - Min: {depth_decoded.min()}, Max: {depth_decoded.max()}")
        
        # 임시 파일로 저장 후 다시 로딩 (PEM_Server 방식)
        temp_dir = tempfile.mkdtemp()
        
        # RGB 저장
        rgb_temp_path = os.path.join(temp_dir, "rgb.png")
        Image.fromarray(rgb_decoded).save(rgb_temp_path)
        
        # 깊이 저장 (imageio 방식)
        depth_temp_path = os.path.join(temp_dir, "depth.png")
        imageio.imwrite(depth_temp_path, depth_decoded.astype(np.uint16))
        
        # 다시 로딩
        rgb_reloaded = load_im(rgb_temp_path).astype(np.uint8)
        depth_reloaded = load_im(depth_temp_path).astype(np.float32)
        
        print(f"RGB 재로딩 후 - Shape: {rgb_reloaded.shape}, Type: {rgb_reloaded.dtype}")
        print(f"Depth 재로딩 후 - Shape: {depth_reloaded.shape}, Type: {depth_reloaded.dtype}")
        print(f"Depth 재로딩 후 - Min: {depth_reloaded.min()}, Max: {depth_reloaded.max()}")
        
        # 스케일링 후 비교
        depth_reloaded_scaled = depth_reloaded * cam_info['depth_scale'] / 1000.0
        print(f"Depth 재로딩 스케일링 후 - Min: {depth_reloaded_scaled.min()}, Max: {depth_reloaded_scaled.max()}")
        print(f"Depth 재로딩 스케일링 후 - 0보다 큰 픽셀: {np.sum(depth_reloaded_scaled > 0)}")
        
        # 차이점 분석
        print(f"\n3. 차이점 분석:")
        print(f"원본 vs 디코딩 후 깊이 동일: {np.array_equal(depth_original, depth_decoded)}")
        print(f"원본 vs 재로딩 후 깊이 동일: {np.array_equal(depth_original, depth_reloaded)}")
        
        if not np.array_equal(depth_original, depth_reloaded):
            diff = np.abs(depth_original.astype(np.float32) - depth_reloaded.astype(np.float32))
            print(f"최대 차이: {diff.max()}")
            print(f"평균 차이: {diff.mean()}")
            print(f"차이가 있는 픽셀 수: {np.sum(diff > 0)}")
        
        # 정리
        import shutil
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"PEM_Server 방식 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import io
    analyze_differences()
