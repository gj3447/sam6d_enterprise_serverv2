#!/usr/bin/env python3
"""
개선된 Full Pipeline API 테스트 (Base64 이미지 직접 입력)
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

def test_full_pipeline():
    print("=" * 80)
    print("Full Pipeline API 테스트 (Base64 이미지 직접 입력)")
    print("=" * 80)
    
    # 테스트 데이터 경로
    rgb_path = "static/test/rgb.png"
    depth_path = "static/test/depth.png"
    camera_path = "static/test/camera.json"
    
    # 파일 존재 확인
    for path in [rgb_path, depth_path, camera_path]:
        if not Path(path).exists():
            print(f"ERROR: File not found: {path}")
            return
    
    print(f"\n테스트 데이터:")
    print(f"  RGB: {rgb_path}")
    print(f"  Depth: {depth_path}")
    print(f"  Camera: {camera_path}")
    
    # 이미지 인코딩
    print(f"\n[1] 이미지 인코딩 중...")
    rgb_b64 = load_image_as_base64(rgb_path)
    depth_b64 = load_image_as_base64(depth_path)
    print(f"  RGB size: {len(rgb_b64)} bytes")
    print(f"  Depth size: {len(depth_b64)} bytes")
    
    # 카메라 파라미터 로드
    print(f"\n[2] 카메라 파라미터 로드 중...")
    cam_params = load_camera_params(camera_path)
    print(f"  Camera params: {list(cam_params.keys())}")
    
    # API 요청
    print(f"\n[3] API 요청 중...")
    request_data = {
        "class_name": "test",
        "object_name": "obj_000005",
        "rgb_image": rgb_b64,
        "depth_image": depth_b64,
        "cam_params": cam_params
    }
    
    print(f"  Class: {request_data['class_name']}")
    print(f"  Object: {request_data['object_name']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/workflow/full-pipeline",
            json=request_data,
            timeout=1200  # 20분 타임아웃
        )
        
        print(f"\n[4] 응답 받음")
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[5] 결과:")
            print(f"  Success: {result['success']}")
            print(f"  Message: {result['message']}")
            
            if 'results' in result and isinstance(result['results'], dict):
                print(f"\n[6] 세부 결과:")
                results = result['results']
                
                if 'render' in results:
                    render_result = results['render']
                    if render_result.get('skipped'):
                        print(f"  Render: Skipped (template already exists)")
                    else:
                        print(f"  Render: {render_result.get('success', 'N/A')}")
                
                if 'ism' in results:
                    ism_result = results['ism']
                    print(f"  ISM: {ism_result.get('success', 'N/A')}")
                    if ism_result.get('success'):
                        detections = ism_result.get('detections', {})
                        num_detections = len(detections.get('boxes', [])) if isinstance(detections, dict) else 0
                        print(f"    Detections: {num_detections} objects")
                        inference_time = ism_result.get('inference_time', 0)
                        print(f"    Time: {inference_time:.2f}s")
                
                if 'pem' in results:
                    pem_result = results['pem']
                    print(f"  PEM: {pem_result.get('success', 'N/A')}")
                    if pem_result.get('success'):
                        num_poses = pem_result.get('num_detections', 0)
                        print(f"    Poses estimated: {num_poses}")
                        inference_time = pem_result.get('inference_time', 0)
                        print(f"    Time: {inference_time:.2f}s")
            
            print(f"\n[7] Output 디렉토리:")
            # output_dir은 results 안에 있을 수도 있고, 최상위에 있을 수도 있음
            output_dir = None
            if 'output_dir' in result:
                output_dir = result['output_dir']
            elif 'results' in result and isinstance(result['results'], dict) and 'output_dir' in result['results']:
                output_dir = result['results']['output_dir']
            
            if output_dir:
                print(f"  {output_dir}")
            else:
                print(f"  (자동 생성됨)")
        else:
            print(f"  Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n[ERROR] 타임아웃 발생 (20분 초과)")
    except Exception as e:
        print(f"\n[ERROR] Exception: {str(e)}")
    
    print("\n" + "=" * 80)
    print("테스트 완료")
    print("=" * 80)

if __name__ == "__main__":
    test_full_pipeline()

