#!/usr/bin/env python3
"""
YCB 오브젝트 간단 테스트 스크립트
Main_Server API를 사용하여 변환된 YCB 메시로 테스트
"""
import sys
from pathlib import Path
import requests
import json

BASE_URL = "http://localhost:8001"

def test_ycb_object(object_name="obj_000002"):
    """YCB 오브젝트 테스트"""
    
    print("=" * 70)
    print(f"YCB 오브젝트 테스트: {object_name}")
    print("=" * 70)
    
    # 1. 객체 정보 확인
    print(f"\n[1] 객체 정보 확인...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/objects/ycb/{object_name}")
        if response.status_code == 200:
            obj_info = response.json()
            print(f"  [OK] CAD 파일: {obj_info.get('cad_file')}")
            print(f"  [OK] 템플릿 존재: {obj_info.get('has_template')}")
            print(f"  [OK] 상태: {obj_info.get('status')}")
            if obj_info.get('has_template'):
                template_files = obj_info.get('template_files', {})
                print(f"  [OK] 템플릿 파일 수: {template_files.get('total_count', 0)}")
            else:
                print(f"  [WARN] 템플릿이 없습니다. 템플릿 생성이 필요합니다.")
        else:
            print(f"  [ERROR] 객체를 찾을 수 없습니다: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] 에러: {e}")
        return False
    
    # 2. 서버 상태 확인
    print(f"\n[2] 서버 상태 확인...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/servers/status")
        if response.status_code == 200:
            status = response.json()
            print(f"  전체 상태: {status['overall_status']}")
            print(f"  정상 서버: {status['healthy_servers']}/{status['total_servers']}")
            for name, server_status in status['servers'].items():
                mark = "[OK]" if server_status['status'] == 'healthy' else "[FAIL]"
                print(f"  {mark} {name.upper()}: {server_status['status']}")
        else:
            print(f"  [ERROR] 서버 상태 확인 실패: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] 에러: {e}")
    
    # 3. YCB 클래스 전체 목록 확인
    print(f"\n[3] YCB 클래스 전체 목록 확인...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/objects/classes/ycb")
        if response.status_code == 200:
            ycb_data = response.json()
            objects = ycb_data.get('objects', [])
            print(f"  총 YCB 객체 수: {len(objects)}")
            
            # 템플릿이 있는 객체들
            with_template = [obj for obj in objects if obj.get('has_template')]
            print(f"  템플릿 있는 객체: {len(with_template)}")
            
            # 처음 10개 객체 출력
            print(f"\n  처음 10개 객체:")
            for obj in objects[:10]:
                template_mark = "[OK]" if obj.get('has_template') else "[NO]"
                print(f"    {template_mark} {obj.get('name')}: {obj.get('status')}")
        else:
            print(f"  [ERROR] 목록 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] 에러: {e}")
    
    print(f"\n{'='*70}")
    print("테스트 완료!")
    print(f"{'='*70}")
    
    return True

if __name__ == "__main__":
    # 커맨드라인 인자로 객체 이름 지정 가능
    object_name = sys.argv[1] if len(sys.argv) > 1 else "obj_000002"
    success = test_ycb_object(object_name)
    sys.exit(0 if success else 1)

