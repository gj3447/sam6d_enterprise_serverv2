# PEM_Server/core/logging_config.py
"""
PEM Server 로깅 설정
"""
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

def setup_logging(
    log_dir: str = "log",
    log_level: str = "INFO",
    log_format: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    로깅 시스템 설정
    
    Args:
        log_dir: 로그 파일 디렉토리
        log_level: 로그 레벨
        log_format: 로그 포맷
        max_bytes: 로그 파일 최대 크기
        backup_count: 백업 파일 개수
        
    Returns:
        logging.Logger: 설정된 로거
    """
    # 로그 디렉토리 생성
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일명 생성 (타임스탬프 포함)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"pem_server_{timestamp}.log"
    log_path = os.path.join(log_dir, log_filename)
    
    # 기본 로그 포맷
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 파일 핸들러 설정 (로테이팅)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    
    # 핸들러 추가
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 로그 시작 메시지
    logger = logging.getLogger(__name__)
    logger.info(f"Logging system initialized")
    logger.info(f"Log file: {log_path}")
    logger.info(f"Log level: {log_level}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 반환"""
    return logging.getLogger(name)
