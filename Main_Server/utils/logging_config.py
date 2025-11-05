#!/usr/bin/env python3
"""
로깅 설정 유틸리티
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_dir: Path = None,
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """로깅 설정
    
    Args:
        log_dir: 로그 디렉토리 경로 (없으면 logs 디렉토리 생성)
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 파일 로그 활성화 여부
        log_to_console: 콘솔 로그 활성화 여부
        
    Returns:
        설정된 Logger 인스턴스
    """
    # 로그 레벨 변환
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 로그 디렉토리 설정
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 로그 포맷 설정
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 핸들러 리스트
    handlers = []
    
    # 콘솔 핸들러
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers.append(console_handler)
    
    # 파일 핸들러
    if log_to_file:
        # 일자별 로그 파일
        log_filename = f"main_server_{datetime.now().strftime('%Y%m%d')}.log"
        log_file = log_dir / log_filename
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers.append(file_handler)
    
    # 루트 로거 설정
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True  # 기존 핸들러 무시
    )
    
    # FastAPI, uvicorn 로거 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info(f"로깅 설정 완료: level={log_level}, file={log_file if log_to_file else 'disabled'}")
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Logger 인스턴스 반환
    
    Args:
        name: 로거 이름 (없으면 호출 모듈 이름)
        
    Returns:
        Logger 인스턴스
    """
    return logging.getLogger(name or __name__)

