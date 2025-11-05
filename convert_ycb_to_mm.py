#!/usr/bin/env python3
"""
YCB .obj 파일을 mm 단위로 변환하는 스크립트
현재 m 단위인 YCB 객체를 mm 단위로 변환 (1000배 스케일업)
"""
import trimesh
import numpy as np
from pathlib import Path
import argparse

def convert_obj_to_mm(obj_path, output_path=None):
    """
    .obj 파일을 mm 단위로 변환 (1000배 스케일업)
    
    Args:
        obj_path: 입력 .obj 파일 경로
        output_path: 출력 .obj 파일 경로 (None이면 기존 파일 백업 후 덮어쓰기)
    """
    obj_path = Path(obj_path)
    
    if not obj_path.exists():
        raise FileNotFoundError(f"File not found: {obj_path}")
    
    print(f"[INFO] Loading mesh: {obj_path}")
    mesh = trimesh.load(str(obj_path))
    
    # Scene인 경우 처리
    if isinstance(mesh, trimesh.Scene):
        print(f"[INFO] Converting Scene to Mesh...")
        mesh = trimesh.util.concatenate([
            trimesh.Trimesh(vertices=m.vertices, faces=m.faces)
            for m in mesh.geometry.values()
        ])
    
    # 텍스처/UV 정보 확인
    has_uv = hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None
    has_material = hasattr(mesh.visual, 'material') and mesh.visual.material is not None
    has_texture = False
    if has_material:
        has_texture = hasattr(mesh.visual.material, 'image') and mesh.visual.material.image is not None
    
    print(f"[INFO] Original mesh:")
    print(f"  Vertices: {len(mesh.vertices)}")
    print(f"  Faces: {len(mesh.faces)}")
    print(f"  Extents: {mesh.extents} (units: m, ~{mesh.extents*1000} mm)")
    print(f"  Bounds center: {mesh.bounds[0] + (mesh.bounds[1] - mesh.bounds[0]) / 2}")
    print(f"  Has UV coordinates: {has_uv}")
    print(f"  Has material: {has_material}")
    print(f"  Has texture image: {has_texture}")
    
    # UV 좌표 저장 (스케일링 후 복원용)
    uv_backup = None
    material_backup = None
    if has_uv:
        uv_backup = mesh.visual.uv.copy()
        print(f"  UV range: [{uv_backup.min(axis=0)}, {uv_backup.max(axis=0)}]")
    if has_material:
        material_backup = mesh.visual.material
    
    # 메시가 이미 mm 단위인지 확인 (extents가 100보다 크면 이미 mm 단위)
    is_mm_unit = mesh.extents.max() > 100.0
    if is_mm_unit:
        print(f"[INFO] Mesh is already in mm units (skipping scale conversion)")
    else:
        print(f"[INFO] Mesh is in m units (will convert to mm)")
        
        # 바운딩 박스 중심을 원점으로 이동 (스케일링 전)
        bounds_center = mesh.bounds[0] + (mesh.bounds[1] - mesh.bounds[0]) / 2
        print(f"[INFO] Moving mesh to origin (centering at bounding box center)")
        print(f"  Center: {bounds_center}")
        mesh.apply_translation(-bounds_center)
        print(f"  After centering - bounds center: {mesh.bounds[0] + (mesh.bounds[1] - mesh.bounds[0]) / 2}")
        
        # 1000배 스케일업 (m → mm)
        # 주의: apply_scale은 vertex만 변경하고 UV는 자동으로 유지됨
        mesh.apply_scale(1000.0)
    
    # mm 단위일 때만 원점 정렬 (이미 mm 단위인 경우)
    if is_mm_unit:
        bounds_center = mesh.bounds[0] + (mesh.bounds[1] - mesh.bounds[0]) / 2
        center_norm = np.linalg.norm(bounds_center)
        if center_norm > 1.0:  # 중심이 원점에서 1mm 이상 떨어져 있으면 정렬
            print(f"[INFO] Recentering mm-unit mesh to origin")
            print(f"  Current center: {bounds_center} (distance: {center_norm:.2f} mm)")
            mesh.apply_translation(-bounds_center)
            print(f"  After centering - bounds center: {mesh.bounds[0] + (mesh.bounds[1] - mesh.bounds[0]) / 2}")
    
    print(f"[INFO] After scaling (1000x):")
    print(f"  Extents: {mesh.extents} (units: mm)")
    print(f"  Bounds center: {mesh.bounds[0] + (mesh.bounds[1] - mesh.bounds[0]) / 2}")
    print(f"  Bounds: min={mesh.bounds[0]}, max={mesh.bounds[1]}")
    
    # UV 좌표 확인 (변경되지 않았는지)
    if has_uv:
        uv_after = mesh.visual.uv
        if uv_backup is not None:
            uv_preserved = np.allclose(uv_backup, uv_after, atol=1e-6)
            print(f"  UV coordinates preserved: {uv_preserved}")
            if not uv_preserved:
                print(f"    [WARNING] UV coordinates changed! Original range: [{uv_backup.min(axis=0)}, {uv_backup.max(axis=0)}]")
                print(f"    [WARNING] UV coordinates changed! After range: [{uv_after.min(axis=0)}, {uv_after.max(axis=0)}]")
    
    # 출력 경로 결정
    if output_path is None:
        # 백업 생성
        backup_path = obj_path.parent / f"{obj_path.stem}_backup.obj"
        print(f"[INFO] Creating backup: {backup_path}")
        if backup_path.exists():
            print(f"[WARNING] Backup file already exists, skipping backup")
        else:
            import shutil
            shutil.copy2(obj_path, backup_path)
        
        output_path = obj_path
    
    # .obj 파일로 저장
    print(f"[INFO] Saving scaled mesh to: {output_path}")
    mesh.export(str(output_path))
    print(f"[INFO] Conversion complete!")
    
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert YCB .obj files from meters to millimeters")
    parser.add_argument("input", type=str, help="Input .obj file path or directory")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output path (default: overwrite input with backup)")
    parser.add_argument("--all", "-a", action="store_true", help="Convert all .obj files in directory")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if args.all and input_path.is_dir():
        # 디렉토리 내 모든 .obj 파일 변환
        obj_files = list(input_path.glob("*.obj"))
        print(f"[INFO] Found {len(obj_files)} .obj files")
        
        for obj_file in obj_files:
            print(f"\n{'='*60}")
            print(f"Processing: {obj_file.name}")
            print(f"{'='*60}")
            try:
                convert_obj_to_mm(obj_file)
            except Exception as e:
                print(f"[ERROR] Failed to convert {obj_file.name}: {e}")
                
    elif input_path.is_file():
        # 단일 파일 변환
        convert_obj_to_mm(input_path, args.output)
    else:
        print(f"[ERROR] Input path not found: {input_path}")

