#!/usr/bin/env python3
"""
Static 폴더 스캔 서비스
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from ..utils.file_utils import (
        get_project_root, get_file_size, get_last_modified,
        get_template_file_counts, list_files_in_dir
    )
    from ..utils.path_utils import get_static_paths
except ImportError:  # 패키지 상위 컨텍스트 없이 실행되는 경우 대비
    from utils.file_utils import (
        get_project_root, get_file_size, get_last_modified,
        get_template_file_counts, list_files_in_dir
    )
    from utils.path_utils import get_static_paths


class StaticScanner:
    """Static 폴더를 스캔하여 객체 정보를 수집하는 클래스"""
    
    def __init__(self):
        self.paths = get_static_paths()
    
    def scan_all_classes(self) -> List[Dict[str, Any]]:
        """모든 클래스 스캔
        
        Returns:
            List[Dict]: 클래스 정보 목록
        """
        classes = []
        meshes_dir = self.paths["meshes"]
        templates_dir = self.paths["templates"]
        
        if not meshes_dir.exists():
            return classes
        
        # 메시 디렉토리의 각 클래스 폴더 스캔
        for class_dir in sorted(meshes_dir.iterdir()):
            if class_dir.is_dir():
                class_name = class_dir.name
                class_info = self.scan_class(class_name)
                if class_info:
                    classes.append(class_info)
        
        return classes
    
    def scan_class(self, class_name: str) -> Optional[Dict[str, Any]]:
        """특정 클래스 스캔
        
        Args:
            class_name: 클래스 이름
            
        Returns:
            Dict: 클래스 정보 또는 None
        """
        meshes_class_dir = self.paths["meshes"] / class_name
        templates_class_dir = self.paths["templates"] / class_name
        
        if not meshes_class_dir.exists():
            return None
        
        # CAD 파일 스캔 - 여러 형식 지원
        cad_files = []
        for ext in ['.ply', '.obj', '.stl']:
            cad_files.extend(list_files_in_dir(meshes_class_dir, f"*{ext}"))
        
        if not cad_files:
            return None
        
        # 객체 정보 수집
        objects = []
        template_count = 0
        
        for cad_file in cad_files:
            object_name = cad_file.stem
            object_info = self.scan_object(class_name, object_name)
            if object_info:
                objects.append(object_info)
                if object_info["has_template"]:
                    template_count += 1
        
        # 클래스 요약
        return {
            "name": class_name,
            "path": str(meshes_class_dir),
            "object_count": len(objects),
            "template_count": template_count,
            "template_completion_rate": (template_count / len(objects) * 100) if objects else 0.0,
            "objects": objects
        }
    
    def scan_object(self, class_name: str, object_name: str) -> Optional[Dict[str, Any]]:
        """특정 객체 스캔
        
        Args:
            class_name: 클래스 이름
            object_name: 객체 이름
            
        Returns:
            Dict: 객체 정보 또는 None
        """
        # CAD 파일 정보 - 여러 형식 지원
        cad_file = None
        for ext in ['.ply', '.obj', '.stl']:
            candidate = self.paths["meshes"] / class_name / f"{object_name}{ext}"
            if candidate.exists():
                cad_file = candidate
                break
        
        if not cad_file or not cad_file.exists():
            return None
        
        cad_info = {
            "name": object_name,
            "cad_file": cad_file.name,
            "cad_path": str(cad_file),
            "cad_size_bytes": get_file_size(cad_file),
            "cad_last_modified": get_last_modified(cad_file)
        }
        
        # 템플릿 정보
        template_dir = self.paths["templates"] / class_name / object_name
        has_template = template_dir.exists() and len(list_files_in_dir(template_dir, "*")) > 0
        
        template_files = get_template_file_counts(template_dir) if has_template else {
            "mask_count": 0,
            "rgb_count": 0,
            "xyz_count": 0,
            "total_count": 0
        }
        
        template_info = {
            "template_path": str(template_dir) if has_template else None,
            "has_template": has_template,
            "template_files": template_files,
            "last_generated": get_last_modified(template_dir) if has_template else None
        }
        
        # 상태 결정
        if has_template:
            status = "ready"
        else:
            status = "needs_template"
        
        return {
            **cad_info,
            **template_info,
            "status": status
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """전체 통계 정보 반환
        
        Returns:
            Dict: 통계 정보
        """
        classes = self.scan_all_classes()
        
        total_classes = len(classes)
        total_objects = sum(c["object_count"] for c in classes)
        total_templates = sum(c["template_count"] for c in classes)
        
        completion_rate = (total_templates / total_objects * 100) if total_objects > 0 else 0.0
        
        return {
            "total_classes": total_classes,
            "total_objects": total_objects,
            "total_templates": total_templates,
            "overall_completion_rate": completion_rate
        }


# 전역 스캐너 인스턴스
_scanner = None

def get_scanner() -> StaticScanner:
    """스캐너 인스턴스 반환 (싱글톤)"""
    global _scanner
    if _scanner is None:
        _scanner = StaticScanner()
    return _scanner


