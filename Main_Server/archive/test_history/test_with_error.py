#!/usr/bin/env python3
import sys
from pathlib import Path
import requests
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8001"

data = {
    "class_name": "test",
    "object_name": "obj_000005",
    "input_images": {
        "rgb_path": "static/test/rgb.png",
        "depth_path": "static/test/depth.png",
        "camera_path": "static/test/camera.json"
    }
}

print("파이프라인 실행 중...")
response = requests.post(f"{BASE_URL}/api/v1/workflow/full-pipeline", json=data, timeout=300)

result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))

if 'results' in result and 'results' in result['results']:
    for step, step_result in result['results']['results'].items():
        if 'error' in step_result:
            print(f"\n{step} 에러: {step_result['error']}")

