#!/usr/bin/env python3
"""
YCB 객체 템플릿 생성 스크립트
Main_Server API를 사용하여 템플릿 생성
"""
import requests
import json
import sys

# Main_Server URL
MAIN_SERVER_URL = "http://localhost:8001"

def create_template(class_name: str, object_name: str, force: bool = False):
    """특정 YCB 객체의 템플릿 생성"""
    
    url = f"{MAIN_SERVER_URL}/api/v1/workflow/render-template-single"
    
    payload = {
        "class_name": class_name,
        "object_name": object_name,
        "force": force
    }
    
    print(f"\n{'='*70}")
    print(f"[INFO] YCB 템플릿 생성 요청: {class_name}/{object_name}")
    print(f"{'='*70}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        print(f"\n[INFO] 요청 전송 중... (시간이 오래 걸릴 수 있습니다)")
        response = requests.post(url, json=payload, timeout=600)  # 10분 타임아웃
        response.raise_for_status()
        
        result = response.json()
        
        if result["success"]:
            print(f"\n[SUCCESS] 템플릿 생성 완료!")
            print(f"메시지: {result['message']}")
            print(f"\n결과:")
            print(json.dumps(result['results'], indent=2, ensure_ascii=False))
            return True
        else:
            print(f"\n[FAILED] 템플릿 생성 실패")
            print(f"메시지: {result['message']}")
            print(f"\n결과:")
            print(json.dumps(result['results'], indent=2, ensure_ascii=False))
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] 요청 실패: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답 내용: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 에러: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    
    print("=" * 70)
    print("YCB 객체 템플릿 생성 스크립트")
    print("=" * 70)

    # Get all YCB objects from the API
    try:
        print("[INFO] ycb 클래스의 모든 객체 목록을 가져옵니다...")
        response = requests.get(f"{MAIN_SERVER_URL}/api/v1/objects/classes/ycb")
        response.raise_for_status()
        class_data = response.json()
        object_names = [obj['name'] for obj in class_data.get('objects', [])]
        
        if not object_names:
            print("[ERROR] ycb 클래스에서 객체를 찾을 수 없습니다.")
            return 1
            
        print(f"[INFO] {len(object_names)}개의 객체를 찾았습니다: {object_names}")

    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] API에서 객체 목록을 가져오는 데 실패했습니다: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] 객체 목록 처리 중 예상치 못한 에러 발생: {e}")
        return 1

    # Loop through all objects and create templates
    success_count = 0
    failure_count = 0
    
    for object_name in object_names:
        success = create_template(
            class_name="ycb",
            object_name=object_name,
            force=True  # True로 설정하면 기존 템플릿 덮어쓰기
        )
        if success:
            success_count += 1
        else:
            failure_count += 1

    print("\n" + "=" * 70)
    print("모든 템플릿 생성 작업 완료")
    print(f"성공: {success_count}개")
    print(f"실패: {failure_count}개")
    print("=" * 70)

    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
