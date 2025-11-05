#!/usr/bin/env python3
"""
YCB 객체 배치 테스트 - rsserver_final_camk 데이터 사용
5개 객체에 대해 전체 파이프라인 테스트
"""
import sys
from pathlib import Path
import requests
import json
import base64

BASE_URL = "http://localhost:8001"
project_root = Path(__file__).resolve().parents[1]

def load_image_as_base64(image_path):
    """이미지를 Base64로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def test_object(rgb_path, depth_path, cam_path, object_name):
    """단일 객체 테스트"""
    
    print(f"\n{'='*70}")
    print(f"[TEST] YCB 객체: {object_name}")
    print(f"{'='*70}")
    
    # 1. 파일 확인
    print(f"\n[1] 테스트 파일 확인...")
    for path, name in [(rgb_path, "RGB"), (depth_path, "Depth"), (cam_path, "Camera")]:
        if path.exists():
            size = path.stat().st_size
            print(f"  [OK] {name}: {path.name} ({size:,} bytes)")
        else:
            print(f"  [ERROR] {name} 파일이 없습니다: {path}")
            return False
    
    # 2. 이미지 인코딩
    print(f"\n[2] 이미지 인코딩 중...")
    try:
        rgb_base64 = load_image_as_base64(rgb_path)
        depth_base64 = load_image_as_base64(depth_path)
        print(f"  [OK] RGB: {len(rgb_base64):,} bytes")
        print(f"  [OK] Depth: {len(depth_base64):,} bytes")
    except Exception as e:
        print(f"  [ERROR] 이미지 인코딩 실패: {e}")
        return False
    
    # 3. 카메라 파라미터 로딩
    print(f"\n[3] 카메라 파라미터 로딩...")
    try:
        with open(cam_path, "r", encoding="utf-8-sig") as f:
            cam_params = json.load(f)
        print(f"  [OK] 카메라 파라미터 로딩 완료")
        print(f"    - cam_K: {len(cam_params.get('cam_K', []))} values")
        print(f"    - depth_scale: {cam_params.get('depth_scale', 'N/A')}")
    except Exception as e:
        print(f"  [ERROR] 카메라 파라미터 로딩 실패: {e}")
        return False
    
    # 4. API 요청
    print(f"\n[4] API 요청 전송 중...")
    request_data = {
        "class_name": "ycb",
        "object_name": object_name,
        "rgb_image": rgb_base64,
        "depth_image": depth_base64,
        "cam_params": cam_params
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/workflow/full-pipeline",
            json=request_data,
            timeout=900
        )
        
        print(f"\n[5] 응답 받음 (Status: {response.status_code})")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n  [SUCCESS] 파이프라인 완료!")
            print(f"  - 성공: {result.get('success', False)}")
            if 'results' in result:
                if 'ism' in result['results']:
                    ism = result['results']['ism']
                    print(f"  - ISM: {ism.get('success', False)}")
                    if ism.get('success'):
                        detections = ism.get('detections', [])
                        print(f"    * 감지된 객체: {len(detections)}개")
                        if detections:
                            top_detection = detections[0]
                            print(f"    * 최고 스코어: {top_detection.get('score', 0):.3f}")
                
                if 'pem' in result['results']:
                    pem = result['results']['pem']
                    print(f"  - PEM: {pem.get('success', False)}")
                    if pem.get('success'):
                        poses = pem.get('poses', [])
                        print(f"    * 포즈 추정: {len(poses)}개")
            
            return True
        else:
            print(f"\n  [ERROR] API 요청 실패")
            print(f"  Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error: {json.dumps(error_data, ensure_ascii=False, indent=2)[:500]}")
            except:
                print(f"  Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n  [ERROR] API 호출 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    
    print("="*70)
    print("YCB 객체 배치 테스트 - rsserver_final_camk")
    print("="*70)
    
    # 입력 파일 경로
    rgb_path = project_root / "static" / "test" / "rsserver_final_camk" / "color_raw.png"
    depth_path = project_root / "static" / "test" / "rsserver_final_camk" / "depth_raw.png"
    cam_path = project_root / "static" / "test" / "rsserver_final_camk" / "camera.json"
    
    # 테스트할 객체 목록
    test_objects = [
        "obj_000002",
        "obj_000003",
        "obj_000004",
        "obj_000005",
        "obj_000006"
    ]
    
    print(f"\n[INFO] 테스트 설정:")
    print(f"  - 테스트 데이터: rsserver_final_camk")
    print(f"  - 테스트 객체: {len(test_objects)}개")
    print(f"  - API 서버: {BASE_URL}")
    
    # 서버 상태 확인
    print(f"\n[0] 서버 상태 확인...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"  [OK] Main Server 정상")
        else:
            print(f"  [WARNING] Main Server 응답 이상: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] Main Server 연결 실패: {e}")
        print(f"  [HINT] 서버를 실행하세요: cd Main_Server && run_dev.bat")
        return
    
    # 각 객체에 대해 테스트
    results = {}
    for obj in test_objects:
        success = test_object(rgb_path, depth_path, cam_path, obj)
        results[obj] = success
    
    # 최종 결과
    print(f"\n{'='*70}")
    print("최종 결과")
    print(f"{'='*70}")
    
    total = len(test_objects)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n총 테스트: {total}개")
    print(f"성공: {passed}개")
    print(f"실패: {failed}개")
    print(f"성공률: {passed/total*100:.1f}%")
    
    print(f"\n상세 결과:")
    for obj, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {obj}")
    
    if passed == total:
        print(f"\n🎉 모든 테스트 성공!")
    else:
        print(f"\n⚠️  일부 테스트 실패. 로그를 확인하세요.")

if __name__ == "__main__":
    main()













