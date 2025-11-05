#!/usr/bin/env python3
"""파이프라인 실행 테스트"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def main():
    from Main_Server.services.workflow_service import get_workflow_service
    
    print("=" * 70)
    print("파이프라인 실행 테스트")
    print("=" * 70)
    
    workflow = get_workflow_service()
    
    print("\n실행 중...")
    result = await workflow.execute_full_pipeline(
        class_name="test",
        object_name="obj_000005",
        input_images={
            "rgb_path": "static/test/rgb.png",
            "depth_path": "static/test/depth.png",
            "camera_path": "static/test/camera.json"
        }
    )
    
    print("\n결과:")
    print(f"성공: {result.get('success')}")
    print(f"출력: {result.get('output_dir')}")
    
    if result.get('success'):
        output_dir = Path(result.get('output_dir'))
        if output_dir.exists():
            files = list(output_dir.rglob("*"))
            file_count = sum(1 for f in files if f.is_file())
            print(f"생성된 파일: {file_count}개")
            for f in files[:10]:
                if f.is_file():
                    print(f"  - {f.relative_to(output_dir.parent)}")
    else:
        print(f"에러: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())

