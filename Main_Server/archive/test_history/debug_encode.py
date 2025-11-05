#!/usr/bin/env python3
import sys
from pathlib import Path
import base64
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

project_root = Path(__file__).resolve().parents[1]
rgb_path = project_root / "static/test/rgb.png"
depth_path = project_root / "static/test/depth.png"
cam_path = project_root / "static/test/camera.json"

print(f"RGB path: {rgb_path}")
print(f"RGB exists: {rgb_path.exists()}")

print(f"\nDepth path: {depth_path}")
print(f"Depth exists: {depth_path.exists()}")

if rgb_path.exists():
    with open(rgb_path, "rb") as f:
        rgb_data = f.read()
        rgb_b64 = base64.b64encode(rgb_data).decode("utf-8")
        print(f"RGB Base64 length: {len(rgb_b64)}")
        print(f"RGB Base64 first 100 chars: {rgb_b64[:100]}")

if depth_path.exists():
    with open(depth_path, "rb") as f:
        depth_data = f.read()
        depth_b64 = base64.b64encode(depth_data).decode("utf-8")
        print(f"Depth Base64 length: {len(depth_b64)}")
        print(f"Depth Base64 first 100 chars: {depth_b64[:100]}")

