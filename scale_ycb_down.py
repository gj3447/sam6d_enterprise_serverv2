#!/usr/bin/env python3
"""
YCB .obj 파일을 1000배 축소하는 스크립트 (mm → 원래 크기)
현재 mm 단위로 변환된 YCB 객체를 1000배 축소
"""
import numpy as np
from pathlib import Path
import argparse
from tqdm import tqdm
import shutil


def parse_obj_file(obj_path):
    """OBJ 파일을 파싱하여 구조화된 데이터 반환"""
    vertices = []
    texture_coords = []  # vt
    normals = []  # vn
    faces = []  # f
    mtllib = None
    face_sections = []  # (usemtl, face_indices) 또는 (None, face_indices)
    current_material = None
    current_faces = []
    
    with open(obj_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if not parts:
                continue
                
            prefix = parts[0]
            data = parts[1:]
            
            if prefix == 'v':  # 버텍스
                if len(data) >= 3:
                    vertices.append([float(data[0]), float(data[1]), float(data[2])])
            elif prefix == 'vt':  # 텍스처 좌표 (보존)
                if len(data) >= 2:
                    texture_coords.append([float(data[0]), float(data[1])])
            elif prefix == 'vn':  # 노멀 (보존)
                if len(data) >= 3:
                    normals.append([float(data[0]), float(data[1]), float(data[2])])
            elif prefix == 'f':  # 페이스
                faces.append(' '.join(data))
                current_faces.append(len(faces) - 1)
            elif prefix == 'mtllib':
                mtllib = ' '.join(data)
            elif prefix == 'usemtl':
                # 이전 섹션 저장
                if current_faces:
                    face_sections.append((current_material, current_faces))
                    current_faces = []
                current_material = ' '.join(data)
    
    # 마지막 섹션 저장
    if current_faces:
        face_sections.append((current_material, current_faces))
    
    # usemtl이 전혀 없는 경우 처리
    if not face_sections and faces:
        face_sections.append((None, list(range(len(faces)))))
    
    return {
        'vertices': np.array(vertices) if vertices else np.array([]),
        'texture_coords': texture_coords,
        'normals': normals,
        'faces': faces,
        'face_sections': face_sections,
        'mtllib': mtllib
    }


def write_obj_file(obj_path, data, vertices_transformed):
    """변환된 데이터를 OBJ 파일로 저장"""
    with open(obj_path, 'w', encoding='utf-8') as f:
        # 헤더
        f.write(f"# Scaled down by 1000x (mm to original units)\n")
        f.write(f"# Vertices: {len(vertices_transformed)}\n")
        f.write(f"# Texture coordinates: {len(data['texture_coords'])}\n")
        f.write(f"# Normals: {len(data['normals'])}\n")
        f.write(f"# Faces: {len(data['faces'])}\n")
        
        # mtllib
        if data['mtllib']:
            f.write(f"mtllib {data['mtllib']}\n")
        f.write("\n")
        
        # 버텍스 (변환된 버전)
        for v in vertices_transformed:
            f.write(f"v {v[0]:.9f} {v[1]:.9f} {v[2]:.9f}\n")
        
        # 텍스처 좌표 (원본 그대로)
        if data['texture_coords']:
            f.write("\n")
            for vt in data['texture_coords']:
                if len(vt) == 2:
                    f.write(f"vt {vt[0]:.9f} {vt[1]:.9f}\n")
                elif len(vt) == 3:
                    f.write(f"vt {vt[0]:.9f} {vt[1]:.9f} {vt[2]:.9f}\n")
        
        # 노멀 (원본 그대로)
        if data['normals']:
            f.write("\n")
            for vn in data['normals']:
                f.write(f"vn {vn[0]:.9f} {vn[1]:.9f} {vn[2]:.9f}\n")
        
        # usemtl과 페이스 (원본 순서 유지)
        f.write("\n")
        for material, face_indices in data['face_sections']:
            if material:
                f.write(f"usemtl {material}\n")
            for face_idx in face_indices:
                f.write(f"f {data['faces'][face_idx]}\n")


def scale_obj_down(obj_path, output_path=None, create_backup=True):
    """
    .obj 파일을 1000배 축소 (mm → 원래 크기)
    
    Args:
        obj_path: 입력 .obj 파일 경로
        output_path: 출력 .obj 파일 경로 (None이면 기존 파일 덮어쓰기)
        create_backup: 백업 파일 생성 여부
    """
    obj_path = Path(obj_path)
    
    if not obj_path.exists():
        raise FileNotFoundError(f"File not found: {obj_path}")
    
    print(f"\n[INFO] Processing: {obj_path.name}")
    
    # OBJ 파일 파싱
    print(f"[INFO] Parsing OBJ file...")
    data = parse_obj_file(obj_path)
    
    if len(data['vertices']) == 0:
        raise ValueError(f"No vertices found in {obj_path}")
    
    vertices = data['vertices']
    
    print(f"[INFO] Original mesh:")
    print(f"  Vertices: {len(vertices)}")
    print(f"  Texture coordinates: {len(data['texture_coords'])}")
    print(f"  Normals: {len(data['normals'])}")
    print(f"  Faces: {len(data['faces'])}")
    
    # 바운딩 박스 계산
    min_bounds = vertices.min(axis=0)
    max_bounds = vertices.max(axis=0)
    bounds_center = (min_bounds + max_bounds) / 2.0
    extents = max_bounds - min_bounds
    
    print(f"  Bounds: min={min_bounds}, max={max_bounds}")
    print(f"  Center: {bounds_center}")
    print(f"  Extents: {extents} (current units: mm)")
    
    # 이미 작은 크기인지 확인 (extents가 10보다 작으면 이미 축소된 것)
    is_already_small = extents.max() < 10.0
    
    if is_already_small:
        print(f"[INFO] Mesh appears to be already in original units (skipping)")
        return obj_path
    
    print(f"[INFO] Scaling down by 1000x (mm -> original units)")
    
    # 1000배 축소 (mm → 원래 크기)
    vertices_scaled = vertices / 1000.0
    
    # 변환 후 정보
    new_min_bounds = vertices_scaled.min(axis=0)
    new_max_bounds = vertices_scaled.max(axis=0)
    new_center = (new_min_bounds + new_max_bounds) / 2.0
    new_extents = new_max_bounds - new_min_bounds
    
    print(f"[INFO] Scaled mesh:")
    print(f"  Bounds: min={new_min_bounds}, max={new_max_bounds}")
    print(f"  Center: {new_center}")
    print(f"  Extents: {new_extents} (scaled units)")
    print(f"  Texture coordinates preserved: {len(data['texture_coords'])} (unchanged)")
    
    # 출력 경로 결정
    if output_path is None:
        output_path = obj_path
    else:
        output_path = Path(output_path)
    
    # 백업 생성
    if create_backup and output_path == obj_path:
        backup_path = obj_path.parent / f"{obj_path.stem}_mm_backup.obj"
        if not backup_path.exists():
            print(f"[INFO] Creating backup: {backup_path.name}")
            shutil.copy2(obj_path, backup_path)
        else:
            print(f"[INFO] Backup already exists: {backup_path.name}")
    
    # 변환된 OBJ 파일 저장
    print(f"[INFO] Saving scaled mesh to: {output_path.name}")
    write_obj_file(output_path, data, vertices_scaled)
    print(f"[INFO] Conversion complete!")
    
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scale down YCB .obj files by 1000x (from mm to original units)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", type=str, help="Input .obj file path or directory")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output path (default: overwrite input)")
    parser.add_argument("--all", "-a", action="store_true", help="Scale all .obj files in directory")
    parser.add_argument("--no-backup", action="store_true", help="Don't create backup files")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if args.all and input_path.is_dir():
        # 디렉토리 내 모든 .obj 파일 변환
        obj_files = sorted(list(input_path.glob("*.obj")))
        print(f"[INFO] Found {len(obj_files)} .obj files")
        
        if not obj_files:
            print(f"[ERROR] No .obj files found in {input_path}")
            exit(1)
        
        success_count = 0
        error_count = 0
        
        for obj_file in tqdm(obj_files, desc="Scaling files"):
            try:
                scale_obj_down(obj_file, create_backup=not args.no_backup)
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"\n[ERROR] Failed to scale {obj_file.name}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*60}")
        print(f"[INFO] Conversion summary:")
        print(f"  Successful: {success_count}")
        print(f"  Failed: {error_count}")
        print(f"  Total: {len(obj_files)}")
        print(f"{'='*60}")
                
    elif input_path.is_file():
        # 단일 파일 변환
        try:
            scale_obj_down(input_path, args.output, create_backup=not args.no_backup)
        except Exception as e:
            print(f"[ERROR] Conversion failed: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
    else:
        print(f"[ERROR] Input path not found: {input_path}")
        exit(1)

