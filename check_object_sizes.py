#!/usr/bin/env python3
"""YCB 객체들의 크기 확인 및 이상치 탐지"""
import trimesh
import numpy as np
from pathlib import Path

ycb_dir = Path("static/meshes/ycb")
obj_files = sorted([f for f in ycb_dir.glob("*.obj")])

sizes = []
for obj_file in obj_files:
    try:
        mesh = trimesh.load(str(obj_file))
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate([m for m in mesh.geometry.values()])
        
        extents = mesh.extents  # [width, height, depth]
        max_extent = extents.max()
        sizes.append((obj_file.name, max_extent))
    except Exception as e:
        print(f"Error loading {obj_file.name}: {e}")
        sizes.append((obj_file.name, -1))

# 크기순으로 정렬
sizes.sort(key=lambda x: x[1], reverse=True)

# 정상 크기 범위 (100-500mm)로 필터링해서 평균 계산
normal_sizes = [s for _, s in sizes if 50 < s < 500]
if normal_sizes:
    normal_avg = np.mean(normal_sizes)
    normal_std = np.std(normal_sizes)
    print(f"정상 크기 객체 수: {len(normal_sizes)}")
    print(f"정상 크기 평균: {normal_avg:.2f}mm")
    print(f"정상 크기 표준편차: {normal_std:.2f}mm")
    print(f"\n비정상적으로 큰 객체 (>500mm 또는 평균의 10배 이상):")
    print("-" * 70)
    
    threshold = max(500, normal_avg * 10)
    abnormal = [(name, size) for name, size in sizes if size > threshold]
    
    if abnormal:
        for name, size in abnormal:
            ratio = size / normal_avg if normal_avg > 0 else 0
            print(f"{name:30s} : {size:10.2f}mm ({ratio:6.1f}배 크다)")
        print(f"\n총 {len(abnormal)}개 객체가 비정상적으로 큽니다.")
    else:
        print("비정상적으로 큰 객체가 없습니다.")
else:
    print("정상 크기 객체를 찾을 수 없습니다.")

print(f"\n전체 객체 크기 분포:")
print("-" * 70)
for i, (name, size) in enumerate(sizes[:20], 1):
    if size > 0:
        status = "비정상" if size > 500 else "정상"
        print(f"{i:2d}. {name:30s} : {size:10.2f}mm [{status}]")
