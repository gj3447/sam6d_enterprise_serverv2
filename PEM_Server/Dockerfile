# PEM_Server Dockerfile
FROM ai_server-server:latest

# 작업 디렉토리 설정
WORKDIR /workspace/Estimation_Server

# Copy PEM_Server code
COPY requirements.txt main.py test_imports.py test_model_loading.py /workspace/Estimation_Server/PEM_Server/

# Estimation_Server 전체를 마운트할 예정이므로 필요한 경로들 설정
ENV PEM_MODEL_TYPE=pem
ENV PEM_CONFIG_PATH=/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/config/base.yaml
ENV PEM_CHECKPOINT_PATH=/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/checkpoints/sam-6d-pem-base.pth
ENV PEM_CAD_MODEL_PATH=/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply
ENV PEM_SERVER_HOST=0.0.0.0
ENV PEM_SERVER_PORT=8003
ENV PEM_LOG_LEVEL=INFO

# Python path 설정 (PEM 모듈 경로 추가)
ENV PYTHONPATH="/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model:/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/utils:/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/model:/workspace/Estimation_Server/SAM-6D/SAM-6D/Pose_Estimation_Model/provider:${PYTHONPATH}"

# 포트 노출
EXPOSE 8003

# 기본 명령어 (sam6d 환경에서 서버 실행)
CMD ["bash", "-c", "source /opt/conda/bin/activate sam6d && cd /workspace/Estimation_Server/PEM_Server && python main.py"]
