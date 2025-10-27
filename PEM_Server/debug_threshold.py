#!/usr/bin/env python3
"""PEM_Server 임계값 디버깅"""

import os
import sys
import numpy as np
import json

# SAM-6D 경로 추가
sys.path.append('/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model')

def debug_threshold():
    """임계값 디버깅"""
    
    print("=== PEM_Server 임계값 디버깅 ===")
    
    # 원본 파일들
    seg_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/sam6d_results/detection_ism.json'
    
    # 세그멘테이션 데이터 로딩
    with open(seg_path, 'r') as f:
        detections = json.load(f)
    
    print(f"총 검출 수: {len(detections)}")
    
    # 각 검출의 점수 확인
    scores = [det['score'] for det in detections]
    print(f"검출 점수들: {scores}")
    print(f"최소 점수: {min(scores):.6f}")
    print(f"최대 점수: {max(scores):.6f}")
    print(f"평균 점수: {np.mean(scores):.6f}")
    
    # 다양한 임계값으로 필터링 테스트
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    for thresh in thresholds:
        filtered = [det for det in detections if det['score'] > thresh]
        print(f"임계값 {thresh}: {len(filtered)}개 검출")
    
    # PEM_Server에서 사용하는 임계값 확인
    print(f"\n=== PEM_Server 임계값 확인 ===")
    
    # test_pose_estimation_api.py에서 사용하는 임계값 확인
    try:
        with open('/workspace/Estimation_Server/PEM_Server/test_pose_estimation_api.py', 'r') as f:
            content = f.read()
            if 'det_score_thresh' in content:
                print("test_pose_estimation_api.py에서 det_score_thresh 사용됨")
                # 임계값 값 찾기
                import re
                matches = re.findall(r'det_score_thresh["\']?\s*:\s*([0-9.]+)', content)
                if matches:
                    print(f"사용된 임계값: {matches}")
    except Exception as e:
        print(f"파일 읽기 실패: {e}")

if __name__ == "__main__":
    debug_threshold()
