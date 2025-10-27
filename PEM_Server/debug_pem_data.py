#!/usr/bin/env python3
"""PEM_Server 데이터 처리 디버깅 스크립트"""

import os
import sys
import numpy as np
import json
import base64
import tempfile
from PIL import Image

# SAM-6D 경로 추가
sys.path.append('/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model')

def debug_pem_server_data():
    """PEM_Server에서 처리되는 데이터 확인"""
    
    print("=== PEM_Server 데이터 처리 시뮬레이션 ===")
    
    # 원본 파일들
    rgb_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/rgb.png'
    depth_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/depth.png'
    cam_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/camera.json'
    seg_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/sam6d_results/detection_ism.json'
    
    # 1. Base64 인코딩 (PEM_Server 테스트 코드 시뮬레이션)
    print("1. Base64 인코딩...")
    
    # RGB 이미지 인코딩
    with open(rgb_path, "rb") as f:
        rgb_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # 깊이 이미지 인코딩 (원본 데이터 타입)
    depth_image = Image.open(depth_path)
    depth_array = np.array(depth_image).astype(np.float32)
    depth_bytes = depth_array.tobytes()
    depth_base64 = base64.b64encode(depth_bytes).decode('utf-8')
    
    print(f"RGB Base64 길이: {len(rgb_base64)}")
    print(f"Depth Base64 길이: {len(depth_base64)}")
    
    # 2. Base64 디코딩 (PEM_Server 시뮬레이션)
    print("\n2. Base64 디코딩...")
    
    # RGB 디코딩
    rgb_data = base64.b64decode(rgb_base64)
    rgb_image = Image.open(io.BytesIO(rgb_data))
    rgb_array = np.array(rgb_image)
    
    # 깊이 디코딩 (원본 데이터 타입)
    depth_bytes_decoded = base64.b64decode(depth_base64)
    depth_array_decoded = np.frombuffer(depth_bytes_decoded, dtype=np.float32)
    depth_array_decoded = depth_array_decoded.reshape(depth_array.shape)
    
    print(f"RGB 디코딩 후 - Shape: {rgb_array.shape}, Type: {rgb_array.dtype}")
    print(f"Depth 디코딩 후 - Shape: {depth_array_decoded.shape}, Type: {depth_array_decoded.dtype}")
    print(f"Depth 원본과 동일: {np.array_equal(depth_array, depth_array_decoded)}")
    
    # 3. 임시 파일 생성 (PEM_Server 시뮬레이션)
    print("\n3. 임시 파일 생성...")
    
    temp_dir = tempfile.mkdtemp()
    
    # RGB 저장
    rgb_temp_path = os.path.join(temp_dir, "rgb.png")
    Image.fromarray(rgb_array).save(rgb_temp_path)
    
    # 깊이 저장 (원본 데이터 타입으로)
    depth_temp_path = os.path.join(temp_dir, "depth.png")
    Image.fromarray(depth_array_decoded.astype(np.uint16)).save(depth_temp_path)
    
    # 카메라 파라미터 복사
    cam_temp_path = os.path.join(temp_dir, "cam.json")
    import shutil
    shutil.copy2(cam_path, cam_temp_path)
    
    # 세그멘테이션 데이터 복사
    seg_temp_path = os.path.join(temp_dir, "seg.json")
    shutil.copy2(seg_path, seg_temp_path)
    
    print(f"임시 파일들 생성됨: {temp_dir}")
    
    # 4. load_test_data_from_files 테스트
    print("\n4. load_test_data_from_files 테스트...")
    
    try:
        from run_inference_custom_function import load_test_data_from_files
        from data_utils import load_im
        
        # 설정 로딩
        import gorilla
        cfg = gorilla.Config.fromfile('/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/config/base.yaml')
        
        # 테스트 데이터 로딩
        input_data, whole_image, whole_pts, model_points, detections = load_test_data_from_files(
            rgb_temp_path, depth_temp_path, cam_temp_path, 
            '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply',
            seg_temp_path, 0.1, cfg.test_dataset, 'cuda'
        )
        
        print(f"검출된 객체 수: {len(detections)}")
        print(f"입력 데이터 키: {input_data.keys()}")
        if 'pts' in input_data:
            print(f"포인트 클라우드 shape: {input_data['pts'].shape}")
        
    except Exception as e:
        print(f"load_test_data_from_files 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 정리
    import shutil
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    import io
    debug_pem_server_data()
