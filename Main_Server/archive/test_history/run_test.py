#!/usr/bin/env python3
"""간단한 파이프라인 테스트"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def test():
    try:
        from Main_Server.services.workflow_service import get_workflow_service
        from Main_Server.services.scanner import get_scanner
    
        print("=== Main Server 파이프라인 테스트 ===\n")
        
        # 1. 객체 확인
        scanner = get_scanner()
        obj = scanner.scan_object("test", "obj_000005")
        
        if not obj:
            print("ERROR: 테스트 객체를 찾을 수 없습니다.")
            return
        
        print(f"✅ 객체 확인: {obj['name']}")
        print(f"   템플릿 존재: {obj['has_template']}")
        print()
        
        # 2. 파이프라인 실행
        print("파이프라인 실행 중...")
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
        
        print(f"\n결과: {'성공' if result.get('success') else '실패'}")
        
        if result.get('success'):
            print(f"출력 디렉토리: {result.get('output_dir')}")
            print(f"\n✅ 테스트 성공!")
        else:
            print(f"에러: {result.get('error')}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())

