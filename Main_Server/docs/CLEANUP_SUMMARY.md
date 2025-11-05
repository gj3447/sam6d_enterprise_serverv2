# Main_Server 정리 요약 (2025-10-30)

## 📋 정리 내용

### 1. 테스트 파일 아카이브
- `test_history/` 폴더 → `archive/test_history/`로 이동
  - 30개의 과거 테스트 파일 보관
  - 개발 과정에서 생성된 테스트 스크립트들

- 중복 테스트 파일 → `archive/tests_backup/`로 이동
  - `test_ycb_simple.py`
  - `test_full_pipeline_ycb.py`
  - `test_from_rss_ycb.py`
  - `test_from_rss_ycb_all.py`
  - `test_ism_ycb_direct.py`
  - `test_all_lm_objects.py`
  - `test_test_object_full.py`

### 2. 문서 아카이브
- `docs/` 폴더의 25개 파일 → `archive/docs_old/`로 이동
  - 이전 문서들은 `archive/docs_old/`에 보관
  - 최신 정보는 루트의 README, DESIGN, EXECUTION_GUIDE 참조

- 추가 마크다운 파일 → `archive/`로 이동
  - `FINAL_TEST_SUCCESS.md`
  - `TEST_RESULT_SUMMARY.md`
  - `SUMMARY_OUTPUT.md`
  - `RUN_YCB_INFERENCE.md`

### 3. 남은 핵심 파일

#### 주요 소스 코드
```
Main_Server/
├── api/                      # API 엔드포인트
├── services/                 # 비즈니스 로직
├── utils/                    # 유틸리티
├── main.py                   # 메인 애플리케이션
└── requirements.txt          # 의존성
```

#### 설정 파일
```
Main_Server/
├── config.env                # 기본 설정
├── config_dev.env           # 개발 설정
├── config_prod.env          # 프로덕션 설정
└── environment.yaml         # Conda 환경
```

#### 실행 스크립트
```
Main_Server/
├── run_dev.bat/sh           # 개발 모드 실행
├── run_server.bat/sh        # 프로덕션 모드 실행
└── stop_server.sh           # 서버 중지
```

#### 문서
```
Main_Server/
├── README.md                # 메인 문서 ⭐
├── README_BACKGROUND.md     # 백그라운드 실행 가이드
├── DESIGN.md                # 설계 문서
└── EXECUTION_GUIDE.md       # 실행 가이드
```

#### 테스트 파일
```
Main_Server/
├── test_api_full_pipeline.py      # API 테스트
├── test_rss_api_call.py           # RSS 테스트
├── test_ycb_full_pipeline.py      # YCB 파이프라인 테스트
├── create_ycb_template.py         # 템플릿 생성
└── rss_connector_save.py          # RSS 커넥터
```

#### 아카이브
```
Main_Server/
└── archive/
    ├── docs_old/              # 이전 문서들
    ├── test_history/          # 과거 테스트
    ├── tests_backup/          # 중복 테스트
    └── *.md                   # 이전 마크다운
```

## 🎯 정리 결과

### Before
- 루트 파일: 40개+
- test_history: 30개
- docs: 25개
- test_*.py: 16개+
- **총 파일 수: 96개+**

### After
- 루트 파일: **20개** (핵심만 유지)
- archive/: **76개** (보관 파일들)
- **정리율: 73% 감소** ✅

## ✅ 유지된 핵심 기능

1. **서버 실행**
   - 개발 모드: `run_dev.bat/sh`
   - 프로덕션 모드: `run_server.bat/sh`

2. **API 테스트**
   - `test_api_full_pipeline.py` - 전체 파이프라인 테스트
   - `test_rss_api_call.py` - RSS 연동 테스트

3. **문서**
   - `README.md` - 빠른 시작 가이드
   - `DESIGN.md` - 상세 설계 문서
   - `EXECUTION_GUIDE.md` - 실행 가이드

4. **유틸리티**
   - `create_ycb_template.py` - 템플릿 생성
   - `rss_connector_save.py` - RSS 커넥터

## 📝 참고사항

- 아카이브된 파일들은 참조용으로 보관됨
- 삭제된 파일이 아니라 `archive/` 폴더로 이동됨
- 필요시 `archive/`에서 파일 복원 가능

## 🔄 다음 단계

1. **서버 실행**: `run_dev.bat` (Windows) 또는 `run_dev.sh` (Linux/Mac)
2. **API 테스트**: `python test_api_full_pipeline.py`
3. **문서 확인**: `README.md` 또는 `DESIGN.md`
4. **문제 발생 시**: `logs/` 폴더의 로그 파일 확인

