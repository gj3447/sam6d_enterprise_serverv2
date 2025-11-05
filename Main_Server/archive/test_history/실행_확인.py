#!/usr/bin/env python3
import sys
import traceback
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("파이프라인 실행 확인")
print("=" * 70)

try:
    # 1. Scanner
    print("\n[1] Scanner 확인...")
    from Main_Server.services.scanner import get_scanner
    s = get_scanner()
    obj = s.scan_object("test", "obj_000005")
    print(f"OK: 템플릿={obj['has_template']}, 파일수={obj['template_files']}")
    
    # 2. Workflow
    print("\n[2] Workflow Service 확인...")
    from Main_Server.services.workflow_service import get_workflow_service
    w = get_workflow_service()
    print("OK")
    
    # 3. 실행
    print("\n[3] 파이프라인 실행...")
    result = asyncio.run(w.execute_full_pipeline(
        "test", "obj_000005", {
            "rgb_path": "static/test/rgb.png",
            "depth_path": "static/test/depth.png",
            "camera_path": "static/test/camera.json"
        }
    ))
    
    print(f"✓ 성공: {result.get('success')}")
    print(f"✓ 출력: {result.get('output_dir')}")
    
    if not result.get('success'):
        print(f"✗ 에러: {result.get('error')}")
    
except ImportError as e:
    print(f"\n✗ Import 에러: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"\n✗ 에러: {e}")
    traceback.print_exc()

print("\n" + "=" * 70)

