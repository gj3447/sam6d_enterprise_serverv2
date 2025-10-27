#!/usr/bin/env python3
"""세그멘테이션 데이터 디버깅 스크립트"""

import os
import sys
import numpy as np
import json
import pycocotools.mask as cocomask

def debug_segmentation():
    """세그멘테이션 데이터 확인"""
    seg_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/sam6d_results/detection_ism.json'
    
    print("=== 세그멘테이션 데이터 분석 ===")
    
    with open(seg_path, 'r') as f:
        detections = json.load(f)
    
    print(f"총 검출 수: {len(detections)}")
    
    # 각 검출 결과 분석
    for i, det in enumerate(detections[:3]):  # 처음 3개만
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
            print(f"  Mask > 0 pixels: {np.sum(mask > 0)}")
        except Exception as e:
            print(f"  마스크 디코딩 실패: {e}")

if __name__ == "__main__":
    debug_segmentation()
