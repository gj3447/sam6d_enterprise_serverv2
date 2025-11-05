#!/usr/bin/env python3
"""파이프라인 실행 및 로그 기록"""
import asyncio
import sys
import traceback
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

# 결과 저장
log_file = Path("Main_Server/test_result.txt")

with open(log_file, "w", encoding="utf-8") as f:
    def log(msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {msg}\n"
        print(log_msg.strip())
        f.write(log_msg)
        f.flush()
    
    try:
        log("=" * 70)
        log("파이프라인 실행 테스트")
        log("=" * 70)
        
        # 1. Scanner
        log("\n[1] Scanner 확인...")
        from Main_Server.services.scanner import get_scanner
        s = get_scanner()
        obj = s.scan_object("test", "obj_000005")
        log(f"✓ 템플릿: {obj['has_template']}, 파일: {obj['template_files']}")
        
        # 2. Workflow
        log("\n[2] Workflow Service 확인...")
        from Main_Server.services.workflow_service import get_workflow_service
        w = get_workflow_service()
        log("✓ Workflow Service loaded")
        
        # 3. 실행
        log("\n[3] 파이프라인 실행 중...")
        result = asyncio.run(w.execute_full_pipeline(
            "test", "obj_000005", {
                "rgb_path": "static/test/rgb.png",
                "depth_path": "static/test/depth.png",
                "camera_path": "static/test/camera.json"
            }
        ))
        
        log(f"\n[결과] 성공: {result.get('success')}")
        log(f"출력: {result.get('output_dir')}")
        
        if not result.get('success'):
            log(f"에러: {result.get('error')}")
        
        # 4. 파일 확인
        log("\n[4] 출력 파일 확인...")
        output_dir = Path(result.get('output_dir', ''))
        if output_dir.exists():
            files = [f for f in output_dir.rglob("*") if f.is_file()]
            log(f"생성된 파일: {len(files)}개")
            for f in files[:10]:
                log(f"  {f.relative_to(output_dir.parent)}")
        else:
            log(f"⚠ 출력 디렉토리 없음: {output_dir}")
        
        log("\n" + "=" * 70)
        log("테스트 완료")
        log(f"로그: {log_file}")
        log("=" * 70)
        
    except Exception as e:
        log(f"\n✗ 에러: {e}")
        log(traceback.format_exc())

