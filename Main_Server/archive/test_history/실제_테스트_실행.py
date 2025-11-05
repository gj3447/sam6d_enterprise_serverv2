#!/usr/bin/env python3
"""실제 파이프라인 테스트 실행"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def test():
    print("=" * 70)
    print("Main Server 전체 파이프라인 테스트")
    print("=" * 70)
    
    from Main_Server.services.workflow_service import get_workflow_service
    
    workflow = get_workflow_service()
    
    print("\n파이프라인 실행 중...")
    
    result = await workflow.execute_full_pipeline(
        class_name="test",
        object_name="obj_000005",
        input_images={
            "rgb_path": "static/test/rgb.png",
            "depth_path": "static/test/depth.png",
            "camera_path": "static/test/camera.json"
        }
    )
    
    print("\n" + "=" * 70)
    print("결과:")
    print(f"  성공: {result.get('success')}")
    print(f"  출력 디렉토리: {result.get('output_dir')}")
    
    if not result.get('success'):
        print(f"  에러: {result.get('error')}")
    
    # 결과 확인
    output_dir = Path(result.get('output_dir', ''))
    if output_dir.exists():
        print(f"\n생성된 파일:")
        for file in output_dir.rglob("*"):
            if file.is_file():
                print(f"  {file.relative_to(output_dir.parent)} ({file.stat().st_size} bytes)")
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test())

