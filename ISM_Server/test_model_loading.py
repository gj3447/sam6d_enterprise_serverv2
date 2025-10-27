#!/usr/bin/env python3
"""모델 로딩 테스트 스크립트"""

import sys
import os
import asyncio

# SAM-6D 모듈 import
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sam6d_path = os.path.join(current_dir, '..', 'SAM-6D', 'SAM-6D', 'Instance_Segmentation_Model')
sam6d_path = os.path.abspath(sam6d_path)
sys.path.append(sam6d_path)

# main.py에서 모델 로딩 함수 import
from main import load_model, load_templates, load_cad_model

async def test_model_loading():
    """모델 로딩 테스트"""
    print("=== 모델 로딩 테스트 시작 ===")
    
    # 모델 로딩 테스트
    print("\n1. 모델 로딩 테스트")
    model_result = await load_model()
    print(f"모델 로딩 결과: {model_result}")
    
    # 템플릿 로딩 테스트
    print("\n2. 템플릿 로딩 테스트")
    template_result = await load_templates()
    print(f"템플릿 로딩 결과: {template_result}")
    
    # CAD 모델 로딩 테스트
    print("\n3. CAD 모델 로딩 테스트")
    cad_result = await load_cad_model()
    print(f"CAD 모델 로딩 결과: {cad_result}")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    asyncio.run(test_model_loading())
