#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실제 추론 테스트"""
import sys
from pathlib import Path
import requests
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8001"

print("=" * 70)
print("실제 추론 실행 테스트")
print("=" * 70)

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

print(f"\n요청 보내는 중...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/workflow/full-pipeline",
        json=data,
        timeout=300
    )
    
    print(f"응답 코드: {response.status_code}")
    result = response.json()
    
    print(f"\n결과:")
    print(f"  성공: {result.get('success')}")
    print(f"  출력: {result.get('output_dir')}")
    print(f"  메시지: {result.get('message')}")
    
    if 'results' in result:
        results = result['results']
        print(f"\n  세부 결과:")
        
        if 'success' in results:
            print(f"    success: {results['success']}")
            print(f"    error: {results.get('error')}")
        
        if 'results' in results:
            for step, step_result in results['results'].items():
                print(f"\n    [{step.upper()}]")
                if isinstance(step_result, dict):
                    if 'skipped' in step_result:
                        print(f"      스킵됨")
                    elif 'success' in step_result:
                        print(f"      성공: {step_result['success']}")
                    elif 'error' in step_result:
                        print(f"      에러: {step_result['error']}")
                    else:
                        print(f"      {json.dumps(step_result, indent=8, ensure_ascii=False)}")
    
    # 파일 확인
    if result.get('output_dir'):
        output_path = Path(result['output_dir'])
        print(f"\n파일 확인: {output_path}")
        if output_path.exists():
            files = list(output_path.rglob("*"))
            print(f"  파일 개수: {len(files)}")
            for f in files[:10]:  # 처음 10개만
                if f.is_file():
                    print(f"  ✓ {f.relative_to(output_path)}")
        else:
            print(f"  폴더가 없습니다!")
    
except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

