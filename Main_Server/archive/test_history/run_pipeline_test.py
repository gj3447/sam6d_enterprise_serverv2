#!/usr/bin/env python3
"""전체 파이프라인 테스트 - 직접 실행"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Main_Server.services.workflow_service import get_workflow_service
from Main_Server.services.scanner import get_scanner
from Main_Server.services.server_monitor import get_monitor


async def test_full_pipeline():
    """전체 파이프라인 테스트"""
    print("=" * 70)
    print("전체 파이프라인 테스트")
    print("=" * 70)
    
    # 1. 서버 상태 확인
    print("\n[1단계] 서버 상태 확인")
    print("-" * 70)
    monitor = get_monitor()
    status_result = await monitor.check_all_servers()
    
    print(f"전체 상태: {status_result['overall_status']}")
    healthy = []
    unhealthy = []
    for name, server_status in status_result['servers'].items():
        if server_status['status'] == 'healthy':
            healthy.append(name)
            print(f"  [OK] {name.upper()}: {server_status['status']}")
        else:
            unhealthy.append(name)
            print(f"  [NO] {name.upper()}: {server_status['status']}")
            if server_status.get('error_message'):
                print(f"      에러: {server_status['error_message']}")
    
    if len(unhealthy) > 0:
        print(f"\n경고: {len(unhealthy)}개 서버가 정상 작동하지 않습니다!")
        print("계속 진행하시겠습니까? (Y/N)")
        # 자동으로 계속 진행
    
    # 2. 객체 상태 확인
    print("\n[2단계] Mesh 템플릿 상태 확인")
    print("-" * 70)
    scanner = get_scanner()
    
    # test 클래스의 obj_000005 확인
    obj_info = scanner.scan_object("test", "obj_000005")
    if obj_info:
        print(f"객체: {obj_info['name']}")
        print(f"상태: {obj_info['status']}")
        print(f"템플릿 존재: {obj_info['has_template']}")
        if obj_info['has_template']:
            files = obj_info['template_files']
            print(f"템플릿 파일: mask={files['mask_count']}, rgb={files['rgb_count']}, xyz={files['xyz_count']}")
    else:
        print("ERROR: 객체를 찾을 수 없습니다!")
        return
    
    # 3. 파이프라인 실행
    print("\n[3단계] 전체 파이프라인 실행")
    print("-" * 70)
    print("실행 순서:")
    print("  1. 템플릿 확인 (이미 존재하면 스킵)")
    print("  2. ISM 서버로 객체 감지")
    print("  3. PEM 서버로 포즈 추정")
    print()
    
    workflow = get_workflow_service()
    
    try:
        result = await workflow.execute_full_pipeline(
            class_name="test",
            object_name="obj_000005",
            input_images={
                "rgb_path": "static/test/rgb.png",
                "depth_path": "static/test/depth.png",
                "camera_path": "static/test/camera.json"
            },
            output_dir=None  # 자동 생성
        )
        
        print("\n[4단계] 결과 확인")
        print("-" * 70)
        
        if result.get('success'):
            print("✅ 파이프라인 성공!")
            print(f"출력 디렉토리: {result.get('output_dir')}")
            
            # 결과 상세
            results = result.get('results', {})
            
            # Render 결과
            if 'render' in results:
                render_result = results['render']
                if render_result.get('skipped'):
                    print("  Render: 템플릿이 이미 존재하여 스킵됨")
                else:
                    print(f"  Render: {render_result.get('success', False)}")
            
            # ISM 결과
            if 'ism' in results:
                ism_result = results['ism']
                print(f"  ISM: {ism_result.get('success', False)}")
                if ism_result.get('success'):
                    print(f"    - 추론 시간: {ism_result.get('inference_time', 0):.3f}초")
                    detections = ism_result.get('detections', {})
                    if detections:
                        print(f"    - 감지된 객체: {len(detections.get('masks', []))}개")
            
            # PEM 결과
            if 'pem' in results:
                pem_result = results['pem']
                print(f"  PEM: {pem_result.get('success', False)}")
                if pem_result.get('success'):
                    print(f"    - 추론 시간: {pem_result.get('inference_time', 0):.3f}초")
                    print(f"    - 검출된 객체: {pem_result.get('num_detections', 0)}개")
        else:
            print("❌ 파이프라인 실패!")
            print(f"에러: {result.get('error')}")
            
            # 에러 상세
            results = result.get('results', {})
            for step, step_result in results.items():
                if isinstance(step_result, dict) and not step_result.get('success'):
                    print(f"  {step.upper()} 실패: {step_result.get('error')}")
        
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())

