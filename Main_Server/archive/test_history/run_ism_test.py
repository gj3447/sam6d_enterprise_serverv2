#!/usr/bin/env python3
"""ISM 서버 테스트 실행 - output에 파일 생성 확인"""
import sys
from pathlib import Path
import time

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Main_Server.services.ism_service import test_ism_server

# 테스트 데이터 경로
rgb_path = str(project_root / "static" / "test" / "rgb.png")
depth_path = str(project_root / "static" / "test" / "depth.png")
cam_json_path = str(project_root / "static" / "test" / "camera.json")
cad_path = str(project_root / "static" / "meshes" / "test" / "obj_000005.ply")
template_dir = str(project_root / "static" / "templates" / "test" / "obj_000005")

# 출력 디렉토리
run_ts = str(int(time.time()))
output_dir = str(project_root / "static" / "output" / run_ts / "ism_test")

print("=" * 70)
print("ISM 서버 테스트 - Output 파일 생성 확인")
print("=" * 70)
print(f"출력 디렉토리: {output_dir}")
print("=" * 70)

# ISM 서버 테스트 실행
result = test_ism_server(
    rgb_path=rgb_path,
    depth_path=depth_path,
    cam_json_path=cam_json_path,
    cad_path=cad_path,
    template_dir=template_dir,
    output_dir=output_dir,
    server_url="http://localhost:8002",
    timeout=600
)

if result:
    print("\n✓ 테스트 성공!")
    print(f"출력 파일 위치: {output_dir}")
    
    # 생성된 파일 확인
    output = Path(output_dir)
    if output.exists():
        files = list(output.glob("*"))
        print(f"\n생성된 파일: {len(files)}개")
        for f in files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")
else:
    print("\n✗ 테스트 실패!")

