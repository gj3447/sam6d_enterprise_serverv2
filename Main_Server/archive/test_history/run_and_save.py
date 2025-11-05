#!/usr/bin/env python3
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

async def main():
    result_text = []
    result_text.append("=" * 70)
    result_text.append("Main Server 파이프라인 실행 테스트")
    result_text.append(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    result_text.append("=" * 70)
    
    try:
        from Main_Server.services.workflow_service import get_workflow_service
        from Main_Server.services.scanner import get_scanner
        
        # Scanner 확인
        scanner = get_scanner()
        obj = scanner.scan_object("test", "obj_000005")
        
        result_text.append(f"\n템플릿: {obj['has_template']}")
        result_text.append(f"파일: {obj['template_files']}")
        
        # 파이프라인 실행
        result_text.append("\n파이프라인 실행 중...")
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
        
        result_text.append(f"\n결과:")
        result_text.append(f"  성공: {result.get('success')}")
        result_text.append(f"  출력: {result.get('output_dir')}")
        
        if not result.get('success'):
            result_text.append(f"  에러: {result.get('error')}")
        
        # 결과 파일 확인
        output_path = Path(result.get('output_dir', ''))
        if output_path.exists():
            files = list(output_path.rglob("*"))
            file_list = [f for f in files if f.is_file()]
            result_text.append(f"\n생성된 파일: {len(file_list)}개")
            for f in file_list[:10]:
                result_text.append(f"  {f.relative_to(output_path.parent)} ({f.stat().st_size} bytes)")
        else:
            result_text.append("\n⚠️ 출력 디렉토리가 존재하지 않습니다!")
            
    except Exception as e:
        result_text.append(f"\n오류 발생: {e}")
        import traceback
        result_text.append(traceback.format_exc())
    
    # 결과 저장
    output_text = "\n".join(result_text)
    
    # 콘솔에 출력
    print(output_text)
    
    # 파일에 저장
    with open("test_run_result.txt", "w", encoding="utf-8") as f:
        f.write(output_text)

if __name__ == "__main__":
    asyncio.run(main())

