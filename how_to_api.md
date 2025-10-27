# How to API (ISM_Server, Render_Server, PEM_Server)

## ISM_Server (Instance Segmentation)
- Base URL: `http://localhost:8002`
- Docs: `http://localhost:8002/docs`

- Health
```bash
GET /health
```

- Inference (Instance Segmentation)
```bash
POST /api/v1/inference

# Request (JSON)
{
  "rgb_image": "<base64>",
  "depth_image": "<base64>",
  "cam_params": {
    "cam_K": [fx, 0, cx, 0, fy, cy, 0, 0, 1],
    "depth_scale": 1.0
  },
  "template_dir": "/path/to/templates",
  "cad_path": "/path/to/cad/model.ply",
  "output_dir": "/path/to/output"
}

# Response (JSON)
{
  "success": true,
  "inference_time": 10.25,
  "num_detections": 4,
  "template_dir_used": "...",
  "cad_path_used": "...",
  "output_dir_used": "..."
}
```

- Sample data
```bash
GET /test/sample
```

---

## Render_Server (Template Rendering)
- Base URL: `http://localhost:8004`
- Docs: `http://localhost:8004/docs`

- Health
```bash
GET /health
```

- Render templates (sync/async)
```bash
POST /render/templates?wait=<true|false>&wait_timeout_sec=<seconds>

# Request (JSON)
{
  "cad_path": "/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply",
  "output_dir": "/workspace/Estimation_Server/Render_Server/test",
  "colorize": false,
  "base_color": 0.05
}

# Async Response
{ "job_id": "<uuid>", "status": "queued" }

# Sync Response
{ "status": "succeeded|failed|timeout", "log_path": "Render_Server/logs/<job_id>.log", "returncode": 0, "elapsed_sec": 84.6 }
```

- Job status (for async)
```bash
GET /jobs/{job_id}
```

- Output
  - Templates: `<output_dir>/templates/` → `rgb_*.png`, `mask_*.png`, `xyz_*.npy`
  - Logs: `Render_Server/logs/<job_id>.log`

---

## PEM_Server (Pose Estimation)
- Base URL: `http://localhost:8003`
- Docs: `http://localhost:8003/docs`

- Health
```bash
GET /api/v1/health
```

- Pose Estimation
```bash
POST /api/v1/pose-estimation

# Request (JSON)
{
  "rgb_image": "<base64>",
  "depth_image": "<base64>",
  "cam_params": {
    "cam_K": [[fx,0,cx],[0,fy,cy],[0,0,1]],
    "depth_scale": 1000.0
  },
  "cad_path": "/path/to/cad/model.ply",
  "seg_data": [
    {
      "scene_id": 1,
      "image_id": 1,
      "category_id": 1,
      "bbox": [x, y, w, h],
      "score": 0.9,
      "segmentation": { "size": [H, W], "counts": "<rle>" }
    }
  ],
  "template_dir": "/path/to/templates",
  "det_score_thresh": 0.2,
  "output_dir": "/path/to/output"
}

# Response (JSON)
{
  "success": true,
  "detections": [ ... ],
  "pose_scores": [ ... ],
  "pred_rot": [ [[...],[...],[...]], ... ],
  "pred_trans": [ [x,y,z], ... ],
  "num_detections": 3,
  "inference_time": 2.45,
  "template_dir_used": "...",
  "cad_path_used": "...",
  "output_dir_used": "..."
}
```
