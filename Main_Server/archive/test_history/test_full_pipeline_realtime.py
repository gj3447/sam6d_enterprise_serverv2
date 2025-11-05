#!/usr/bin/env python3
"""실제 파이프라인 테스트 - 추론 실행"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Main_Server.services.workflow_service import get_workflow_service
from Main_Server.services.scanner import get_scanner
from Main_Server.services.server_monitor import get_monitor


async def test_full_pipeline():
    """전체 파이프라인 테스트 실행"""
    print("=" * 70)
    print("Main_Server 전체 파이프라인 추론 테스트")
    print("=" * 70)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 서버 상태 확인
    print("[1단계] 서버 상태 확인...")
    monitor = get_monitor()
    status_result = await monitor.check_all_servers()
    
    print(f"  전체 상태: {status_result['overall_status']}")
    for name, server_status in status_result['servers'].items():
        status_mark = "✅" if server_status['status'] == 'healthy' else "❌"
        print(f"  {status_mark} {name.upper()}: {server_status['status']}")
        if server_status['status'] != 'healthy':
            print(f"     에러: {server_status.get('error_message')}")
    
    # 서버가 모두 정상인지 확인
    healthy_count = status_result.get('healthy_servers', 0)
    if healthy_count < 3:
        print(f"\n❌ 경고: {3 - healthy_count}개 서버가 정상 작동하지 않습니다.")
        print("파이프라인 실행을 중단합니다.")
        return
    
    print("\n✅ 모든 서버가 정상 작동 중입니다.\n")
    
    # 2. 객체 상태 확인
    print("[2단계] 객체 상태 확인...")
    scanner = get_scanner()
    
    # test/obj_000005 확인
    obj_info = scanner.scan_object("test", "obj_000005")
    if not obj_info:
        print("❌ 테스트 객체를 찾을 수 없습니다!")
        return
    
    print(f"  객체: {obj_info['name']}")
    print(f"  CAD 파일: {obj_info['cad_file']}")
    print(f"  상태: {obj_info['status']}")
    print(f"  템플릿 존재: {obj_info['has_template']}")
    
    if obj_info['has_template']:
        files = obj_info['template_files']
        print(f"  템플릿 파일: mask={files['mask_count']}, rgb={files['rgb_count']}, xyz={files['xyz_count']}")
    else:
        print("  ⚠️ 템플릿이 없습니다. 파이프라인에서 생성됩니다.")
    
    print("\n✅ 객체 상태 확인 완료\n")
    
    # 3. 파이프라인 실행
    print("[3단계] 전체 파이프라인 실행...")
    print("  실행 순서:")
    print("    1. 템플릿 확인 (없으면 Render 서버로 생성)")
    print("    2. ISM 서버로 객체 감지")
    print("    3. PEM 서버로 포즈 추정")
    print("    4. 결과 반환")
    print()
    
    workflow = get_workflow_service()
    
    try:
        start_time = datetime.now()
        
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
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        print(f"\n⏱️  실행 시간: {elapsed:.2f}초\n")
        
        # 4. 결과 확인
        print("[4단계] 결과 확인...")
        print("-" * 70)
        
        if result.get('success'):
            print("✅ 파이프라인 성공!\n")
            
            print(f"📁 출력 디렉토리: {result.get('output_dir')}")
            print()
            
            # 각 단계 결과
            results = result.get('results', {})
            
            # Render 단계
            if 'render' in results:
                render_result = results['render']
                if render_result.get('skipped'):
                    print("✅ Render: 템플릿이 이미 존재하여 스킵됨")
                elif render_result.get('success'):
                    print("✅ Render: 템플릿 생성 완료")
                else:
                    print(f"❌ Render: 실패 - {render_result.get('error')}")
            print()
            
            # ISM 단계
            if 'ism' in results:
                ism_result = results['ism']
                if ism_result.get('success'):
                    print("✅ ISM: 객체 감지 성공")
                    print(f"   추론 시간: {ism_result.get('inference_time', 0):.3f}초")
                    detections = ism_result.get('detections', {})
                    if detections:
                        masks = detections.get('masks', [])
                        boxes = detections.get('boxes', [])
                        scores = detections.get('scores', [])
                        print(f"   감지된 객체: {len(masks)}개")
                        if scores:
                            print(f"   점수: {[f'{s:.3f}' for s in scores[:3]]}")
                else:
                    print(f"❌ ISM: 실패 - {ism_result.get('error')}")
            print()
            
            # PEM 단계
            if 'pem' in results:
                pem_result = results['pem']
                if pem_result.get('success'):
                    print("✅ PEM: 포즈 추정 성공")
                    print(f"   추론 시간: {pem_result.get('inference_time', 0):.3f}초")
                    print(f"   검출된 객체: {pem_result.get('num_detections', 0)}개")
                    poses = pem_result.get('poses', [])
                    if poses:
                        print(f"   포즈 수: {len(poses)}개")
                else:
                    print(f"❌ PEM: 실패 - {pem_result.get('error')}")
            
            print()
            print("=" * 70)
            print("테스트 완료 - 성공!")
            print("=" * 70)
            
            # 결과 파일 확인
            output_dir = Path(result.get('output_dir'))
            if output_dir.exists():
                print(f"\n📂 생성된 파일:")
                for file in sorted(output_dir.rglob("*")):
                    if file.is_file():
                        print(f"   {file.relative_to(output_dir)} ({file.stat().st_size} bytes)")
            
        else:
            print("❌ 파이프라인 실패!\n")
            print(f"에러: {result.get('error')}\n")
            
            # 에러 상세
            results = result.get('results', {})
            for step, step_result in results.items():
                if isinstance(step_result, dict) and not step_result.get('success'):
                    print(f"❌ {step.upper()}: {step_result.get('error')}")
            
            print()
            print("=" * 70)
            print("테스트 완료 - 실패")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}\n")
        import traceback
        traceback.print_exc()
        print()
        print("=" * 70)
        print("테스트 완료 - 오류 발생")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())

