#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def check():
    from Main_Server.services.workflow_service import get_workflow_service
    from Main_Server.services.scanner import get_scanner
    
    # 1. Scanner 확인
    scanner = get_scanner()
    obj = scanner.scan_object("test", "obj_000005")
    print(f"템플릿: {obj['has_template']}")
    print(f"파일 수: {obj['template_files']}")
    
    # 2. 파이프라인 실행
    workflow = get_workflow_service()
    result = await workflow.execute_full_pipeline(
        class_name="test",
        object_name="obj_000005",
        input_images={
            "rgb_path": "static/test/rgb.png",
            "depth_path": "static/test/depth.png",
            "camera_path": "static/test/camera.json"
        }
    )
    
    # 3. 결과 확인
    print(f"\n성공: {result.get('success')}")
    print(f"출력: {result.get('output_dir')}")
    
    output_path = Path(result.get('output_dir', ''))
    if output_path.exists():
        files = list(output_path.rglob("*"))
        for f in files:
            if f.is_file():
                print(f"파일: {f.relative_to(output_path.parent)}")

if __name__ == "__main__":
    asyncio.run(check())

