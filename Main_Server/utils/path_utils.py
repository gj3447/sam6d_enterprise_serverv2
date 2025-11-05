#!/usr/bin/env python3
"""
경로 유틸리티 함수
"""
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """프로젝트 루트 경로 반환"""
    return Path(__file__).resolve().parents[2]  # Main_Server의 부모의 부모 = Estimation_Server


def get_static_paths() -> dict:
    """Static 폴더 경로 반환"""
    project_root = Path(__file__).resolve().parents[2]
    return {
        "root": project_root,
        "meshes": project_root / "static" / "meshes",
        "templates": project_root / "static" / "templates",
        "output": project_root / "static" / "output",
        "test": project_root / "static" / "test"
    }


def get_mesh_path(class_name: str, object_name: Optional[str] = None) -> Path:
    """메시 파일 경로 반환"""
    paths = get_static_paths()
    if object_name:
        return paths["meshes"] / class_name / f"{object_name}.ply"
    return paths["meshes"] / class_name


def get_template_path(class_name: str, object_name: Optional[str] = None) -> Path:
    """템플릿 디렉토리 경로 반환"""
    paths = get_static_paths()
    if object_name:
        return paths["templates"] / class_name / object_name
    return paths["templates"] / class_name


def get_output_path(run_id: Optional[str] = None) -> Path:
    """출력 디렉토리 경로 반환"""
    paths = get_static_paths()
    if run_id:
        return paths["output"] / run_id
    return paths["output"]


def is_valid_path(path: Path, must_exist: bool = False) -> bool:
    """경로 유효성 검사"""
    if must_exist:
        return path.exists()
    return path.parent.exists() if path.is_file() else True


def relative_to_project_root(path: Path) -> str:
    """프로젝트 루트 기준 상대 경로"""
    project_root = Path(__file__).resolve().parents[2]
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


