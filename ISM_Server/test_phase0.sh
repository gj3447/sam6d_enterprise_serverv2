#!/bin/bash
# Phase 0: Docker 환경 및 라이브러리 Import 테스트 스크립트

echo "=== Phase 0: Docker 환경 및 라이브러리 Import 테스트 ==="

# 1. ISM_Server Docker 이미지 빌드
echo "1. ISM_Server Docker 이미지 빌드 중..."
docker-compose build

# 2. Docker 컨테이너 실행
echo "2. Docker 컨테이너 실행 중..."
docker-compose up -d

# 잠시 대기
sleep 5

# 3. 컨테이너 접속하여 기본 환경 확인
echo "3. 기본 환경 확인 중..."
docker exec ism-server bash -c "
echo '=== Python 환경 확인 ==='
source /opt/conda/etc/profile.d/conda.sh
source /opt/conda/etc/profile.d/conda.sh
conda activate sam6d
python --version
echo ''

echo '=== 작업 디렉토리 확인 ==='
pwd
ls -la /workspace/Estimation_Server/
echo ''

echo '=== 기본 라이브러리 Import 테스트 ==='
python -c '
import torch
print(f\"PyTorch version: {torch.__version__}\")
print(f\"CUDA available: {torch.cuda.is_available()}\")

import numpy as np
print(f\"NumPy version: {np.__version__}\")

from PIL import Image
print(\"PIL imported successfully\")

import trimesh
print(\"Trimesh imported successfully\")

import cv2
print(f\"OpenCV version: {cv2.__version__}\")
'
"

# 4. SAM-6D 관련 라이브러리 Import 테스트
echo "4. SAM-6D 관련 라이브러리 Import 테스트 중..."
docker exec ism-server bash -c "
source /opt/conda/etc/profile.d/conda.sh
source /opt/conda/etc/profile.d/conda.sh
conda activate sam6d
cd /workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model

echo '=== SAM-6D 라이브러리 Import 테스트 ==='
python -c '
import sys
sys.path.append(\"/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model\")

# Hydra 테스트
from hydra import initialize, compose
print(\"Hydra imported successfully\")

# SAM-6D 모델 테스트
from model.utils import Detections
print(\"SAM-6D model utils imported successfully\")

# 추론 함수 테스트
from run_inference_custom_function import load_templates_from_files
print(\"run_inference_custom_function imported successfully\")
'
"

# 5. FastAPI 라이브러리 설치 및 테스트
echo "5. FastAPI 라이브러리 설치 및 테스트 중..."
docker exec ism-server bash -c "
source /opt/conda/etc/profile.d/conda.sh
conda activate sam6d
cd /workspace/ISM_Server

echo '=== FastAPI 라이브러리 설치 ==='
pip install fastapi uvicorn[standard] pydantic python-multipart

echo '=== 설치 확인 ==='
python -c '
import fastapi
print(f\"FastAPI version: {fastapi.__version__}\")

import uvicorn
print(\"Uvicorn imported successfully\")

import pydantic
print(f\"Pydantic version: {pydantic.__version__}\")
'
"

# 6. 최소 FastAPI 서버 테스트
echo "6. 최소 FastAPI 서버 테스트 중..."
docker exec ism-server bash -c "
source /opt/conda/etc/profile.d/conda.sh
conda activate sam6d
cd /workspace/ISM_Server

echo '=== FastAPI 서버 실행 테스트 ==='
timeout 10s uvicorn main:app --host 0.0.0.0 --port 8002 &
SERVER_PID=\$!

# 서버 시작 대기
sleep 3

# 테스트 요청
echo '=== API 테스트 ==='
curl -s http://localhost:8002/ || echo \"API 테스트 실패\"
curl -s http://localhost:8002/health || echo \"Health API 테스트 실패\"

# 서버 종료
kill \$SERVER_PID 2>/dev/null || true
"

echo "=== Phase 0 테스트 완료 ==="
echo "모든 테스트가 성공하면 Phase 1로 진행할 수 있습니다."

# 컨테이너 정리
echo "컨테이너 정리 중..."
docker-compose down
