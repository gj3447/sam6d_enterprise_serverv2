#!/usr/bin/env python3
"""
스캐너 테스트 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 경로 조정
from Main_Server.services.scanner import get_scanner

def main():
    scanner = get_scanner()
    
    # 전체 클래스 스캔
    print("=" * 60)
    print("Static 폴더 스캔 결과")
    print("=" * 60)
    
    classes = scanner.scan_all_classes()
    
    print(f"\n총 {len(classes)}개 클래스 발견:\n")
    
    for class_info in classes:
        print(f"[{class_info['name']}]")
        print(f"  경로: {class_info['path']}")
        print(f"  객체 수: {class_info['object_count']}개")
        print(f"  템플릿 수: {class_info['template_count']}개")
        print(f"  완성률: {class_info['template_completion_rate']:.1f}%")
        
        # 각 객체의 상태 출력
        if class_info['objects']:
            print("\n  객체 목록:")
            for obj in class_info['objects'][:5]:  # 처음 5개만
                status_mark = "[OK]" if obj['has_template'] else "[NO]"
                print(f"    {status_mark} {obj['name']}: {obj['status']}")
            
            if len(class_info['objects']) > 5:
                print(f"    ... 외 {len(class_info['objects']) - 5}개 더")
        print()
    
    # 통계 정보
    stats = scanner.get_statistics()
    print("\n" + "=" * 60)
    print("전체 통계")
    print("=" * 60)
    print(f"총 클래스: {stats['total_classes']}개")
    print(f"총 객체: {stats['total_objects']}개")
    print(f"총 템플릿: {stats['total_templates']}개")
    print(f"전체 완성률: {stats['overall_completion_rate']:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    main()

