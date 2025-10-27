#!/usr/bin/env python3
"""
Render 서버만 테스트하는 스크립트
CAD 모델을 사용하여 템플릿 생성 테스트
"""

import base64
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests


def get_project_root() -> Path:
    """프로젝트 루트 경로 반환"""
    return Path(__file__).resolve().parents[2]  # services의 부모의 부모 = Estimation_Server


def to_container_path(host_path: Path) -> str:
    """호스트 경로를 컨테이너 경로로 변환"""
    project_root = get_project_root()
    rel = host_path.resolve().relative_to(project_root)
    return str(Path("/workspace/Estimation_Server").joinpath(rel).as_posix())


def test_render_only(
    cad_path: str,
    template_output_dir: str,
    server_url: str = "http://localhost:8004",
    wait: bool = True,
    wait_timeout_sec: int = 3600
):
    """Render 서버만 테스트
    
    Args:
        cad_path: CAD 모델 파일 경로
        template_output_dir: 템플릿 출력 디렉토리 경로
        server_url: Render 서버 URL (기본값: http://localhost:8004)
        wait: 완료까지 대기 여부 (기본값: True)
        wait_timeout_sec: 대기 타임아웃 (초, 기본값: 3600)
    
    Returns:
        Dict[str, Any]: Render 서버 응답 결과 또는 None
    """
    print("[INFO] Render 서버만 테스트 시작")
    print("=" * 50)
    
    # 경로를 Path 객체로 변환
    cad_path = Path(cad_path)
    template_output_dir = Path(template_output_dir)
    
    # 출력 디렉토리 생성
    template_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] CAD 파일: {cad_path}")
    print(f"[INFO] 템플릿 출력 디렉토리: {template_output_dir}")
    
    # 파일 존재 여부 확인
    if not cad_path.exists():
        print(f"[ERROR] CAD 파일이 존재하지 않습니다: {cad_path}")
        return None
    
    # 컨테이너 경로로 변환
    cad_path_container = to_container_path(cad_path)
    template_output_container = to_container_path(template_output_dir)
    
    print(f"[INFO] 컨테이너 CAD 경로: {cad_path_container}")
    print(f"[INFO] 컨테이너 템플릿 출력 경로: {template_output_container}")
    
    # Render 서버 요청 데이터 구성
    render_request = {
        "cad_path": cad_path_container,
        "output_dir": template_output_container,
    }
    
    # Render 서버 호출
    print("\n[INFO] Render 서버 호출")
    print("-" * 30)
    
    url = f"{server_url}/render/templates"
    params = {
        "wait": wait,
        "wait_timeout_sec": wait_timeout_sec
    }
    
    print(f"[INFO] Render 서버에 요청 전송 중...")
    print(f"   - CAD 경로: {cad_path_container}")
    print(f"   - 출력 디렉토리: {template_output_container}")
    print(f"   - 대기 여부: {wait}")
    print(f"   - 타임아웃: {wait_timeout_sec}초")
    
    try:
        start_time = time.time()
        response = requests.post(
            url,
            json=render_request,
            params=params,
            headers={"Content-Type": "application/json"},
            timeout=wait_timeout_sec + 60  # 서버 타임아웃보다 조금 더 길게
        )
        end_time = time.time()
        
        print(f"[INFO] 요청 처리 시간: {end_time - start_time:.3f}초")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] Render 템플릿 생성 성공!")
            
            if wait:
                # 동기 실행인 경우
                print(f"   - 성공 여부: {result.get('success', True)}")
                print(f"   - 처리 시간: {result.get('processing_time', 0):.3f}초")
                print(f"   - 생성된 템플릿 수: {result.get('templates_generated', 0)}")
                
                if result.get('error_message'):
                    print(f"   - 에러 메시지: {result['error_message']}")
            else:
                # 비동기 실행인 경우
                job_id = result.get('job_id')
                print(f"   - 작업 ID: {job_id}")
                print(f"   - 상태: {result.get('status', 'queued')}")
                
                if job_id:
                    # 작업 상태 확인
                    print(f"[INFO] 작업 상태 확인 중... (작업 ID: {job_id})")
                    status_result = check_job_status(server_url, job_id)
                    if status_result:
                        result.update(status_result)
        else:
            print(f"[ERROR] Render 템플릿 생성 실패: HTTP {response.status_code}")
            print(f"   응답 내용: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Render 요청 실패: {e}")
        return None
    
    # ===== 결과 확인 =====
    print(f"\n[INFO] 템플릿 출력 디렉토리 확인: {template_output_dir}")
    if template_output_dir.exists():
        files = list(template_output_dir.iterdir())
        print(f"   - 생성된 파일 수: {len(files)}")
        for file in files:
            if file.is_file():
                print(f"   - {file.name} ({file.stat().st_size} bytes)")
            elif file.is_dir():
                sub_files = list(file.iterdir())
                print(f"   - {file.name}/ ({len(sub_files)}개 파일)")
                for sub_file in sub_files[:5]:  # 최대 5개만 표시
                    print(f"     - {sub_file.name} ({sub_file.stat().st_size} bytes)")
                if len(sub_files) > 5:
                    print(f"     ... 및 {len(sub_files) - 5}개 더")
    else:
        print("   - 템플릿 출력 디렉토리가 존재하지 않습니다.")
    
    return result


