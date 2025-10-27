#!/usr/bin/env python3
"""체크포인트 파일 경로 테스트"""

import os
import sys

# SAM-6D 모듈 import
current_dir = os.path.dirname(os.path.abspath(__file__))
sam6d_path = os.path.join(current_dir, '..', 'SAM-6D', 'SAM-6D', 'Instance_Segmentation_Model')
sam6d_path = os.path.abspath(sam6d_path)
sys.path.append(sam6d_path)

def test_checkpoint_path():
    """체크포인트 파일 경로 테스트"""
    print(f"Current working directory: {os.getcwd()}")
    
    # 체크포인트 디렉토리 확인
    checkpoint_dir = "./checkpoints/segment-anything/"
    checkpoint_file = "sam_vit_h_4b8939.pth"
    full_path = os.path.join(checkpoint_dir, checkpoint_file)
    
    print(f"Checkpoint directory: {checkpoint_dir}")
    print(f"Checkpoint file: {checkpoint_file}")
    print(f"Full path: {full_path}")
    print(f"Directory exists: {os.path.exists(checkpoint_dir)}")
    print(f"File exists: {os.path.exists(full_path)}")
    
    if os.path.exists(checkpoint_dir):
        print(f"Directory contents: {os.listdir(checkpoint_dir)}")
    
    # 절대 경로로도 확인
    abs_path = os.path.abspath(full_path)
    print(f"Absolute path: {abs_path}")
    print(f"Absolute path exists: {os.path.exists(abs_path)}")

if __name__ == "__main__":
    test_checkpoint_path()
