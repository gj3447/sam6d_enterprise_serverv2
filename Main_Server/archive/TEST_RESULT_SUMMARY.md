# 추론 API 테스트 결과 요약

## ✅ 성공적으로 실행됨!

### 테스트 요청
- 클래스: `test`
- 객체: `obj_000005`
- RGB 이미지: `static/test/rgb.png` (Base64 인코딩)
- Depth 이미지: `static/test/depth.png` (Base64 인코딩)
- 카메라 파라미터: `static/test/camera.json` (cam_K, depth_scale)

## 📂 생성된 파일

### 출력 디렉토리: `static/output/20251029_113613/`

#### ISM 결과 (성공!)
- `detection_ism.json` (21KB) - 34개 객체 감지
- `detection_ism.npz` (49KB)
- `vis_ism.png` (762KB) - 시각화 이미지

#### PEM 결과 (실패 - CUDA OOM)
- 파일 없음
- 에러: CUDA out of memory

## 📊 ISM 결과 상세

### 감지된 객체 수
- 총 34개 객체 감지
- Score 범위: 0.195 ~ 0.429

### 상위 감지 결과 (Score 높은 순)
1. Score: 0.429 - Box: [376, 227, 435, 309]
2. Score: 0.388 - Box: [581, 304, 633, 351]
3. Score: 0.364 - Box: [110, 119, 166, 186]
4. Score: 0.321 - Box: [301, 128, 134, 187]
5. Score: 0.307 - Box: [122, 119, 166, 174]

### 추론 시간
- ISM: 25초
- PEM: 51초 (실패)

## ⚠️ PEM 실패 원인

### CUDA Out of Memory 에러
```
CUDA out of memory. Tried to allocate 7.40 GiB 
(GPU 0; 11.99 GiB total capacity; 18.19 GiB already allocated)
```

### 해결 방법
1. GPU 메모리 해제 (다른 프로세스 종료)
2. 배치 사이즈 줄이기
3. 이미지 크기 줄이기

## 🎯 결론

### 정상 동작
- ✅ API 엔드포인트
- ✅ 이미지 인코딩
- ✅ 카메라 파라미터 처리
- ✅ ISM 추론 성공
- ✅ 파일 생성 (detection_ism.json, vis_ism.png)

### 개선 필요
- ⚠️ PEM: GPU 메모리 부족
- ⚠️ ISM: 34개는 너무 많은 감지 결과 (스코어 임계값 조정 필요)

## 💡 실제 사용 시 개선 사항

1. **Score 임계값 조정**: ISM 결과가 너무 많음 (34개 → 필터링 필요)
2. **GPU 메모리 관리**: PEM 실행 전 메모리 정리
3. **결과 검증**: Score 0.2 이상만 사용

