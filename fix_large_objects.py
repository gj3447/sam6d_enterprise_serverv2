#!/usr/bin/env python3
"""비정상적으로 큰 YCB 객체들을 1000배 축소하는 스크립트"""
import trimesh
import numpy as np
from pathlib import Path
import shutil

ycb_dir = Path("static/meshes/ycb")
obj_files = sorted([f for f in ycb_dir.glob("*.obj")])

# 정상 크기 범위 (50-500mm)로 평균 계산
normal_sizes = []
for obj_file in obj_files:
    try:
        mesh = trimesh.load(str(obj_file))
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate([m for m in mesh.geometry.values()])
        max_extent = mesh.extents.max()
        if 50 < max_extent < 500:
            normal_sizes.append(max_extent)
    except:
        pass

normal_avg = np.mean(normal_sizes) if normal_sizes else 188
threshold = max(500, normal_avg * 10)

print(f"정상 크기 평균: {normal_avg:.2f}mm")
print(f"임계값: {threshold:.2f}mm (이보다 큰 객체들을 수정)")
print("-" * 70)

# 비정상적으로 큰 파일들 찾기
abnormal_files = []
for obj_file in obj_files:
    try:
        mesh = trimesh.load(str(obj_file))
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate([m for m in mesh.geometry.values()])
        max_extent = mesh.extents.max()
        if max_extent > threshold:
            abnormal_files.append((obj_file, max_extent))
    except Exception as e:
        print(f"Error checking {obj_file.name}: {e}")

print(f"\n총 {len(abnormal_files)}개 파일을 수정합니다:")
for obj_file, size in abnormal_files[:10]:
    ratio = size / normal_avg
    print(f"  {obj_file.name:30s} : {size:10.2f}mm ({ratio:6.1f}배)")
if len(abnormal_files) > 10:
    print(f"  ... 외 {len(abnormal_files)-10}개 파일")

print("\n수정 시작...")
print("-" * 70)

success_count = 0
error_count = 0

for obj_file, size in abnormal_files:
    try:
        print(f"\n처리 중: {obj_file.name} ({size:.2f}mm)", end=" -> ")
        
        # 백업 생성 (이미 있으면 스킵)
        backup_path = obj_file.parent / f"{obj_file.stem}_backup.obj"
        if not backup_path.exists():
            shutil.copy2(obj_file, backup_path)
        
        # 메시 로드
        mesh = trimesh.load(str(obj_file))
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate([m for m in mesh.geometry.values()])
        
        # 1000배 축소
        original_vertices = mesh.vertices.copy()
        mesh.vertices = mesh.vertices / 1000.0
        
        # 저장
        mesh.export(str(obj_file))
        
        # 확인
        mesh_check = trimesh.load(str(obj_file))
        if isinstance(mesh_check, trimesh.Scene):
            mesh_check = trimesh.util.concatenate([m for m in mesh_check.geometry.values()])
        new_size = mesh_check.extents.max()
        print(f"{new_size:.2f}mm (축소율: {size/new_size:.1f}배)")
        success_count += 1
        
    except Exception as e:
        print(f"오류 발생: {e}")
        error_count += 1

print("\n" + "=" * 70)
print(f"완료: {success_count}개 성공, {error_count}개 실패")
if success_count > 0:
    print(f"\n백업 파일은 {ycb_dir} 폴더에 저장되었습니다.")
    print("예: obj_000007_backup.obj")
