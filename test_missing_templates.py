#!/usr/bin/env python3
"""
템플릿 없는 객체만 생성 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_missing_templates():
    """템플릿 없는 객체만 생성"""
    print("=" * 80)
    print("테스트: 템플릿 없는 객체만 생성 (POST /api/v1/workflow/render-templates-missing)")
    print("=" * 80)
    
    # lm 클래스의 템플릿 없는 객체만 생성
    request_data = {
        "class_name": "lm"
    }
    
    print(f"\n요청 데이터:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/workflow/render-templates-missing",
            json=request_data
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n결과:")
            print(f"  Success: {result['success']}")
            print(f"  Message: {result['message']}")
            
            if 'results' in result:
                results = result['results']
                print(f"  Total: {results.get('total', 'N/A')}")
                print(f"  Successful: {results.get('successful', 'N/A')}")
                
                if 'objects' in results and results['objects']:
                    print(f"\n처리된 객체 ({len(results['objects'])}개):")
                    for i, obj in enumerate(results['objects'][:5], 1):
                        print(f"    {i}. {obj['class_name']}/{obj['object_name']}")
                    if len(results['objects']) > 5:
                        print(f"    ... 외 {len(results['objects']) - 5}개")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    print("\n" + "=" * 80)

def test_all_templates_force():
    """모든 객체 템플릿 재생성 (force=True)"""
    print("=" * 80)
    print("테스트: 모든 객체 템플릿 재생성 (POST /api/v1/workflow/render-templates-all)")
    print("=" * 80)
    
    # 모든 객체 재생성 (force=False로 템플릿 없는 것만)
    request_data = {
        "class_name": "test",
        "force": False  # 템플릿 없는 것만
    }
    
    print(f"\n요청 데이터:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    print("\n주의: force=True로 설정하면 기존 템플릿도 재생성됩니다!")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/workflow/render-templates-all",
            json=request_data
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n결과:")
            print(f"  Success: {result['success']}")
            print(f"  Message: {result['message']}")
            
            if 'results' in result:
                results = result['results']
                print(f"  Total: {results.get('total', 'N/A')}")
                print(f"  Successful: {results.get('successful', 'N/A')}")
                print(f"  Force Regenerate: {results.get('force_regenerate', False)}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    # 1. 템플릿 없는 객체만 생성
    test_missing_templates()

