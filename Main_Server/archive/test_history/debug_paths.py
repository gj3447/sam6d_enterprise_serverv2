#!/usr/bin/env python3
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Main_Server.utils.path_utils import get_project_root, get_static_paths

print("=" * 60)
print("경로 진단")
print("=" * 60)

# Project root
root = get_project_root()
print(f"\n[1] Project Root: {root}")
print(f"    존재: {root.exists()}")

# Static paths
paths = get_static_paths()
print(f"\n[2] Static Paths:")
for name, path in paths.items():
    print(f"    {name}: {path}")
    print(f"         존재: {path.exists()}")

# Test files
print(f"\n[3] Test Files:")
test_rgb = paths["root"] / "static" / "test" / "rgb.png"
test_depth = paths["root"] / "static" / "test" / "depth.png"
test_camera = paths["root"] / "static" / "test" / "camera.json"

for name, path in [
    ("RGB", test_rgb),
    ("Depth", test_depth),
    ("Camera", test_camera)
]:
    print(f"    {name}: {path.exists()} - {path}")

# CAD file
cad_path = paths["meshes"] / "test" / "obj_000005.ply"
print(f"\n[4] CAD File:")
print(f"    {cad_path.exists()} - {cad_path}")

# Template
template_dir = paths["templates"] / "test" / "obj_000005"
print(f"\n[5] Template:")
print(f"    {template_dir.exists()} - {template_dir}")
if template_dir.exists():
    files = list(template_dir.iterdir())
    print(f"    파일 개수: {len(files)}")

print("\n" + "=" * 60)

