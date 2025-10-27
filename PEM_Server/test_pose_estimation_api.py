#!/usr/bin/env python3
"""
PEM Server API 테스트 예제
Example 폴더의 데이터를 사용한 포즈 추정 API 테스트
"""

import requests
import base64
import json
import os
import time
from pathlib import Path

# 서버 설정
SERVER_URL = "http://localhost:8003"
API_BASE = f"{SERVER_URL}/api/v1"

# Example 데이터 경로
EXAMPLE_DIR = "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example"
RGB_PATH = os.path.join(EXAMPLE_DIR, "rgb.png")
DEPTH_PATH = os.path.join(EXAMPLE_DIR, "depth.png")
CAD_PATH = os.path.join(EXAMPLE_DIR, "obj_000005.ply")
CAMERA_PATH = os.path.join(EXAMPLE_DIR, "camera.json")
TEMPLATE_DIR = os.path.join(EXAMPLE_DIR, "outputs", "templates")
ISM_RESULT_PATH = os.path.join(EXAMPLE_DIR, "outputs", "sam6d_results", "detection_ism.json")

def encode_image_to_base64(image_path):
    """이미지를 Base64로 인코딩"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Failed to encode image {image_path}: {e}")
        return None

def encode_depth_image_to_base64(depth_path):
    """깊이 이미지를 원본 데이터 타입으로 Base64 인코딩"""
    try:
        import numpy as np
        from PIL import Image
        
        # 깊이 이미지를 numpy 배열로 로딩
        depth_image = Image.open(depth_path)
        depth_array = np.array(depth_image).astype(np.float32)
        
        # numpy 배열을 bytes로 변환 후 Base64 인코딩
        depth_bytes = depth_array.tobytes()
        return base64.b64encode(depth_bytes).decode('utf-8'), depth_array.shape
    except Exception as e:
        print(f"Failed to encode depth image {depth_path}: {e}")
        return None, None

def load_json_file(file_path):
    """JSON 파일 로드"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load JSON file {file_path}: {e}")
        return None

