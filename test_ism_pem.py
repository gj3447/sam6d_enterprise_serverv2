#!/usr/bin/env python3
"""
ISM + PEM 서버 테스트 스크립트
"""
import base64
import json
import requests
import os
from pathlib import Path

# 테스트 데이터 경로
test_dir = Path("static/test")
rgb_path = test_dir / "rgb.png"
depth_path = test_dir / "depth.png"
camera_path = test_dir / "camera.json"

# 템플릿 및 CAD 경로
template_dir = "/workspace/Estimation_Server/static/templates/test/obj_000005"
cad_path = "/workspace/Estimation_Server/static/meshes/test/obj_000005.ply"

# 출력 디렉토리
output_dir = "static/output/test_result_new"
os.makedirs(output_dir, exist_ok=True)

def image_to_base64(image_path):
    """이미지를 base64로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def main():
    print("=" * 60)
    print("ISM + PEM 서버 테스트")
    print("=" * 60)
    
    # 파일 존재 확인
    print("\n[1] 파일 확인")
    print(f"   RGB: {rgb_path.exists()} - {rgb_path}")
    print(f"   Depth: {depth_path.exists()} - {depth_path}")
    print(f"   Camera: {camera_path.exists()} - {camera_path}")
    print(f"   Template Dir: {Path(template_dir.replace('/workspace/Estimation_Server/', '')).exists()}")
    print(f"   CAD Path: {Path(cad_path.replace('/workspace/Estimation_Server/', '')).exists()}")
    print(f"   Output Dir: {output_dir}")
    
    # 이미지 인코딩
    print("\n[2] 이미지 인코딩 중...")
    rgb_b64 = image_to_base64(rgb_path)
    depth_b64 = image_to_base64(depth_path)
    print(f"   RGB: {len(rgb_b64)} bytes")
    print(f"   Depth: {len(depth_b64)} bytes")
    
    # 카메라 파라미터 로드
    print("\n[3] 카메라 파라미터 로드...")
    with open(camera_path, "r", encoding="utf-8-sig") as f:
        cam_params = json.load(f)
    print(f"   cam_K: {len(cam_params['cam_K'])} values")
    
    # ISM 추론 요청
    print("\n[4] ISM 서버에 추론 요청...")
    ism_url = "http://localhost:8002/api/v1/inference"
    ism_request = {
        "rgb_image": rgb_b64,
        "depth_image": depth_b64,
        "cam_params": cam_params,
        "template_dir": template_dir,
        "cad_path": cad_path,
        "output_dir": f"/workspace/Estimation_Server/{output_dir}",
    }
    
    try:
        response = requests.post(
            ism_url,
            json=ism_request,
            headers={"Content-Type": "application/json"},
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[ISM 결과]")
            print(f"   Success: {result.get('success')}")
            print(f"   Inference Time: {result.get('inference_time', 0):.3f}s")
            
            if result.get('success'):
                # ISM 결과는 JSON 파일에서 로드
                import json as json_module
                ism_result_path = f"{output_dir}/detection_ism.json"
                with open(ism_result_path, 'r', encoding='utf-8') as f:
                    ism_detections = json_module.load(f)
                
                print(f"   Detected Objects: {len(ism_detections)}")
                if ism_detections:
                    top_scores = [round(d['score'], 3) for d in sorted(ism_detections, key=lambda x: x['score'], reverse=True)[:5]]
                    print(f"   Top 5 Scores: {top_scores}")
                
                # PEM 서버에 포즈 추정 요청
                print("\n[5] PEM 서버에 포즈 추정 요청...")
                pem_url = "http://localhost:8003/api/v1/pose-estimation"
                
                # 상위 5개만 선택 (스코어로 정렬)
                ism_detections_sorted = sorted(ism_detections, key=lambda x: x['score'], reverse=True)
                top_5_detections = ism_detections_sorted[:5]
                print(f"   Selecting top 5 detections")
                top_5_scores = [round(d['score'], 3) for d in top_5_detections]
                print(f"   Top 5 Scores: {top_5_scores}")
                
                pem_request = {
                    "rgb_image": rgb_b64,
                    "depth_image": depth_b64,
                    "seg_data": top_5_detections,
                    "cad_path": cad_path,
                    "template_dir": template_dir,
                    "cam_params": cam_params,
                    "output_dir": f"/workspace/Estimation_Server/{output_dir}"
                }
                
                pem_response = requests.post(
                    pem_url,
                    json=pem_request,
                    headers={"Content-Type": "application/json"},
                    timeout=300
                )
                
                if pem_response.status_code == 200:
                    pem_result = pem_response.json()
                    print(f"\n[PEM 결과]")
                    print(f"   Success: {pem_result.get('success')}")
                    print(f"   Elapsed Time: {pem_result.get('elapsed_time', 0):.3f}s")
                    
                    if pem_result.get('success'):
                        poses = pem_result.get('poses', [])
                        print(f"   Estimated Poses: {len(poses)}")
                        for i, pose in enumerate(poses[:3]):
                            print(f"      Pose {i}: R={pose.get('R')}, t={pose.get('t')}")
                    else:
                        print(f"   Error: {pem_result.get('error_message')}")
                else:
                    print(f"\n[ERROR] PEM 요청 실패: {pem_response.status_code}")
                    print(f"   Response: {pem_response.text}")
            else:
                print(f"   Error: {result.get('error_message')}")
        else:
            print(f"\n[ERROR] ISM 요청 실패: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"출력 파일 위치: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()

