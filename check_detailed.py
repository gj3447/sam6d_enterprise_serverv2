import requests

r = requests.get('http://localhost:8001/api/v1/objects/classes/lm')
data = r.json()

print(f"LM 클래스 상세 정보:")
print(f"  전체: {data['object_count']}개")
print(f"  완료: {data['template_count']}개")
print(f"  완성률: {data['template_count']/data['object_count']*100:.1f}%")

print(f"\n객체별 상세:")
for obj in data['objects'][:10]:
    status = "[OK]" if obj['has_template'] else "[  ]"
    files = obj['template_files']['total_countмотр'] if obj['has_template'] else 0
    print(f"{status} {obj['name']}: {files} files")
