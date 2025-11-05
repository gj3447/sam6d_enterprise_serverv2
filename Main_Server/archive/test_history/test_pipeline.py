#!/usr/bin/env python3
"""
파이프라인 테스트 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from services.workflow_service import get_workflow_service


async def test_full_pipeline():
    """전체 파이프라인 테스트"""
    
    workflow = get_workflow_service()
    
    # 테스트 데이터 경로
    input_images = {
        "rgb_path": "static/test/rgb.png",
        "depth_path": "static/test/depth.png",
        "camera_path": "static/test/camera.json"
    }
    
    # 파이프라인 실행
    result = await workflow.execute_full_pipeline(
        class_name="test",
        object_name="obj_000005",
        input_images=input_images,
        output_dir=None  # 자동 생성
    )
    
    print("\n" + "=" * 60)
    print("파이프라인 실행 결과")
    print("=" * 60)
    print(f"성공 여부: {result['success']}")
    print(f"출력 디렉토리: {result['output_dir']}")
    
    if result['success']:
        print("\n✅ 파이프라인 성공!")
        print("\n각 단계 결과:")
        for step, step_result in result['results'].items():
            print(f"\n[{step.upper()}]")
            if isinstance(step_result, dict):
                if step_result.get("skipped"):
                    print("  → 이미 존재하여 스킵됨")
                elif step_result.get("success"):
                    print("  → 성공")
                    if "inference_time" in step_result:
                        print(f"  → 추론 시간: {step_result['inference_time']:.3f}초")
                else:
                    print(f"  → 실패: {step_result.get('error', 'Unknown error')}")
    else:
        print("\n❌ 파이프라인 실패!")
        print(f"에러: {result.get('error', 'Unknown error')}")
    
    return result


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())

