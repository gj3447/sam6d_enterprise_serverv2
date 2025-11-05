#!/usr/bin/env python3
"""
ISM 서버로 직접 추론 테스트
"""
import requests
import json
import base64
import os
from pathlib import Path

# 서버 URL
ISM_SERVER_URL = "http://localhost:8002"

def load_image_as_base64(image_path):
    """이미지를 Base64로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def test_ism_inference():
    """ISM 추론 테스트"""
    
    print("=" * 70)
    print("YCB obj_000002 추론 테스트 (ISM PROVIDER 직접)")
    print("=" * 70)
    
    # 프로젝트 루트
    project_root = Path(__file__).resolve().parents[1]
    
    # 입력 파일 경로
    rgb_path = project_root / "static" / "test" / "rgb.png"
    depth_path = project_root / "static" / "test" / "depth.png"
    cam_path = project_root / "static" / "test" / "camera.json"
    
    # 템플릿과 CAD 경로 (컨테이너 경로)
    template_dir = "/workspace/Estimation_Server/static/templates/ycb/obj_000002"
    cad_path = "/workspace/Estimation_Server/static/meshes/ycb/obj_000002.obj"
    
    print(f"\n[INFO] 입력 파일:")
    print(f"  RGB: {rgb_path}")
    print(f"  Depth: {depth_path}")
    print(f"  Camera: {cam_path}")
    print(f"  Template: {template_dir}")
    print(f"  CAD: {cad_path}")
    
    # 파일 존재 확인
    for path in [rgb_path, depth_path, cam_path]:
        if not path.exists():
            print(f"\n[ERROR] 파일이 없습니다: {path}")
            return False
    
    print(f"\n[INFO] 컨테이너 경로 사용:")
    print(f"  Template: {template_dir}")
    print(f"  CAD: {cad_path}")
    
    # 이미지 인코딩
    print(f"\n[INFO] 이미지 인코딩 중...")
    rgb_base64 = load_image_as_base64(rgb_path)
    depth_base64 = load_image_as_base64(depth_path)
    
    # 카메라 파라미터 로딩
    with open(cam_path, "r", encoding="utf-8-sig") as f:
        cam_params = json.load(f)
    
    # 출력 디렉토리
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = str(project_root / "static" / "output" / f"ycb_ism_{timestamp}")
    
    # 요청 데이터
    url = f"{ISM_SERVER_URL}/api/v1/inference"
    payload = {
        "rgb_image": rgb_base64,
        "depth_image": depth_base64,
        "cam_params": cam_params,
        "template_dir": template_dir,
        "cad_path": cad_path,
        "output_dir": output_dir
    }
    
    print(f"\n[INFO] ISM 추론 요청...")
    print(f"  URL: {url}")
    print(f"  출력: {output_dir}")
    
    try:
        print(f"\n[INFO] 추론 실행 중... (시간이 오래 걸릴 수 있습니다)")
        response = requests.post(url, json=payload, timeout=600)
        response.raise_for_status()
        
        result = response.json()
        
        if result["success"]:
            print(f"\n[SUCCESS] 추론 완료!")
            print(f"결과 디렉토리: {output_dir}")
            print(f"추론 시간: {result['inference_time']:.2f}초")
            print(f"템플릿 사용: {result['template_dir_used']}")
            print(f"CAD 사용: {result['cad_path_used']}")
            print(f"\n감지 결과:")
            detections = result['detections']
            if 'masks' in detections:
                print(f"  - 감지된 객체 수: {len(detections['masks'])}")
                if 'scores' in detections:
                    print(f"  - Score: {detections['scores'][:3] if len(detections['scores']) >= 3 else detections['scores']}")
            return True
        else:
            print(f"\n[FAILED] 추론 실패")
            print(f"에러 메시지: {result.get('error_message', 'Unknown error')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] 요청 실패: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 에러: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = test_ism_inference()
    sys.exit(0 if success else 1)

