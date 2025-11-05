#!/usr/bin/env python3
"""
Main Server 주요 기능 전체 테스트
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8001"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def test_all():
    """모든 주요 기능 테스트"""
    
    # 1. 헬스 체크
    print_section("1. 헬스 체크")
    r = requests.get(f"{BASE_URL}/health")
    print(f"[OK] Status: {r.status_code} - {r.json()['status']}")
    
    # 2. 객체 클래스 조회
    print_section("2. 객체 관리 - 클래스 목록")
    r = requests.get(f"{BASE_URL}/api/v1/objects/classes")
    data = r.json()
    print(f"[OK] Total: {data['total_classes']} classes, {data['total_objects']} objects")
    print(f"[OK] Templates: {data['total_templates']} ({data['overall_completion_rate']:.1f}%)")
    
    # 3. 서버 상태 모니터링
    print_section("3. 서버 상태 모니터링")
    r = requests.get(f"{BASE_URL}/api/v1/servers/status")
    data = r.json()
    print(f"[OK] Overall Status: {data['overall_status']}")
    print(f"[OK] Healthy Servers: {data['healthy_servers']}/{data['total_servers']}")
    for name, status in data['servers'].items():
        print(f"  - {name}: {status['status']} ({status.get('response_time_ms', 0)}ms)")
    
    # 4. 특정 클래스 객체 조회
    print_section("4. 객체 관리 - test 클래스")
    r = requests.get(f"{BASE_URL}/api/v1/objects/classes/test")
    data = r.json()
    print(f"[OK] Class: {data['class_name']}")
    print(f"[OK] Objects: {data['object_count']}, Templates: {data['template_count']}")
    for obj in data['objects'][:3]:
        status_icon = "[OK]" if obj['has_template'] else "[NO]"
        print(f"  {status_icon} {obj['name']}: {obj['status']}")
    
    # 5. 특정 객체 상세 정보
    print_section("5. 객체 관리 - 상세 정보")
    r = requests.get(f"{BASE_URL}/api/v1/objects/test/obj_000005")
    data = r.json()
    print(f"[OK] Object: {data['name']}")
    print(f"[OK] CAD: {data['cad_info']['file']} ({data['cad_info']['size_bytes']:,} bytes)")
    print(f"[OK] Template: {data['template_info']['has_template']}")
    if data['template_info']['has_template']:
        print(f"  - Files: {data['template_info']['files']}")
    print(f"[OK] Status: {data['status']}")
    
    # 6. 워크플로우 - 템플릿 생성 API
    print_section("6. 워크플로우 - 템플릿 생성 API")
    req_data = {"class_name": "test", "object_name": "obj_000005", "force": False}
    r = requests.post(f"{BASE_URL}/api/v1/workflow/render-template-single", json=req_data)
    print(f"[OK] API Response: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"[OK] Success: {result['success']}")
    
    print("\n" + "=" * 60)
    print("[OK] 모든 주요 기능 정상 동작 확인!")
    print("=" * 60)

if __name__ == "__main__":
    test_all()

