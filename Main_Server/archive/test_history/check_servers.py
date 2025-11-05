import requests
import sys

servers = {
    "ISM": "http://localhost:8002/health",
    "PEM": "http://localhost:8003/api/v1/health",
    "Render": "http://localhost:8004/health"
}

print("서버 상태 확인:")
print("=" * 50)

for name, url in servers.items():
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"✓ {name}: 정상")
        else:
            print(f"✗ {name}: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ {name}: {e}")

print("=" * 50)

