#!/usr/bin/env python3
"""
Main Server 워크플로우 기능 테스트
"""
import requests
import json
import base64
from pathlib import Path

BASE_URL = "http://localhost:8001"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def test_full_pipeline():
    """전체 파이프라인 테스트 (Render → ISM → PEM)"""
    print_section("6. 전체 파이프라인 테스트")
    
    # 테스트 데이터 준비
    rgb_path = Path("static/test/rgb.png")
    depth_path = Path("static/test/depth.png")
    camera_path = Path("static/test/camera.json")
    
    if not all([rgb_path.exists(), depth_path.exists(), camera_path.exists()]):
        print("ERROR: Test files not found")
        return
    
    # 입력 이미지 인코딩
    with open(rgb_path, "rb") as f:
        rgb_b64 = base64.b64encode(f.read()).decode("utf-8")
    with open(depth_path, "rb") as f:
        depth_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    # 카메라 파라미터 로드
    with open(camera_path, "r", encoding="utf-8-sig") as f:
        cam_params = json.load(f)
    
    request_data = {
        "class_name": "test",
        "object_name": "obj_000005",
        "input_images": {
            "rgb_path": str(rgb_path),
            "depth_path": str(depth_path),
            "camera_path": str(camera_path)
        },
        "output_dir": "static/output/test_pipeline_main"
    }
    
    print("Request data prepared")
    print(f"  Class: {request_data['class_name']}")
    print(f"  Object: {request_data['object_name']}")
    print(f"  RGB Path: {request_data['input_images']['rgb_path']}")
    print(f"  Depth Path: {request_data['input_images']['depth_path']}")
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/v1/workflow/full-pipeline",
            json=request_data,
            timeout=600
        )
        
        print(f"\nStatus: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            print(f"Success: {result['success']}")
            if result['success']:
                print(f"Output Dir: {result['results']['output_dir']}")
            else:
                print(f"Error: {result.get('error_message', 'Unknown error')}")
        else:
            print(f"Error: {r.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def test_render_single_template():
    """단일 템플릿 생성 테스트"""
    print_section("7. 단일 템플릿 생성 테스트")
    
    request_data = {
        "class_name": "test",
        "object_name": "obj_000005",
        "force": False
    }
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/v1/workflow/render-template-single",
            json=request_data,
            timeout=300
        )
        
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            print(f"Success: {result['success']}")
            print(f"Message: {result['message']}")
        else:
            print(f"Error: {r.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def main():
    print("=" * 60)
    print("Main Server 워크플로우 기능 테스트")
    print("=" * 60)
    
    test_render_single_template()
    # test_full_pipeline()  # 너무 오래 걸릴 수 있으므로 선택적 실행
    
    print("\n" + "=" * 60)
    print("워크플로우 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()

