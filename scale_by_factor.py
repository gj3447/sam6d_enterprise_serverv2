#!/usr/bin/env python3
"""
Scale OBJ meshes by an arbitrary factor while preserving faces/materials/UVs.

Usage:
  python scale_by_factor.py static/meshes/ycb/obj_000002.obj --factor 0.1
  python scale_by_factor.py static/meshes/ycb --factor 0.1 --all
"""
from pathlib import Path
import argparse
import numpy as np
from tqdm import tqdm
import shutil


def parse_obj_file(obj_path: Path):
    vertices = []
    texture_coords = []
    normals = []
    faces = []
    mtllib = None
    face_sections = []
    current_material = None
    current_faces = []

    with obj_path.open('r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            p = s.split()
            prefix, data = p[0], p[1:]
            if prefix == 'v' and len(data) >= 3:
                vertices.append([float(data[0]), float(data[1]), float(data[2])])
            elif prefix == 'vt' and len(data) >= 2:
                texture_coords.append([float(data[0]), float(data[1])])
            elif prefix == 'vn' and len(data) >= 3:
                normals.append([float(data[0]), float(data[1]), float(data[2])])
            elif prefix == 'f':
                faces.append(' '.join(data))
                current_faces.append(len(faces) - 1)
            elif prefix == 'mtllib':
                mtllib = ' '.join(data)
            elif prefix == 'usemtl':
                if current_faces:
                    face_sections.append((current_material, current_faces))
                    current_faces = []
                current_material = ' '.join(data)
    if current_faces:
        face_sections.append((current_material, current_faces))
    if not face_sections and faces:
        face_sections.append((None, list(range(len(faces)))))
    return {
        'vertices': np.array(vertices) if vertices else np.array([]),
        'texture_coords': texture_coords,
        'normals': normals,
        'faces': faces,
        'face_sections': face_sections,
        'mtllib': mtllib,
    }


def write_obj_file(obj_path: Path, data, vertices_transformed):
    with obj_path.open('w', encoding='utf-8') as f:
        f.write(f"# Scaled by factor\n")
        f.write(f"# Vertices: {len(vertices_transformed)}\n")
        f.write(f"# Texture coordinates: {len(data['texture_coords'])}\n")
        f.write(f"# Normals: {len(data['normals'])}\n")
        f.write(f"# Faces: {len(data['faces'])}\n")
        if data['mtllib']:
            f.write(f"mtllib {data['mtllib']}\n\n")
        for v in vertices_transformed:
            f.write(f"v {v[0]:.9f} {v[1]:.9f} {v[2]:.9f}\n")
        if data['texture_coords']:
            f.write("\n")
            for vt in data['texture_coords']:
                if len(vt) == 2:
                    f.write(f"vt {vt[0]:.9f} {vt[1]:.9f}\n")
                else:
                    f.write(f"vt {vt[0]:.9f} {vt[1]:.9f} {vt[2]:.9f}\n")
        if data['normals']:
            f.write("\n")
            for vn in data['normals']:
                f.write(f"vn {vn[0]:.9f} {vn[1]:.9f} {vn[2]:.9f}\n")
        f.write("\n")
        for material, face_indices in data['face_sections']:
            if material:
                f.write(f"usemtl {material}\n")
            for face_idx in face_indices:
                f.write(f"f {data['faces'][face_idx]}\n")


def scale_obj(obj_path: Path, factor: float, create_backup: bool = True):
    data = parse_obj_file(obj_path)
    V = data['vertices']
    if len(V) == 0:
        raise ValueError(f"No vertices in {obj_path}")
    V2 = V * factor
    if create_backup:
        backup = obj_path.with_name(obj_path.stem + f"_backup_scale{factor}.obj")
        if not backup.exists():
            shutil.copy2(obj_path, backup)
    write_obj_file(obj_path, data, V2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', type=str, help='OBJ file or directory')
    ap.add_argument('--factor', type=float, required=True, help='Scale factor (e.g., 0.1)')
    ap.add_argument('--all', action='store_true', help='Scale all .obj files in the directory')
    ap.add_argument('--no-backup', action='store_true', help="Don't create backup files")
    args = ap.parse_args()

    p = Path(args.input)
    if p.is_file():
        scale_obj(p, args.factor, create_backup=not args.no_backup)
        print(f"[OK] Scaled {p.name} by {args.factor}x")
        return
    if p.is_dir() and args.all:
        files = sorted(p.glob('*.obj'))
        for f in tqdm(files, desc=f"Scaling {args.factor}x"):
            scale_obj(f, args.factor, create_backup=not args.no_backup)
        print(f"[OK] Scaled {len(files)} files by {args.factor}x")
        return
    raise SystemExit('[ERROR] Provide a file path or use --all with a directory')


if __name__ == '__main__':
    main()


