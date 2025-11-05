from pathlib import Path
import json

project_root = Path(__file__).resolve().parents[1]
cam_json_path = project_root / Path("static/test/camera.json")

print(f"Camera path: {cam_json_path}")
print(f"Exists: {cam_json_path.exists()}")
print(f"Size: {cam_json_path.stat().st_size}")

with open(cam_json_path, "rb") as f:
    content = f.read()
    print(f"First 10 bytes: {content[:10]}")
    print(f"Is PNG: {content.startswith(b'\x89PNG')}")
    print(f"Decoded: {content.decode('utf-8')}")
    cam_params = json.loads(content.decode("utf-8"))
    print(f"Loaded: {cam_params}")

