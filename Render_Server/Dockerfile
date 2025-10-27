# Render_Server Dockerfile
FROM ai_server-server:latest

# 작업 디렉토리 설정
WORKDIR /workspace/Estimation_Server

# Copy Render_Server code (only existing files)
COPY requirements.txt render_*.py /workspace/Estimation_Server/Render_Server/

# Estimation_Server 전체를 마운트할 예정이므로 필요한 경로들 설정
ENV RENDER_SERVER_HOST=0.0.0.0
ENV RENDER_SERVER_PORT=8004
ENV RENDER_LOG_LEVEL=INFO
ENV BLENDER_PROC_SAMPLES=50
ENV DISPLAY=:99

# Python path 설정 (Render 모듈 경로 추가)
ENV PYTHONPATH="/workspace/Estimation_Server/SAM-6D/SAM-6D/Render"

# 포트 노출
EXPOSE 8004

# 기본 명령어 (sam6d 환경에서 컨테이너 유지)
CMD ["bash", "-c", "source /opt/conda/bin/activate sam6d && cd /workspace/Estimation_Server/Render_Server && echo 'Render Server Docker environment is ready!' && tail -f /dev/null"]
