#!/usr/bin/env python3
"""
PEM 서버만 테스트하는 스크립트
ISM 결과를 직접 전달하여 PEM 포즈 추정 테스트
"""

import base64
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List

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


def encode_depth_image_to_base64(depth_path: Path) -> tuple:
    """깊이 이미지를 원본 데이터 타입으로 Base64 인코딩"""
    try:
        import numpy as np
        from PIL import Image
        
        # 깊이 이미지를 numpy 배열로 로딩
        depth_image = Image.open(depth_path)
        depth_array = np.array(depth_image).astype(np.float32)
        
        # numpy 배열을 bytes로 변환 후 Base64 인코딩
        depth_bytes = depth_array.tobytes()
        return base64.b64encode(depth_bytes).decode('utf-8'), depth_array.shape
    except Exception as e:
        print(f"Failed to encode depth image {depth_path}: {e}")
        return None, None


def load_ism_result_from_file(ism_result_path: Path) -> List[Dict[str, Any]]:
    """ISM 결과 파일에서 seg_data 추출"""
    try:
        with open(ism_result_path, 'r') as f:
            ism_data = json.load(f)
        
        # ISM 결과를 PEM 입력 형식으로 변환
        seg_data = []
        if isinstance(ism_data, list):
            # 이미 리스트 형태인 경우
            for item in ism_data:
                seg_data.append({
                    "scene_id": 0,
                    "image_id": 0,
                    "category_id": item.get("category_id", 1),
                    "bbox": item.get("bbox", [0, 0, 0, 0]),
                    "score": item.get("score", 0.0),
                    "segmentation": item.get("segmentation", {"size": None, "counts": ""}),
                })
        elif isinstance(ism_data, dict) and "detections" in ism_data:
            # ISM 서버 응답 형태인 경우
            det = ism_data["detections"]
            masks = det.get("masks", []) or []
            boxes = det.get("boxes", []) or []
            scores = det.get("scores", []) or []
            object_ids = det.get("object_ids", []) or []
            n = max(len(boxes), len(scores), len(object_ids), len(masks))
            
            for i in range(n):
                bbox = boxes[i] if i < len(boxes) else [0, 0, 0, 0]
                score = float(scores[i]) if i < len(scores) else 0.0
                cat_id = int(object_ids[i]) if i < len(object_ids) else 1
                seg = {"size": None, "counts": ""}
                seg_data.append({
                    "scene_id": 0,
                    "image_id": 0,
                    "category_id": cat_id,
                    "bbox": bbox,
                    "score": score,
                    "segmentation": seg,
                })
        
        return seg_data
    except Exception as e:
        print(f"Failed to load ISM result from {ism_result_path}: {e}")
        return []


