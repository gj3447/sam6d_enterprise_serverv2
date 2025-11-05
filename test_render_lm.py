#!/usr/bin/env python3
"""
LM 객체 템플릿 직접 생성 테스트
"""
import requests
import json

# Render 서버 직접 호출
print("=" * 60)
print("LM 객체 템플릿 생성 - Render 서버 직접 호출")
print("=" * 60)

cad_path = "/workspace/Estimation_Server/static/meshes/lm/obj_000001.ply"
output_dir = "/workspace/Estimation_Server/static/templates/lm/obj_000001"

request_data = {
    "cad_path": cad_path,
    "output_dir": output_dir
}

print(f"CAD Path: {cad_path}")
print(f"Output Dir: {output_dir}")

try:
    response = requests.post(
        "http://localhost:8004/render/templates",
        json=request_data,
        params={"wait": True, "wait_timeout_sec": 1800},
        timeout=3720
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message', 'N/A')}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Exception: {str(e)}")

print("\n" + "=" * 60)

