#!/usr/bin/env python3
"""
Main_Server API를 통한 전체 파이프라인 테스트
"""
import requests
import json
import base64
from pathlib import Path

BASE_URL = "http://localhost:8001"

def load_image_as_base64(image_path: Path) -> str:
    """이미지를 Base64로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def test_api_full_pipeline():
    """Main_Server API를 통한 전체 파이프라인 테스트"""
    
    print("=" * 70)
    print("Main_Server API 전체 파이프라인 테스트")
    print("=" * 70)
    
    # 프로젝트 루트
    project_root = Path(__file__).resolve().parents[1]
    
    # 입력 파일 경로
    rgb_path = project_root / "static" / "test" / "rgb.png"
    depth_path = project_root / "static" / "test" / "depth.png"
    cam_path = project_root / "static" / "test" / "camera.json"
    
    print(f"\n[INFO] 입력 파일:")
    print(f"  RGB: {rgb_path}")
    print(f"  Depth: {depth_path}")
    print(f"  Camera: {cam_path}")
    
    # 이미지 인코딩
    print(f"\n[INFO] 이미지 인코딩 중...")
    rgb_base64 = load_image_as_base64(rgb_path)
    depth_base64 = load_image_as_base64(depth_path)
    
    # 카메라 파라미터 로딩
    with open(cam_path, "r", encoding="utf-8-sig") as f:
        cam_params = json.load(f)
    
    # API 요청 데이터
    request_data = {
        "class_name": "ycb",
        "object_name": "obj_000002",
        "rgb_image": rgb_base64,
        "depth_image": depth_base64,
        "cam_params": cam_params
    }
    
    # API 호출
    print(f"\n{'='*70}")
    print("[STEP] Main_Server API 호출 (전체 파이프라인)")
    print(f"{'='*70}")
    api_url = f"{BASE_URL}/api/v1/workflow/full-pipeline"
    
    try:
        print(f"[INFO] API 요청 중... (시간이 오래 걸릴 수 있습니다)")
        response = requests.post(api_url, json=request_data, timeout=900)
        response.raise_for_status()
        result = response.json()
        
        print(f"\n[SUCCESS] API 응답 수신!")
        print(f"  성공: {result.get('success')}")
        print(f"  메시지: {result.get('message')}")
        
        if result.get('success'):
            if 'results' in result and 'output_dir' in result['results']:
                output_dir = result['results']['output_dir']
                print(f"  출력 디렉토리: {output_dir}")
                
                # 결과 상세 확인
                results = result.get('results', {}).get('results', {})
                
                if 'ism' in results:
                    ism_result = results['ism']
                    print(f"\n  [ISM 결과]")
                    print(f"    성공: {ism_result.get('success', False)}")
                    if ism_result.get('success'):
                        detections = ism_result.get('detections', {})
                        num_detections = len(detections.get('masks', []) or [])
                        print(f"    감지된 객체 수: {num_detections}")
                        print(f"    추론 시간: {ism_result.get('inference_time', 0):.2f}초")
                
                if 'pem' in results:
                    pem_result = results['pem']
                    print(f"\n  [PEM 결과]")
                    print(f"    성공: {pem_result.get('success', False)}")
                    if pem_result.get('success'):
                        print(f"    추론 시간: {pem_result.get('inference_time', 0):.2f}초")
                    else:
                        print(f"    에러: {pem_result.get('error_message', 'Unknown error')}")
        else:
            print(f"  에러: {result.get('results', {}).get('error', 'Unknown error')}")
        
        return result.get('success', False)
        
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] API 요청 실패: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"  응답: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"  응답 텍스트: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 에러: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_full_pipeline_from_rss(base="http://192.168.0.197:51000", obj="obj_000002"):
    payload = {
        "class_name": "ycb",
        "object_name": obj,
        "base": base,
        "align_color": True,
        "frame_guess": True,
    }
    r = requests.post(f"{BASE_URL}/api/v1/workflow/full-pipeline-from-rss", json=payload, timeout=900)
    print("[RSS PIPELINE]", r.status_code)
    try:
        print(json.dumps(r.json(), ensure_ascii=False, indent=2)[:2000])
    except Exception:
        print(r.text[:1000])

if __name__ == "__main__":
    import sys
    success = test_api_full_pipeline()
    print(f"\n{'='*70}")
    if success:
        print("[COMPLETE] 테스트 성공!")
    else:
        print("[FAILED] 테스트 실패!")
    print(f"{'='*70}")
    sys.exit(0 if success else 1)