def check_job_status(server_url: str, job_id: str) -> Optional[Dict[str, Any]]:
    """작업 상태 확인"""
    try:
        url = f"{server_url}/jobs/{job_id}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[WARNING] 작업 상태 확인 실패: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"[WARNING] 작업 상태 확인 실패: {e}")
        return None


def main():
    """메인 함수 - 기본 테스트 데이터로 실행"""
    project_root = get_project_root()
    
    # 기본 테스트 데이터 경로 설정
    cad_path = str(project_root / "static" / "meshes" / "test" / "obj_000005.ply")
    
    # 템플릿 출력 디렉토리 설정 (CAD 파일명으로 폴더 생성)
    cad_filename = Path(cad_path).stem  # obj_000005
    template_output_dir = str(project_root / "static" / "templates" / "test" / cad_filename)
    
    # Render 서버 상태 확인
    print("[INFO] Render 서버 상태 확인 중...")
    
    try:
        response = requests.get("http://localhost:8004/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("[SUCCESS] Render 서버가 정상적으로 실행 중입니다.")
            print(f"   - 상태: {data.get('status', 'unknown')}")
        else:
            print(f"[ERROR] Render 서버 상태 확인 실패: {response.status_code}")
            return
    except Exception as e:
        print(f"[ERROR] Render 서버 연결 실패: {e}")
        return
    
    print("\n" + "=" * 50)
    
    # Render 서버 테스트 실행
    result = test_render_only(
        cad_path=cad_path,
        template_output_dir=template_output_dir,
        server_url="http://localhost:8004",
        wait=True,
        wait_timeout_sec=3600
    )
    
    if result:
        print("\n" + "=" * 50)
        print("[SUCCESS] Render 서버 테스트 완료!")
        if result.get('processing_time'):
            print(f"   - 처리 시간: {result['processing_time']:.3f}초")
        if result.get('templates_generated'):
            print(f"   - 생성된 템플릿 수: {result['templates_generated']}")
    else:
        print("\n" + "=" * 50)
        print("[ERROR] Render 서버 테스트 실패!")


def example_usage():
    """사용 예시 함수"""
    project_root = get_project_root()
    
    # 사용자 정의 경로 설정 예시
    custom_cad_path = str(project_root / "static" / "meshes" / "test" / "obj_000005.ply")
    custom_template_output_dir = str(project_root / "static" / "templates" / "test" / "custom_obj")
    
    # Render 서버 호출 예시
    result = test_render_only(
        cad_path=custom_cad_path,
        template_output_dir=custom_template_output_dir,
        server_url="http://localhost:8004",
        wait=True,
        wait_timeout_sec=3600
    )
    
    return result


def batch_render_meshes():
    """static/meshes/test/ 안의 모든 CAD 파일에 대해 템플릿 생성"""
    project_root = get_project_root()
    meshes_dir = project_root / "static" / "meshes" / "test"
    templates_base_dir = project_root / "static" / "templates" / "test"
    
    if not meshes_dir.exists():
        print(f"[ERROR] 메시 디렉토리가 존재하지 않습니다: {meshes_dir}")
        return
    
    # 지원하는 CAD 파일 확장자
    supported_extensions = ['.ply', '.obj', '.stl']
    
    # CAD 파일 찾기
    cad_files = []
    for ext in supported_extensions:
        cad_files.extend(meshes_dir.glob(f"*{ext}"))
    
    if not cad_files:
        print(f"[ERROR] {meshes_dir}에서 CAD 파일을 찾을 수 없습니다.")
        print(f"   지원하는 확장자: {supported_extensions}")
        return
    
    print(f"[INFO] {len(cad_files)}개의 CAD 파일을 발견했습니다.")
    
    # 각 CAD 파일에 대해 템플릿 생성
    for cad_file in cad_files:
        print(f"\n{'='*60}")
        print(f"[INFO] 처리 중: {cad_file.name}")
        print(f"{'='*60}")
        
        # CAD 파일명으로 템플릿 디렉토리 생성
        cad_filename = cad_file.stem
        template_output_dir = templates_base_dir / cad_filename
        
        result = test_render_only(
            cad_path=str(cad_file),
            template_output_dir=str(template_output_dir),
            server_url="http://localhost:8004",
            wait=True,
            wait_timeout_sec=3600
        )
        
        if result:
            print(f"[SUCCESS] {cad_file.name} 템플릿 생성 완료!")
        else:
            print(f"[ERROR] {cad_file.name} 템플릿 생성 실패!")


if __name__ == "__main__":
    main()
