#!/usr/bin/env python3
"""
obj_000005로 전체 파이프라인 테스트
"""
import asyncio
import base64
import json
import requests
from pathlib import Path

# 설정
MAIN_SERVER_URL = "http://localhost:8001"
TEST_DIR = Path("static/test")
MESH_PATH = Path("static/meshes/test/obj_000005.ply")
TEMPLATE_DIR = Path("static/templates/test/obj_000005")

def encode_image_to_base64(image_path: Path) -> str:
    """이미지를 base64로 인코딩"""
    with open(image_path, "rb") as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode("utf-8")

def load_camera_params():
    """카메라 파라미터 로드"""
    with open(TEST_DIR / "camera.json", "r", encoding="utf-8-sig") as f:
        return json.load(f)

async def test_full_pipeline():
    """전체 파이프라인 테스트"""
    print("=" * 60)
    print("obj_000005 전체 파이프라인 테스트")
    print("=" * 60)
    
    # Main 서버가 실행 중인지 확인
    print("\n[1] Main 서버 상태 확인...")
    try:
        response = requests.get(f"{MAIN_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Main 서버가 정상적으로 실행 중입니다.")
        else:
            print(f"[ERROR] Main 서버 오류: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Main 서버에 연결할 수 없습니다: {e}")
        return
    
    # 입력 데이터 준비
    print("\n[2] 입력 데이터 준비...")
    rgb_path = TEST_DIR / "rgb.png"
    depth_path = TEST_DIR / "depth.png"
    
    if not rgb_path.exists() or not depth_path.exists():
        print(f"[ERROR] 테스트 이미지 파일을 찾을 수 없습니다.")
        return
    
    rgb_b64 = encode_image_to_base64(rgb_path)
    depth_b64 = encode_image_to_base64(depth_path)
    cam_params = load_camera_params()
    
    print(f"[OK] RGB 이미지 로드: {rgb_path}")
    print(f"[OK] Depth 이미지 로드: {depth_path}")
    print(f"[OK] 카메라 파라미터 로드")
    
    # 전체 파이프라인 호출
    print("\n[3] 전체 파이프라인 실행...")
    payload = {
        "class_name": "test",
        "object_name": "obj_000005",
        "rgb_image": rgb_b64,
        "depth_image": depth_b64,
        "cam_params": cam_params
    }
    
    try:
        response = requests.post(
            f"{MAIN_SERVER_URL}/api/v1/workflow/full-pipeline",
            json=payload,
            timeout=1200  # 20분 타임아웃
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n[OK] 파이프라인 실행 완료!")
            print(f"  - Success: {result.get('success')}")
            print(f"  - Output Directory: {result.get('output_dir')}")
            
            # 결과 요약
            if result.get("success"):
                results = result.get("results", {})
                print("\n[4] 결과 요약:")
                
                if "render" in results:
                    render = results["render"]
                    print(f"  Render: {'Skipped' if render.get('skipped') else 'Success'}")
                
                if "ism" in results:
                    ism = results["ism"]
                    print(f"  ISM: {ism.get('success')}, Detections: {ism.get('num_detections', 0)}")
                
                if "pem" in results:
                    pem = results["pem"]
                    print(f"  PEM: {pem.get('success')}, Detections: {pem.get('num_detections', 0)}")
                
                # Output 디렉토리 확인
                output_dir = result.get("output_dir")
                if output_dir:
                    output_path = Path(output_dir)
                    print(f"\n[5] Output 디렉토리 구조:")
                    print(f"  {output_path}")
                    
                    files = list(output_path.glob("**/*"))
                    print(f"  생성된 파일 수: {len(files)}")
                    
                    # 주요 파일 확인
                    important_files = [
                        "input_rgb.png",
                        "input_depth.png",
                        "camera_params.json",
                        "pipeline_metadata.json"
                    ]
                    
                    print("\n  주요 파일:")
                    for file_name in important_files:
                        file_path = output_path / file_name
                        if file_path.exists():
                            size = file_path.stat().st_size
                            print(f"    [OK] {file_name} ({size} bytes)")
                        else:
                            print(f"    [ERROR] {file_name} (없음)")
                    
                    # 메타데이터 읽기
                    metadata_path = output_path / "pipeline_metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        
                        print("\n  메타데이터:")
                        pipeline_info = metadata.get("pipeline_info", {})
                        print(f"    시작 시간: {pipeline_info.get('start_time')}")
                        print(f"    종료 시간: {pipeline_info.get('end_time')}")
                        print(f"    소요 시간: {pipeline_info.get('duration_seconds')}초")
                        print(f"    성공 여부: {pipeline_info.get('success')}")
                        
                        request_info = metadata.get("request_info", {})
                        print(f"\n    요청 정보:")
                        print(f"      클래스: {request_info.get('class_name')}")
                        print(f"      객체: {request_info.get('object_name')}")
                        print(f"      템플릿 존재: {request_info.get('template_existed')}")
                
            else:
                print(f"  [ERROR] Error: {result.get('error')}")
        else:
            print(f"\n[ERROR] 서버 오류: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] 요청 실패: {e}")
    except Exception as e:
        print(f"\n[ERROR] 예외 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())

