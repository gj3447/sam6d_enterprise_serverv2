#!/usr/bin/env python3
"""PEM_Server 실제 실행 과정 추적"""

import os
import sys
import numpy as np
import json
import base64
import tempfile
import pycocotools.mask as cocomask

# SAM-6D 경로 추가
sys.path.append('/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model')

def trace_pem_server_execution():
    """PEM_Server 실제 실행 과정 추적"""
    
    print("=== PEM_Server 실제 실행 과정 추적 ===")
    
    # 원본 파일들
    rgb_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/rgb.png'
    depth_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/depth.png'
    cam_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/camera.json'
    seg_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/sam6d_results/detection_ism.json'
    cad_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply'
    
    try:
        # PEM_Server 방식으로 데이터 준비
        print("1. 데이터 준비...")
        
        # Base64 인코딩
        with open(rgb_path, "rb") as f:
            rgb_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        from PIL import Image
        depth_image = Image.open(depth_path)
        depth_array = np.array(depth_image).astype(np.float32)
        depth_bytes = depth_array.tobytes()
        depth_base64 = base64.b64encode(depth_bytes).decode('utf-8')
        
        # 카메라 파라미터
        cam_params = json.load(open(cam_path))
        
        # 세그멘테이션 데이터
        seg_data = json.load(open(seg_path))
        
        print(f"RGB Base64 길이: {len(rgb_base64)}")
        print(f"Depth Base64 길이: {len(depth_base64)}")
        print(f"세그멘테이션 검출 수: {len(seg_data)}")
        
        # 2. 임시 파일 생성 (PEM_Server 방식)
        print("\n2. 임시 파일 생성...")
        
        temp_dir = tempfile.mkdtemp()
        
        # RGB 디코딩 및 저장
        rgb_data = base64.b64decode(rgb_base64)
        rgb_image = Image.open(io.BytesIO(rgb_data))
        rgb_array = np.array(rgb_image)
        rgb_temp_path = os.path.join(temp_dir, "rgb.png")
        Image.fromarray(rgb_array).save(rgb_temp_path)
        
        # 깊이 디코딩 및 저장
        depth_bytes_decoded = base64.b64decode(depth_base64)
        depth_decoded = np.frombuffer(depth_bytes_decoded, dtype=np.float32)
        depth_decoded = depth_decoded.reshape(depth_array.shape)
        
        import imageio
        depth_temp_path = os.path.join(temp_dir, "depth.png")
        imageio.imwrite(depth_temp_path, depth_decoded.astype(np.uint16))
        
        # 카메라 파라미터 저장
        cam_temp_path = os.path.join(temp_dir, "cam.json")
        with open(cam_temp_path, 'w') as f:
            json.dump(cam_params, f)
        
        # 세그멘테이션 데이터 저장
        seg_temp_path = os.path.join(temp_dir, "seg.json")
        with open(seg_temp_path, 'w') as f:
            json.dump(seg_data, f)
        
        print(f"임시 파일들 생성됨: {temp_dir}")
        
        # 3. load_test_data_from_files 실행
        print("\n3. load_test_data_from_files 실행...")
        
        from run_inference_custom_function import load_test_data_from_files
        import gorilla
        
        # 설정 로딩
        cfg = gorilla.Config.fromfile('/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/config/base.yaml')
        
        # det_score_thresh = 0.1로 설정
        det_score_thresh = 0.1
        
        print(f"임계값: {det_score_thresh}")
        print(f"설정 파일 로딩 완료")
        
        # 테스트 데이터 로딩
        input_data, whole_image, whole_pts, model_points, detections = load_test_data_from_files(
            rgb_temp_path, depth_temp_path, cam_temp_path, cad_path, seg_temp_path, 
            det_score_thresh, cfg.test_dataset, 'cuda'
        )
        
        print(f"검출된 객체 수: {len(detections)}")
        print(f"입력 데이터 키: {input_data.keys()}")
        
        if len(detections) > 0:
            print(f"첫 번째 검출 점수: {detections[0]['score']}")
            print(f"입력 데이터 shape:")
            for key, value in input_data.items():
                if hasattr(value, 'shape'):
                    print(f"  {key}: {value.shape}")
        
        # 정리
        import shutil
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"실행 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import io
    trace_pem_server_execution()