def test_server_health():
    """서버 헬스 체크 테스트"""
    print("=== 서버 헬스 체크 테스트 ===")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 서버 상태: {data['status']}")
            print(f"✅ 모델 로드됨: {data['model']['loaded']}")
            print(f"✅ 디바이스: {data['model']['device']}")
            print(f"✅ 파라미터 수: {data['model']['parameters']:,}")
            return True
        else:
            print(f"❌ 서버 헬스 체크 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return False

def test_pose_estimation_status():
    """포즈 추정 서비스 상태 테스트"""
    print("\n=== 포즈 추정 서비스 상태 테스트 ===")
    try:
        response = requests.get(f"{API_BASE}/pose-estimation/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 서비스 상태: {data['status']}")
            print(f"✅ 모델 로드됨: {data['model_loaded']}")
            print(f"✅ 디바이스: {data['device']}")
            return True
        else:
            print(f"❌ 상태 확인 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 상태 확인 실패: {e}")
        return False

def test_sample_data():
    """샘플 데이터 테스트"""
    print("\n=== 샘플 데이터 테스트 ===")
    try:
        # 샘플 디렉토리 경로를 파라미터로 전달
        params = {
            "sample_dir": EXAMPLE_DIR
        }
        response = requests.get(f"{API_BASE}/pose-estimation/sample", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 샘플 데이터 로드 성공")
            print(f"✅ 파일 존재 여부:")
            for file_type, exists in data['file_exists'].items():
                status = "✅" if exists else "❌"
                print(f"   {status} {file_type}: {exists}")
            return data['sample_request']
        else:
            print(f"❌ 샘플 데이터 로드 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 샘플 데이터 로드 실패: {e}")
        return None

def test_pose_estimation_with_sample_data():
    """샘플 데이터를 사용한 포즈 추정 테스트"""
    print("\n=== 샘플 데이터 포즈 추정 테스트 ===")
    
    # 샘플 데이터 가져오기
    sample_data = test_sample_data()
    if not sample_data:
        print("❌ 샘플 데이터를 가져올 수 없습니다.")
        return False
    
    try:
        print("포즈 추정 요청 전송 중...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE}/pose-estimation",
            json=sample_data,
            timeout=120  # 2분 타임아웃
        )
        
        end_time = time.time()
        request_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 포즈 추정 성공!")
            print(f"✅ 요청 처리 시간: {request_time:.3f}s")
            print(f"✅ 추론 시간: {data['inference_time']:.3f}s")
            print(f"✅ 검출된 객체 수: {data['num_detections']}")
            print(f"✅ 포즈 점수: {data['pose_scores']}")
            
            if data['detections']:
                print(f"✅ 검출 결과:")
                for i, detection in enumerate(data['detections']):
                    print(f"   객체 {i+1}: 점수={detection['score']:.3f}")
            
            return True
        else:
            print(f"❌ 포즈 추정 실패: {response.status_code}")
            print(f"응답 내용: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 요청 타임아웃 (2분 초과)")
        return False
    except Exception as e:
        print(f"❌ 포즈 추정 실패: {e}")
        return False

def test_pose_estimation_with_custom_data():
    """커스텀 데이터를 사용한 포즈 추정 테스트"""
    print("\n=== 커스텀 데이터 포즈 추정 테스트 ===")
    
    # 파일 존재 여부 확인
    files_to_check = [RGB_PATH, DEPTH_PATH, CAD_PATH, CAMERA_PATH, ISM_RESULT_PATH]
    missing_files = []
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 다음 파일들이 없습니다: {missing_files}")
        return False
    
    # 이미지 인코딩
    print("이미지 인코딩 중...")
    rgb_base64 = encode_image_to_base64(RGB_PATH)
    depth_base64, depth_shape = encode_depth_image_to_base64(DEPTH_PATH)
    
    if not rgb_base64 or not depth_base64:
        print("❌ 이미지 인코딩 실패")
        return False
    
    # 카메라 파라미터 로드
    cam_params = load_json_file(CAMERA_PATH)
    if not cam_params:
        print("❌ 카메라 파라미터 로드 실패")
        return False
    
    # ISM 결과 로드
    ism_data = load_json_file(ISM_RESULT_PATH)
    if not ism_data:
        print("❌ ISM 결과 로드 실패")
        return False
    
    # 요청 데이터 구성
    request_data = {
        "rgb_image": rgb_base64,
        "depth_image": depth_base64,
        "cam_params": cam_params,
        "cad_path": CAD_PATH,
        "seg_data": ism_data,
        "template_dir": TEMPLATE_DIR,
                "det_score_thresh": 0.1,
        "output_dir": None
    }
    
    try:
        print("포즈 추정 요청 전송 중...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE}/pose-estimation",
            json=request_data,
            timeout=120  # 2분 타임아웃
        )
        
        end_time = time.time()
        request_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 포즈 추정 성공!")
            print(f"✅ 요청 처리 시간: {request_time:.3f}s")
            print(f"✅ 추론 시간: {data['inference_time']:.3f}s")
            print(f"✅ 검출된 객체 수: {data['num_detections']}")
            
            if data['pose_scores']:
                print(f"✅ 포즈 점수: {[f'{score:.3f}' for score in data['pose_scores']]}")
            
            if data['detections']:
                print(f"✅ 검출 결과:")
                for i, detection in enumerate(data['detections']):
                    print(f"   객체 {i+1}: 점수={detection['score']:.3f}")
                    if 'R' in detection:
                        print(f"     회전 행렬: {len(detection['R'])}x{len(detection['R'][0])}")
                    if 't' in detection:
                        print(f"     변위 벡터: {detection['t']}")
            
            return True
        else:
            print(f"❌ 포즈 추정 실패: {response.status_code}")
            print(f"응답 내용: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 요청 타임아웃 (2분 초과)")
        return False
    except Exception as e:
        print(f"❌ 포즈 추정 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 PEM Server API 테스트 시작")
    print(f"서버 URL: {SERVER_URL}")
    print(f"Example 데이터 경로: {EXAMPLE_DIR}")
    
    # 테스트 실행
    tests = [
        ("서버 헬스 체크", test_server_health),
        ("포즈 추정 서비스 상태", test_pose_estimation_status),
        ("샘플 데이터 포즈 추정", test_pose_estimation_with_sample_data),
        ("커스텀 데이터 포즈 추정", test_pose_estimation_with_custom_data),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"테스트: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print(f"\n{'='*50}")
    print("테스트 결과 요약")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 모든 테스트가 성공했습니다!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")

if __name__ == "__main__":
    main()
