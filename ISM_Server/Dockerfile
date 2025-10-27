# ISM_Server Dockerfile
FROM ai_server-server:latest

# 작업 디렉토리 설정
WORKDIR /workspace/Estimation_Server

# Copy ISM_Server code
COPY requirements.txt main.py test_imports.py test_model_loading.py /workspace/Estimation_Server/ISM_Server/

# Estimation_Server 전체를 마운트할 예정이므로 필요한 경로들 설정
ENV ISM_MODEL_TYPE=sam
ENV ISM_STABILITY_THRESHOLD=0.97
ENV ISM_TEMPLATE_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/outputs/templates
ENV ISM_CAD_MODEL_PATH=/workspace/Estimation_Server/SAM-6D/SAM-6D/Data/Example/obj_000005.ply
ENV ISM_CONFIG_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/configs
ENV ISM_CHECKPOINTS_DIR=/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model/checkpoints
ENV ISM_SERVER_HOST=0.0.0.0
ENV ISM_SERVER_PORT=8002
ENV ISM_LOG_LEVEL=INFO

# Python path 설정
ENV PYTHONPATH="/workspace/Estimation_Server/SAM-6D/SAM-6D/Instance_Segmentation_Model:${PYTHONPATH}"

# 포트 노출
EXPOSE 8002

# 기본 명령어 (sam6d 환경에서 서버 실행)
CMD ["bash", "-c", "source /opt/conda/bin/activate sam6d && cd /workspace/Estimation_Server/ISM_Server && python main.py"]
