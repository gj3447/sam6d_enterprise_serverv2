import requests
import json

# API 요청
response = requests.post(
    "http://localhost:8001/api/v1/workflow/full-pipeline",
    json={
        "class_name": "test",
        "object_name": "obj_000005",
        "rgb_image": "test",
        "depth_image": "test",
        "cam_params": {"test": "data"}
    },
    timeout=10
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message', 'N/A')[:100]}...")
else:
    print(f"Error: {response.text[:200]}...")

