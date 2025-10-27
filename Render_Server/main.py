from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import time

from Render_Server.runner import start_job, get_job


app = FastAPI(title="Render Server (minimal)")


class RenderRequest(BaseModel):
    cad_path: str = Field(..., description="입력 CAD 파일 절대경로")
    output_dir: str = Field(..., description="출력 디렉터리 절대경로")
    colorize: bool = False
    base_color: float = 0.05


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/render/templates")
def create_templates(req: RenderRequest, wait: bool = False, wait_timeout_sec: int = 1800):
    try:
        job_id = start_job(
            cad_path=req.cad_path,
            output_dir=req.output_dir,
            colorize=req.colorize,
            base_color=req.base_color,
        )
        if not wait:
            return {"job_id": job_id, "status": "queued"}

        # wait mode: 완료 혹은 실패 또는 타임아웃까지 대기
        start_ts = time.time()
        poll_interval = 2.0
        while True:
            job = get_job(job_id)
            status = job.get("status")
            if status in ("succeeded", "failed"):
                return job
            if time.time() - start_ts > wait_timeout_sec:
                job.update({
                    "status": "timeout",
                    "ended_at": time.time(),
                    "elapsed_sec": round(time.time() - job.get("started_at", start_ts), 3),
                })
                return job
            time.sleep(poll_interval)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    job = get_job(job_id)
    if "error" in job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


