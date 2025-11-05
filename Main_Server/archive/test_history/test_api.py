#!/usr/bin/env python3
"""
Main_Server API 테스트 스크립트
"""
import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_health():
    """헬스 체크 테스트"""
    print("=" * 60)
    print("[TEST 1] 헬스 체크")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_objects_classes():
    """클래스 목록 조회 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 2] 클래스 목록 조회")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/objects/classes", timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"\n총 {data['total_classes']}개 클래스:")
        for cls in data['classes']:
            print(f"  [{cls['name']}]")
            print(f"    - 객체: {cls['object_count']}개")
            print(f"    - 템플릿: {cls['template_count']}개")
            print(f"    - 완성률: {cls['template_completion_rate']:.1f}%")
        
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_objects_class_detail():
    """특정 클래스 조회 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 3] 특정 클래스 상세 조회 (test)")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/objects/classes/test", timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"\n클래스: {data['class_name']}")
        print(f"객체 수: {data['object_count']}")
        print(f"템플릿 수: {data['template_count']}")
        
        if data['objects']:
            print(f"\n객체 목록:")
            for obj in data['objects']:
                status = "[OK]" if obj['has_template'] else "[NO]"
                print(f"  {status} {obj['name']}: {obj['status']}")
        
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_objects_detail():
    """특정 객체 상세 조회 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 4] 특정 객체 상세 조회 (test/obj_000005)")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/objects/test/obj_000005", timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"\n객체: {data['name']}")
        print(f"클래스: {data['class_name']}")
        print(f"상태: {data['status']}")
        print(f"\nCAD 정보:")
        print(f"  - 파일: {data['cad_info']['file']}")
        print(f"  - 경로: {data['cad_info']['path']}")
        print(f"  - 크기: {data['cad_info']['size_bytes']} bytes")
        
        print(f"\n템플릿 정보:")
        print(f"  - 존재: {data['template_info']['has_template']}")
        if data['template_info']['has_template']:
            files = data['template_info']['files']
            print(f"  - mask: {files.get('mask_count', 0)}개")
            print(f"  - rgb: {files.get('rgb_count', 0)}개")
            print(f"  - xyz: {files.get('xyz_count', 0)}개")
        
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_servers_status():
    """서버 상태 조회 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 5] 서버 상태 확인")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/servers/status", timeout=15)
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"\n전체 상태: {data['overall_status']}")
        print(f"정상 서버: {data['healthy_servers']}/{data['total_servers']}\n")
        
        for name, status in data['servers'].items():
            emoji = "[OK]" if status['status'] == 'healthy' else "[NO]"
            print(f"{emoji} {name.upper()}")
            print(f"   URL: {status['url']}")
            print(f"   상태: {status['status']}")
            if status['response_time_ms']:
                print(f"   응답 시간: {status['response_time_ms']}ms")
            if status['error_message']:
                print(f"   에러: {status['error_message']}")
        
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_objects_scan():
    """재스캔 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 6] 객체 디렉토리 재스캔")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/objects/scan",
            json={"force": True},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"\n성공: {data['success']}")
        print(f"통계:")
        stats = data['statistics']
        print(f"  - 클래스: {stats['total_classes']}개")
        print(f"  - 객체: {stats['total_objects']}개")
        print(f"  - 템플릿: {stats['total_templates']}개")
        print(f"  - 완성률: {stats['overall_completion_rate']:.1f}%")
        
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("\n")
    print("=" * 60)
    print("Main_Server API 테스트 시작")
    print("=" * 60)
    
    # 서버가 시작될 때까지 대기
    print("\n서버 시작 대기 중...")
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ 서버 연결 성공!")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("❌ 서버 연결 실패")
        return
    
    # 테스트 실행
    tests = [
        test_health,
        test_objects_classes,
        test_objects_class_detail,
        test_objects_detail,
        test_servers_status,
        test_objects_scan,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 테스트 중 에러: {e}")
            results.append(False)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\n✅ 통과: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] 모든 테스트 통과!")
    else:
        print("⚠️ 일부 테스트 실패")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

