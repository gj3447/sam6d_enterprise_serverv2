#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""추론 파이프라인 테스트"""
import sys
from pathlib import Path
import requests
import json
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://localhost:8001"

def test_pipeline():
    """전체 파이프라인 테스트"""
    print("=" * 60)
    print("추론 파이프라인 테스트")
    print("=" * 60)
    
    # 서버 상태 확인
    print("\n[1] 서버 상태 확인...")
    response = requests.get(f"{BASE_URL}/api/v1/servers/status")
    status = response.json()
    
    print(f"  전체 상태: {status['overall_status']}")
    print(f"  정상 서버: {status['healthy_servers']}/{status['total_servers']}")
    
    for name, server_status in status['servers'].items():
        mark = "[OK]" if server_status['status'] == 'healthy' else "[NO]"
        print(f"  {mark} {name.upper()}: {server_status['status']}")
    
    # 파이프라인 실행
    print("\n[2] 파이프라인 실행...")
    
    # 현재 날짜-시간으로 폴더 생성 확인
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / "static" / "output" / timestamp
    print(f"  출력 디렉토리: {output_dir}")
    
    request_data = {
        "class_name": "test",
        "object_name": "obj_000005",
        "input_images": {
            "rgb_path": "static/test/rgb.png",
            "depth_path": "static/test/depth.png",
            "camera_path": "static/test/camera.json"
        }
        # output_dir은 비워서 자동 생성되도록 함
    }
    
    print(f"\n  요청 데이터:")
    print(f"    클래스: {request_data['class_name']}")
    print(f"    객체: {request_data['object_name']}")
    
    try:
        print(f"\n  파이프라인 실행 중...")
        response = requests.post(
            f"{BASE_URL}/api/v1/workflow/full-pipeline",
            json=request_data,
            timeout=1800  # 30분 타임아웃
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n  [SUCCESS] 파이프라인 실행 성공!")
            print(f"    출력 디렉토리: {result.get('output_dir')}")
            
            if result.get('results'):
                print(f"\n    각 단계 결과:")
                for step, step_result in result['results'].items():
                    print(f"      [{step.upper()}]")
                    if isinstance(step_result, dict):
                        if step_result.get('success'):
                            print(f"        성공: {step_result.get('success')}")
                        elif step_result.get('skipped'):
                            print(f"        스킵됨")
                        else:
                            print(f"        결과: {json.dumps(step_result, indent=8, ensure_ascii=False)}")
            
            # 실제 파일 확인
            if result.get('output_dir'):
                output_path = Path(result['output_dir'])
                if output_path.exists():
                    print(f"\n    생성된 디렉토리: {output_path}")
                    for item in output_path.iterdir():
                        if item.is_dir():
                            files = list(item.iterdir())
                            print(f"      {item.name}/: {len(files)}개 파일")
                        else:
                            print(f"      {item.name}")
        else:
            print(f"\n  [ERROR] 파이프라인 실행 실패: {response.status_code}")
            print(f"    응답: {response.text}")
    except requests.exceptions.Timeout:
        print(f"\n  [TIMEOUT] 요청 시간 초과 (30분)")
    except Exception as e:
        print(f"\n  [ERROR] 오류 발생: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_pipeline()

