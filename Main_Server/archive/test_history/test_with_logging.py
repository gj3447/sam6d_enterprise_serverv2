#!/usr/bin/env python3
"""
파이프라인 실행 테스트 - 상세 로그 기록
"""
import asyncio
import sys
import traceback
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

# 로깅 설정
log_dir = Path("Main_Server/logs")
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"test_{timestamp}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def test():
    logger.info("=" * 70)
    logger.info("파이프라인 실행 테스트 시작")
    logger.info(f"로그 파일: {log_file}")
    logger.info("=" * 70)
    
    try:
        # 1. Scanner 확인
        logger.info("\n[1단계] Scanner 확인")
        try:
            from Main_Server.services.scanner import get_scanner
            scanner = get_scanner()
            logger.info("✓ Scanner import 성공")
            
            obj = scanner.scan_object("test", "obj_000005")
            logger.info(f"  - 템플릿 존재: {obj['has_template']}")
            logger.info(f"  - 파일 수: {obj['template_files']}")
        except Exception as e:
            logger.error(f"✗ Scanner 에러: {e}")
            logger.error(traceback.format_exc())
            return
        
        # 2. Workflow Service 확인
        logger.info("\n[2단계] Workflow Service 확인")
        try:
            from Main_Server.services.workflow_service import get_workflow_service
            workflow = get_workflow_service()
            logger.info("✓ Workflow Service import 성공")
        except Exception as e:
            logger.error(f"✗ Workflow Service 에러: {e}")
            logger.error(traceback.format_exc())
            return
        
        # 3. 파이프라인 실행
        logger.info("\n[3단계] 파이프라인 실행")
        try:
            logger.info("execute_full_pipeline 호출 중...")
            result = await workflow.execute_full_pipeline(
                class_name="test",
                object_name="obj_000005",
                input_images={
                    "rgb_path": "static/test/rgb.png",
                    "depth_path": "static/test/depth.png",
                    "camera_path": "static/test/camera.json"
                }
            )
            
            logger.info(f"✓ 파이프라인 실행 완료")
            logger.info(f"  - 성공: {result.get('success')}")
            logger.info(f"  - 출력: {result.get('output_dir')}")
            
            if not result.get('success'):
                logger.error(f"  - 에러: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"✗ 파이프라인 실행 에러: {e}")
            logger.error(traceback.format_exc())
            return
        
        # 4. 결과 파일 확인
        logger.info("\n[4단계] 결과 파일 확인")
        try:
            output_dir = Path(result.get('output_dir', ''))
            if output_dir.exists():
                files = [f for f in output_dir.rglob("*") if f.is_file()]
                logger.info(f"✓ 생성된 파일: {len(files)}개")
                for f in files[:10]:
                    logger.info(f"  - {f.relative_to(output_dir.parent)} ({f.stat().st_size} bytes)")
            else:
                logger.warning(f"⚠ 출력 디렉토리 없음: {output_dir}")
        except Exception as e:
            logger.error(f"✗ 결과 확인 에러: {e}")
            logger.error(traceback.format_exc())
        
        logger.info("\n" + "=" * 70)
        logger.info("테스트 완료")
        logger.info(f"로그 파일: {log_file}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"\n✗ 치명적 에러: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test())

