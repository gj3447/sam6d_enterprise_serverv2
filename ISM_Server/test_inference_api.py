#!/usr/bin/env python3
"""
ISM Server 추론 API 테스트 스크립트
Example 데이터를 사용하여 추론 API를 테스트합니다.
"""

import requests
import json
import base64
import os
import time
from pathlib import Path

# 서버 설정
SERVER_URL = "http://localhost:8002"
API_ENDPOINT = f"{SERVER_URL}/api/v1/inference"
SAMPLE_ENDPOINT = f"{SERVER_URL}/test/sample"
STATUS_ENDPOINT = f"{SERVER_URL}/api/v1/status"

def test_server_status():
    """서버 상태 확인"""
    print("[INFO] 서버 상태 확인 중...")
    try:
        response = requests.get(STATUS_ENDPOINT, timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"[SUCCESS] 서버 상태: {status}")
            return True
        else:
            print(f"[ERROR] 서버 상태 확인 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] 서버 연결 실패: {e}")
        return False

def get_sample_data():
    """샘플 데이터 가져오기"""
    print("[INFO] 샘플 데이터 가져오는 중...")
    try:
        response = requests.get(SAMPLE_ENDPOINT, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] 샘플 데이터 가져오기 성공")
            print(f"   - RGB 이미지 크기: {len(data['rgb_image'])} bytes")
            print(f"   - Depth 이미지 크기: {len(data['depth_image'])} bytes")
            print(f"   - 카메라 파라미터: {data['cam_params']}")
            return data
        else:
            print(f"[ERROR] 샘플 데이터 가져오기 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] 샘플 데이터 요청 실패: {e}")
        return None

def test_inference_api(sample_data):
    """추론 API 테스트"""
    print("[INFO] 추론 API 테스트 시작...")
    
    # 추론 요청 데이터 준비 (클라이언트가 모든 경로 제공)
    inference_request = {
        "rgb_image": sample_data["rgb_image"],
        "depth_image": sample_data["depth_image"],
        "cam_params": sample_data["cam_params"],
        "template_dir": "../SAM-6D/SAM-6D/Data/Example/outputs/templates",
        "cad_path": "../SAM-6D/SAM-6D/Data/Example/obj_000005.ply",
        "output_dir": "../SAM-6D/SAM-6D/Data/Example/outputs"  # 결과 저장 경로 추가
    }
    
    print(f"[INFO] 추론 요청 전송 중...")
    print(f"   - RGB 이미지: {len(inference_request['rgb_image'])} bytes")
    print(f"   - Depth 이미지: {len(inference_request['depth_image'])} bytes")
    print(f"   - 카메라 파라미터: {inference_request['cam_params']}")
    print(f"   - 템플릿 디렉토리: {inference_request['template_dir']}")
    print(f"   - CAD 모델 경로: {inference_request['cad_path']}")
    print(f"   - 출력 디렉토리: {inference_request['output_dir']}")
    
    try:
        start_time = time.time()
        response = requests.post(
            API_ENDPOINT,
            json=inference_request,
            headers={"Content-Type": "application/json"},
            timeout=60  # 추론 시간이 오래 걸릴 수 있음
        )
        end_time = time.time()
        
        print(f"[INFO] 요청 처리 시간: {end_time - start_time:.3f}초")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] 추론 성공!")
            print(f"   - 성공 여부: {result['success']}")
            print(f"   - 추론 시간: {result['inference_time']:.3f}초")
            print(f"   - 감지 결과 수: {len(result['detections'])}")
            print(f"   - 사용된 템플릿 디렉토리: {result['template_dir_used']}")
            print(f"   - 사용된 CAD 경로: {result['cad_path_used']}")
            print(f"   - 사용된 출력 디렉토리: {result['output_dir_used']}")
            
            if result['error_message']:
                print(f"   - 에러 메시지: {result['error_message']}")
            
            return result
        else:
            print(f"[ERROR] 추론 실패: HTTP {response.status_code}")
            print(f"   응답 내용: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 추론 요청 실패: {e}")
        return None

def test_multiple_requests(sample_data, num_requests=3):
    """여러 번의 추론 요청 테스트"""
    print(f"[INFO] {num_requests}번의 연속 추론 요청 테스트...")
    
    results = []
    for i in range(num_requests):
        print(f"\n--- 요청 {i+1}/{num_requests} ---")
        result = test_inference_api(sample_data)
        results.append(result)
        
        if i < num_requests - 1:  # 마지막 요청이 아니면 잠시 대기
            print("[INFO] 2초 대기 중...")
            time.sleep(2)
    
    # 결과 요약
    successful_requests = sum(1 for r in results if r and r.get('success', False))
    print(f"\n[INFO] 테스트 결과 요약:")
    print(f"   - 총 요청 수: {num_requests}")
    print(f"   - 성공한 요청 수: {successful_requests}")
    print(f"   - 실패한 요청 수: {num_requests - successful_requests}")
    
    if successful_requests > 0:
        avg_inference_time = sum(r['inference_time'] for r in results if r and r.get('success', False)) / successful_requests
        print(f"   - 평균 추론 시간: {avg_inference_time:.3f}초")
    
    return results

def main():
    """메인 테스트 함수"""
    print("[INFO] ISM Server 추론 API 테스트 시작")
    print("=" * 50)
    
    # 1. 서버 상태 확인
    if not test_server_status():
        print("[ERROR] 서버가 실행되지 않았습니다. 테스트를 중단합니다.")
        return
    
    print("\n" + "=" * 50)
    
    # 2. 샘플 데이터 가져오기
    sample_data = get_sample_data()
    if not sample_data:
        print("[ERROR] 샘플 데이터를 가져올 수 없습니다. 테스트를 중단합니다.")
        return
    
    print("\n" + "=" * 50)
    
    # 3. 단일 추론 테스트
    result = test_inference_api(sample_data)
    if not result:
        print("[ERROR] 추론 테스트가 실패했습니다.")
        return
    
    print("\n" + "=" * 50)
    
    # 4. 여러 번의 추론 테스트
    test_multiple_requests(sample_data, num_requests=3)
    
    print("\n" + "=" * 50)
    print("[SUCCESS] 모든 테스트가 완료되었습니다!")

if __name__ == "__main__":
    main()
