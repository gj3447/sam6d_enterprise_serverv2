#!/usr/bin/env python3
"""파이프라인 실행 테스트 - 로그 기록"""
import sys
import traceback
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

log_messages = []

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    log_messages.append(log_msg)
    print(log_msg)

try:
    log("테스트 시작")
    
    # 1. Scanner 테스트
    log("Scanner import 시도...")
    from Main_Server.services.scanner import get_scanner
    s = get_scanner()
    obj = s.scan_object("test", "obj_000005")
    log(f"Scanner OK: 템플릿={obj['has_template']}, 파일={obj['template_files']}")
    
    # 2. Workflow 테스트  
    log("Workflow import 시도...")
    from Main_Server.services.workflow_service import get_workflow_service
    w = get_workflow_service()
    log("Workflow OK")
    
    # 3. 파이프라인 실행
    log("파이프라인 실행 시작...")
    import asyncio
    r = asyncio.run(w.execute_full_pipeline(
        "test", "obj_000005", {
            "rgb_path": "static/test/rgb.png",
            "depth_path": "static/test/depth.png",
            "camera_path": "static/test/camera.json"
        }
    ))
    log(f"파이프라인 완료: success={r.get('success')}")
    log(f"Output: {r.get('output_dir')}")
    
except Exception as e:
    log(f"에러: {e}")
    log(traceback.format_exc())

# 파일에 저장
with open("test_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log_messages))

print(f"\n로그 저장됨: test_log.txt")

