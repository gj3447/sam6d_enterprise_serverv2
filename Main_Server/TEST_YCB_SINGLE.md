# YCB 객체 단일 테스트 가이드

## 현재 상황

Main Server는 프로덕션 모드로 실행 중입니다.
- URL: http://localhost:8001
- 상태: 정상 ✅

## 테스트 방법

### 방법 1: Python 스크립트로 테스트

```bash
cd Main_Server
python test_ycb_full_pipeline.py obj_000002
```

### 방법 2: curl로 API 직접 호출

```bash
# 헬스 체크
curl http://localhost:8001/health

# 서버 상태 확인
curl http://localhost:8001/api/v1/servers/status

# 전체 파이프라인 테스트
curl -X POST http://localhost:8001/api/v1/workflow/full-pipeline \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

### 방법 3: Swagger UI 사용

브라우저에서 http://localhost:8001/docs 접속하여 직접 테스트

## 테스트 데이터

- RGB 이미지: `static/test/rsserver_final_camk/color_raw.png`
- Depth 이미지: `static/test/rsserver_final_camk/depth_raw.png`
- Camera: `static/test/rsserver_final_camk/camera.json`

## 테스트할 YCB 객체

1. obj_000002
2. obj_000003
3. obj_000004
4. obj_000005
5. obj_000006

## 주의사항

1. 프로덕션 모드로 실행 중 (안정적)
2. 무한 루프 문제 해결됨
3. 배치 테스트는 하나씩 실행 권장 (무거움)

## 다음 단계

각 객체에 대해 개별적으로 테스트하세요.













