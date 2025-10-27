# Main_Server 설계 문서

## 개요
Main_Server는 전체 시스템의 중앙 관리 서버로, 객체 데이터베이스 관리, 서버 상태 모니터링, 워크플로우 오케스트레이션을 담당합니다.

## 주요 기능

### 1. 객체 데이터베이스 관리 (Object Database Management)

#### 1.1 Static 폴더 스캔 및 분석
- **메시 폴더 스캔**: `static/meshes/` 하위 폴더들을 스캔하여 객체 클래스 감지
- **템플릿 폴더 스캔**: `static/templates/` 하위 폴더들을 스캔하여 템플릿 상태 확인
- **CAD 파일 감지**: 각 클래스 폴더 내의 CAD 파일 개수 및 타입 분석
- **템플릿 상태 확인**: 각 객체의 템플릿 생성 여부 확인

#### 1.2 객체 목록 API
- **클래스 목록**: 사용 가능한 객체 클래스 목록 반환
- **객체 상세 정보**: 특정 클래스의 객체 목록 및 상태 반환
- **템플릿 상태**: 각 객체의 템플릿 생성 상태 반환
- **통계 정보**: 전체 객체 수, 템플릿 생성률 등 통계 제공

### 2. 서버 상태 모니터링 (Server Health Monitoring)

#### 2.1 서버 상태 확인
- **ISM 서버**: 포트 8002 상태 확인
- **PEM 서버**: 포트 8003 상태 확인  
- **Render 서버**: 포트 8004 상태 확인
- **전체 시스템 상태**: 모든 서버의 통합 상태 반환

#### 2.2 서버 메트릭 수집
- **CPU/메모리 사용률**: 각 서버의 리소스 사용량 모니터링
- **응답 시간**: API 호출 응답 시간 측정
- **에러율**: 서버별 에러 발생률 추적

### 3. 워크플로우 오케스트레이션 (Workflow Orchestration)

#### 3.1 전체 파이프라인 실행
- **Render → ISM → PEM**: 3단계 파이프라인 자동 실행
- **배치 처리**: 여러 객체에 대한 일괄 처리
- **에러 복구**: 실패한 단계의 재시도 및 복구

#### 3.2 작업 관리
- **작업 큐**: 대기 중인 작업 목록 관리
- **작업 상태**: 진행 중인 작업의 상태 추적
- **결과 저장**: 처리 결과의 자동 저장 및 정리

## API 엔드포인트 설계

### 객체 관리 API

#### GET /api/v1/objects/classes
**설명**: 사용 가능한 객체 클래스 목록 반환
**응답 예시**:
```json
{
  "classes": [
    {
      "name": "test",
      "path": "static/meshes/test",
      "object_count": 1,
      "template_count": 1,
      "template_completion_rate": 100.0
    },
    {
      "name": "ycb", 
      "path": "static/meshes/ycb",
      "object_count": 21,
      "template_count": 15,
      "template_completion_rate": 71.4
    }
  ],
  "total_classes": 2,
  "total_objects": 22,
  "total_templates": 16
}
```

#### GET /api/v1/objects/classes/{class_name}
**설명**: 특정 클래스의 객체 목록 반환
**응답 예시**:
```json
{
  "class_name": "test",
  "objects": [
    {
      "name": "obj_000005",
      "cad_file": "obj_000005.ply",
      "cad_path": "static/meshes/test/obj_000005.ply",
      "template_path": "static/templates/test/obj_000005",
      "has_template": true,
      "template_files": {
        "mask_count": 42,
        "rgb_count": 42,
        "xyz_count": 42
      },
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "object_count": 1,
  "template_count": 1
}
```

#### GET /api/v1/objects/{class_name}/{object_name}
**설명**: 특정 객체의 상세 정보 반환
**응답 예시**:
```json
{
  "name": "obj_000005",
  "class": "test",
  "cad_info": {
    "file": "obj_000005.ply",
    "path": "static/meshes/test/obj_000005.ply",
    "size_bytes": 1024000,
    "last_modified": "2024-01-15T09:00:00Z"
  },
  "template_info": {
    "has_template": true,
    "path": "static/templates/test/obj_000005",
    "files": {
      "mask_files": 42,
      "rgb_files": 42,
      "xyz_files": 42
    },
    "last_generated": "2024-01-15T10:30:00Z"
  },
  "status": "ready"
}
```

### 서버 상태 API

#### GET /api/v1/servers/status
**설명**: 모든 서버의 상태 확인
**응답 예시**:
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

### 워크플로우 API

