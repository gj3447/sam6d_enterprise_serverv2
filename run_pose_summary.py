import json
import requests

url = "http://localhost:8001/api/v1/workflow/full-pipeline-from-rss"
payload = {
    "class_name": "ycb",
    "object_name": "obj_000002",
    "align_color": True,
    "frame_guess": True
}
resp = requests.post(url, json=payload, timeout=900)
print("Status:", resp.status_code)
try:
    data = resp.json()
except ValueError:
    print("Non-JSON response:\n", resp.text[:1000])
else:
    with open("pose_results_api.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved to pose_results_api.json")
