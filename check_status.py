import requests
import json

r = requests.get('http://localhost:8001/api/v1/objects/classes')
data = r.json()

print(f"전체 통계:")
print(f"  클래스 수: {data['total_classes']}")
print(f"  전체 객체 수: {data['total_objects']}")
print(f"  템플릿 완료: {data['total_templates']}")
print(f"  완성률: {data['overall_completion_rate']:.1f}%")

print(f"\n클래스별:")
for class_info in data['classes']:
    print(f"\n{class_info['name']}:")
    print(f"  객체 수: {class_info['object_count']}")
    print(f"  템플릿 수: {class_info['template_count']}")
    print(f"  완성률: {class_info['template_completion_rate']:.1f}%")
    
    r2 = requests.get(f"http://localhost:8001/api/v1/objects/classes/{class_info['name']}")
    if r2.status_code == 200:
        class_data = r2.json()
        ready = [obj for obj in class_data['objects'] if obj['has_template']]
        print(f"  Ready: {len(ready)}개")
        if ready:
            for obj in ready[:5]:
                print(f"    [OK] {obj['name']}")
        needs = [obj for obj in class_data['objects'] if not obj['has_template']]
        print(f"  Needs Template: {len(needs)}개")
        if needs and len(needs) <= 5:
            for obj in needs:
                print(f"    [  ] {obj['name']}")
        elif needs:
            for obj in needs[:3]:
                print(f"    [  ] {obj['name']}")
            print(f"    ... 외 {len(needs)-3}개")

