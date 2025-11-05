#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch-run YCB inference for all objects using a saved test folder
containing color_raw.png, depth_raw.png, and camera.json.

Usage:
  python Main_Server/test_from_rss_ycb_all.py static/test/20251030_120201
  python Main_Server/test_from_rss_ycb_all.py static/test/20251030_120201 --range 2 6  # obj_000002..obj_000006
"""
import sys
import re
import json
import base64
from pathlib import Path
import requests

BASE_URL = "http://localhost:8001"


def b64(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode()


def list_ycb_objects(mesh_dir: Path) -> list[str]:
    objs = []
    pat = re.compile(r"obj_(\d{6})\.obj$")
    for f in sorted(mesh_dir.glob("obj_*.obj")):
        m = pat.search(f.name)
        if m:
            objs.append(f"obj_{m.group(1)}")
    return objs


def run_one(test_dir: Path, object_name: str) -> dict:
    color_path = test_dir / "color_raw.png"
    depth_path = test_dir / "depth_raw.png"
    cam_path = test_dir / "camera.json"
    payload = {
        "class_name": "ycb",
        "object_name": object_name,
        "rgb_image": b64(color_path),
        "depth_image": b64(depth_path),
        "cam_params": json.loads(cam_path.read_text(encoding="utf-8")),
    }
    r = requests.post(f"{BASE_URL}/api/v1/workflow/full-pipeline", json=payload, timeout=600)
    try:
        return r.json()
    except Exception:
        return {"success": False, "status_code": r.status_code, "text": r.text[:200]}


def main():
    test_dir = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path("static/test/20251030_120201")).resolve()
    mesh_dir = Path("static/meshes/ycb")

    # optional range arguments: start end inclusive for numeric ids
    rng = None
    if "--range" in sys.argv:
        i = sys.argv.index("--range")
        start = int(sys.argv[i+1])
        end = int(sys.argv[i+2])
        rng = (start, end)

    objs = list_ycb_objects(mesh_dir)
    if rng:
        filtered = []
        for name in objs:
            n = int(name.split("_")[-1])
            if rng[0] <= n <= rng[1]:
                filtered.append(name)
        objs = filtered

    print(f"[INFO] Total YCB objects: {len(objs)}")
    results_dir = test_dir / "batch_results.json"
    all_results = {}

    # check servers once
    try:
        status = requests.get(f"{BASE_URL}/api/v1/servers/status", timeout=10).json()
        print(f"[STATUS] overall={status.get('overall_status')}")
    except Exception as e:
        print("[WARN] status check failed:", e)

    for idx, name in enumerate(objs, 1):
        print(f"\n===== ({idx}/{len(objs)}) {name} =====")
        try:
            res = run_one(test_dir, name)
            all_results[name] = res.get("success", False)
        except Exception as e:
            print(f"[ERROR] {name} failed: {e}")
            all_results[name] = False
            continue
        # brief summary
        if isinstance(res, dict) and res.get("success") and isinstance(res.get("results"), dict):
            r2 = res["results"].get("results", {})
            ism_ok = r2.get("ism", {}).get("success")
            pem_ok = r2.get("pem", {}).get("success")
            print(f"ISM={ism_ok}, PEM={pem_ok}")
        else:
            print(str(res)[:200])

    results_dir.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"\n[DONE] Saved summary: {results_dir}")


if __name__ == "__main__":
    main()


