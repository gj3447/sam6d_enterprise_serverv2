#!/usr/bin/env python3
import sys
from pathlib import Path
import requests
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8001"

# 간단한 테스트
print("=" * 60)
print("간단 테스트")

# 1. 서버 상태
print("\n[1] 서버 상태")
response = requests.get(f"{BASE_URL}/api/v1/servers/status")
status = response.json()
print(f"전체: {status['overall_status']}")
for name, s in status['servers'].items():
    print(f"  {name}: {s['status']}")

# 2. 객체 조회
print("\n[2] 객체 조회")
response = requests.get(f"{BASE_URL}/api/v1/objects/test/obj_000005")
obj = response.json()
print(f"객체: {obj['name']}, 상태: {obj['status']}")

# 3. 파이프라인 실행
print("\n[3] 파이프라인 실행")
data = {
    "class_name": "test",
    "object_name": "obj_000005",
    "input_images": {
        "rgb_path": "static/test/rgb.png",
        "depth_path": "static/test/depth.png",
        "camera_path": "static/test/camera.json"
    }
}

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/workflow/full-pipeline",
        json=data,
        timeout=300
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print("성공!")
        print(f"출력: {result.get('output_dir')}")
    else:
        print("실패")
        print(f"에러: {result.get('error')}")
        print(f"응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
except Exception as e:
    print(f"예외 발생: {e}")

print("\n" + "=" * 60)

