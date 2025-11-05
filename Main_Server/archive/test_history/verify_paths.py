#!/usr/bin/env python3
"""
경로 검증 스크립트
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Main_Server.utils.path_utils import get_static_paths, get_project_root
from Main_Server.services.scanner import get_scanner
from Main_Server.services.workflow_service import get_workflow_service

def main():
    print("=" * 60)
    print("경로 및 기능 검증")
    print("=" * 60)
    
    # 1. 프로젝트 루트 확인
    print("\n[1] 프로젝트 루트:")
    project_root = get_project_root()
    print(f"   {project_root}")
    print(f"   존재: {project_root.exists()}")
    
    # 2. Static 경로 확인
    print("\n[2] Static 경로들:")
    paths = get_static_paths()
    for name, path in paths.items():
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"   {status} {name}: {path}")
    
    # 3. Mesh 관리 기능 확인
    print("\n[3] Mesh 관리 기능:")
    scanner = get_scanner()
    
    # 특정 객체 스캔
    obj_info = scanner.scan_object("test", "obj_000005")
    if obj_info:
        print(f"   ✓ 객체 스캔 성공")
        print(f"     - 이름: {obj_info['name']}")
        print(f"     - CAD 파일: {obj_info['cad_file']}")
        print(f"     - 템플릿 존재: {obj_info['has_template']}")
        print(f"     - 상태: {obj_info['status']}")
        if obj_info['has_template']:
            print(f"     - 템플릿 파일 수: {obj_info['template_files']['total_count']}")
    else:
        print("   ✗ 객체 스캔 실패")
    
    # 4. Output 경로 확인
    print("\n[4] Output 경로 설정:")
    workflow = get_workflow_service()
    
    # 테스트 출력 디렉토리
    test_output = paths["output"] / "test_run_12345"
    test_output.mkdir(parents=True, exist_ok=True)
    
    print(f"   ✓ 출력 디렉토리: {paths['output']}")
    print(f"   ✓ 테스트 디렉토리 생성: {test_output}")
    
    # Output 하위 구조 확인
    ism_output = test_output / "ism"
    pem_output = test_output / "pem"
    ism_output.mkdir(exist_ok=True)
    pem_output.mkdir(exist_ok=True)
    
    print(f"   ✓ ISM 출력: {ism_output}")
    print(f"   ✓ PEM 출력: {pem_output}")
    
    # 5. 경로 매핑 확인
    print("\n[5] 경로 매핑 (컨테이너):")
    
    def to_container_path(host_path: Path) -> str:
        project_root = get_project_root()
        rel = host_path.resolve().relative_to(project_root)
        return str(Path("/workspace/Estimation_Server").joinpath(rel).as_posix())
    
    test_cases = [
        ("meshes/test/obj_000005.ply", paths["meshes"] / "test" / "obj_000005.ply"),
        ("templates/test/obj_000005", paths["templates"] / "test" / "obj_000005"),
        ("output/test_run_12345", test_output),
    ]
    
    for name, host_path in test_cases:
        if host_path.exists():
            container_path = to_container_path(host_path)
            print(f"   {name}")
            print(f"     호스트: {host_path}")
            print(f"     컨테이너: {container_path}")
    
    print("\n" + "=" * 60)
    print("검증 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()

