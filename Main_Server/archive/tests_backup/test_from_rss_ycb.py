#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Use saved RSS frames (color_raw.png, depth_raw.png, camera.json) to run YCB full pipeline.

Usage:
  python Main_Server/test_from_rss_ycb.py static/test/20251030_120201 obj_000002
"""
import sys
from pathlib import Path
import json
import base64
import requests

BASE_URL = "http://localhost:8001"


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def main():
    test_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("static/test/20251030_120201")
    object_name = sys.argv[2] if len(sys.argv) > 2 else "obj_000002"

    color_path = test_dir / "color_raw.png"
    depth_path = test_dir / "depth_raw.png"
    cam_path = test_dir / "camera.json"

    assert color_path.exists(), f"Missing: {color_path}"
    assert depth_path.exists(), f"Missing: {depth_path}"
    assert cam_path.exists(), f"Missing: {cam_path}"

    cam = json.loads(cam_path.read_text(encoding="utf-8"))

    payload = {
        "class_name": "ycb",
        "object_name": object_name,
        "rgb_image": b64(color_path),
        "depth_image": b64(depth_path),
        "cam_params": cam,
        "frame_guess": True,
    }

    # server status
    try:
        r = requests.get(f"{BASE_URL}/api/v1/servers/status", timeout=10)
        print("[STATUS]", r.status_code, r.text[:200])
    except Exception as e:
        print("[WARN] status check failed:", e)

    # run pipeline
    r = requests.post(f"{BASE_URL}/api/v1/workflow/full-pipeline", json=payload, timeout=600)
    print("[PIPELINE]", r.status_code)
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:2000])
    except Exception:
        print(r.text[:1000])


if __name__ == "__main__":
    main()


