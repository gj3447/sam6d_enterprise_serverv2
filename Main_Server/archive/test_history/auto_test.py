#!/usr/bin/env python3
"""자동 테스트 및 결과 저장"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from Main_Server.services.workflow_service import get_workflow_service
from Main_Server.services.scanner import get_scanner
from Main_Server.services.server_monitor import get_monitor


async def run_tests():
    """테스트 실행 및 결과 반환"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    print("=" * 70)
    print("Main_Server 전체 파이프라인 테스트")
    print("=" * 70)
    
    # 1. 서버 상태 확인
    print("\n[1단계] 서버 상태 확인...")
    try:
        monitor = get_monitor()
        status_result = await monitor.check_all_servers()
        
        results["tests"]["server_status"] = {
            "success": True,
            "overall_status": status_result['overall_status'],
            "servers": {}
        }
        
        healthy_count = 0
        for name, server_status in status_result['servers'].items():
            results["tests"]["server_status"]["servers"][name] = {
                "status": server_status['status'],
                "response_time_ms": server_status.get('response_time_ms'),
                "error": server_status.get('error_message')
            }
            if server_status['status'] == 'healthy':
                healthy_count += 1
                print(f"  [OK] {name.upper()}: {server_status['status']}")
            else:
                print(f"  [NO] {name.upper()}: {server_status['status']}")
        
        results["tests"]["server_status"]["healthy_count"] = healthy_count
        results["tests"]["server_status"]["total_servers"] = len(status_result['servers'])
        
    except Exception as e:
        results["tests"]["server_status"] = {
            "success": False,
            "error": str(e)
        }
        print(f"  [ERROR] 서버 상태 확인 실패: {e}")
    
    # 2. 객체 상태 확인
    print("\n[2단계] 객체 상태 확인...")
    try:
        scanner = get_scanner()
        
        # 전체 통계
        stats = scanner.get_statistics()
        results["tests"]["object_status"] = {
            "success": True,
            "statistics": stats
        }
        
        print(f"  클래스: {stats['total_classes']}개")
        print(f"  객체: {stats['total_objects']}개")
        print(f"  템플릿: {stats['total_templates']}개")
        print(f"  완성률: {stats['overall_completion_rate']:.1f}%")
        
        # test/obj_000005 상세
        obj_info = scanner.scan_object("test", "obj_000005")
        if obj_info:
            results["tests"]["object_status"]["test_object"] = {
                "name": obj_info['name'],
                "status": obj_info['status'],
                "has_template": obj_info['has_template'],
                "template_files": obj_info['template_files']
            }
            print(f"  테스트 객체: {obj_info['name']} - {obj_info['status']}")
        
    except Exception as e:
        results["tests"]["object_status"] = {
            "success": False,
            "error": str(e)
        }
        print(f"  [ERROR] 객체 상태 확인 실패: {e}")
    
    # 3. 파이프라인 실행 (선택적)
    print("\n[3단계] 전체 파이프라인 실행...")
    
    # 서버가 모두 정상인 경우에만 실행
    if results["tests"]["server_status"].get("healthy_count", 0) == 3:
        try:
            workflow = get_workflow_service()
            
            print("  실행 중... (소요 시간: 약 5-10초)")
            result = await workflow.execute_full_pipeline(
                class_name="test",
                object_name="obj_000005",
                input_images={
                    "rgb_path": "static/test/rgb.png",
                    "depth_path": "static/test/depth.png",
                    "camera_path": "static/test/camera.json"
                },
                output_dir=None  # 자동 생성
            )
            
            results["tests"]["pipeline_execution"] = {
                "success": result.get('success', False),
                "output_dir": result.get('output_dir'),
                "results_summary": {}
            }
            
            if result.get('success'):
                print("  [OK] 파이프라인 성공!")
                
                results_summary = results["tests"]["pipeline_execution"]["results_summary"]
                step_results = result.get('results', {})
                
                # Render 결과
                if 'render' in step_results:
                    render_result = step_results['render']
                    if render_result.get('skipped'):
                        results_summary["render"] = {"skipped": True, "reason": "Template already exists"}
                    else:
                        results_summary["render"] = {"success": render_result.get('success', False)}
                
                # ISM 결과
                if 'ism' in step_results:
                    ism_result = step_results['ism']
                    results_summary["ism"] = {
                        "success": ism_result.get('success', False),
                        "inference_time": ism_result.get('inference_time'),
                        "error": ism_result.get('error') if not ism_result.get('success') else None
                    }
                    if ism_result.get('success'):
                        detections = ism_result.get('detections', {})
                        results_summary["ism"]["num_detections"] = len(detections.get('masks', []))
                
                # PEM 결과
                if 'pem' in step_results:
                    pem_result = step_results['pem']
                    results_summary["pem"] = {
                        "success": pem_result.get('success', False),
                        "inference_time": pem_result.get('inference_time'),
                        "error": pem_result.get('error') if not pem_result.get('success') else None
                    }
                    if pem_result.get('success'):
                        results_summary["pem"]["num_detections"] = pem_result.get('num_detections', 0)
            else:
                print("  [NO] 파이프라인 실패!")
                results["tests"]["pipeline_execution"]["error"] = result.get('error')
                
        except Exception as e:
            results["tests"]["pipeline_execution"] = {
                "success": False,
                "error": str(e)
            }
            print(f"  [ERROR] 파이프라인 실행 실패: {e}")
    else:
        results["tests"]["pipeline_execution"] = {
            "skipped": True,
            "reason": "Not all servers are healthy"
        }
        print("  [SKIP] 파이프라인 스킵 (서버 상태 이상)")
    
    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)
    
    return results


def main():
    """메인 함수"""
    results = asyncio.run(run_tests())
    
    # 결과를 JSON 파일로 저장
    output_file = Path(__file__).parent / "test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n결과 저장: {output_file}")


if __name__ == "__main__":
    main()

