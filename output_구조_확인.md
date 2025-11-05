# 추론 Output 저장 위치 및 구조

## 📁 전체 Output 디렉토리 위치

```
static/output/
```

---

## 🎯 파이프라인별 Output 구조

### 1. **Full Pipeline 실행** (Main_Server)

출력 디렉토리 명명 규칙:
- 지정 안함: `static/output/<YYYYMMDD_HHMMSS>/`
- 지정함: 사용자 지정 경로

#### 구조:
```
static/output/20250128_143022/
├── ism/                          # ISM 결과
│   ├── detection_ism.json       # 탐지 결과 JSON
│   ├── detection_ism.npz        # 탐지 결과 NumPy
│   └── vis_ism.png              # ISM 시각화 이미지 ⭐
└── pem/                          # PEM 결과
    ├── detection_pem.json       # 포즈 추정 결과 JSON
    └── vis_pem.png              # PEM 시각화 이미지 ⭐
```

---

### 2. **ISM 단독 실행**

구조:
```
static/output/<임의_이름>/
├── detection_ism.json
├── detection_ism.npz
└── vis_ism.png                  # 탐지 시각화
```

**예시**: `static/output/test_ism_result/`

---

### 3. **PEM 단독 실행**

구조:
```
static/output/<임의_이름>/
├── detection_pem.json
└── vis_pem.png                  # 포즈 추정 시각화
```

**예시**: `static/output/pem_only_test/`

---

## 📊 파일 상세

### ISM Output 파일

#### `detection_ism.json`
```json
[
    {
        "scene_id": 0,
        "image_id": 0,
        "category_id": 1,
        "bbox": [x1, y1, x2, y2],
        "score": 0.95,
        "segmentation": {
            "size": [height, width],
            "counts": "RLE_encoded_string"
        }
    }
]
```

#### `detection_ism.npz`
- NumPy 바이너리 형식
- 모든 탐지 결과를 압축 저장

#### `vis_ism.png`
- RGB 이미지에 탐지 결과 오버레이
- Bounding box와 segmentation mask 시각화

---

### PEM Output 파일

#### `detection_pem.json`
```json
[
    {
        "translation": [x, y, z],      # 3D 위치 (meters)
        "rotation": [qx, qy, qz, qw],  # Quaternion 자세
        "confidence": 0.92              # 신뢰도
    }
]
```

#### `vis_pem.png`
- RGB 이미지에 3D 포즈 시각화
- CAD 모델을 추정된 포즈로 렌더링

---

## 🔍 실제 저장 위치 확인

### 현재 저장된 Output들:

#### 1. `test_result_new/` (Full Pipeline 테스트)
```
static/output/test_result_new/
├── detection_ism.json       ✅
├── detection_ism.npz        ✅
├── detection_pem.json       ✅
├── vis_ism.png             ✅ (2948 lines)
└── vis_pem.png             ✅ (1787 lines)
```

#### 2. `test_ism_result/` (ISM 단독 테스트)
```
static/output/test_ism_result/
├── detection_ism.json       ✅
├── detection_ism.npz        ✅
└── vis_ism.png             ✅
```

---

## 🎯 코드에서 Output 경로 설정

### Main_Server (workflow_service.py)

```python
# 전체 파이프라인 실행 시
if not output_dir:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = str(self.paths["output"] / timestamp)

output_path = Path(output_dir)
output_path.mkdir(parents=True, exist_ok=True)

# ISM 출력: output_path / "ism"
# PEM 출력: output_path / "pem"
```

### `self.paths` 설정:
```python
# Main_Server/utils/path_utils.py
{
    "meshes": static/meshes/,
    "templates": static/templates/,
    "output": static/output/    # ← 여기!
}
```

---

## 📌 요약

### Output 저장 위치
- **기본 경로**: `static/output/`
- **Full Pipeline**: `static/output/<timestamp>/ism/`, `pem/`
- **단독 실행**: `static/output/<custom_name>/`

### 생성 파일
1. **JSON**: 탐지/포즈 결과 (텍스트)
2. **NPZ**: NumPy 바이너리 (ISM만)
3. **PNG**: 시각화 이미지 (ISM, PEM 각각)

### 특징
- ✅ 자동 디렉토리 생성
- ✅ 타임스탬프 기반 중복 방지
- ✅ 단계별 분리 (ism/, pem/)
- ✅ 시각화 이미지 자동 저장

