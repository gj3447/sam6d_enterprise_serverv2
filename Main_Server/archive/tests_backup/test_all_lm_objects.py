#!/usr/bin/env python3
"""
LM 클래스의 모든 객체를 하나씩 테스트하는 스크립트
"""
import sys
import json
import base64
from pathlib import Path
from datetime import datetime
import requests

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def load_image_as_base64(image_path: Path) -> str:
    """이미지를 base64로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def test_lm_object(obj_name: str, test_num: int, total: int):
    """특정 LM 객체를 테스트"""
    print(f"\n{'='*70}")
    print(f"[{test_num}/{total}] Testing: {obj_name}")
    print(f"{'='*70}")
    
    # 테스트 파일 경로
    rgb_path = project_root / "static" / "test" / "rgb.png"
    depth_path = project_root / "static" / "test" / "depth.png"
    camera_path = project_root / "static" / "test" / "camera.json"
    
    # 이미지 인코딩
    print(f"\n[1/5] 인코딩 중...")
    rgb_b64 = load_image_as_base64(rgb_path)
    depth_b64 = load_image_as_base64(depth_path)
    print(f"  RGB: {len(rgb_b64):,} chars")
    print(f"  Depth: {len(depth_b64):,} chars")
    
    # 카메라 파라미터 로드
    print(f"\n[2/5] 카메라 파라미터 로드...")
    with open(camera_path, "r", encoding="utf-8-sig") as f:
        cam_params = json.load(f)
    print(f"  Camera params: {list(cam_params.keys())}")
    
    # API 요청 데이터
    request_data = {
        "class_name": "lm",
        "object_name": obj_name,
        "rgb_image": rgb_b64,
        "depth_image": depth_b64,
        "cam_params": cam_params
    }
    
    # API 호출
    print(f"\n[3/5] API 호출 중...")
    api_url = "http://localhost:8001/api/v1/workflow/full-pipeline"
    
    try:
        response = requests.post(
            api_url,
            json=request_data,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 결과 분석
            print(f"\n[4/5] 결과 분석...")
            success = result.get("success", False)
            output_dir = result.get("results", {}).get("output_dir", "")
            
            print(f"  성공: {success}")
            print(f"  출력: {output_dir}")
            
            if success:
                # 각 단계 결과 확인
                ism_result = result.get("results", {}).get("results", {}).get("ism", {})
                pem_result = result.get("results", {}).get("results", {}).get("pem", {})
                
                ism_success = ism_result.get("success", False)
                pem_success = pem_result.get("success", False)
                
                print(f"\n[5/5] 단계별 결과:")
                print(f"  ISM: {'성공' if ism_success else '실패'}")
                if ism_success:
                    ism_time = ism_result.get("inference_time", 0)
                    print(f"    시간: {ism_time:.2f}초")
                
                print(f"  PEM: {'성공' if pem_success else '실패'}")
                if pem_success:
                    pem_time = pem_result.get("inference_time", 0)
                    num_detections = pem_result.get("num_detections", 0)
                    print(f"    시간: {pem_time:.2f}초")
                    print(f"    감지: {num_detections}개")
                else:
                    pem_error = pem_result.get("error_message", pem_result.get("error", "Unknown"))
                    print(f"    에러: {pem_error}")
                
                return {"success": True, "output": output_dir, "ism": ism_success, "pem": pem_success}
            else:
                error_msg = result.get("message", "Unknown error")
                print(f"  실패: {error_msg}")
                return {"success": False, "error": error_msg}
        else:
            print(f"  HTTP 에러: {response.status_code}")
            print(f"  내용: {response.text[:200]}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"  예외 발생: {e}")
        return {"success": False, "error": str(e)}

def main():
    print("="*70)
    print("LM 클래스 전체 객체 테스트")
    print("="*70)
    
    # LM 객체 목록
    lm_objects = [
        "obj_000001", "obj_000002", "obj_000003", "obj_000004", "obj_000005",
        "obj_000006", "obj_000007", "obj_000008", "obj_000009", "obj_000010",
        "obj_000011", "obj_000012", "obj_000013", "obj_000014", "obj_000015"
    ]
    
    total = len(lm_objects)
    results = []
    
    start_time = datetime.now()
    
    for idx, obj_name in enumerate(lm_objects, 1):
        result = test_lm_object(obj_name, idx, total)
        result["object_name"] = obj_name
        results.append(result)
        
        # 진행 상황 표시
        print(f"\n진행률: {idx}/{total} ({idx*100//total}%)")
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    # 전체 결과 요약
    print(f"\n{'='*70}")
    print("전체 테스트 결과 요약")
    print(f"{'='*70}")
    
    successful = [r for r in results if r.get("success")]
    successful_ism = [r for r in results if r.get("ism")]
    successful_pem = [r for r in results if r.get("pem")]
    
    print(f"\n총 객체 수: {total}")
    print(f"성공한 테스트: {len(successful)}/{total}")
    print(f"ISM 성공: {len(successful_ism)}/{total}")
    print(f"PEM 성공: {len(successful_pem)}/{total}")
    print(f"총 소요 시간: {elapsed:.1f}초")
    
    if successful_pem:
        print(f"\nPEM 성공한 객체:")
        for r in successful_pem:
            print(f"  - {r['object_name']}")
    
    if len(successful_pem) < total:
        failed = [r for r in results if not r.get("pem")]
        print(f"\nPEM 실패한 객체 ({len(failed)}):")
        for r in failed:
            error = r.get("error", "Unknown")
            print(f"  - {r['object_name']}: {error[:100]}")
    
    print(f"\n{'='*70}")
    print("테스트 완료!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()

