import requests

r = requests.get('http://localhost:8001/api/v1/objects/classes/lm')
data = r.json()
print(f'Total Objects: {data["object_count"]}')
print(f'Objects with Templates: {data["template_count"]}')
completion = data["template_count"] / data["object_count"] * 100 if data["object_count"] > 0 else 0
print(f'Completion Rate: {completion:.1f}%')

if data['objects']:
    for obj in data['objects'][:3]:
        print(f'  - {obj["name"]}: {obj["status"]}')

