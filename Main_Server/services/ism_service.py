#!/usr/bin/env python3
"""
ISM 서버만 테스트하는 간단한 스크립트
"""

import base64
import json
import os
import time
from pathlib import Path
from typing import Dict, Any

import requests


def get_project_root() -> Path:
    """프로젝트 루트 경로 반환"""
    return Path(__file__).resolve().parents[2]  # services의 부모의 부모 = Estimation_Server


def to_container_path(host_path: Path) -> str:
    """호스트 경로를 컨테이너 경로로 변환"""
    project_root = get_project_root()
    rel = host_path.resolve().relative_to(project_root)
    return str(Path("/workspace/Estimation_Server").joinpath(rel).as_posix())


def encode_image_base64(image_path: Path) -> str:
    """이미지를 base64로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def test_ism_server(
    rgb_path: str,
    depth_path: str,
    cam_json_path: str,
    cad_path: str,
    template_dir: str,
    output_dir: str,
    server_url: str = "http://localhost:8002",
    timeout: int = 600
):
    """ISM 서버 테스트
    
    Args:
        rgb_path: RGB 이미지 파일 경로
        depth_path: Depth 이미지 파일 경로
        cam_json_path: 카메라 파라미터 JSON 파일 경로
        cad_path: CAD 모델 파일 경로
        template_dir: 템플릿 디렉토리 경로
        output_dir: 출력 디렉토리 경로
        server_url: ISM 서버 URL (기본값: http://localhost:8002)
        timeout: 요청 타임아웃 (초, 기본값: 600)
    
    Returns:
        Dict[str, Any]: ISM 서버 응답 결과 또는 None
    """
    print("[INFO] ISM 서버 테스트 시작")
    print("=" * 50)
    
    # 경로를 Path 객체로 변환
    rgb_path = Path(rgb_path)
    depth_path = Path(depth_path)
    cam_json_path = Path(cam_json_path)
    cad_path = Path(cad_path)
    template_dir = Path(template_dir)
    output_dir = Path(output_dir)
    
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] 출력 디렉토리: {output_dir}")
    
    # 컨테이너 경로로 변환
    cad_path_container = to_container_path(cad_path)
    template_dir_container = to_container_path(template_dir)
    output_dir_container = to_container_path(output_dir)
    
    # 이미지 인코딩
    print("[INFO] 이미지 인코딩 중...")
    rgb_b64 = encode_image_base64(rgb_path)
    depth_b64 = encode_image_base64(depth_path)
    
    # 카메라 파라미터 로드
    with open(cam_json_path, "r", encoding="utf-8-sig") as f:
        cam_params = json.load(f)
    
    # ISM 서버 요청 데이터 구성
    inference_request = {
        "rgb_image": rgb_b64,
        "depth_image": depth_b64,
        "cam_params": cam_params,
        "template_dir": template_dir_container,
        "cad_path": cad_path_container,
        "output_dir": output_dir_container,
    }
    
    print(f"[INFO] ISM 서버에 요청 전송 중...")
    print(f"   - 템플릿 디렉토리: {template_dir_container}")
    print(f"   - CAD 경로: {cad_path_container}")
    print(f"   - 출력 디렉토리: {output_dir_container}")
    
    # ISM 서버 호출
    url = f"{server_url}/api/v1/inference"
    
    try:
        start_time = time.time()
        response = requests.post(
            url,
            json=inference_request,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )
        end_time = time.time()
        
        print(f"[INFO] 요청 처리 시간: {end_time - start_time:.3f}초")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] ISM 추론 성공!")
            print(f"   - 성공 여부: {result['success']}")
            print(f"   - 추론 시간: {result['inference_time']:.3f}초")
            print(f"   - 감지 결과 수: {len(result.get('detections', {}).get('masks', []))}")
            print(f"   - 사용된 출력 디렉토리: {result['output_dir_used']}")
            
            if result.get('error_message'):
                print(f"   - 에러 메시지: {result['error_message']}")
            
            # 출력 디렉토리 확인
            print(f"\n[INFO] 출력 디렉토리 확인: {output_dir}")
            if output_dir.exists():
                files = list(output_dir.iterdir())
                print(f"   - 생성된 파일 수: {len(files)}")
                for file in files:
                    print(f"   - {file.name} ({file.stat().st_size} bytes)")
            else:
                print("   - 출력 디렉토리가 존재하지 않습니다.")
            
            return result
        else:
            print(f"[ERROR] ISM 추론 실패: HTTP {response.status_code}")
            print(f"   응답 내용: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] ISM 요청 실패: {e}")
        return None


def main():
    """메인 함수 - 기본 테스트 데이터로 실행"""
    project_root = get_project_root()
    
    # 기본 테스트 데이터 경로 설정
    rgb_path = str(project_root / "static" / "test" / "rgb.png")
    depth_path = str(project_root / "static" / "test" / "depth.png")
    cam_json_path = str(project_root / "static" / "test" / "camera.json")
    cad_path = str(project_root / "static" / "meshes" / "test" / "obj_000005.ply")
    template_dir = str(project_root / "static" / "templates" / "test" / "obj_000005")
    
    # 출력 디렉토리 설정 (현재 시간으로 폴더 생성)
    run_ts = str(int(time.time()))
    output_dir = str(project_root / "static" / "output" / run_ts / "ism_test")
    
    # 서버 상태 확인
    print("[INFO] ISM 서버 상태 확인 중...")
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("[SUCCESS] ISM 서버가 정상적으로 실행 중입니다.")
        else:
            print(f"[ERROR] ISM 서버 상태 확인 실패: {response.status_code}")
            return
    except Exception as e:
        print(f"[ERROR] ISM 서버 연결 실패: {e}")
        return
    
    print("\n" + "=" * 50)
    
    # ISM 서버 테스트 실행
    result = test_ism_server(
        rgb_path=rgb_path,
        depth_path=depth_path,
        cam_json_path=cam_json_path,
        cad_path=cad_path,
        template_dir=template_dir,
        output_dir=output_dir,
        server_url="http://localhost:8002",
        timeout=600
    )
    
    if result:
        print("\n" + "=" * 50)
        print("[SUCCESS] ISM 서버 테스트 완료!")
    else:
        print("\n" + "=" * 50)
        print("[ERROR] ISM 서버 테스트 실패!")


def example_usage():
    """사용 예시 함수"""
    project_root = get_project_root()
    
    # 사용자 정의 경로 설정 예시
    custom_rgb_path = str(project_root / "static" / "test" / "rgb.png")
    custom_depth_path = str(project_root / "static" / "test" / "depth.png")
    custom_cam_json_path = str(project_root / "static" / "test" / "camera.json")
    custom_cad_path = str(project_root / "static" / "meshes" / "test" / "obj_000005.ply")
    custom_template_dir = str(project_root / "static" / "templates" / "test" / "obj_000005")
    custom_output_dir = str(project_root / "static" / "output" / "custom_test")
    
    # ISM 서버 호출 예시
    result = test_ism_server(
        rgb_path=custom_rgb_path,
        depth_path=custom_depth_path,
        cam_json_path=custom_cam_json_path,
        cad_path=custom_cad_path,
        template_dir=custom_template_dir,
        output_dir=custom_output_dir,
        server_url="http://localhost:8002",
        timeout=600
    )
    
    return result


if __name__ == "__main__":
    main()
