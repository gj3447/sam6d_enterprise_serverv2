# Main_Server (포트 8001) 설계 문서

## 개요
Main_Server는 포트 8001에서 실행되는 중앙 관리 서버로, 전체 시스템의 객체 데이터베이스 관리와 서버 오케스트레이션을 담당합니다.

## 서버 구성
- **포트**: 8001
- **기능**: Static 폴더 스캔, 서버 상태 모니터링, 워크플로우 오케스트레이션
- **프레임워크**: FastAPI
- **데이터 저장**: 파일 시스템 기반 (데이터베이스 없음)

## 주요 기능

### 1. Static 폴더 스캔 및 객체 관리

#### 1.1 메시 폴더 스캔 (`static/meshes/`)
```
static/meshes/
├── test/           # 클래스: test
│   └── obj_000005.ply
├── ycb/            # 클래스: ycb  
│   ├── 001_chips_can.ply
│   ├── 002_master_chef_can.ply
│   └── ...
└── lm/             # 클래스: lm
    ├── 01_ape.ply
    ├── 02_benchvise.ply
    └── ...
```

#### 1.2 템플릿 폴더 스캔 (`static/templates/`)
```
static/templates/
├── test/
│   └── obj_000005/     # 템플릿 생성됨
│       ├── mask_*.png
│       ├── rgb_*.png
│       └── xyz_*.npy
├── ycb/
│   ├── 001_chips_can/  # 템플릿 생성됨
│   └── 002_master_chef_can/  # 템플릿 없음
└── lm/
    └── 01_ape/         # 템플릿 생성됨
```

### 2. API 엔드포인트 (포트 8001)

#### 2.1 객체 관리 API

**GET /api/v1/objects/classes**
- 모든 객체 클래스 목록 반환
- 각 클래스별 객체 수, 템플릿 수, 완성률 포함

**GET /api/v1/objects/classes/{class_name}**
- 특정 클래스의 객체 목록 반환
- 각 객체의 템플릿 상태 포함

**GET /api/v1/objects/{class_name}/{object_name}**
- 특정 객체의 상세 정보 반환
- CAD 파일 정보, 템플릿 정보, 상태 포함

**POST /api/v1/objects/scan**
- Static 폴더 재스캔 실행
- 실시간 파일 시스템 스캔

#### 2.2 서버 상태 API

**GET /api/v1/servers/status**
- ISM(8002), PEM(8003), Render(8004) 서버 상태 확인
- 전체 시스템 상태 반환

**GET /api/v1/servers/health**
- Main_Server 자체 헬스 체크

#### 2.3 워크플로우 API

**POST /api/v1/workflow/render-templates**
- 템플릿 생성 작업 시작
- 특정 클래스/객체의 템플릿 생성

**POST /api/v1/workflow/full-pipeline**
- 전체 파이프라인 실행 (Render → ISM → PEM)
- 단일 객체에 대한 완전한 처리

## 핵심 구현 로직

### 1. Static 폴더 스캔 로직 (실시간)
```python
def scan_static_folders():
    """Static 폴더를 실시간으로 스캔하여 객체 정보 반환"""
    project_root = Path(__file__).parent.parent
    meshes_dir = project_root / "static" / "meshes"
    templates_dir = project_root / "static" / "templates"
    
    classes = []
    for class_dir in meshes_dir.iterdir():
        if class_dir.is_dir():
            class_name = class_dir.name
            objects = scan_class_objects(class_name, class_dir, templates_dir)
            classes.append({
                "name": class_name,
                "object_count": len(objects),
                "template_count": sum(1 for obj in objects if obj["has_template"]),
                "objects": objects
            })
    return classes

def scan_class_objects(class_name, meshes_class_dir, templates_dir):
    """특정 클래스의 객체들 실시간 스캔"""
    template_class_dir = templates_dir / class_name
    objects = []
    
    for cad_file in meshes_class_dir.glob("*.ply"):
        object_name = cad_file.stem
        template_dir = template_class_dir / object_name
        
        # 템플릿 상태 확인
        has_template = template_dir.exists() and any(template_dir.iterdir())
        template_files = 0
        if has_template:
            template_files = len(list(template_dir.iterdir()))
        
        objects.append({
            "name": object_name,
            "cad_file": cad_file.name,
            "cad_path": str(cad_file),
            "has_template": has_template,
            "template_files": template_files,
            "status": "ready" if has_template else "needs_template"
        })
    
    return objects
```

### 2. 서버 상태 모니터링
```python
async def check_all_servers():
    """모든 서버 상태 확인"""
    servers = {
        "ism": "http://localhost:8002",
        "pem": "http://localhost:8003", 
        "render": "http://localhost:8004"
    }
    
    results = {}
    for name, url in servers.items():
        status = await check_server_health(url)
        results[name] = status
        
    return results
```

