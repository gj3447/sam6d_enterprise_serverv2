#!/usr/bin/env python3
"""세그멘테이션 데이터 처리 차이점 분석"""

import os
import sys
import numpy as np
import json
import base64
import tempfile
import pycocotools.mask as cocomask

# SAM-6D 경로 추가
sys.path.append('/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model')

def analyze_segmentation_differences():
    """세그멘테이션 데이터 처리 차이점 분석"""
    
    print("=== 세그멘테이션 데이터 처리 차이점 분석 ===")
    
    # 원본 파일들
    seg_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/sam6d_results/detection_ism.json'
    depth_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/depth.png'
    cam_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/camera.json'
    
    # 원본 세그멘테이션 데이터 로딩
    with open(seg_path, 'r') as f:
        detections_original = json.load(f)
    
    print(f"원본 검출 수: {len(detections_original)}")
    
    # 깊이 이미지 로딩
    from data_utils import load_im
    depth_original = load_im(depth_path).astype(np.float32)
    cam_info = json.load(open(cam_path))
    depth_scaled = depth_original * cam_info['depth_scale'] / 1000.0
    
    print(f"깊이 이미지 - Shape: {depth_scaled.shape}, Min: {depth_scaled.min()}, Max: {depth_scaled.max()}")
    
    # 각 검출 결과 분석
    valid_detections = 0
    for i, det in enumerate(detections_original[:5]):  # 처음 5개만
        print(f"\n검출 {i+1}:")
        print(f"  Score: {det['score']}")
        print(f"  Bbox: {det['bbox']}")
        
        seg = det['segmentation']
        h, w = seg['size']
        print(f"  Size: {h}x{w}")
        
        # 마스크 디코딩
        try:
            rle = cocomask.frPyObjects(seg, h, w)
            mask = cocomask.decode(rle)
            print(f"  Mask shape: {mask.shape}")
            print(f"  Mask sum: {np.sum(mask)}")
            
            # 마스크와 깊이 교집합 확인
            mask_depth_intersection = np.logical_and(mask > 0, depth_scaled > 0)
            intersection_pixels = np.sum(mask_depth_intersection)
            print(f"  마스크-깊이 교집합 픽셀 수: {intersection_pixels}")
            
            if intersection_pixels > 32:
                print(f"  ✅ 유효한 검출 (교집합 > 32)")
                valid_detections += 1
            else:
                print(f"  ❌ 무효한 검출 (교집합 <= 32)")
                
        except Exception as e:
            print(f"  마스크 디코딩 실패: {e}")
    
    print(f"\n총 유효한 검출 수: {valid_detections}")
    
    # PEM_Server 방식 시뮬레이션
    print(f"\n=== PEM_Server 방식 시뮬레이션 ===")
    
    # Base64 인코딩/디코딩 시뮬레이션
    temp_dir = tempfile.mkdtemp()
    
    # 세그멘테이션 데이터를 Base64로 인코딩/디코딩
    seg_json_str = json.dumps(detections_original)
    seg_base64 = base64.b64encode(seg_json_str.encode('utf-8')).decode('utf-8')
    seg_decoded_str = base64.b64decode(seg_base64).decode('utf-8')
    detections_pem = json.loads(seg_decoded_str)
    
    print(f"PEM_Server 검출 수: {len(detections_pem)}")
    print(f"원본과 PEM_Server 검출 데이터 동일: {detections_original == detections_pem}")
    
    # 임시 파일로 저장
    seg_temp_path = os.path.join(temp_dir, "seg.json")
    with open(seg_temp_path, 'w') as f:
        json.dump(detections_pem, f)
    
    # 다시 로딩해서 확인
    with open(seg_temp_path, 'r') as f:
        detections_reloaded = json.load(f)
    
    print(f"재로딩 후 검출 수: {len(detections_reloaded)}")
    print(f"원본과 재로딩 검출 데이터 동일: {detections_original == detections_reloaded}")
    
    # 정리
    import shutil
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    analyze_segmentation_differences()