def call_pem_pose(
    pem_base_url: str,
    rgb_b64: str,
    depth_b64: str,
    cam_params: Dict[str, Any],
    cad_path_container: str,
    seg_data: List[Dict[str, Any]],
    template_dir_container: str,
    output_dir_container: str,
    det_score_thresh: float = 0.2,
    timeout: int = 900,
) -> Dict[str, Any]:
    """PEM 서버 호출"""
    url = f"{pem_base_url}/api/v1/pose-estimation"
    payload = {
        "rgb_image": rgb_b64,
        "depth_image": depth_b64,
        "cam_params": cam_params,
        "cad_path": cad_path_container,
        "seg_data": seg_data,
        "template_dir": template_dir_container,
        "det_score_thresh": det_score_thresh,
        "output_dir": output_dir_container,
    }
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def test_pem_only(
    rgb_path: str,
    depth_path: str,
    cam_json_path: str,
    cad_path: str,
    template_dir: str,
    ism_result_path: str,
    output_dir: str,
    server_url: str = "http://localhost:8003",
    det_score_thresh: float = 0.2,
    timeout: int = 900
):
    """PEM 서버만 테스트
    
    Args:
        rgb_path: RGB 이미지 파일 경로
        depth_path: Depth 이미지 파일 경로
        cam_json_path: 카메라 파라미터 JSON 파일 경로
        cad_path: CAD 모델 파일 경로
        template_dir: 템플릿 디렉토리 경로
        ism_result_path: ISM 결과 JSON 파일 경로
        output_dir: 출력 디렉토리 경로
        server_url: PEM 서버 URL (기본값: http://localhost:8003)
        det_score_thresh: 검출 점수 임계값 (기본값: 0.2)
        timeout: 요청 타임아웃 (초, 기본값: 900)
    
    Returns:
        Dict[str, Any]: PEM 서버 응답 결과 또는 None
    """
    print("[INFO] PEM 서버만 테스트 시작")
    print("=" * 50)
    
    # 경로를 Path 객체로 변환
    rgb_path = Path(rgb_path)
    depth_path = Path(depth_path)
    cam_json_path = Path(cam_json_path)
    cad_path = Path(cad_path)
    template_dir = Path(template_dir)
    ism_result_path = Path(ism_result_path)
    output_dir = Path(output_dir)
    
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] 출력 디렉토리: {output_dir}")
    print(f"[INFO] ISM 결과 파일: {ism_result_path}")
    
    # 파일 존재 여부 확인
    if not ism_result_path.exists():
        print(f"[ERROR] ISM 결과 파일이 존재하지 않습니다: {ism_result_path}")
        return None
    
    # 컨테이너 경로로 변환
    cad_path_container = to_container_path(cad_path)
    template_dir_container = to_container_path(template_dir)
    output_dir_container = to_container_path(output_dir)
    
    # 이미지 인코딩
    print("[INFO] 이미지 인코딩 중...")
    rgb_b64 = encode_image_base64(rgb_path)
    depth_b64, depth_shape = encode_depth_image_to_base64(depth_path)
    
    if not depth_b64:
        print("[ERROR] 깊이 이미지 인코딩 실패")
        return None
    
    # 카메라 파라미터 로드
    with open(cam_json_path, "r", encoding="utf-8") as f:
        cam_params = json.load(f)
    
    # ISM 결과에서 seg_data 추출
    print("[INFO] ISM 결과에서 seg_data 추출 중...")
    seg_data = load_ism_result_from_file(ism_result_path)
    
    if not seg_data:
        print("[ERROR] ISM 결과에서 seg_data 추출 실패")
        return None
    
    print(f"[INFO] {len(seg_data)}개 검출 데이터 추출 완료")
    
    # PEM 서버 호출
    print("\n[INFO] PEM 서버 호출")
    print("-" * 30)
    
    print(f"[INFO] PEM 서버에 요청 전송 중...")
    print(f"   - 템플릿 디렉토리: {template_dir_container}")
    print(f"   - CAD 경로: {cad_path_container}")
    print(f"   - 출력 디렉토리: {output_dir_container}")
    print(f"   - 검출 데이터 수: {len(seg_data)}")
    
    try:
        pem_start_time = time.time()
        pem_result = call_pem_pose(
            pem_base_url=server_url,
            rgb_b64=rgb_b64,
            depth_b64=depth_b64,
            cam_params=cam_params,
            cad_path_container=cad_path_container,
            seg_data=seg_data,
            template_dir_container=template_dir_container,
            output_dir_container=output_dir_container,
            det_score_thresh=det_score_thresh,
            timeout=timeout,
        )
        pem_end_time = time.time()
        
        print(f"[INFO] PEM 요청 처리 시간: {pem_end_time - pem_start_time:.3f}초")
        print(f"[SUCCESS] PEM 추론 성공!")
        print(f"   - 성공 여부: {pem_result['success']}")
        print(f"   - 추론 시간: {pem_result['inference_time']:.3f}초")
        print(f"   - 검출된 객체 수: {pem_result['num_detections']}")
        
        if pem_result.get('pose_scores'):
            print(f"   - 포즈 점수: {[f'{score:.3f}' for score in pem_result['pose_scores']]}")
        
        if pem_result.get('error_message'):
            print(f"   - 에러 메시지: {pem_result['error_message']}")
            
    except Exception as e:
        print(f"[ERROR] PEM 요청 실패: {e}")
        return None
    
    # ===== 결과 확인 =====
    print(f"\n[INFO] 최종 출력 디렉토리 확인: {output_dir}")
    if output_dir.exists():
        files = list(output_dir.iterdir())
        print(f"   - 생성된 파일 수: {len(files)}")
        for file in files:
            print(f"   - {file.name} ({file.stat().st_size} bytes)")
    else:
        print("   - 출력 디렉토리가 존재하지 않습니다.")
    
    return pem_result


