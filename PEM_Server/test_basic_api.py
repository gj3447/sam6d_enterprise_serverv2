#!/usr/bin/env python3
"""
PEM Server 간단한 테스트 스크립트
"""

import requests
import json

def test_basic_endpoints():
    """기본 엔드포인트 테스트"""
    base_url = "http://localhost:8003"
    
    print("=== PEM Server 기본 테스트 ===")
    
    # 1. 루트 엔드포인트
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ 루트 엔드포인트: {response.status_code}")
        print(f"   응답: {response.json()}")
    except Exception as e:
        print(f"❌ 루트 엔드포인트 실패: {e}")
    
    # 2. 헬스 체크
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"✅ 헬스 체크: {response.status_code}")
        data = response.json()
        print(f"   모델 로드됨: {data['model']['loaded']}")
        print(f"   디바이스: {data['model']['device']}")
    except Exception as e:
        print(f"❌ 헬스 체크 실패: {e}")
    
    # 3. 모델 상태
    try:
        response = requests.get(f"{base_url}/api/v1/model/status")
        print(f"✅ 모델 상태: {response.status_code}")
        data = response.json()
        print(f"   로드됨: {data['loaded']}")
        print(f"   디바이스: {data['device']}")
        print(f"   파라미터: {data['parameters']:,}")
    except Exception as e:
        print(f"❌ 모델 상태 실패: {e}")
    
    # 4. 포즈 추정 상태
    try:
        response = requests.get(f"{base_url}/api/v1/pose-estimation/status")
        print(f"✅ 포즈 추정 상태: {response.status_code}")
        data = response.json()
        print(f"   서비스 상태: {data['status']}")
        print(f"   모델 로드됨: {data['model_loaded']}")
    except Exception as e:
        print(f"❌ 포즈 추정 상태 실패: {e}")
    
    # 5. 샘플 데이터
    try:
        # 기본 경로로 샘플 데이터 요청
        params = {"sample_dir": "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example"}
        response = requests.get(f"{base_url}/api/v1/pose-estimation/sample", params=params)
        print(f"✅ 샘플 데이터: {response.status_code}")
        data = response.json()
        print(f"   파일 존재 여부:")
        for file_type, exists in data['file_exists'].items():
            status = "✅" if exists else "❌"
            print(f"     {status} {file_type}: {exists}")
    except Exception as e:
        print(f"❌ 샘플 데이터 실패: {e}")

if __name__ == "__main__":
    test_basic_endpoints()
