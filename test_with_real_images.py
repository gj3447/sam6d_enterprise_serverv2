#!/usr/bin/env python3
"""
실제 테스트 이미지로 Full Pipeline 테스트
"""
import requests
import base64
import json
from pathlib import Path

BASE_URL = "http://localhost:8001"

def load_image_as_base64(image_path: str) -> str:
    """이미지 파일을 base64로 인코딩"""
    with open(image_path, "rb") as f:
        image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')

def load_camera_params(camera_path: str) -> dict:
    """카메라 파라미터 로드"""
    with open(camera_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    print("=" * 80)
    print("Full Pipeline API 테스트 - 실제 이미지 사용")
    print("=" * 80)
    
    # 테스트 데이터 경로
    rgb_path = "static/test/rgb.png"
    depth_path = "static/test/depth.png"
    camera_path = "static/test/camera.json"
    
    print(f"\n테스트 데이터:")
    print(f"  RGB: {rgb_path}")
    print(f"  Depth: {depth_path}")
    print(f"  Camera: {camera_path}")
    
    # 파일 확인
    for path in [rgb_path, depth_path, camera_path]:
        if not Path(path).exists():
            print(f"\n[ERROR] File not found: {path}")
            return
        else:
            file_size = Path(path).stat().st_size
            print(f"  OK: {path} ({file_size:,} bytes)")
    
    # 이미지 인코딩
    print(f"\n[1] 이미지 인코딩 중...")
    rgb_b64 = load_image_as_base64(rgb_path)
    depth_b64 = load_image_as_base64(depth_path)
    print(f"  RGB size: {len(rgb_b64):,} bytes")
    print(f"  Depth size: {len(depth_b64):,} bytes")
    
    # 카메라 파라미터 로드
    print(f"\n[2] 카메라 파라미터 로드 중...")
    cam_params = load_camera_params(camera_path)
    print(f"  Camera params keys: {list(cam_params.keys())}")
    
    # API 요청
    print(f"\n[3] API 요청 전송 중...")
    request_data = {
        "class_name": "test",
        "object_name": "obj_000005",
        "rgb_image": rgb_b64,
        "depth_image": depth_b64,
        "cam_params": cam_params
    }
    
    print(f"  Class: {request_data['class_name']}")
    print(f"  Object: {request_data['object_name']}")
    print(f"  Request data size: {len(str(request_data)):,} chars")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/workflow/full-pipeline",
            json=request_data,
            timeout=1200  # 20분
        )
        
        print(f"\n[4] 응답 받음")
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = results.json()
            print(f"  Success: {result['success']}")
            print(f"  Message: {result['message']}")
            
            if 'results' in result and isinstance(result['results'], dict):
                results_dict = result['results']
                print(f"\n[5] 결과:")
                
                if 'render' in results_dict:
                    r = results_dict['render']
                    if r.get('skipped'):
                        print(f"  Render: Skipped (template exists)")
                    else:
                        print(f"  Render: {r.get('success', 'N/A')}")
                
                if 'ism' in results_dict:
                    r = results_dict['ism']
                    print(f"  ISM: {r.get('success', 'N/A')}")
                    if r.get('success'):
                        inference_time = r.get('inference_time', 0)
                        print(f"    Time: {inference_time:.2f}s")
                
                if 'pem' in results_dict:
                    r = results_dict['pem']
                    print(f"  PEM: {r.get('success', 'N/A')}")
                    if r.get('success'):
                        num_poses = r.get('num_detections', 0)
                        print(f"    Poses: {num_poses}")
                        inference_time = r.get('inference_time', 0)
                        print(f"    Time: {inference_time:.2f}s")
            
            print(f"\n[6] Output 디렉토리 생성됨")
            
        else:
            print(f"  Error: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("\n[ERROR] 타임아웃 발생")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()





















