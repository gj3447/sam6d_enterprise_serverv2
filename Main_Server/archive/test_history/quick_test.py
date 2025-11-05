#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import requests
import json

# 경로 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 간단한 테스트
print("=" * 60)
print("Main_Server 기능 테스트")
print("=" * 60)

# 1. 경로 확인
print("\n[1] 경로 확인:")
from Main_Server.utils.path_utils import get_static_paths
paths = get_static_paths()
for name, path in paths.items():
    exists = path.exists()
    mark = "[OK]" if exists else "[NO]"
    print(f"  {mark} {name}: {path}")

# 2. Scanner 테스트
print("\n[2] Scanner 기능 테스트:")
try:
    from Main_Server.services.scanner import get_scanner
    scanner = get_scanner()
    
    # 전체 클래스 스캔
    classes = scanner.scan_all_classes()
    print(f"  발견된 클래스: {len(classes)}개")
    
    for cls in classes:
        print(f"\n  [{cls['name']}]")
        print(f"    객체 수: {cls['object_count']}개")
        print(f"    템플릿 수: {cls['template_count']}개")
        print(f"    완성률: {cls['template_completion_rate']:.1f}%")
        
        # 첫 번째 객체 확인
        if cls['objects']:
            obj = cls['objects'][0]
            print(f"\n    첫 번째 객체: {obj['name']}")
            print(f"      CAD 파일: {obj['cad_file']}")
            print(f"      템플릿 존재: {obj['has_template']}")
            print(f"      상태: {obj['status']}")
            if obj['has_template']:
                files = obj['template_files']
                print(f"      템플릿 파일: mask={files['mask_count']}, rgb={files['rgb_count']}, xyz={files['xyz_count']}")
    
    # 통계
    stats = scanner.get_statistics()
    print(f"\n  전체 통계:")
    print(f"    클래스: {stats['total_classes']}개")
    print(f"    객체: {stats['total_objects']}개")
    print(f"    템플릿: {stats['total_templates']}개")
    print(f"    완성률: {stats['overall_completion_rate']:.1f}%")
    
    print("\n  [OK] Scanner 기능 정상")
except Exception as e:
    print(f"  [NO] Scanner 오류: {e}")

# 3. Workflow 테스트 (경로만)
print("\n[3] Workflow 경로 설정:")
try:
    from Main_Server.services.workflow_service import WorkflowService
    
    workflow = WorkflowService()
    
    # 출력 디렉토리 테스트
    import time
    run_id = str(int(time.time()))
    output_dir = paths["output"] / run_id
    
    print(f"  출력 디렉토리: {paths['output']}")
    print(f"  생성될 경로: {output_dir}")
    
    # 하위 디렉토리 구조
    ism_dir = output_dir / "ism"
    pem_dir = output_dir / "pem"
    print(f"  ISM 출력: {ism_dir}")
    print(f"  PEM 출력: {pem_dir}")
    
    print("\n  [OK] Workflow 경로 설정 정상")
except Exception as e:
    print(f"  [NO] Workflow 오류: {e}")

# 4. 서버 상태 테스트 (다른 서버들)
print("\n[4] 다른 서버 상태 확인:")
servers = {
    "ISM (8002)": "http://localhost:8002/health",
    "PEM (8003)": "http://localhost:8003/api/v1/health",
    "Render (8004)": "http://localhost:8004/health"
}

for name, url in servers.items():
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"  [OK] {name}: 정상")
        else:
            print(f"  [NO] {name}: HTTP {response.status_code}")
    except Exception as e:
        print(f"  [NO] {name}: {e}")

print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)