def example_usage():
    """사용 예시 함수"""
    project_root = get_project_root()
    
    # 사용자 정의 경로 설정 예시
    custom_rgb_path = str(project_root / "static" / "test" / "rgb.png")
    custom_depth_path = str(project_root / "static" / "test" / "depth.png")
    custom_cam_json_path = str(project_root / "static" / "test" / "camera.json")
    custom_cad_path = str(project_root / "static" / "meshes" / "test" / "obj_000005.ply")
    custom_template_dir = str(project_root / "static" / "templates" / "test" / "obj_000005")
    custom_ism_result_path = str(project_root / "static" / "output" / "1761294743" / "ism_test" / "detection_ism.json")
    custom_output_dir = str(project_root / "static" / "output" / "custom_pem_test")
    
    # PEM 서버 호출 예시
    result = test_pem_only(
        rgb_path=custom_rgb_path,
        depth_path=custom_depth_path,
        cam_json_path=custom_cam_json_path,
        cad_path=custom_cad_path,
        template_dir=custom_template_dir,
        ism_result_path=custom_ism_result_path,
        output_dir=custom_output_dir,
        server_url="http://localhost:8003",
        det_score_thresh=0.2,
        timeout=900
    )
    
    return result


def main():
    """메인 함수 - 기본 테스트 데이터로 실행"""
    project_root = get_project_root()
    
    # 기본 테스트 데이터 경로 설정
    rgb_path = str(project_root / "static" / "test" / "rgb.png")
    depth_path = str(project_root / "static" / "test" / "depth.png")
    cam_json_path = str(project_root / "static" / "test" / "camera.json")
    cad_path = str(project_root / "static" / "meshes" / "test" / "obj_000005.ply")
    template_dir = str(project_root / "static" / "templates" / "test" / "obj_000005")
    
    # ISM 결과 파일 경로 (이전에 생성된 결과 사용)
    ism_result_path = str(project_root / "static" / "output" / "1761294743" / "ism_test" / "detection_ism.json")
    
    # 출력 디렉토리 설정 (현재 시간으로 폴더 생성)
    run_ts = str(int(time.time()))
    output_dir = str(project_root / "static" / "output" / run_ts / "pem_only_test")
    
    # PEM 서버 상태 확인
    print("[INFO] PEM 서버 상태 확인 중...")
    
    try:
        response = requests.get("http://localhost:8003/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("[SUCCESS] PEM 서버가 정상적으로 실행 중입니다.")
            print(f"   - 모델 로드됨: {data['model']['loaded']}")
            print(f"   - 디바이스: {data['model']['device']}")
        else:
            print(f"[ERROR] PEM 서버 상태 확인 실패: {response.status_code}")
            return
    except Exception as e:
        print(f"[ERROR] PEM 서버 연결 실패: {e}")
        return
    
    print("\n" + "=" * 50)
    
    # PEM 서버 테스트 실행
    result = test_pem_only(
        rgb_path=rgb_path,
        depth_path=depth_path,
        cam_json_path=cam_json_path,
        cad_path=cad_path,
        template_dir=template_dir,
        ism_result_path=ism_result_path,
        output_dir=output_dir,
        server_url="http://localhost:8003",
        det_score_thresh=0.2,
        timeout=900
    )
    
    if result:
        print("\n" + "=" * 50)
        print("[SUCCESS] PEM 서버 테스트 완료!")
        print(f"   - PEM 추론 시간: {result['inference_time']:.3f}초")
        print(f"   - 검출된 객체 수: {result['num_detections']}")
    else:
        print("\n" + "=" * 50)
        print("[ERROR] PEM 서버 테스트 실패!")


if __name__ == "__main__":
    main()
