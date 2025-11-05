#!/usr/bin/env python3
"""실제 이미지로 테스트"""
import requests

# LFS 문제로 포인터 파일만 있으므로, 사전 생성된 실제 테스트 데이터 사용
print("=" * 70)
print("가상 이미지로 파이프라인 테스트")
print("=" * 70)

# 빈 문자열로 테스트 (실제로는 이미지 데이터가 있어야 함)
# 이 테스트는 파이프라인이 호출되는지 확인하는 용도
data = {
    "class_name": "test",
    "object_name": "obj_000005",
    "input_images": {
        "rgb_path": "static/test/rgb.png",
        "depth_path": "static/test/depth.png",
        "camera_path": "static/test/camera.json"
    }
}

response = requests.post(
    "http://localhost:8001/api/v1/workflow/full-pipeline",
    json=data,
    timeout=300
)

result = response.json()
print("\n응답:")
print(f"  성공: {result.get('success')}")
print(f"  출력: {result.get('output_dir')}")

if 'results' in result and 'results' in result['results']:
    for step, step_result in result['results']['results'].items():
        print(f"\n  {step}:")
        if 'skipped' in step_result:
            print(f"    스킵됨")
        elif 'success' in step_result:
            print(f"    성공: {step_result['success']}")
            if 'error' in step_result:
                print(f"    에러: {step_result['error']}")
            elif 'error_message' in step_result:
                print(f"    에러: {step_result['error_message']}")

