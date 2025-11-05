#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from Main_Server.services.workflow_service import get_workflow_service
from Main_Server.services.scanner import get_scanner
from Main_Server.services.server_monitor import get_monitor

async def main():
    print("=== Main Server 파이프라인 테스트 ===")
    
    # 1. 서버 상태
    print("\n1. 서버 상태 확인...")
    monitor = get_monitor()
    status = await monitor.check_all_servers()
    print(f"   전체: {status['overall_status']}")
    healthy = [n for n, s in status['servers'].items() if s['status'] == 'healthy']
    print(f"   정상 서버: {len(healthy)}/{len(status['servers'])} - {healthy}")
    
    if len(healthy) < 3:
        print("\n❌ 서버가 부족합니다. 테스트를 중단합니다.")
        return
    
    # 2. 객체 확인
    print("\n2. 객체 확인...")
    scanner = get_scanner()
    obj = scanner.scan_object("test", "obj_000005")
    if obj:
        print(f"   객체: {obj['name']}")
        print(f"   템플릿: {obj['has_template']}")
    
    # 3. 파이프라인 실행
    print("\n3. 파이프라인 실행...")
    workflow = get_workflow_service()
    
    try:
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
            print(f"출력: {result.get('output_dir')}")
        else:
            print(f"에러: {result.get('error')}")
            
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())

