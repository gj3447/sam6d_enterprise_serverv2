#!/usr/bin/env python3
"""PEM_Server 필터링 조건 완화"""

import os
import sys
import numpy as np
import json
import pycocotools.mask as cocomask

# SAM-6D 경로 추가
sys.path.append('/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model')

def debug_filtering():
    """필터링 조건 디버깅"""
    
    print("=== PEM_Server 필터링 조건 디버깅 ===")
    
    # 원본 파일들
    rgb_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/rgb.png'
    depth_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/depth.png'
    cam_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/camera.json'
    seg_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/sam6d_results/detection_ism.json'
    cad_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply'
    
    # 데이터 로딩
    from data_utils import load_im, get_point_cloud_from_depth, get_bbox
    import trimesh
    
    # 세그멘테이션 데이터
    with open(seg_path) as f:
        dets = json.load(f)
    
    # 카메라 정보
    cam_info = json.load(open(cam_path))
    K = np.array(cam_info['cam_K']).reshape(3, 3)
    
    # 이미지 로딩
    whole_image = load_im(rgb_path).astype(np.uint8)
    whole_depth = load_im(depth_path).astype(np.float32) * cam_info['depth_scale'] / 1000.0
    whole_pts = get_point_cloud_from_depth(whole_depth, K)
    
    # CAD 모델
    mesh = trimesh.load_mesh(cad_path)
    model_points = mesh.sample(1024).astype(np.float32) / 1000.0
    radius = np.max(np.linalg.norm(model_points, axis=1))
    
    print(f"총 검출 수: {len(dets)}")
    print(f"CAD 모델 반지름: {radius}")
    print(f"깊이 이미지 - Min: {whole_depth.min()}, Max: {whole_depth.max()}")
    print(f"0보다 큰 깊이 픽셀: {np.sum(whole_depth > 0)}")
    
    # 각 검출에 대해 필터링 조건 확인
    valid_detections = 0
    
    for i, inst in enumerate(dets[:5]):  # 처음 5개만
        print(f"\n검출 {i+1}:")
        print(f"  Score: {inst['score']}")
        
        seg = inst['segmentation']
        h, w = seg['size']
        
        # 마스크 디코딩
        try:
            rle = cocomask.frPyObjects(seg, h, w)
        except:
            rle = seg
        mask = cocomask.decode(rle)
        
        # 필터링 조건 1: 마스크와 깊이 교집합
        mask_depth_intersection = np.logical_and(mask > 0, whole_depth > 0)
        intersection_pixels = np.sum(mask_depth_intersection)
        print(f"  마스크-깊이 교집합 픽셀: {intersection_pixels}")
        
        if intersection_pixels > 32:
            print(f"  ✅ 조건 1 통과 (교집합 > 32)")
            
            # bbox 계산
            bbox = get_bbox(mask_depth_intersection)
            y1, y2, x1, x2 = bbox
            print(f"  Bbox: [{y1}, {y2}, {x1}, {x2}]")
            
            # 포인트 클라우드 추출
            mask_cropped = mask_depth_intersection[y1:y2, x1:x2]
            choose = mask_cropped.astype(np.float32).flatten().nonzero()[0]
            
            if len(choose) > 0:
                cloud = whole_pts.copy()[y1:y2, x1:x2, :].reshape(-1, 3)[choose, :]
                center = np.mean(cloud, axis=0)
                tmp_cloud = cloud - center[None, :]
                flag = np.linalg.norm(tmp_cloud, axis=1) < radius * 1.2
                valid_points = np.sum(flag)
                print(f"  유효한 포인트 수: {valid_points}")
                
                if valid_points >= 4:
                    print(f"  ✅ 조건 2 통과 (포인트 >= 4)")
                    valid_detections += 1
                else:
                    print(f"  ❌ 조건 2 실패 (포인트 < 4)")
            else:
                print(f"  ❌ 포인트 클라우드 추출 실패")
        else:
            print(f"  ❌ 조건 1 실패 (교집합 <= 32)")
    
    print(f"\n총 유효한 검출 수: {valid_detections}")

if __name__ == "__main__":
    debug_filtering()
