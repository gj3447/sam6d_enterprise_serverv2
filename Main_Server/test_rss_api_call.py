#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke test for RSS-based full pipeline API without specifying base/host/port.
It should default to http://192.168.0.197:51000 as configured in workflow_service.
"""
import json
import sys
import requests

BASE_URL = "http://localhost:8001"

def main():
    object_name = sys.argv[1] if len(sys.argv) > 1 else "obj_000002"
    payload = {
        "class_name": "ycb",
        "object_name": object_name,
        "align_color": True,
        "frame_guess": True,
    }
    r = requests.post(f"{BASE_URL}/api/v1/workflow/full-pipeline-from-rss", json=payload, timeout=900)
    print("[STATUS]", r.status_code)
    ct = r.headers.get("content-type", "")
    if ct.startswith("application/json"):
        try:
            print(json.dumps(r.json(), ensure_ascii=False, indent=2)[:2000])
        except Exception:
            print(r.text[:1000])
    else:
        print(r.text[:1000])

if __name__ == "__main__":
    main()