#### POST /api/v1/workflow/render-templates
**설명**: 템플릿 생성 작업 시작
**요청 예시**:
```json
{
  "class_name": "test",
  "object_names": ["obj_000005"],
  "force_regenerate": false
}
```

#### POST /api/v1/workflow/full-pipeline
**설명**: 전체 파이프라인 실행 (Render → ISM → PEM)
**요청 예시**:
```json
{
  "class_name": "test",
  "object_name": "obj_000005",
  "input_images": {
    "rgb_path": "static/test/rgb.png",
    "depth_path": "static/test/depth.png",
    "camera_path": "static/test/camera.json"
  },
  "output_dir": "static/output/run_12345"
}
```

## 데이터베이스 스키마

### Objects 테이블
```sql
CREATE TABLE objects (
    id INTEGER PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL,
    object_name VARCHAR(100) NOT NULL,
    cad_file VARCHAR(200) NOT NULL,
    cad_path VARCHAR(500) NOT NULL,
    cad_size_bytes INTEGER,
    cad_last_modified DATETIME,
    template_path VARCHAR(500),
    has_template BOOLEAN DEFAULT FALSE,
    template_mask_count INTEGER DEFAULT 0,
    template_rgb_count INTEGER DEFAULT 0,
    template_xyz_count INTEGER DEFAULT 0,
    template_last_generated DATETIME,
    status VARCHAR(20) DEFAULT 'unknown',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_name, object_name)
);
```

### Server_Status 테이블
```sql
CREATE TABLE server_status (
    id INTEGER PRIMARY KEY,
    server_name VARCHAR(20) NOT NULL,
    server_url VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    last_check DATETIME NOT NULL,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Workflow_Jobs 테이블
```sql
CREATE TABLE workflow_jobs (
    id INTEGER PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    class_name VARCHAR(50),
    object_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    input_data JSON,
    output_data JSON,
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 구현 계획

### Phase 1: 기본 구조 및 객체 스캔
1. **FastAPI 서버 기본 구조** 설정
2. **Static 폴더 스캔** 기능 구현
3. **객체 데이터베이스** 초기화 및 관리
4. **기본 API 엔드포인트** 구현

### Phase 2: 서버 모니터링
1. **서버 상태 확인** 기능 구현
2. **헬스 체크** API 구현
3. **메트릭 수집** 시스템 구축

### Phase 3: 워크플로우 오케스트레이션
1. **템플릿 생성** 워크플로우 구현
2. **전체 파이프라인** 실행 기능 구현
3. **작업 관리** 시스템 구축

### Phase 4: 고급 기능
1. **배치 처리** 기능 구현
2. **에러 복구** 메커니즘 구현
3. **성능 최적화** 및 모니터링 강화

## 기술 스택
- **웹 프레임워크**: FastAPI
- **데이터베이스**: SQLite (개발) / PostgreSQL (운영)
- **ORM**: SQLAlchemy
- **비동기 처리**: asyncio
- **HTTP 클라이언트**: httpx
- **로깅**: Python logging
- **설정 관리**: Pydantic Settings

## 파일 구조
```
Main_Server/
├── api/
│   ├── endpoints/
│   │   ├── objects.py      # 객체 관리 API
│   │   ├── servers.py      # 서버 상태 API
│   │   └── workflow.py     # 워크플로우 API
│   ├── models.py           # Pydantic 모델
│   └── dependencies.py     # 의존성 주입
├── core/
│   ├── config.py           # 설정 관리
│   ├── database.py         # 데이터베이스 연결
│   └── scanner.py          # Static 폴더 스캔
├── services/
│   ├── object_service.py   # 객체 관리 서비스
│   ├── server_monitor.py   # 서버 모니터링
│   └── workflow_service.py # 워크플로우 관리
├── utils/
│   ├── file_utils.py       # 파일 유틸리티
│   └── path_utils.py       # 경로 유틸리티
├── main.py                 # FastAPI 애플리케이션
├── requirements.txt        # 의존성 목록
└── README.md              # 사용법 문서
```

## 보안 고려사항
- **API 인증**: JWT 토큰 기반 인증
- **입력 검증**: Pydantic 모델을 통한 데이터 검증
- **경로 보안**: 파일 시스템 접근 제한
- **CORS 설정**: 적절한 CORS 정책 적용

## 성능 최적화
- **캐싱**: Redis를 활용한 API 응답 캐싱
- **비동기 처리**: I/O 집약적 작업의 비동기 처리
- **연결 풀링**: 데이터베이스 연결 풀 관리
- **배치 처리**: 대량 데이터 처리 시 배치 최적화
