#!/usr/bin/env python3
import sys
from pathlib import Path
import requests
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8001"

print("=" * 60)
print("파일 확인 테스트")

# 파이프라인 실행
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
    
    result = response.json()
    
    print(f"\n전체 응답:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get('success'):
        print("\n성공!")
        if result.get('output_dir'):
            print(f"출력: {result.get('output_dir')}")
            
            # 파일 목록 확인
            output_path = Path(result.get('output_dir'))
            if output_path.exists():
                files = list(output_path.rglob("*"))
                print(f"\n파일 수: {len([f for f in files if f.is_file()])}")
                for f in files:
                    if f.is_file():
                        print(f"  {f}")
    else:
        print("\n실패")
        print(f"에러: {result.get('error')}")
        
except Exception as e:
    print(f"예외 발생: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

