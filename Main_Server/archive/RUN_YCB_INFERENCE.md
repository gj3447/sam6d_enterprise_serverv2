# YCB 객체 추론 가이드

## OBJ 파일 지원 확인 ✓

SAM-6D와 현재 서버는 **OBJ 파일을 완벽하게 지원**합니다.

## 사용 방법

### 1. 템플릿 생성
```bash
cd Main_Server
python create_ycb_template.py
```

### 2. 추론 실행
```bash
cd Main_Server
python test_ism_ycb_direct.py
```

## 테스트 결과

### 템플릿 생성
- **파일**: `static/meshes/ycb/obj_000002.obj`
- **생성 시간**: 64.6초
- **템플릿 파일**: 126개 (mask, rgb, xyz)

### 추론 결과
- **감지된 객체**: 20개
- **최고 스코어**: 0.31
- **추론 시간**: 10.66초
- **상태**: ✅ 성공

## 파일 구조

```
static/
├── meshes/ycb/          # OBJ CAD 모델 파일
│   ├── obj_000002.obj
│   ├── obj_000003.obj
│   └── ...
├── templates/ycb/       # 생성된 템플릿
│   └── obj_000002/
│       ├── mask_*.png
│       ├── rgb_*.png
│       └── xyz_*.npy
└── test/                # 입력 이미지
    ├── rgb.png
    ├── depth.png
    └── camera.json
```

## 참고사항

- Render 서버 URL: `http://localhost:8004`
- ISM 서버 URL: `http://localhost:8002`
- Main 서버 URL: `http://localhost:8001`
- 컨테이너 경로: `/workspace/Estimation_Server/`

