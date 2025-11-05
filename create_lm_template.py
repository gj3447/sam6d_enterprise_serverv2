#!/usr/bin/env python3
"""
LM 클래스 객체 템플릿 생성
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def main():
    # 1. LM 클래스 객체 확인
    print("=" * 60)
    print("LM 클래스 객체 확인")
    print("=" * 60)
    
    r = requests.get(f"{BASE_URL}/api/v1/objects/classes/lm")
    data = r.json()
    
    print(f"Total Objects: {data['object_count']}")
    print(f"Objects with Templates: {data['template_count']}")
    
    # 템플릿이 없는 객체 찾기
    no_template = [obj for obj in data['objects'] if not obj['has_template']]
    
    if no_template:
        print(f"\nTemplates needed: {len(no_template)}")
        selected = no_template[0]
        print(f"Selected: {selected['name']}")
        
        # 2. 템플릿 생성 요청
        print("\n" + "=" * 60)
        print(f"템플릿 생성 요청: lm/{selected['name']}")
        print("=" * 60)
        
        request_data = {
            "class_name": "lm",
            "object_name": selected['name'],
            "force": False
        }
        
        print(f"Sending request to: {BASE_URL}/api/v1/workflow/render-template-single")
        print(f"Data: {json.dumps(request_data, indent=2)}")
        
        r = requests.post(
            f"{BASE_URL}/api/v1/workflow/render-template-single",
            json=request_data,
            timeout=3600
        )
        
        print(f"\nResponse Status: {r.status_code}")
        
        if r.status_code == 200:
            result = r.json()
            print(f"Success: {result['success']}")
            print(f"Message: {result['message']}")
            
            if 'results' in result:
                results = result['results']
                print(f"Total: {results.get('total', 0)}")
                print(f"Successful: {results.get('successful', 0)}")
        else:
            print(f"Error: {r.text}")
    else:
        print("\nAll objects already have templates!")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

