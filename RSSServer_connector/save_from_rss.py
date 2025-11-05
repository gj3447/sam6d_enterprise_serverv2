#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch and save data from an RSSServer at a given base address.

Targets (relative to base):
  - streams/color_jpeg      -> color.jpg
  - streams/depth_jpeg      -> depth.jpg
  - camera/calibration      -> camera_calibration.json
  - camera/status           -> camera_status.json

Usage examples:
  python save_from_rss.py --base http://192.168.0.197:51000 --out ../static/output/rss_capture
  python save_from_rss.py --host 192.168.0.197 --port 51000 --out ../static/output/rss_capture
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple, Optional

import requests
import numpy as np
from PIL import Image


def build_base_url(host: str | None, port: int | None, base: str | None) -> str:
    if base:
        return base.rstrip('/')
    host = host or '192.168.0.197'
    port = port or 51000
    return f"http://{host}:{port}"


def fetch_binary(url: str) -> bytes:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.content


def fetch_json(url: str) -> Dict:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return json.loads(r.text)


def save_binary(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def save_json(path: Path, obj: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def main() -> None:
    ap = argparse.ArgumentParser(description='Save RSSServer streams and camera info')
    ap.add_argument('--host', type=str, default=None)
    ap.add_argument('--port', type=int, default=None)
    ap.add_argument('--base', type=str, default=None)
    # Default to a folder inside RSSServer_connector/output (requested)
    default_out = (Path(__file__).parent / 'output').as_posix()
    ap.add_argument('--out', type=str, default=default_out)
    ap.add_argument('--flat', action='store_true', help='Do not create a timestamped subfolder')
    ap.add_argument('--align_color', action='store_true', default=True, help='Produce depth aligned to color frame if extrinsics available (default: on)')
    # Auto-infer via Main_Server
    ap.add_argument('--class_name', type=str, default=None, help='YCB class name (e.g., ycb) for auto inference')
    ap.add_argument('--object_name', type=str, default=None, help='Object/mesh name (e.g., obj_000004) for auto inference')
    ap.add_argument('--main_url', type=str, default='http://localhost:8001', help='Main_Server base URL to call full-pipeline')
    args = ap.parse_args()

    base_url = build_base_url(args.host, args.port, args.base)
    base_out = Path(args.out)
    if args.flat:
        out_dir = base_out
    else:
        from datetime import datetime
        out_dir = base_out / datetime.now().strftime('%Y%m%d_%H%M%S')

    print(f"[INFO] Base URL: {base_url}")
    print(f"[INFO] Output  : {out_dir}")

    jobs = [
        ("streams/color_jpeg", out_dir / 'color.jpg', 'bin'),
        ("streams/depth_jpeg", out_dir / 'depth.jpg', 'bin'),
        ("camera/calibration", out_dir / 'camera_calibration.json', 'json'),
        ("camera/status", out_dir / 'camera_status.json', 'json'),
    ]

    for rel, dst, kind in jobs:
        url = f"{base_url}/{rel}"
        try:
            print(f"[GET] {url}")
            if kind == 'bin':
                data = fetch_binary(url)
                save_binary(dst, data)
            else:
                obj = fetch_json(url)
                save_json(dst, obj)
            print(f"[OK ] Saved: {dst}")
        except Exception as e:
            print(f"[ERR] {url}: {e}")

    # Compose camera.json (cam_K + depth_scale) compatible with test files
    try:
        calib_path = out_dir / 'camera_calibration.json'
        status_path = out_dir / 'camera_status.json'
        cam_K = None
        depth_scale = None
        color_cam_K = None
        depth_cam_K = None
        T_depth_to_color = None  # 4x4

        def extract_K(js: Dict) -> np.ndarray | None:
            # helper: recursively search for 3x3 matrix in common calibration formats
            def try_make_mat(val) -> np.ndarray | None:
                try:
                    if isinstance(val, dict) and 'data' in val:
                        arr = np.array(val['data'], dtype=float).reshape(3, 3)
                        return arr
                    arr = np.array(val, dtype=float)
                    if arr.size == 9:
                        return arr.reshape(3, 3)
                except Exception:
                    return None
                return None

            # direct keys, including variations
            for key in ['K', 'CamK', 'camK', 'cam_K', 'camera_matrix', 'intrinsic_matrix', 'color_camera_matrix', 'depth_camera_matrix']:
                if key in js:
                    mat = try_make_mat(js[key])
                    if mat is not None:
                        return mat

            # OpenCV/Realsense style nested dicts
            # Prefer depth intrinsics by default
            for key in ['depth_intrinsics', 'depth', 'color_intrinsics', 'color', 'rgb', 'camera', 'intrinsics', 'left', 'right']:
                if key in js and isinstance(js[key], dict):
                    sub = js[key]
                    # Direct fx,fy,ppx,ppy (Intel RealSense style)
                    fx = sub.get('fx'); fy = sub.get('fy')
                    cx = sub.get('cx', sub.get('ppx'))
                    cy = sub.get('cy', sub.get('ppy'))
                    if all(v is not None for v in [fx, fy, cx, cy]):
                        return np.array([[float(fx), 0.0, float(cx)], [0.0, float(fy), float(cy)], [0.0, 0.0, 1.0]])
                    m = extract_K(sub)
                    if m is not None:
                        return m

            # Separate fx, fy, cx, cy
            intr = js.get('intrinsics') or js
            fx = intr.get('fx'); fy = intr.get('fy')
            cx = intr.get('cx', intr.get('ppx'))
            cy = intr.get('cy', intr.get('ppy'))
            if all(v is not None for v in [fx, fy, cx, cy]):
                return np.array([[float(fx), 0.0, float(cx)], [0.0, float(fy), float(cy)], [0.0, 0.0, 1.0]])
            return None

        def extract_extrinsics(js: Dict) -> Optional[np.ndarray]:
            # Try common structures to obtain 4x4 depth->color transform
            def from_rt(rot, trans) -> Optional[np.ndarray]:
                try:
                    R = np.array(rot, dtype=float)
                    if R.size == 9:
                        R = R.reshape(3, 3)
                    t = np.array(trans, dtype=float).reshape(3)
                    T = np.eye(4, dtype=float)
                    T[:3, :3] = R
                    T[:3, 3] = t
                    return T
                except Exception:
                    return None

            # flat keys (support common aliases)
            for k in ['T_depth_to_color', 'T_dc', 'extrinsic_depth_to_color', 'depth_to_color', 'depth_to_color_extrinsics']:
                if k in js:
                    node = js[k]
                    if isinstance(node, dict):
                        R = node.get('R') or node.get('rotation') or node.get('rot')
                        t = node.get('t') or node.get('translation')
                        T = from_rt(R, t)
                        if T is not None:
                            return T
                        if 'matrix' in node:
                            try:
                                M = np.array(node['matrix'], dtype=float)
                                if M.size == 16:
                                    return M.reshape(4, 4)
                            except Exception:
                                pass
                    else:
                        try:
                            M = np.array(node, dtype=float)
                            if M.size == 16:
                                return M.reshape(4, 4)
                        except Exception:
                            pass

            # nested candidates
            for k in ['extrinsics', 'calibration', 'transforms']:
                if k in js and isinstance(js[k], dict):
                    sub = js[k]
                    for kk in ['depth_to_color', 'DepthToColor', 'depth2color', 'T_depth_to_color', 'depth_to_color_extrinsics']:
                        if kk in sub:
                            node = sub[kk]
                            if isinstance(node, dict):
                                R = node.get('R') or node.get('rotation') or node.get('rot')
                                t = node.get('t') or node.get('translation')
                                T = from_rt(R, t)
                                if T is not None:
                                    return T
                                if 'matrix' in node:
                                    try:
                                        M = np.array(node['matrix'], dtype=float)
                                        if M.size == 16:
                                            return M.reshape(4, 4)
                                    except Exception:
                                        pass
            return None

        def extract_depth_scale(js: Dict) -> float | None:
            # Common keys
            for k in ['depth_scale', 'depthScale', 'depth_unit', 'depthUnit', 'depth_scale_mm']:
                if k in js:
                    val = js[k]
                    try:
                        v = float(val)
                        # direct numeric scale provided
                        return v
                    except Exception:
                        pass
                    # string units
                    if isinstance(val, str):
                        low = val.lower()
                        if low in ['mm', 'millimeter', 'millimetre']:
                            return 1.0  # values in mm → our code divides by 1000 later
                        if low in ['m', 'meter', 'metre']:
                            return 1000.0  # values in meters → convert to mm-equivalent scale
            return None

        calib = None
        status = None
        if calib_path.exists():
            calib = json.loads(calib_path.read_text(encoding='utf-8'))
            _k = extract_K(calib)
            if _k is not None:
                cam_K = _k
            # explicit depth/color intrinsics
            if isinstance(calib.get('depth_intrinsics'), dict):
                di = calib['depth_intrinsics']
                fx, fy = di.get('fx'), di.get('fy')
                cx = di.get('cx', di.get('ppx'))
                cy = di.get('cy', di.get('ppy'))
                if all(v is not None for v in [fx, fy, cx, cy]):
                    depth_cam_K = np.array([[float(fx), 0.0, float(cx)], [0.0, float(fy), float(cy)], [0.0, 0.0, 1.0]])
            # try color intrinsics explicitly for alternative output
            if isinstance(calib.get('color_intrinsics'), dict):
                ci = calib['color_intrinsics']
                fx, fy = ci.get('fx'), ci.get('fy')
                cx = ci.get('cx', ci.get('ppx'))
                cy = ci.get('cy', ci.get('ppy'))
                if all(v is not None for v in [fx, fy, cx, cy]):
                    color_cam_K = np.array([[float(fx), 0.0, float(cx)], [0.0, float(fy), float(cy)], [0.0, 0.0, 1.0]])
            _ds = extract_depth_scale(calib)
            if _ds is not None:
                depth_scale = _ds
            Td2c = extract_extrinsics(calib)
            if Td2c is not None:
                T_depth_to_color = Td2c
        if status_path.exists():
            status = json.loads(status_path.read_text(encoding='utf-8'))
            _k = extract_K(status)
            if _k is not None:
                cam_K = _k
            _ds = extract_depth_scale(status)
            if _ds is not None:
                depth_scale = _ds
            if T_depth_to_color is None:
                Td2c = extract_extrinsics(status)
                if Td2c is not None:
                    T_depth_to_color = Td2c

        # save extrinsics if found for transparency/debugging
        try:
            if T_depth_to_color is not None:
                extri = {
                    'matrix_4x4': T_depth_to_color.tolist()
                }
                save_json(out_dir / 'extrinsics_depth_to_color.json', extri)
                print(f"[OK ] Saved: {out_dir / 'extrinsics_depth_to_color.json'}")
            else:
                print('[WARN] No depth->color extrinsics found in calibration/status')
        except Exception as e:
            print(f"[WARN] Failed to save extrinsics: {e}")

        if cam_K is None:
            raise RuntimeError('Could not infer intrinsic matrix from calibration/status')
        if depth_scale is None:
            depth_scale = 1.0

        camera_json = {
            'cam_K': [float(cam_K[0,0]), 0.0, float(cam_K[0,2]), 0.0, float(cam_K[1,1]), float(cam_K[1,2]), 0.0, 0.0, 1.0],
            'depth_scale': float(depth_scale)
        }
        # If color intrinsics are available, prefer color K for single-folder (color-frame) pipeline
        if 'color_intrinsics' in (calib or {}) and isinstance(color_cam_K, np.ndarray):
            camera_json['cam_K'] = [float(color_cam_K[0,0]), 0.0, float(color_cam_K[0,2]), 0.0, float(color_cam_K[1,1]), float(color_cam_K[1,2]), 0.0, 0.0, 1.0]
        save_json(out_dir / 'camera.json', camera_json)
        print(f"[OK ] Saved: {out_dir / 'camera.json'}")

        # Single-folder mode: do not create a separate _color folder
    except Exception as e:
        print(f"[WARN] camera.json generation skipped: {e}")

    # Try fetch raw color stream and save as PNG
    try:
        # Load resolution from calibration or status
        calib_path = out_dir / 'camera_calibration.json'
        status_path = out_dir / 'camera_status.json'
        width: Optional[int] = None
        height: Optional[int] = None
        if calib_path.exists():
            calib = json.loads(calib_path.read_text(encoding='utf-8'))
            # Common keys
            width = calib.get('image_width') or calib.get('width') or calib.get('img_width')
            height = calib.get('image_height') or calib.get('height') or calib.get('img_height')
        if (width is None or height is None) and status_path.exists():
            status = json.loads(status_path.read_text(encoding='utf-8'))
            width = width or status.get('image_width') or status.get('width')
            height = height or status.get('image_height') or status.get('height')

        raw_url = f"{base_url}/streams/color_raw"
        print(f"[GET] {raw_url}")
        raw = fetch_binary(raw_url)

        if width is None or height is None:
            # Fallback: infer from saved color.jpg
            jpg_path = out_dir / 'color.jpg'
            if jpg_path.exists():
                with Image.open(jpg_path) as im:
                    width, height = im.size
            else:
                raise RuntimeError('Width/Height unknown; cannot decode raw. Please ensure calibration/status contains resolution or color.jpg exists.')

        expected = int(width) * int(height) * 3
        if len(raw) < expected:
            raise RuntimeError(f'Raw size {len(raw)} < expected {expected} for {width}x{height}x3')

        arr = np.frombuffer(raw[:expected], dtype=np.uint8).reshape((int(height), int(width), 3))
        # Many RGB cameras serve raw as BGR; convert to RGB for viewing
        arr_rgb = arr[..., ::-1]
        img = Image.fromarray(arr_rgb, mode='RGB')
        png_path = out_dir / 'color_raw.png'
        img.save(png_path)
        # Also keep the un-swapped preview for debugging
        Image.fromarray(arr, mode='RGB').save(out_dir / 'color_raw_bgr_preview.png')
        print(f"[OK ] Saved: {png_path}")
        # single-folder: no mirroring
    except Exception as e:
        print(f"[WARN] color_raw PNG save skipped: {e}")

    # Try fetch raw depth stream (Z16) and save as 16-bit PNG
    try:
        calib_path = out_dir / 'camera_calibration.json'
        status_path = out_dir / 'camera_status.json'
        width: Optional[int] = None
        height: Optional[int] = None
        if calib_path.exists():
            calib = json.loads(calib_path.read_text(encoding='utf-8'))
            width = calib.get('depth_width') or calib.get('image_width') or calib.get('width')
            height = calib.get('depth_height') or calib.get('image_height') or calib.get('height')
        if (width is None or height is None) and status_path.exists():
            status = json.loads(status_path.read_text(encoding='utf-8'))
            width = width or status.get('depth_width') or status.get('image_width') or status.get('width')
            height = height or status.get('depth_height') or status.get('image_height') or status.get('height')

        # fallback from color if still missing
        if width is None or height is None:
            jpg_path = out_dir / 'color.jpg'
            if jpg_path.exists():
                with Image.open(jpg_path) as im:
                    width, height = im.size
        if width is None or height is None:
            raise RuntimeError('Width/Height unknown; cannot decode depth_raw.')

        raw_url = f"{base_url}/streams/depth_raw"
        print(f"[GET] {raw_url}")
        raw = fetch_binary(raw_url)

        expected = int(width) * int(height) * 2  # uint16
        if len(raw) < expected:
            raise RuntimeError(f'depth_raw size {len(raw)} < expected {expected} for {width}x{height}x2')

        depth = np.frombuffer(raw[:expected], dtype=np.uint16).reshape((int(height), int(width)))
        # Save original Z16 as 16-bit PNG
        depth_png = Image.fromarray(depth, mode='I;16')
        depth_png_path = out_dir / 'depth_raw.png'
        depth_png.save(depth_png_path)
        print(f"[OK ] Saved: {depth_png_path}")
        # Also keep the raw binary dump for debugging
        (out_dir / 'depth_raw.bin').write_bytes(raw[:expected])
        # single-folder: no mirroring
    except Exception as e:
        print(f"[WARN] depth_raw save skipped: {e}")

    # Optional: align depth to color frame if requested and calibration available
    try:
        if args.align_color:
            # prerequisites
            depth_png_path = out_dir / 'depth_raw.png'
            color_png_path = out_dir / 'color_raw.png'
            if not depth_png_path.exists() or not color_png_path.exists():
                raise RuntimeError('Missing depth_raw.png or color_raw.png for alignment')

            if T_depth_to_color is None:
                raise RuntimeError('No extrinsics (depth->color) found in calibration/status')
            if color_cam_K is None:
                raise RuntimeError('No color intrinsics found for alignment')
            if depth_cam_K is None:
                depth_cam_K = cam_K  # fallback

            # load images
            depth_img = np.array(Image.open(depth_png_path)).astype(np.float32)  # Z16 -> float
            H_d, W_d = depth_img.shape
            H_c, W_c = Image.open(color_png_path).size
            # Note: PIL .size returns (W, H)
            W_c, H_c = Image.open(color_png_path).size

            # convert to meters (assume input in mm if scale==1.0)
            # depth_scale here denotes mm-per-unit if string-based; be conservative
            z_m = depth_img / 1000.0

            fx_d, fy_d, cx_d, cy_d = float(depth_cam_K[0,0]), float(depth_cam_K[1,1]), float(depth_cam_K[0,2]), float(depth_cam_K[1,2])
            fx_c, fy_c, cx_c, cy_c = float(color_cam_K[0,0]), float(color_cam_K[1,1]), float(color_cam_K[0,2]), float(color_cam_K[1,2])

            # grid of depth pixels
            us = np.arange(W_d, dtype=np.float32)
            vs = np.arange(H_d, dtype=np.float32)
            uu, vv = np.meshgrid(us, vs)

            Z = z_m
            valid = Z > 0
            Xd = (uu - cx_d) / fx_d * Z
            Yd = (vv - cy_d) / fy_d * Z

            # transform to color
            R = T_depth_to_color[:3, :3]
            t = T_depth_to_color[:3, 3]
            Xc = R[0,0]*Xd + R[0,1]*Yd + R[0,2]*Z + t[0]
            Yc = R[1,0]*Xd + R[1,1]*Yd + R[1,2]*Z + t[1]
            Zc = R[2,0]*Xd + R[2,1]*Yd + R[2,2]*Z + t[2]

            # project
            uc = fx_c * (Xc / (Zc + 1e-9)) + cx_c
            vc = fy_c * (Yc / (Zc + 1e-9)) + cy_c

            # rasterize (nearest)
            aligned = np.zeros((int(H_c), int(W_c)), dtype=np.float32)
            # clamp and mask
            uc_i = np.rint(uc).astype(np.int32)
            vc_i = np.rint(vc).astype(np.int32)
            m = valid & (Zc > 0) & (uc_i >= 0) & (uc_i < int(W_c)) & (vc_i >= 0) & (vc_i < int(H_c))
            inds = np.where(m)
            rr = vc_i[inds]
            cc = uc_i[inds]
            # keep nearest depth per pixel
            flat_idx = rr * int(W_c) + cc
            order = np.argsort(Zc[inds])
            flat_idx = flat_idx[order]
            z_vals = Zc[inds][order]
            # fill with nearest
            seen = set()
            for i in range(len(flat_idx)):
                k = int(flat_idx[i])
                if k in seen:
                    continue
                seen.add(k)
                r = k // int(W_c)
                c = k % int(W_c)
                aligned[r, c] = z_vals[i]

            # save as 16-bit in millimeters
            aligned_mm = np.clip(np.rint(aligned * 1000.0), 0, 65535).astype(np.uint16)
            aligned_path = out_dir / 'depth_aligned_to_color.png'
            Image.fromarray(aligned_mm, mode='I;16').save(aligned_path)
            print(f"[OK ] Saved: {aligned_path}")

            # single-folder: no mirroring
    except Exception as e:
        print(f"[WARN] depth alignment skipped: {e}")

    # Optional: auto-run inference via Main_Server full pipeline
    try:
        if args.class_name and args.object_name:
            print('[INFO] Auto inference requested - preparing payload...')
            color_path = out_dir / 'color_raw.png'
            if not color_path.exists():
                color_path = out_dir / 'color.jpg'
            depth_path = out_dir / 'depth_aligned_to_color.png'
            if not depth_path.exists():
                depth_path = out_dir / 'depth_raw.png'
            if not depth_path.exists():
                depth_path = out_dir / 'depth.jpg'

            cam_path = out_dir / 'camera.json'
            if not (color_path.exists() and depth_path.exists() and cam_path.exists()):
                raise RuntimeError('Missing inputs for inference (color/depth/camera.json)')

            rgb_b64 = base64.b64encode(color_path.read_bytes()).decode('utf-8')
            depth_b64 = base64.b64encode(depth_path.read_bytes()).decode('utf-8')
            cam_params = json.loads(cam_path.read_text(encoding='utf-8'))

            payload = {
                'class_name': args.class_name,
                'object_name': args.object_name,
                'rgb_image': rgb_b64,
                'depth_image': depth_b64,
                'cam_params': cam_params,
            }

            url = f"{args.main_url.rstrip('/')}/api/v1/workflow/full-pipeline"
            print(f"[POST] {url} ({args.class_name}/{args.object_name})")
            resp = requests.post(url, json=payload, timeout=1800)
            print(f"[INFO] Pipeline response status: {resp.status_code}")
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = {'text': resp.text}
            (out_dir / 'pipeline_response.json').write_text(json.dumps(resp_json, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"[OK ] Saved: {out_dir / 'pipeline_response.json'}")
    except Exception as e:
        print(f"[WARN] auto inference skipped: {e}")

    print('[DONE] All endpoints fetched.')


if __name__ == '__main__':
    main()


