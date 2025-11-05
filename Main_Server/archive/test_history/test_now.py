#!/usr/bin/env python3
import asyncio
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

print("시작")

try:
    from Main_Server.services.scanner import get_scanner
    s = get_scanner()
    obj = s.scan_object("test", "obj_000005")
    print(f"Scanner: {obj['has_template']}, {obj['template_files']}")
    
    from Main_Server.services.workflow_service import get_workflow_service
    w = get_workflow_service()
    print("Workflow loaded")
    
    print("파이프라인 실행...")
    result = asyncio.run(w.execute_full_pipeline(
        "test", "obj_000005", {
            "rgb_path": "static/test/rgb.png",
            "depth_path": "static/test/depth.png",
            "camera_path": "static/test/camera.json"
        }
    ))
    
    print(f"결과: success={result.get('success')}")
    print(f"Output: {result.get('output_dir')}")
    
    if not result.get('success'):
        print(f"에러: {result.get('error')}")
    
except Exception as e:
    print(f"에러: {e}")
    traceback.print_exc()
    
print("끝")