### 3. 워크플로우 오케스트레이션
```python
async def execute_full_pipeline(class_name, object_name, input_images):
    """전체 파이프라인 실행 (Render → ISM → PEM)"""
    
    # 기존 test_*.py 함수들을 import해서 사용
    from test_render_only import test_render_only
    from test_ism_only import test_ism_server  
    from test_pem_only import test_pem_only
    
    # 1단계: 템플릿 생성 (Render 서버)
    template_result = await test_render_only(
        cad_path=f"static/meshes/{class_name}/{object_name}.ply",
        template_output_dir=f"static/templates/{class_name}/{object_name}"
    )
    
    # 2단계: 객체 감지 (ISM 서버)  
    ism_result = await test_ism_server(
        rgb_path=input_images["rgb_path"],
        depth_path=input_images["depth_path"],
        cam_json_path=input_images["camera_path"],
        cad_path=f"static/meshes/{class_name}/{object_name}.ply",
        template_dir=f"static/templates/{class_name}/{object_name}",
        output_dir=f"static/output/{int(time.time())}/ism"
    )
    
    # 3단계: 포즈 추정 (PEM 서버)
    pem_result = await test_pem_only(
        rgb_path=input_images["rgb_path"],
        depth_path=input_images["depth_path"],
        cam_json_path=input_images["camera_path"],
        cad_path=f"static/meshes/{class_name}/{object_name}.ply",
        template_dir=f"static/templates/{class_name}/{object_name}",
        ism_result_path=f"static/output/{int(time.time())}/ism/detection_ism.json",
        output_dir=f"static/output/{int(time.time())}/pem"
    )
    
    return {
        "template": template_result,
        "ism": ism_result, 
        "pem": pem_result
    }
```

## 구현 파일 구조 (간소화)

```
Main_Server/
├── api/
│   ├── __init__.py
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── objects.py          # 객체 관리 API
│   │   ├── servers.py          # 서버 상태 API
│   │   └── workflow.py         # 워크플로우 API
│   └── models.py               # Pydantic 모델
├── services/
│   ├── __init__.py
│   ├── scanner.py              # Static 폴더 스캔 로직
│   ├── server_monitor.py       # 서버 모니터링
│   └── workflow_service.py     # 워크플로우 관리
├── utils/
│   ├── __init__.py
│   └── file_utils.py           # 파일 유틸리티
├── test_ism_only.py            # ISM 서버 테스트 함수
├── test_pem_only.py            # PEM 서버 테스트 함수  
├── test_render_only.py         # Render 서버 테스트 함수
├── main.py                     # FastAPI 애플리케이션 진입점
├── requirements.txt            # 의존성 목록
└── README.md                   # 사용법 문서
```

## Docker 설정

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  main-server:
    build: .
    ports:
      - "8001:8001"
    volumes:
      - .:/app
      - ./static:/app/static
    environment:
      - PROJECT_ROOT=/app
    depends_on:
      - ism-server
      - pem-server  
      - render-server
    networks:
      - estimation-network

networks:
  estimation-network:
    external: true
```

## API 응답 예시

### GET /api/v1/objects/classes
```json
{
  "classes": [
    {
      "name": "test",
      "path": "static/meshes/test",
      "object_count": 1,
      "template_count": 1,
      "template_completion_rate": 100.0,
      "objects": [
        {
          "name": "obj_000005",
          "has_template": true,
          "template_files": 126,
          "status": "ready"
        }
      ]
    },
    {
      "name": "ycb",
      "path": "static/meshes/ycb", 
      "object_count": 21,
      "template_count": 15,
      "template_completion_rate": 71.4,
      "objects": [
        {
          "name": "001_chips_can",
          "has_template": true,
          "template_files": 126,
          "status": "ready"
        },
        {
          "name": "002_master_chef_can",
          "has_template": false,
          "template_files": 0,
          "status": "needs_template"
        }
      ]
    }
  ],
  "total_classes": 2,
  "total_objects": 22,
  "total_templates": 16,
  "overall_completion_rate": 72.7
}
```

### GET /api/v1/servers/status
```json
{
  "servers": {
    "ism": {
      "url": "http://localhost:8002",
      "status": "healthy",
      "response_time_ms": 45,
      "last_check": "2024-01-15T10:30:00Z"
    },
    "pem": {
      "url": "http://localhost:8003",
      "status": "healthy", 
      "response_time_ms": 52,
      "last_check": "2024-01-15T10:30:00Z"
    },
    "render": {
      "url": "http://localhost:8004",
      "status": "healthy",
      "response_time_ms": 38,
      "last_check": "2024-01-15T10:30:00Z"
    }
  },
  "overall_status": "healthy",
  "healthy_servers": 3,
  "total_servers": 3
}
```

## 실행 방법

### 개발 환경
```bash
cd Main_Server
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Docker 환경
```bash
cd Main_Server
docker-compose up -d
```

### API 문서
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

이렇게 Main_Server가 8001번 포트에서 실행되어 static 폴더를 스캔하고 객체 데이터베이스를 관리하며, 다른 서버들과 연동하는 중앙 관리 서버 역할을 하게 됩니다.
