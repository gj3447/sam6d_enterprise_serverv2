#!/usr/bin/env python3
"""SAM 모델 로딩 테스트"""

import os
import sys

# SAM-6D 모듈 import
current_dir = os.path.dirname(os.path.abspath(__file__))
sam6d_path = os.path.join(current_dir, '..', 'SAM-6D', 'SAM-6D', 'Instance_Segmentation_Model')
sam6d_path = os.path.abspath(sam6d_path)
sys.path.append(sam6d_path)

def test_sam_loading():
    """SAM 모델 로딩 테스트"""
    try:
        print("Testing SAM model loading...")
        from model.sam import load_sam
        
        checkpoint_dir = "./checkpoints/segment-anything/"
        print(f"Loading SAM model from: {checkpoint_dir}")
        
        sam = load_sam('vit_h', checkpoint_dir)
        print("✅ SAM model loaded successfully!")
        print(f"Model type: {type(sam)}")
        
        return True
        
    except Exception as e:
        print(f"❌ SAM model loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_sam_loading()
