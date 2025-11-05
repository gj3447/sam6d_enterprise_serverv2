#!/usr/bin/env python3
"""RSS에서 YCB 객체 25개를 순차 추론하는 유틸 스크립트."""

import json
import time
from pathlib import Path

import requests


def main():
    base_url = "http://localhost:8001/api/v1/workflow/full-pipeline-from-rss"
    rss_base = "http://192.168.0.197:51000"
    objects = [f"obj_{i:06d}" for i in range(2, 27)]  # obj_000002 ~ obj_000026

    print(f"[RSS BATCH] 총 {len(objects)}개 YCB 객체 순차 추론 시작")
    summary = []

    for idx, obj_name in enumerate(objects, start=1):
        payload = {
            "class_name": "ycb",
            "object_name": obj_name,
            "base": rss_base,
            "align_color": True,
            "frame_guess": True,
        }

        start = time.time()
        try:
            resp = requests.post(base_url, json=payload, timeout=900)
            elapsed = time.time() - start
            try:
                data = resp.json()
            except Exception:
                data = {"success": False, "message": resp.text}

            success = data.get("success", False) if isinstance(data, dict) else False
            results = data.get("results", {}) if isinstance(data, dict) else {}
            output_dir = results.get("output_dir") if isinstance(results, dict) else None
            steps = results.get("results", {}) if isinstance(results, dict) else {}
            ism = steps.get("ism", {}) if isinstance(steps, dict) else {}
            pem = steps.get("pem", {}) if isinstance(steps, dict) else {}

            ism_detections = None
            if isinstance(ism, dict):
                detections = ism.get("detections", {}) or {}
                masks = detections.get("masks", []) if isinstance(detections, dict) else []
                ism_detections = len(masks)

            pem_detections = pem.get("num_detections") if isinstance(pem, dict) else None

            summary.append(
                {
                    "object": obj_name,
                    "http_status": resp.status_code,
                    "success": success,
                    "ism_success": ism.get("success") if isinstance(ism, dict) else None,
                    "ism_detections": ism_detections,
                    "pem_success": pem.get("success") if isinstance(pem, dict) else None,
                    "pem_detections": pem_detections,
                    "output_dir": output_dir,
                    "elapsed_sec": round(elapsed, 2),
                    "message": data.get("message") if isinstance(data, dict) else resp.text[:200],
                }
            )

            status = "OK" if success else "FAIL"
            print(
                f"[{idx:02d}/{len(objects)}] {obj_name}: {status} "
                f"(HTTP {resp.status_code}, {elapsed:.1f}s, ISM={ism_detections}, PEM={pem_detections})"
            )

        except Exception as exc:
            elapsed = time.time() - start
            summary.append(
                {
                    "object": obj_name,
                    "http_status": None,
                    "success": False,
                    "ism_success": None,
                    "ism_detections": None,
                    "pem_success": None,
                    "pem_detections": None,
                    "output_dir": None,
                    "elapsed_sec": round(elapsed, 2),
                    "message": str(exc),
                }
            )
            print(f"[{idx:02d}/{len(objects)}] {obj_name}: ERROR - {exc}")
            break

    print("\n[요약]")
    success_count = sum(1 for item in summary if item["success"])
    print(f"성공 {success_count}/{len(summary)}")
    for item in summary:
        print(json.dumps(item, ensure_ascii=False))

    output_path = Path("rss_batch_summary.json")
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n상세 요약: {output_path.resolve()}")


if __name__ == "__main__":
    main()

