import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def test():
    try:
        print("테스트 시작")
        from Main_Server.services.scanner import get_scanner
        s = get_scanner()
        obj = s.scan_object("test", "obj_000005")
        print(f"OK: {obj['has_template']}")
        
        from Main_Server.services.workflow_service import get_workflow_service
        w = get_workflow_service()
        r = await w.execute_full_pipeline("test", "obj_000005", {
            "rgb_path": "static/test/rgb.png",
            "depth_path": "static/test/depth.png",
            "camera_path": "static/test/camera.json"
        })
        print(f"성공: {r.get('success')}")
        print(f"출력: {r.get('output_dir')}")
        
        output_dir = Path(r.get('output_dir', ''))
        if output_dir.exists():
            files = [f for f in output_dir.rglob("*") if f.is_file()]
            print(f"파일수: {len(files)}")
            for f in files[:5]:
                print(f"  {f.name}")
    except Exception as e:
        print(f"에러: {e}")

asyncio.run(test())

