#!/usr/bin/env python3
"""
test 클래스 obj_000005 객체 전체 파이프라인 테스트 (ISM + PEM)
"""
import sys
from pathlib import Path
import requests
import json
import base64

BASE_URL = "http://localhost:8001"
project_root = Path(__file__).resolve().parents[1]

def load_image_as_base64(image_path):
    """이미지를 Base64로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def test_full_pipeline():
    """전체 파이프라인 테스트"""
    
    print("=" * 70)
    print("test 클래스 obj_000005 전체 파이프라인 테스트")
    print("=" * 70)
    
    # 1. 테스트 파일 경로 확인
    print(f"\n[1] 테스트 파일 확인...")
    rgb_path = project_root / "static" / "test" / "rgb.png"
    depth_path = project_root / "static" / "test" / "depth.png"
    cam_path = project_root / "static" / "test" / "camera.json"
    
    for path, name in [(rgb_path, "RGB"), (depth_path, "Depth"), (cam_path, "Camera")]:
        if path.exists():
            print(f"  [OK] {name}: {path}")
        else:
            print(f"  [ERROR] {name} 파일이 없습니다: {path}")
            return False
    
    # 2. 이미지 인코딩
    print(f"\n[2] 이미지 인코딩 중...")
    try:
        rgb_base64 = load_image_as_base64(rgb_path)
        depth_base64 = load_image_as_base64(depth_path)
        print(f"  [OK] RGB 이미지 인코딩 완료 ({len(rgb_base64)} bytes)")
        print(f"  [OK] Depth 이미지 인코딩 완료 ({len(depth_base64)} bytes)")
    except Exception as e:
        print(f"  [ERROR] 이미지 인코딩 실패: {e}")
        return False
    
    # 3. 카메라 파라미터 로딩
    print(f"\n[3] 카메라 파라미터 로딩...")
    try:
        with open(cam_path, "r", encoding="utf-8-sig") as f:
            cam_params = json.load(f)
        print(f"  [OK] 카메라 파라미터 로딩 완료")
        print(f"    - cam_K: {cam_params.get('cam_K', 'N/A')}")
        print(f"    - depth_scale: {cam_params.get('depth_scale', 'N/A')}")
    except Exception as e:
        print(f"  [ERROR] 카메라 파라미터 로딩 실패: {e}")
        return False
    
    # 4. 객체 정보 확인
    print(f"\n[4] 객체 정보 확인...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/objects/test/obj_000005")
        if response.status_code == 200:
            obj_info = response.json()
            print(f"  [OK] 객체 찾음: obj_000005")
            print(f"  [OK] 상태: {obj_info.get('status')}")
            print(f"  [OK] CAD 파일: {obj_info.get('cad_file')}")
            print(f"  [OK] CAD 경로: {obj_info.get('cad_path')}")
            has_template = obj_info.get('has_template', False)
            if has_template:
                template_files = obj_info.get('template_files', {})
                print(f"  [OK] 템플릿 존재: {template_files.get('total_count', 0)}개 파일")
            else:
                print(f"  [WARN] 템플릿이 없습니다.")
        else:
            print(f"  [ERROR] 객체를 찾을 수 없습니다: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] 객체 정보 확인 실패: {e}")
        return False
    
    # 5. 서버 상태 확인
    print(f"\n[5] 서버 상태 확인...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/servers/status")
        if response.status_code == 200:
            status = response.json()
            print(f"  전체 상태: {status['overall_status']}")
            
            ism_ok = status['servers'].get('ism', {}).get('status') == 'healthy'
            pem_ok = status['servers'].get('pem', {}).get('status') == 'healthy'
            render_ok = status['servers'].get('render', {}).get('status') == 'healthy'
            
            print(f"  [{'OK' if ism_ok else 'FAIL'}] ISM: {status['servers'].get('ism', {}).get('status')}")
            print(f"  [{'OK' if pem_ok else 'FAIL'}] PEM: {status['servers'].get('pem', {}).get('status')}")
            print(f"  [{'OK' if render_ok else 'FAIL'}] RENDER: {status['servers'].get('render', {}).get('status')}")
            
            if not (ism_ok and pem_ok):
                print(f"  [ERROR] 필요한 서버가 정상 작동하지 않습니다.")
                return False
        else:
            print(f"  [ERROR] 서버 상태 확인 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] 서버 상태 확인 실패: {e}")
        return False
    
    # 6. 전체 파이프라인 실행
    print(f"\n{'='*70}")
    print("[6] 전체 파이프라인 실행 (ISM + PEM)...")
    print(f"{'='*70}")
    
    pipeline_request = {
        "class_name": "test",
        "object_name": "obj_000005",
        "rgb_image": rgb_base64,
        "depth_image": depth_base64,
        "cam_params": cam_params
    }
    
    try:
        print(f"[INFO] 파이프라인 요청 중... (시간이 오래 걸릴 수 있습니다)")
        response = requests.post(
            f"{BASE_URL}/api/v1/workflow/full-pipeline",
            json=pipeline_request,
            timeout=600
        )
        
        print(f"[INFO] 응답 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[ERROR] 파이프라인 실행 실패: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  에러 내용: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"  응답 내용: {response.text[:500]}")
            return False
        
        result = response.json()
        
        print(f"\n[RESULT] 파이프라인 실행 결과:")
        print(f"  성공: {result.get('success')}")
        print(f"  메시지: {result.get('message')}")
        
        if result.get('success'):
            results = result.get('results', {})
            output_dir = results.get('output_dir', 'N/A')
            print(f"  출력 디렉토리: {output_dir}")
            
            # ISM 결과 확인
            if 'results' in results:
                pipeline_results = results['results']
                print(f"\n  [ISM 단계]")
                if 'ism' in pipeline_results:
                    ism_result = pipeline_results['ism']
                    if isinstance(ism_result, dict):
                        if ism_result.get('success'):
                            detections = ism_result.get('detections', {})
                            if 'masks' in detections:
                                num_detections = len(detections['masks'])
                                print(f"    [OK] ISM 추론 성공")
                                print(f"      - 감지된 객체 수: {num_detections}")
                                if 'scores' in detections and len(detections['scores']) > 0:
                                    max_score = max(detections['scores'])
                                    print(f"      - 최고 스코어: {max_score:.3f}")
                                if 'inference_time' in ism_result:
                                    print(f"      - 추론 시간: {ism_result['inference_time']:.2f}초")
                            else:
                                print(f"    [WARN] 감지된 객체가 없습니다")
                        else:
                            print(f"    [FAIL] ISM 추론 실패: {ism_result.get('error', 'Unknown error')}")
                
                # PEM 결과 확인
                print(f"\n  [PEM 단계]")
                if 'pem' in pipeline_results:
                    pem_result = pipeline_results['pem']
                    if isinstance(pem_result, dict):
                        if pem_result.get('success'):
                            print(f"    [OK] PEM 추론 성공")
                            if 'poses' in pem_result and len(pem_result['poses']) > 0:
                                print(f"      - 추정된 포즈 수: {len(pem_result['poses'])}")
                                first_pose = pem_result['poses'][0]
                                if 'translation' in first_pose:
                                    trans = first_pose['translation']
                                    print(f"      - 첫 번째 포즈 위치: [{trans[0]:.3f}, {trans[1]:.3f}, {trans[2]:.3f}]")
                                if 'rotation' in first_pose:
                                    print(f"      - 회전 정보: 있음")
                            if 'inference_time' in pem_result:
                                print(f"      - 추론 시간: {pem_result['inference_time']:.2f}초")
                        else:
                            print(f"    [FAIL] PEM 추론 실패: {pem_result.get('error', 'Unknown error')}")
                
                # detection_pem.json 파일 확인
                if output_dir and Path(output_dir).exists():
                    pem_dir = Path(output_dir) / "pem"
                    detection_file = pem_dir / "detection_pem.json"
                    if detection_file.exists():
                        print(f"\n  [detection_pem.json 확인]")
                        try:
                            with open(detection_file, 'r') as f:
                                detections_data = json.load(f)
                            print(f"    [OK] 파일 읽기 성공")
                            if isinstance(detections_data, list) and len(detections_data) > 0:
                                first_det = detections_data[0]
                                has_pose = 'R' in first_det or 't' in first_det or 'pose_score' in first_det
                                has_seg = 'segmentation' in first_det
                                print(f"      - 감지 데이터 수: {len(detections_data)}")
                                print(f"      - 포즈 정보 포함: {'YES' if has_pose else 'NO'}")
                                print(f"      - 세그멘테이션 포함: {'YES' if has_seg else 'NO'}")
                                if has_pose:
                                    if 'R' in first_det:
                                        print(f"      - 회전 행렬: {len(first_det['R'])}x{len(first_det['R'][0]) if first_det['R'] else 0}")
                                    if 't' in first_det:
                                        print(f"      - 이동 벡터: {first_det['t']}")
                                else:
                                    print(f"      [WARN] 포즈 정보가 없습니다! (세그멘테이션만 있음)")
                        except Exception as e:
                            print(f"    [ERROR] 파일 읽기 실패: {e}")
            
            print(f"\n{'='*70}")
            print("[SUCCESS] 전체 파이프라인 테스트 완료!")
            print(f"{'='*70}")
            return True
        else:
            error_msg = results.get('error', 'Unknown error') if 'results' in result else result.get('message', 'Unknown error')
            print(f"  [ERROR] 파이프라인 실행 실패: {error_msg}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"[ERROR] 요청 시간 초과 (600초)")
        return False
    except Exception as e:
        print(f"[ERROR] 파이프라인 실행 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)

