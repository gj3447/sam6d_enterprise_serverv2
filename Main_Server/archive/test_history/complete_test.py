#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""전체 파이프라인 완전 테스트"""
import sys
from pathlib import Path
import requests
import json
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://localhost:8001"

def test_complete_pipeline():
    """전체 파이프라인: 템플릿 없으면 생성 → ISM → PEM"""
    print("=" * 70)
    print("전체 파이프라인 테스트")
    print("=" * 70)
    
    # 1. 서버 상태 확인
    print("\n[1단계] 서버 상태 확인")
    print("-" * 70)
    response = requests.get(f"{BASE_URL}/api/v1/servers/status")
    status = response.json()
    
    print(f"전체 상태: {status['overall_status']}")
    healthy = []
    unhealthy = []
    for name, server_status in status['servers'].items():
        if server_status['status'] == 'healthy':
            healthy.append(name)
            print(f"  [OK] {name.upper()}: {server_status['status']}")
        else:
            unhealthy.append(name)
            print(f"  [NO] {name.upper()}: {server_status['status']} - {server_status.get('error_message')}")
    
    if len(unhealthy) > 0:
        print(f"\n경고: {len(unhealthy)}개 서버가 정상 작동하지 않습니다!")
    
    # 2. 객체 상태 확인
    print("\n[2단계] Mesh 템플릿 상태 확인")
    print("-" * 70)
    response = requests.get(f"{BASE_URL}/api/v1/objects/test/obj_000005")
    obj_info = response.json()
    
    print(f"객체: {obj_info['name']}")
    print(f"상태: {obj_info['status']}")
    print(f"템플릿 존재: {obj_info['template_info']['has_template']}")
    
    if obj_info['template_info']['has_template']:
        files = obj_info['template_info']['files']
        print(f"템플릿 파일: mask={files['mask_count']}, rgb={files['rgb_count']}, xyz={files['xyz_count']}")
    
    # 3. 파이프라인 실행
    print("\n[3단계] 전체 파이프라인 실행")
    print("-" * 70)
    print("실행 순서:")
    print("  1. 템플릿 생성 (Render) - 템플릿이 없으면")
    print("  2. 객체 감지 (ISM)")
    print("  3. 포즈 추정 (PEM)")
    
    # 시간 기반 출력 폴더
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    expected_output = project_root / "static" / "output" / timestamp
    print(f"\n예상 출력 폴더: {expected_output}")
    
    request_data = {
        "class_name": "test",
        "object_name": "obj_000005",
        "input_images": {
            "rgb_path": "static/test/rgb.png",
            "depth_path": "static/test/depth.png",
            "camera_path": "static/test/camera.json"
        }
    }
    
    print(f"\n파이프라인 시작...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/workflow/full-pipeline",
            json=request_data,
            timeout=1800  # 30분
        )
        
        result = response.json()
        
        print(f"\n실행 결과:")
        print(f"  성공: {result.get('success')}")
        print(f"  출력 디렉토리: {result.get('output_dir')}")
        
        if result.get('results'):
            for step_name, step_result in result['results'].items():
                print(f"\n  [{step_name.upper()}]")
                if isinstance(step_result, dict):
                    if step_result.get('success'):
                        print(f"    성공: {step_result.get('success')}")
                        if step_result.get('inference_time'):
                            print(f"    추론 시간: {step_result['inference_time']:.3f}초")
                    elif step_result.get('skipped'):
                        print(f"    스킵됨: 템플릿이 이미 존재함")
                    else:
                        print(f"    실패: {step_result.get('error', 'Unknown error')}")
        
        # 실제 파일 확인
        if result.get('output_dir'):
            output_path = Path(result['output_dir'])
            print(f"\n[4단계] 생성된 파일 확인")
            print("-" * 70)
            if output_path.exists():
                print(f"출력 폴더: {output_path}")
                for item in sorted(output_path.rglob("*")):
                    if item.is_file():
                        rel_path = item.relative_to(output_path)
                        print(f"  ✓ {rel_path}")
            else:
                print(f"출력 폴더가 생성되지 않았습니다: {output_path}")
        
    except requests.exceptions.Timeout:
        print("\n[TIMEOUT] 30분 내에 완료되지 않았습니다")
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
    
    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)

if __name__ == "__main__":
    test_complete_pipeline()

