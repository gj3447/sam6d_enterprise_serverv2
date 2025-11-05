#!/usr/bin/env python3
"""
파일 유틸리티 함수
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


def get_project_root() -> Path:
    """프로젝트 루트 경로 반환"""
    return Path(__file__).resolve().parents[2]  # Main_Server의 부모의 부모 = Estimation_Server


def to_container_path(host_path: Path) -> str:
    """호스트 경로를 컨테이너 경로로 변환"""
    project_root = get_project_root()
    rel = host_path.resolve().relative_to(project_root)
    return str(Path("/workspace/Estimation_Server").joinpath(rel).as_posix())


def get_file_size(path: Path) -> int:
    """파일 크기 반환 (bytes)"""
    try:
        return path.stat().st_size if path.is_file() else 0
    except Exception:
        return 0


def get_last_modified(path: Path) -> Optional[str]:
    """파일 마지막 수정 시간 반환 (ISO 형식)"""
    try:
        timestamp = path.stat().st_mtime
        return datetime.fromtimestamp(timestamp).isoformat()
    except Exception:
        return None


def count_files_in_dir(directory: Path, pattern: str = "*") -> int:
    """디렉토리 내 파일 개수 반환"""
    try:
        if not directory.exists() or not directory.is_dir():
            return 0
        return len(list(directory.glob(pattern)))
    except Exception:
        return 0


def list_files_in_dir(directory: Path, pattern: str = "*") -> List[Path]:
    """디렉토리 내 파일 목록 반환"""
    try:
        if not directory.exists() or not directory.is_dir():
            return []
        return sorted(list(directory.glob(pattern)))
    except Exception:
        return []


def get_template_file_counts(template_dir: Path) -> Dict[str, int]:
    """템플릿 디렉토리의 파일 개수 반환 (파일 리스트가 아닌 개수만)"""
    counts = {
        "mask_count": count_files_in_dir(template_dir, "mask_*.png"),
        "rgb_count": count_files_in_dir(template_dir, "rgb_*.png"),
        "xyz_count": count_files_in_dir(template_dir, "xyz_*.npy"),
        "total_count": 0
    }
    
    # 전체 파일 개수
    try:
        if template_dir.exists() and template_dir.is_dir():
            counts["total_count"] = len(list(template_dir.iterdir()))
    except Exception:
        pass
    
    return counts


def ensure_dir(path: Path) -> Path:
    """디렉토리가 존재하도록 보장 (없으면 생성)"""
    path.mkdir(parents=True, exist_ok=True)
    return path


