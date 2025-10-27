#!/usr/bin/env python3
"""run_inference_custom_function.py vs PEM_Server 실제 실행 비교"""

import os
import sys
import numpy as np
import json
import time

# SAM-6D 경로 추가
sys.path.append('/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model')

def compare_execution():
    """실제 실행 과정 비교"""
    
    print("=== run_inference_custom_function.py vs PEM_Server 실행 비교 ===")
    
    # 원본 파일들
    rgb_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/rgb.png'
    depth_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/depth.png'
    cam_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/camera.json'
    seg_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/sam6d_results/detection_ism.json'
    cad_path = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply'
    template_dir = '/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/templates'
    
    try:
        # 1. run_inference_custom_function.py 방식
        print("\n1. run_inference_custom_function.py 방식:")
        
        from run_inference_custom_function import (
            load_templates_from_files, 
            load_test_data_from_files, 
            run_pose_estimation_core,
            init_model_and_config
        )
        import gorilla
        import torch
        
        # 모델 초기화
        model, cfg = init_model_and_config(
            gpus="0", 
            model_name="pose_estimation_model", 
            config_path="/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/config/base.yaml", 
            iter_num=0
        )
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 템플릿 로딩
        print("템플릿 로딩...")
        all_tem, all_tem_pts, all_tem_choose = load_templates_from_files(
            template_dir, cfg.test_dataset, device
        )
        
        # 템플릿 특징 추출
        print("템플릿 특징 추출...")
        with torch.no_grad():
            all_tem_pts, all_tem_feat = model.feature_extraction.get_obj_feats(
                all_tem, all_tem_pts, all_tem_choose
            )
        
        # 테스트 데이터 로딩
        print("테스트 데이터 로딩...")
        input_data, whole_image, whole_pts, model_points, detections = load_test_data_from_files(
            rgb_path, depth_path, cam_path, cad_path, seg_path, 
            0.0, cfg.test_dataset, device  # 임계값 0.0
        )
        
        print(f"검출된 객체 수: {len(detections)}")
        print(f"입력 데이터 키: {input_data.keys()}")
        
        if len(detections) > 0:
            print(f"첫 번째 검출 점수: {detections[0]['score']}")
            print(f"입력 데이터 shape:")
            for key, value in input_data.items():
                if hasattr(value, 'shape'):
                    print(f"  {key}: {value.shape}")
        
        # 추가 데이터 저장
        input_data['whole_image'] = whole_image
        input_data['model_points'] = model_points
        
        # 핵심 추론 실행
        print("핵심 추론 실행...")
        result = run_pose_estimation_core(
            model, input_data, all_tem_pts, all_tem_feat, 
            device, detections, None, save_async=False
        )
        
        print(f"추론 결과:")
        print(f"  검출 수: {result['num_detections']}")
        print(f"  포즈 점수: {result['pose_scores']}")
        print(f"  추론 시간: {result['inference_time']:.3f}s")
        
    except Exception as e:
        print(f"실행 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    compare_execution()
