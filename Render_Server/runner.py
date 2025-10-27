import os
import sys
import time
import uuid
import threading
import subprocess
from typing import Dict, Any


# 간단한 인메모리 작업 레지스트리
JOBS: Dict[str, Dict[str, Any]] = {}

# 동시 실행 제한(필요 시 값 조정)
_SEMAPHORE = threading.Semaphore(value=1)


def start_job(cad_path: str, output_dir: str, colorize: bool = False, base_color: float = 0.05, timeout_sec: int = 1800) -> str:
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "status": "queued",
        "cad_path": cad_path,
        "output_dir": output_dir,
        "created_at": time.time()
    }

    worker = threading.Thread(
        target=_run_job,
        args=(job_id, cad_path, output_dir, colorize, base_color, timeout_sec),
        daemon=True,
    )
    worker.start()
    return job_id


def get_job(job_id: str) -> Dict[str, Any]:
    return JOBS.get(job_id, {"error": "not_found"})


def _run_job(job_id: str, cad_path: str, output_dir: str, colorize: bool, base_color: float, timeout_sec: int) -> None:
    start_ts = time.time()
    os.makedirs(output_dir, exist_ok=True)
    logs_dir = os.path.join("Render_Server", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, f"{job_id}.log")

    with _SEMAPHORE:
        # BlenderProc 스크립트는 python이 아닌 `blenderproc run`으로 실행해야 함
        cmd = [
            "blenderproc",
            "run",
            "Render_Server/render_custom_templates.py",
            "--cad_path", cad_path,
            "--output_dir", output_dir,
            "--base_color", str(base_color),
        ]
        # colorize는 스크립트가 문자열 truthy를 사용하므로 True일 때만 전달
        if colorize:
            cmd += ["--colorize", "True"]

        JOBS[job_id].update({
            "status": "running",
            "started_at": start_ts,
            "cmd": " ".join(cmd),
            "log_path": log_path,
        })

        try:
            with open(log_path, "w", encoding="utf-8") as logf:
                proc = subprocess.Popen(cmd, stdout=logf, stderr=logf, cwd=os.getcwd())
                JOBS[job_id]["pid"] = proc.pid
                try:
                    rc = proc.wait(timeout=timeout_sec)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    rc = -9
        except Exception as e:
            rc = -1
            with open(log_path, "a", encoding="utf-8") as logf:
                logf.write(f"\n[runner] Exception: {repr(e)}\n")

        end_ts = time.time()
        JOBS[job_id].update({
            "status": "succeeded" if rc == 0 else "failed",
            "returncode": rc,
            "ended_at": end_ts,
            "elapsed_sec": round(end_ts - start_ts, 3),
        })


