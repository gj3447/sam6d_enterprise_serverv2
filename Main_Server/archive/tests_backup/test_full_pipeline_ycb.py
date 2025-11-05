#!/usr/bin/env python3
"""
YCB obj_000002 완전한 파이프라인 테스트 (ISM + PEM)
"""
import requests
import json
import base64
import os
from pathlib import Path

# 서버 URL
ISM_SERVER_URL = "http://localhost:8002"
PEM_SERVER_URL = "http://localhost:8003"

def load_image_as_base64(image_path):
    """이미지를 Base64로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def test_full_pipeline():
    """전체 파이프라인 테스트"""
    
    print("=" * 70)
    print("YCB obj_000002 완전한 파이프라인 테스트 (ISM → PEM)")
    print("=" * 70)
    
    # 프로젝트 루트
    project_root = Path(__file__).resolve().parents[1]
    
    # 입력 파일 경로
    rgb_path = project_root / "static" / "test" / "rgb.png"
    depth_path = project_root / "static" / "test" / "depth.png"
    cam_path = project_root / "static" / "test" / "camera.json"
    
    # 템플릿과 CAD 경로 (컨테이너 경로)
    template_dir = "/workspace/Estimation_Server/static/templates/ycb/obj_000002"
    cad_path = "/workspace/Estimation_Server/static/meshes/ycb/obj_000002.obj"
    
    print(f"\n[INFO] 입력 파일:")
    print(f"  RGB: {rgb_path}")
    print(f"  Depth: {depth_path}")
    print(f"  Camera: {cam_path}")
    print(f"  Template: {template_dir}")
    print(f"  CAD: {cad_path}")
    
    # 이미지 인코딩
    print(f"\n[INFO] 이미지 인코딩 중...")
    rgb_base64 = load_image_as_base64(rgb_path)
    depth_base64 = load_image_as_base64(depth_path)
    
    # 카메라 파라미터 로딩
    with open(cam_path, "r", encoding="utf-8-sig") as f:
        cam_params = json.load(f)
    
    # 출력 디렉 smoktory
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = str(project_root / "static" / "output" / f"ycb_full_{timestamp}")
    
    print(f"\n{'='*70}")
    print("[STEP 1] ISM 추론 실행...")
    print(f"{'='*70}")
    
    # ISM 추론
    ism_url = f"{ISM_SERVER_URL}/api/v1/inference"
    ism_payload = {
        "rgb_image": rgb_base64,
        "depth_image": depth_base64,
        "cam_params": cam_params,
        "template_dir": template_dir,
        "cad_path": cad_path,
        "output_dir": output_dir
    }
    
    try:
        response = requests.post(ism_url, json=ism_payload, timeout=600)
        response.raise_for_status()
        ism_result = response.json()
        
        if not ism_result["success"]:
            print(f"[ERROR] ISM 추론 실패: {ism_result.get('error_message')}")
            return False
        
        print(f"[SUCCESS] ISM 추론 완료!")
        print(f"  - 추론 시간: {ism_result['inference_time']:.2f}초")
        detections = ism_result['detections']
        if 'masks' in detections:
            print(f"  - 감지된 객체 수: {len(detections['masks'])}")
            if 'scores' in detections and len(detections['scores']) > 0:
                print(f"  - 최고 스코어: {max(detections['scores']):.3f}")
        
    except Exception as e:
        print(f"[ERROR] ISM 요청 실패: {e}")
        return False
    
    # ISM 결과에서 최고 스코어 세그멘테이션 데이터 추출
    detections = ism_result['detections']
    if 'scores' not in detections or len(detections['scores']) == 0:
        print("[WARNING] 감지된 객체가 없습니다.")
        return False
    
    # 최고 스코어 찾기
    max_score_idx = detections['scores'].index(max(detections['scores']))
    
    # 세그멘테이션 데이터 구성
    seg_data = [{
        "scene_id": 0,
        "image_id": 0,
        "category_id": 1,
        "bbox": detections['boxes'][max_score_idx] if 'boxes' in detections else [0, 0, 100, 100],
        "score": detections['scores'][max_score_idx],
        "segmentation": detections['masks'][max_score_idx] if 'masks' in detections else {}
    }]
    
    print(f"\n{'='*70}")
    print("[STEP 2] PEM 추론 실행...")
    print(f"{'='*70}")
    
    # PEM 추론
    pem_url = f"{PEM_SERVER_URL}/api/v1/pose-estimation"
    pem_payload = {
        "rgb_image": rgb_base64,
        "depth_image": depth_base64,
        "cam_params": cam_params,
        "cad_path": cad_path,
        "template_dir": template_dir,
        "seg_data": seg_data,
        "output_dir": output_dir
    }
    
    try:
        print("[INFO] PEM 추론 요청 중... (시간이 오래 걸릴 수 있습니다)")
        response = requests.post(pem_url, json=pem_payload, timeout=600)
        response.raise_for_status()
        pem_result = response.json()
        
        if pem_result["success"]:
            print(f"[SUCCESS] PEM 추론 완료!")
            print(f"  - 추론 시간: {pem_result['inference_time']:.2f}초")
            print(f"  - 결과 디렉토리: {output_dir}")
            
            if 'poses' in pem_result and len(pem_result['poses']) > 0:
                print(f"  - 포즈 추정 성공: {len(pem_result['poses'])}개")
                
        else:
            print(f"[WARNING] PEM 추론 실패: {pem_result.get('error_message')}")
            
    except Exception as e:
        print(f"[ERROR] PEM 요청 실패: {e}")
        return False
    
    print(f"\n{'='*70}")
    print("[COMPLETE] 전체 파이프라인 완료!")
    print(f"{'='*70}")
    print(f"결과 위치: {output_dir}")
    
    return True

if __name__ == "__main__":
    import sys
    success = test_full_pipeline()
    sys.exit(0 if success else 1)

