#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSSServer connector: fetch and save endpoints from a running RSS server.

Endpoints fetched under the given base URL:
  - streams/color_jpeg      -> color.jpg
  - streams/depth_jpeg      -> depth.jpg
  - camera/calibration      -> camera_calibration.json
  - camera/status           -> camera_status.json

Usage examples:
  python rss_connector_save.py --host 192.168.0.197 --port 51000 --out static/output/rss_capture
  python rss_connector_save.py --base http://192.168.0.197:51000 --out ./rss_dump
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict

import requests


def build_base_url(host: str | None, port: int | None, base: str | None) -> str:
    if base:
        return base.rstrip('/')
    if not host:
        host = '127.0.0.1'
    if not port:
        port = 51000
    return f"http://{host}:{port}"


def fetch_binary(url: str) -> bytes:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.content


def fetch_json(url: str) -> Dict:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    # Some servers return text/plain with JSON body; try json() first, fallback to loads()
    try:
        return r.json()
    except Exception:
        return json.loads(r.text)


def save_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def save_json(path: Path, obj: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description='Fetch and save RSSServer endpoints.')
    parser.add_argument('--host', type=str, default=None, help='RSS server host (e.g., 192.168.0.197)')
    parser.add_argument('--port', type=int, default=None, help='RSS server port (e.g., 51000)')
    parser.add_argument('--base', type=str, default=None, help='Full base URL (e.g., http://192.168.0.197:51000)')
    parser.add_argument('--out', type=str, default='static/output/rss_capture', help='Output directory')
    args = parser.parse_args()

    base_url = build_base_url(args.host, args.port, args.base)
    out_dir = Path(args.out)

    print(f"[INFO] Base URL: {base_url}")
    print(f"[INFO] Output   : {out_dir}")

    # Endpoints mapping to output filenames
    endpoints = [
        ("streams/color_jpeg", out_dir / 'color.jpg', 'binary'),
        ("streams/depth_jpeg", out_dir / 'depth.jpg', 'binary'),
        ("camera/calibration", out_dir / 'camera_calibration.json', 'json'),
        ("camera/status", out_dir / 'camera_status.json', 'json'),
    ]

    for path, out_path, kind in endpoints:
        url = f"{base_url}/{path}"
        try:
            print(f"[FETCH] {url}")
            if kind == 'binary':
                data = fetch_binary(url)
                save_file(out_path, data)
            else:
                obj = fetch_json(url)
                save_json(out_path, obj)
            size = os.path.getsize(out_path)
            print(f"[OK] Saved -> {out_path} ({size} bytes)")
        except Exception as e:
            print(f"[ERROR] Failed to fetch {url}: {e}")

    print("[DONE] Capture complete.")


if __name__ == '__main__':
    main()


