#!/usr/bin/env python3
"""
워크플로우 오케스트레이션 서비스
"""
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime
import time
import httpx
import requests
import base64
import json
import cv2
import numpy as np
import io
import os

try:
    from ..utils.path_utils import get_static_paths, get_project_root
    from ..services.scanner import get_scanner
except ImportError:
    from utils.path_utils import get_static_paths, get_project_root
    from services.scanner import get_scanner
import requests
import base64
from PIL import Image
from pycocotools import mask as mask_utils


SAVE_INPUT_IMAGES = os.getenv("MAIN_SERVER_SAVE_INPUT_IMAGES", "false").lower() == "true"
SAVE_SERVER_RESPONSES = os.getenv("MAIN_SERVER_SAVE_SERVER_RESPONSES", "false").lower() == "true"
SAVE_CAMERA_PARAMS = os.getenv("MAIN_SERVER_SAVE_CAMERA_PARAMS", "true").lower() == "true"


class WorkflowService:
    """전체 워크플로우를 오케스트레이션하는 서비스"""
    
    def __init__(self):
        self.paths = get_static_paths()
        self.scanner = get_scanner()
    
    def _normalize_tag(self, tag: Optional[str], default: str) -> str:
        """출력 디렉토리 이름에 사용할 태그 문자열 정규화"""
        value = (tag or default or "").lower()
        sanitized = []
        for ch in value:
            if ch.isalnum():
                sanitized.append(ch)
            elif ch in ("-", "_"):
                sanitized.append(ch)
            else:
                sanitized.append("-")
        normalized = "".join(sanitized).strip("-_")
        return normalized or default or "pipeline"

    async def render_templates(
        self,
        class_name: str,
        object_names: list,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """템플릿 생성 워크플로우
        
        Args:
            class_name: 클래스 이름
            object_names: 객체 이름 목록
            force_regenerate: 강제 재생성 여부
            
        Returns:
            Dict: 워크플로우 결과
        """
        results = []
        
        for object_name in object_names:
            try:
                # CAD 파일 경로 - 여러 형식 지원 (.ply, .obj, .stl)
                cad_path = None
                for ext in ['.ply', '.obj', '.stl']:
                    candidate = self.paths["meshes"] / class_name / f"{object_name}{ext}"
                    if candidate.exists():
                        cad_path = candidate
                        break
                
                if not cad_path or not cad_path.exists():
                    results.append({
                        "object_name": object_name,
                        "success": False,
                        "error": f"CAD file not found: {object_name} (looking for .ply, .obj, or .stl)"
                    })
                    continue
                
                # 템플릿 출력 디렉토리
                template_output_dir = self.paths["templates"] / class_name / object_name
                
                # 이미 템플릿이 있고 강제 재생성이 아닌 경우 스킵
                if template_output_dir.exists() and not force_regenerate:
                    results.append({
                        "object_name": object_name,
                        "success": True,
                        "skipped": True,
                        "message": "Template already exists"
                    })
                    continue
                
                # Render 서버 호출
                result = await self._call_render_server(
                    cad_path=str(cad_path),
                    template_output_dir=str(template_output_dir)
                )
                
                if result and result.get("success"):
                    results.append({
                        "object_name": object_name,
                        "success": True,
                        "result": result
                    })
                else:
                    results.append({
                        "object_name": object_name,
                        "success": False,
                        "error": "Render server failed"
                    })
                    
            except Exception as e:
                results.append({
                    "object_name": object_name,
                    "success": False,
                    "error": str(e)
                })
        
        successful = sum(1 for r in results if r.get("success"))
        
        return {
            "success": successful > 0,
            "total": len(object_names),
            "successful": successful,
            "results": results
        }
    
    async def execute_full_pipeline(
        self,
        class_name: str,
        object_name: str,
        rgb_image: str,
        depth_image: str,
        cam_params: Dict[str, Any],
        output_dir: Optional[str] = None,
        frame_guess: bool = False,
        request_tag: Optional[str] = None,
        output_mode: str = "full",
    ) -> Dict[str, Any]:
        """전체 파이프라인 실행 (Render → ISM → PEM)
        
        Args:
            class_name: 클래스 이름
            object_name: 객체 이름
            rgb_image: Base64 인코딩된 RGB 이미지
            depth_image: Base64 인코딩된 Depth 이미지
            cam_params: 카메라 파라미터 (intrinsics)
            output_dir: 출력 디렉토리 (없으면 자동 생성)
            
        Returns:
            Dict: 파이프라인 결과
        """
        mode = (output_mode or "full").lower()
        if mode not in {"full", "results_only", "none"}:
            mode = "full"

        save_all = mode == "full"
        save_summary = mode in {"full", "results_only"}

        tag_value = self._normalize_tag(request_tag, "full-pipeline")
        if save_summary:
            if not output_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = str(self.paths["output"] / f"{timestamp}_{tag_value}")
            output_path: Optional[Path] = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = None
            output_dir = None
        
        # 경로 준비 (클래스/객체 이름으로 자동 계산)
        # CAD 파일 경로 - 여러 형식 지원
        cad_path = None
        for ext in ['.ply', '.obj', '.stl']:
            candidate = self.paths["meshes"] / class_name / f"{object_name}{ext}"
            if candidate.exists():
                cad_path = candidate
                break
        
        if not cad_path or not cad_path.exists():
            return {
                "success": False,
                "error": f"CAD file not found: {object_name} (looking for .ply, .obj, or .stl)"
            }
        
        template_dir = self.paths["templates"] / class_name / object_name
        
        results = {}
        image_shape = self._infer_image_shape(rgb_image)
        
        # 파이프라인 메타데이터 수집
        start_time = datetime.now()
        
        if save_all and output_path is not None:
            self._save_input_data(output_path, rgb_image, depth_image, cam_params)
        
        try:
            # 1단계: 템플릿 생성 (Render)
            print("[INFO] Step 1: Rendering templates...")
            if not template_dir.exists():
                render_result = await self._call_render_server(
                    cad_path=str(cad_path),
                    template_output_dir=str(template_dir)
                )
                results["render"] = render_result
            else:
                print("[INFO] Template already exists, skipping render step")
                results["render"] = {"skipped": True}
            
            # 2단계: 객체 감지 (ISM)
            print("[INFO] Step 2: Running ISM inference...")
            ism_output_dir = (output_path / "ism") if (save_all and output_path is not None) else None
            ism_result = await self._call_ism_server(
                rgb_image=rgb_image,
                depth_image=depth_image,
                cam_params=cam_params,
                cad_path=str(cad_path),
                template_dir=str(template_dir),
                output_dir=str(ism_output_dir) if ism_output_dir is not None else None,
                parent_output_dir=str(output_path) if save_all and output_path is not None else None,
                save_outputs=save_all,
            )
            results["ism"] = ism_result
            
            # 3단계: 포즈 추정 (PEM)
            print("[INFO] Step 3: Running PEM inference...")
            pem_output_dir = (output_path / "pem") if (save_all and output_path is not None) else None
            pem_result = await self._call_pem_server(
                rgb_image=rgb_image,
                depth_image=depth_image,
                cam_params=cam_params,
                cad_path=str(cad_path),
                template_dir=str(template_dir),
                ism_result=ism_result,
                output_dir=str(pem_output_dir) if pem_output_dir is not None else None,
                parent_output_dir=str(output_path) if save_all and output_path is not None else None,
                frame_guess=frame_guess,
                save_outputs=save_all,
                image_shape=image_shape,
            )
            results["pem"] = pem_result

            pose_summary = self._extract_pose_summary(pem_result)

            # 파이프라인 성공 - 메타데이터 저장
            end_time = datetime.now()
            if save_all and output_path is not None:
                metadata = self._create_metadata(
                    class_name=class_name,
                    object_name=object_name,
                    cad_path=str(cad_path),
                    template_dir=str(template_dir),
                    template_existed=template_dir.exists(),
                    cam_params=cam_params,
                    start_time=start_time,
                    end_time=end_time,
                    results=results,
                    success=True,
                    request_tag=tag_value
                )
                self._save_metadata(output_path, metadata)
            if save_summary and output_path is not None:
                self._save_pose_summary(output_path, True, pose_summary, None)
            
            return {
                "success": True,
                "output_dir": output_dir if save_summary else None,
                "request_tag": tag_value,
                "pose_results": pose_summary,
                "num_poses": len(pose_summary),
            }
            
        except Exception as e:
            # 파이프라인 실패 - 메타데이터 저장
            end_time = datetime.now()
            if save_all and output_path is not None:
                metadata = self._create_metadata(
                    class_name=class_name,
                    object_name=object_name,
                    cad_path=str(cad_path) if cad_path else None,
                    template_dir=str(template_dir),
                    template_existed=template_dir.exists(),
                    cam_params=cam_params,
                    start_time=start_time,
                    end_time=end_time,
                    results=results,
                    success=False,
                    error=str(e),
                    request_tag=tag_value
                )
                self._save_metadata(output_path, metadata)
            
            pose_summary = self._extract_pose_summary(results.get("pem"))
            if save_summary and output_path is not None:
                self._save_pose_summary(output_path, False, pose_summary, str(e))

            return {
                "success": False,
                "error": str(e),
                "output_dir": output_dir if save_summary else None,
                "request_tag": tag_value,
                "pose_results": pose_summary,
                "num_poses": len(pose_summary),
            }
    
    def _to_container_path(self, host_path: Path) -> str:
        """호스트 경로를 컨테이너 경로로 변환"""
        project_root = get_project_root()
        rel = host_path.resolve().relative_to(project_root)
        return str(Path("/workspace/Estimation_Server").joinpath(rel).as_posix())
    
    async def _call_render_server(
        self,
        cad_path: str,
        template_output_dir: str
    ) -> Dict[str, Any]:
        """Render 서버 호출"""
        cad_path_obj = Path(cad_path)
        template_dir_obj = Path(template_output_dir)
        
        # 컨테이너 경로로 변환
        cad_container = self._to_container_path(cad_path_obj)
        template_container = self._to_container_path(template_dir_obj)
        
        # Render 서버 호출
        url = "http://localhost:8004/render/templates"
        data = {
            "cad_path": cad_container,
            "output_dir": template_container
        }
        params = {"wait": True, "wait_timeout_sec": 3600}
        
        try:
            async with httpx.AsyncClient(timeout=3720.0) as client:
                response = await client.post(url, json=data, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"success": False, "error": response.text}
        except httpx.TimeoutException as e:
            return {"success": False, "error": f"Render Server timeout: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _check_server_health(self, server_name: str, health_url: str) -> bool:
        """서버 헬스 체크"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                if response.status_code == 200:
                    print(f"[INFO] {server_name} 서버 헬스 체크: OK")
                    return True
                else:
                    print(f"[WARN] {server_name} 서버 헬스 체크 실패: HTTP {response.status_code}")
                    return False
        except Exception as e:
            print(f"[WARN] {server_name} 서버 헬스 체크 실패: {str(e)}")
            return False
    
    async def _monitor_request_progress(self, server_name: str, start_time: float, timeout: float):
        """요청 진행 상황 모니터링 (백그라운드 태스크)"""
        elapsed = 0
        warning_thresholds = [30, 60, 120, 180, 300]  # 30초, 1분, 2분, 3분, 5분 경고
        last_warning = 0
        
        while elapsed < timeout:
            await asyncio.sleep(10)  # 10초마다 체크
            elapsed = time.time() - start_time
            
            # 경고 임계값 체크
            for threshold in warning_thresholds:
                if elapsed >= threshold and elapsed - last_warning >= 60:  # 1분마다 한 번만 경고
                    remaining = timeout - elapsed
                    print(f"[INFO] {server_name} 서버 요청 진행 중... (경과: {elapsed:.0f}초, 남은 시간: {remaining:.0f}초)")
                    last_warning = elapsed
                    break
            
            # 타임아웃 임박 경고 (60초 전)
            if timeout - elapsed <= 60 and elapsed - last_warning >= 10:
                print(f"[WARN] {server_name} 서버 타임아웃 임박! (남은 시간: {timeout - elapsed:.0f}초)")
                last_warning = elapsed
    
    async def _call_ism_server(
        self,
        rgb_image: str,
        depth_image: str,
        cam_params: Dict[str, Any],
        cad_path: str,
        template_dir: str,
        output_dir: Optional[str],
        parent_output_dir: Optional[str] = None,
        save_outputs: bool = True,
    ) -> Dict[str, Any]:
        """ISM 서버 호출"""
        cad_obj = Path(cad_path)
        template_obj = Path(template_dir)
        output_container = None
        parent_output_path = None
        if save_outputs and output_dir:
            output_obj = Path(output_dir)
            output_obj.mkdir(parents=True, exist_ok=True)
            output_container = self._to_container_path(output_obj)
            parent_output_path = Path(parent_output_dir) if parent_output_dir else output_obj.parent
        
        # 컨테이너 경로로 변환
        cad_container = self._to_container_path(cad_obj)
        template_container = self._to_container_path(template_obj)
        
        print(f"[INFO] ISM 서버 호출 시작")
        print(f"  CAD: {cad_container}")
        print(f"  Template: {template_container}")
        if output_container:
            print(f"  Output: {output_container}")
        
        # 서버 헬스 체크
        health_ok = await self._check_server_health("ISM", "http://localhost:8002/health")
        if not health_ok:
            print(f"[WARN] ISM 서버 헬스 체크 실패했지만 요청을 계속 진행합니다...")
        
        inference_request = {
            "rgb_image": rgb_image,
            "depth_image": depth_image,
            "cam_params": cam_params,
            "template_dir": template_container,
            "cad_path": cad_container,
        }
        if output_container:
            inference_request["output_dir"] = output_container
        
        # ISM 서버 호출
        url = "http://localhost:8002/api/v1/inference"
        timeout = 600.0
        start_time = time.time()
        
        try:
            # 진행 상황 모니터링 태스크 시작
            monitor_task = asyncio.create_task(
                self._monitor_request_progress("ISM", start_time, timeout)
            )
            
            try:
                # 비동기 HTTP 클라이언트 사용 (httpx)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    print(f"[INFO] ISM 서버에 요청 전송 중... (타임아웃: {timeout}초)")
                    response = await client.post(
                        url,
                        json=inference_request,
                        headers={"Content-Type": "application/json"},
                    )
                    
                    elapsed = time.time() - start_time
                    monitor_task.cancel()  # 모니터링 태스크 종료
                    
                    print(f"[INFO] ISM 서버 응답 수신 완료 (소요 시간: {elapsed:.2f}초)")
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # 결과 요약 출력
                        if "detections" in result:
                            detections = result.get("detections", {})
                            if isinstance(detections, dict):
                                num_detections = len(detections.get("masks", [])) if isinstance(detections.get("masks"), list) else 0
                                print(f"[INFO] ISM 추론 완료: {num_detections}개 객체 탐지")
                        
                        # ISM 응답 로그 저장 (상위 디렉토리에)
                        if save_outputs and parent_output_path is not None and SAVE_SERVER_RESPONSES:
                            try:
                                ism_log_path = parent_output_path / "ism_server_response.json"
                                with open(ism_log_path, "w", encoding="utf-8") as f:
                                    json.dump(result, f, indent=2, ensure_ascii=False)
                                print(f"[INFO] ISM response saved to: {ism_log_path}")
                            except Exception as log_err:
                                print(f"[WARN] Failed to save ISM response log: {log_err}")
                        elif save_outputs and parent_output_path is not None:
                            print("[INFO] Skipping ISM response persistence (MAIN_SERVER_SAVE_SERVER_RESPONSES != true)")
                        return result
                    else:
                        error_text = response.text[:500] if len(response.text) > 500 else response.text
                        error_msg = f"HTTP {response.status_code}: {error_text}"
                        print(f"[ERROR] ISM 서버 오류: {error_msg}")
                        return {"success": False, "error": error_msg}
            except asyncio.CancelledError:
                monitor_task.cancel()
                raise
            except httpx.TimeoutException as e:
                elapsed = time.time() - start_time
                monitor_task.cancel()
                error_msg = f"ISM Server timeout after {elapsed:.2f}초: {str(e)}"
                print(f"[ERROR] {error_msg}")
                return {"success": False, "error": error_msg}
            except httpx.ConnectError as e:
                elapsed = time.time() - start_time
                monitor_task.cancel()
                error_msg = f"ISM Server connection error after {elapsed:.2f}초: {str(e)}"
                print(f"[ERROR] {error_msg}")
                return {"success": False, "error": error_msg}
            except httpx.HTTPStatusError as e:
                elapsed = time.time() - start_time
                monitor_task.cancel()
                error_msg = f"ISM Server HTTP error after {elapsed:.2f}초: HTTP {e.response.status_code} - {e.response.text[:200]}"
                print(f"[ERROR] {error_msg}")
                return {"success": False, "error": error_msg}
            except Exception as e:
                elapsed = time.time() - start_time
                monitor_task.cancel()
                error_msg = f"ISM Server unexpected error after {elapsed:.2f}초: {str(e)}"
                print(f"[ERROR] {error_msg}")
                import traceback
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"ISM Server request failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "error": error_msg}
    
    async def _call_pem_server(
        self,
        rgb_image: str,
        depth_image: str,
        cam_params: Dict[str, Any],
        cad_path: str,
        template_dir: str,
        ism_result: Dict[str, Any],
        output_dir: Optional[str],
        parent_output_dir: Optional[str] = None,
        frame_guess: bool = False,
        save_outputs: bool = True,
        image_shape: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """PEM 서버 호출"""
        cad_obj = Path(cad_path)
        template_obj = Path(template_dir)
        parent_output_path = Path(parent_output_dir) if (save_outputs and parent_output_dir) else None
        output_container = None
        if save_outputs and output_dir:
            output_obj = Path(output_dir)
            output_obj.mkdir(parents=True, exist_ok=True)
            output_container = self._to_container_path(output_obj)
            if parent_output_path is None:
                parent_output_path = output_obj.parent

        # 컨테이너 경로로 변환
        cad_container = self._to_container_path(cad_obj)
        template_container = self._to_container_path(template_obj)
        
        # 이미지와 카메라 파라미터는 이미 전달받음
        
        # ISM 결과 로드
        seg_data = self._extract_seg_data(ism_result, top_k=10, image_shape=image_shape)
        
        if not seg_data:
            return {"success": False, "error": "Failed to extract seg_data from ISM result"}
        
        # PEM 요청 데이터
        pem_request = {
            "rgb_image": rgb_image,
            "depth_image": depth_image,
            "cam_params": cam_params,
            "cad_path": cad_container,
            "seg_data": seg_data,
            "template_dir": template_container,
            "det_score_thresh": 0.2,
        }
        if output_container:
            pem_request["output_dir"] = output_container

        # 카메라 프레임 유추 옵션 전달 (PEM 서버가 지원할 경우 적용)
        if frame_guess:
            pem_request["frame_guess"] = True
        
        # PEM 서버 호출
        url = "http://localhost:8003/api/v1/pose-estimation"
        timeout = 900.0
        start_time = time.time()
        
        print(f"[INFO] PEM 서버 호출 시작")
        print(f"  CAD: {cad_container}")
        print(f"  Template: {template_container}")
        print(f"  탐지된 객체 수: {len(seg_data)}")
        if output_container:
            print(f"  Output: {output_container}")
        
        # 서버 헬스 체크
        health_ok = await self._check_server_health("PEM", "http://localhost:8003/api/v1/health")
        if not health_ok:
            print(f"[WARN] PEM 서버 헬스 체크 실패했지만 요청을 계속 진행합니다...")
        
        try:
            # 진행 상황 모니터링 태스크 시작
            monitor_task = asyncio.create_task(
                self._monitor_request_progress("PEM", start_time, timeout)
            )
            
            try:
                # 비동기 HTTP 클라이언트 사용 (httpx)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    print(f"[INFO] PEM 서버에 요청 전송 중... (타임아웃: {timeout}초)")
                    response = await client.post(
                        url,
                        json=pem_request,
                    )
                    
                    elapsed = time.time() - start_time
                    monitor_task.cancel()  # 모니터링 태스크 종료
                    
                    print(f"[INFO] PEM 서버 응답 수신 완료 (소요 시간: {elapsed:.2f}초)")
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # 결과 요약 출력
                        if "poses" in result:
                            poses = result.get("poses", [])
                            if isinstance(poses, list):
                                print(f"[INFO] PEM 추론 완료: {len(poses)}개 포즈 추정")
                                if poses:
                                    scores = [p.get("score", 0) for p in poses if isinstance(p, dict)]
                                    if scores:
                                        print(f"[INFO] 포즈 점수 범위: {min(scores):.4f} ~ {max(scores):.4f}")
                        
                        # PEM 응답 로그 저장 (상위 디렉토리에)
                        if save_outputs and parent_output_path is not None and SAVE_SERVER_RESPONSES:
                            try:
                                pem_log_path = parent_output_path / "pem_server_response.json"
                                with open(pem_log_path, "w", encoding="utf-8") as f:
                                    json.dump(result, f, indent=2, ensure_ascii=False)
                                print(f"[INFO] PEM response saved to: {pem_log_path}")
                            except Exception as log_err:
                                print(f"[WARN] Failed to save PEM response log: {log_err}")
                        elif save_outputs and parent_output_path is not None:
                            print("[INFO] Skipping PEM response persistence (MAIN_SERVER_SAVE_SERVER_RESPONSES != true)")
                        return result
                    else:
                        error_text = response.text[:500] if len(response.text) > 500 else response.text
                        error_msg = f"HTTP {response.status_code}: {error_text}"
                        print(f"[ERROR] PEM 서버 오류: {error_msg}")
                        return {"success": False, "error": error_msg}
            except asyncio.CancelledError:
                monitor_task.cancel()
                raise
            except httpx.TimeoutException as e:
                elapsed = time.time() - start_time
                monitor_task.cancel()
                error_msg = f"PEM Server timeout after {elapsed:.2f}초: {str(e)}"
                print(f"[ERROR] {error_msg}")
                return {"success": False, "error": error_msg}
            except httpx.ConnectError as e:
                elapsed = time.time() - start_time
                monitor_task.cancel()
                error_msg = f"PEM Server connection error after {elapsed:.2f}초: {str(e)}"
                print(f"[ERROR] {error_msg}")
                return {"success": False, "error": error_msg}
            except httpx.HTTPStatusError as e:
                elapsed = time.time() - start_time
                monitor_task.cancel()
                error_msg = f"PEM Server HTTP error after {elapsed:.2f}초: HTTP {e.response.status_code} - {e.response.text[:200]}"
                print(f"[ERROR] {error_msg}")
                return {"success": False, "error": error_msg}
            except Exception as e:
                elapsed = time.time() - start_time
                monitor_task.cancel()
                error_msg = f"PEM Server unexpected error after {elapsed:.2f}초: {str(e)}"
                print(f"[ERROR] {error_msg}")
                import traceback
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"PEM Server request failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "error": error_msg}
    
    def _encode_image_base64(self, image_path: Path) -> str:
        """이미지를 base64로 인코딩"""
        try:
            # 파일 존재 확인
            if not image_path.exists():
                raise Exception(f"Image file does not exist: {image_path}")
            
            with open(image_path, "rb") as f:
                image_data = f.read()
                
            # 빈 파일 체크
            if len(image_data) == 0:
                raise Exception(f"Image file is empty: {image_path}")
                
            encoded = base64.b64encode(image_data).decode("utf-8")
            return encoded
        except Exception as e:
            raise Exception(f"Failed to encode image {image_path}: {str(e)}")
    
    def _encode_depth_image_to_base64(self, depth_path: Path) -> tuple:
        """깊이 이미지를 base64로 인코딩"""
        try:
            with Image.open(depth_path) as depth_image:
                depth_array = np.array(depth_image).astype(np.float32)
                depth_bytes = depth_array.tobytes()
                encoded = base64.b64encode(depth_bytes).decode('utf-8')
                return encoded, depth_array.shape
        except Exception as e:
            raise Exception(f"Failed to encode depth image {depth_path}: {str(e)}")

    def _rss_build_base(self, host: Optional[str], port: Optional[int], base: Optional[str]) -> str:
        if base:
            return base.rstrip('/')
        host = host or '192.168.0.197'
        port = port or 51000
        return f"http://{host}:{port}"

    def _rss_fetch_binary(self, url: str) -> bytes:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.content

    def _rss_fetch_json(self, url: str) -> Dict[str, Any]:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return json.loads(r.text)

    def _rss_extract_K(self, js: Dict[str, Any]) -> Optional[np.ndarray]:
        def try_make_mat(val) -> Optional[np.ndarray]:
            try:
                if isinstance(val, dict) and 'data' in val:
                    arr = np.array(val['data'], dtype=float).reshape(3, 3)
                    return arr
                arr = np.array(val, dtype=float)
                if arr.size == 9:
                    return arr.reshape(3, 3)
            except Exception:
                return None
            return None

        for key in ['K', 'CamK', 'camK', 'cam_K', 'camera_matrix', 'intrinsic_matrix', 'color_camera_matrix', 'depth_camera_matrix']:
            if key in js:
                mat = try_make_mat(js[key])
                if mat is not None:
                    return mat

        for key in ['depth_intrinsics', 'depth', 'color_intrinsics', 'color', 'rgb', 'camera', 'intrinsics', 'left', 'right']:
            if key in js and isinstance(js[key], dict):
                sub = js[key]
                fx = sub.get('fx'); fy = sub.get('fy')
                cx = sub.get('cx', sub.get('ppx'))
                cy = sub.get('cy', sub.get('ppy'))
                if all(v is not None for v in [fx, fy, cx, cy]):
                    return np.array([[float(fx), 0.0, float(cx)], [0.0, float(fy), float(cy)], [0.0, 0.0, 1.0]])
                m = self._rss_extract_K(sub)
                if m is not None:
                    return m

        intr = js.get('intrinsics') or js
        fx = intr.get('fx'); fy = intr.get('fy')
        cx = intr.get('cx', intr.get('ppx'))
        cy = intr.get('cy', intr.get('ppy'))
        if all(v is not None for v in [fx, fy, cx, cy]):
            return np.array([[float(fx), 0.0, float(cx)], [0.0, float(fy), float(cy)], [0.0, 0.0, 1.0]])
        return None

    def _rss_extract_depth_scale(self, js: Dict[str, Any]) -> Optional[float]:
        for k in ['depth_scale', 'depthScale', 'depth_unit', 'depthUnit', 'depth_scale_mm']:
            if k in js:
                val = js[k]
                try:
                    return float(val)
                except Exception:
                    if isinstance(val, str):
                        low = val.lower()
                        if low in ['mm', 'millimeter', 'millimetre']:
                            return 1.0
                        if low in ['m', 'meter', 'metre']:
                            return 1000.0
        return None

    def _rss_extract_extrinsics(self, js: Dict[str, Any]) -> Optional[np.ndarray]:
        """depth->color extrinsics 4x4 행렬 추출"""
        def from_rt(rot, trans) -> Optional[np.ndarray]:
            try:
                R = np.array(rot, dtype=float)
                if R.size == 9:
                    R = R.reshape(3, 3)
                t = np.array(trans, dtype=float).reshape(3)
                T = np.eye(4, dtype=float)
                T[:3, :3] = R
                T[:3, 3] = t
                return T
            except Exception:
                return None

        for k in ['T_depth_to_color', 'T_dc', 'extrinsic_depth_to_color', 'depth_to_color']:
            if k in js:
                node = js[k]
                if isinstance(node, dict):
                    R = node.get('R') or node.get('rotation') or node.get('rot')
                    t = node.get('t') or node.get('translation')
                    T = from_rt(R, t)
                    if T is not None:
                        return T
                    if 'matrix' in node:
                        try:
                            M = np.array(node['matrix'], dtype=float)
                            if M.size == 16:
                                return M.reshape(4, 4)
                        except Exception:
                            pass
                else:
                    try:
                        M = np.array(node, dtype=float)
                        if M.size == 16:
                            return M.reshape(4, 4)
                    except Exception:
                        pass

        for k in ['extrinsics', 'calibration', 'transforms']:
            if k in js and isinstance(js[k], dict):
                sub = js[k]
                for kk in ['depth_to_color', 'DepthToColor', 'depth2color', 'T_depth_to_color']:
                    if kk in sub:
                        node = sub[kk]
                        if isinstance(node, dict):
                            R = node.get('R') or node.get('rotation') or node.get('rot')
                            t = node.get('t') or node.get('translation')
                            T = from_rt(R, t)
                            if T is not None:
                                return T
                            if 'matrix' in node:
                                try:
                                    M = np.array(node['matrix'], dtype=float)
                                    if M.size == 16:
                                        return M.reshape(4, 4)
                                except Exception:
                                    pass
        return None

    async def execute_full_pipeline_from_rss(
        self,
        class_name: str,
        object_name: str,
        base: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        align_color: bool = False,
        output_dir: Optional[str] = None,
        frame_guess: bool = False,
        request_tag: Optional[str] = None,
        output_mode: str = "full",
    ) -> Dict[str, Any]:
        """RSS 서버에서 직접 데이터 수집 후 전체 파이프라인 실행"""
        start_ts = datetime.now()
        print(f"[RSS] >>> begin execute_from_rss at {start_ts.isoformat()} class={class_name} obj={object_name}")
        base_url = self._rss_build_base(host, port, base)
        print(f"[RSS] base_url={base_url} align_color={align_color} frame_guess={frame_guess}")

        # 캘리브/상태 수집
        print("[RSS] fetch calibration/status ...")
        calib = self._rss_fetch_json(f"{base_url}/camera/calibration")
        status = self._rss_fetch_json(f"{base_url}/camera/status")
        print("[RSS] calibration/status fetched")

        depth_scale = self._rss_extract_depth_scale(calib) or self._rss_extract_depth_scale(status) or 1.0
        camK_depth = self._rss_extract_K(calib)
        if camK_depth is None:
            camK_depth = self._rss_extract_K(status)
        camK_color = None
        if isinstance(calib.get('color_intrinsics'), dict):
            ci = calib['color_intrinsics']
            fx, fy = ci.get('fx'), ci.get('fy')
            cx = ci.get('cx', ci.get('ppx'))
            cy = ci.get('cy', ci.get('ppy'))
            if all(v is not None for v in [fx, fy, cx, cy]):
                camK_color = np.array([[float(fx), 0.0, float(cx)], [0.0, float(fy), float(cy)], [0.0, 0.0, 1.0]])
        print(f"[RSS] depth_scale={depth_scale} camK_depth={'ok' if camK_depth is not None else 'none'} camK_color={'ok' if camK_color is not None else 'none'}")
        T_d2c = self._rss_extract_extrinsics(calib) or self._rss_extract_extrinsics(status)
        print(f"[RSS] extrinsics(depth->color)={'ok' if T_d2c is not None else 'none'}")

        camK = camK_color if (align_color and camK_color is not None) else camK_depth
        if camK is None:
            raise Exception('Failed to infer camera intrinsics from RSS calibration/status')

        cam_params = {
            'cam_K': [float(camK[0,0]), 0.0, float(camK[0,2]), 0.0, float(camK[1,1]), float(camK[1,2]), 0.0, 0.0, 1.0],
            'depth_scale': float(depth_scale)
        }
        print("[RSS] cam_params prepared")

        # 컬러/뎁스 수집 (raw 기반 → PNG 바이트로 변환)
        print("[RSS] fetch color_jpeg ...")
        color_jpg_start = time.time()
        color_jpg = self._rss_fetch_binary(f"{base_url}/streams/color_jpeg")
        print(f"[RSS] color_jpeg fetched ({time.time() - color_jpg_start:.2f}초)")
        
        with Image.open(io.BytesIO(color_jpg)) as im:
            W, H = im.size
        print(f"[RSS] color size W={W} H={H}")

        print("[RSS] fetch color_raw ...")
        color_raw_start = time.time()
        color_raw = self._rss_fetch_binary(f"{base_url}/streams/color_raw")
        print(f"[RSS] color_raw fetched ({time.time() - color_raw_start:.2f}초)")
        
        expected = W * H * 3
        if len(color_raw) < expected:
            raise Exception(f"color_raw size {len(color_raw)} < expected {expected}")
        arr = np.frombuffer(color_raw[:expected], dtype=np.uint8).reshape((H, W, 3))
        arr_rgb = arr[..., ::-1]
        rgb_png_bytes = io.BytesIO()
        Image.fromarray(arr_rgb).save(rgb_png_bytes, format='PNG')
        rgb_b64 = base64.b64encode(rgb_png_bytes.getvalue()).decode('utf-8')
        print("[RSS] color prepared")

        print("[RSS] fetch depth_raw ...")
        depth_raw_start = time.time()
        depth_raw = self._rss_fetch_binary(f"{base_url}/streams/depth_raw")
        print(f"[RSS] depth_raw fetched ({time.time() - depth_raw_start:.2f}초)")
        
        expected_d = W * H * 2
        if len(depth_raw) < expected_d:
            raise Exception(f"depth_raw size {len(depth_raw)} < expected {expected_d}")
        depth = np.frombuffer(depth_raw[:expected_d], dtype=np.uint16).reshape((H, W))
        print("[RSS] depth prepared (raw)")

        # align depth to color if requested and extrinsics available
        if align_color and (T_d2c is not None) and (camK_color is not None) and (camK_depth is not None):
            z_m = depth.astype(np.float32) / 1000.0
            fx_d, fy_d, cx_d, cy_d = float(camK_depth[0,0]), float(camK_depth[1,1]), float(camK_depth[0,2]), float(camK_depth[1,2])
            fx_c, fy_c, cx_c, cy_c = float(camK_color[0,0]), float(camK_color[1,1]), float(camK_color[0,2]), float(camK_color[1,2])

            us = np.arange(W, dtype=np.float32)
            vs = np.arange(H, dtype=np.float32)
            uu, vv = np.meshgrid(us, vs)
            Z = z_m
            valid = Z > 0
            Xd = (uu - cx_d) / fx_d * Z
            Yd = (vv - cy_d) / fy_d * Z

            R = T_d2c[:3, :3]
            t = T_d2c[:3, 3]
            Xc = R[0,0]*Xd + R[0,1]*Yd + R[0,2]*Z + t[0]
            Yc = R[1,0]*Xd + R[1,1]*Yd + R[1,2]*Z + t[1]
            Zc = R[2,0]*Xd + R[2,1]*Yd + R[2,2]*Z + t[2]

            uc = fx_c * (Xc / (Zc + 1e-9)) + cx_c
            vc = fy_c * (Yc / (Zc + 1e-9)) + cy_c

            aligned = np.zeros((H, W), dtype=np.float32)
            uc_i = np.rint(uc).astype(np.int32)
            vc_i = np.rint(vc).astype(np.int32)
            m = valid & (Zc > 0) & (uc_i >= 0) & (uc_i < W) & (vc_i >= 0) & (vc_i < H)
            inds = np.where(m)
            flat_idx = vc_i[inds] * W + uc_i[inds]
            order = np.argsort(Zc[inds])
            flat_idx = flat_idx[order]
            z_vals = Zc[inds][order]
            seen = set()
            for i in range(len(flat_idx)):
                k = int(flat_idx[i])
                if k in seen:
                    continue
                seen.add(k)
                r = k // W
                c = k % W
                aligned[r, c] = z_vals[i]
            depth = np.clip(np.rint(aligned * 1000.0), 0, 65535).astype(np.uint16)

        depth_png_bytes = io.BytesIO()
        Image.fromarray(depth, mode='I;16').save(depth_png_bytes, format='PNG')
        depth_b64 = base64.b64encode(depth_png_bytes.getvalue()).decode('utf-8')

        mode = (output_mode or "full").lower()
        if mode not in {"full", "results_only", "none"}:
            mode = "full"

        label = self._normalize_tag(request_tag, "full-pipeline-from-rss")
        effective_output_dir = output_dir
        if mode != "none" and not effective_output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            effective_output_dir = str(self.paths["output"] / f"{timestamp}_{label}")

        # 기존 파이프라인 호출
        print("[PIPELINE] call execute_full_pipeline ...")
        result = await self.execute_full_pipeline(
            class_name=class_name,
            object_name=object_name,
            rgb_image=rgb_b64,
            depth_image=depth_b64,
            cam_params=cam_params,
            output_dir=effective_output_dir,
            frame_guess=frame_guess,
            request_tag=label,
            output_mode=mode,
        )
        end_ts = datetime.now()
        print(f"[RSS] <<< end execute_from_rss at {end_ts.isoformat()} duration={(end_ts-start_ts).total_seconds():.2f}s success={result.get('success', False)}")
        return result
    
    def _extract_seg_data(
        self,
        ism_data,
        top_k: int = 5,
        image_shape: Optional[Tuple[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """ISM 결과에서 seg_data 추출 (상위 N개만 선택)
        
        Args:
            ism_data: ISM 추론 결과
            top_k: 상위 몇 개를 선택할지 (기본값: 5)
            
        Returns:
            상위 top_k개의 seg_data
        """
        seg_data = []
        
        if isinstance(ism_data, list):
            for item in ism_data:
                seg_data.append({
                    "scene_id": 0,
                    "image_id": 0,
                    "category_id": item.get("category_id", 1),
                    "bbox": item.get("bbox", [0, 0, 0, 0]),
                    "score": item.get("score", 0.0),
                    "segmentation": item.get("segmentation", {"size": None, "counts": ""}),
                })
        elif isinstance(ism_data, dict) and "detections" in ism_data:
            det = ism_data["detections"]
            masks = det.get("masks", []) or []
            boxes = det.get("boxes", []) or []
            scores = det.get("scores", []) or []
            object_ids = det.get("object_ids", []) or []
            n = max(len(boxes), len(scores), len(object_ids), len(masks))
            
            for i in range(n):
                bbox = boxes[i] if i < len(boxes) else [0, 0, 0, 0]
                score = float(scores[i]) if i < len(scores) else 0.0
                cat_id = int(object_ids[i]) if i < len(object_ids) else 1
                seg = None
                if i < len(masks):
                    mask_item = masks[i]
                    if isinstance(mask_item, dict):
                        size = mask_item.get("size")
                        counts = mask_item.get("counts")
                        if size and counts:
                            seg = {
                                "size": size,
                                "counts": counts,
                            }
                        elif size and isinstance(counts, (bytes, str)):
                            seg = {
                                "size": size,
                                "counts": counts.decode("utf-8") if isinstance(counts, bytes) else counts,
                            }
                    elif isinstance(mask_item, list):
                        try:
                            mask_array = np.array(mask_item, dtype=np.uint8)
                            if mask_array.ndim == 2:
                                h, w = mask_array.shape
                                if mask_array.max() > 0:
                                    rle = mask_utils.encode(np.asfortranarray(mask_array))
                                    counts = rle.get("counts")
                                    if isinstance(counts, bytes):
                                        counts = counts.decode("utf-8")
                                    seg = {
                                        "size": [int(h), int(w)],
                                        "counts": counts,
                                    }
                        except Exception as mask_err:
                            print(f"[WARN] Failed to convert mask array to RLE: {mask_err}")
                if seg is None:
                    seg = self._create_bbox_segmentation(bbox, image_shape)
                if seg is None:
                    print(f"[WARN] Skipping detection due to missing segmentation data (bbox={bbox})")
                    continue
                seg_data.append({
                    "scene_id": 0,
                    "image_id": 0,
                    "category_id": cat_id,
                    "bbox": bbox,
                    "score": score,
                    "segmentation": seg,
                })
        
        # Score 기준으로 정렬 후 상위 N개만 선택
        seg_data_sorted = sorted(seg_data, key=lambda x: x["score"], reverse=True)
        top_seg_data = seg_data_sorted[:top_k]
        
        print(f"[INFO] ISM 결과: 총 {len(seg_data)}개 → 상위 {len(top_seg_data)}개만 PEM에 전달")
        for idx, item in enumerate(top_seg_data, 1):
            print(f"  {idx}. Score: {item['score']:.4f}, BBox: {item['bbox']}")
        
        return top_seg_data
    
    def _infer_image_shape(self, rgb_image_b64: str) -> Optional[Tuple[int, int]]:
        try:
            rgb_bytes = base64.b64decode(rgb_image_b64)
            rgb_array = np.frombuffer(rgb_bytes, dtype=np.uint8)
            img = cv2.imdecode(rgb_array, cv2.IMREAD_COLOR)
            if img is None:
                return None
            h, w = img.shape[:2]
            return int(h), int(w)
        except Exception as e:
            print(f"[WARN] Failed to infer image shape: {e}")
            return None

    def _create_bbox_segmentation(
        self,
        bbox: List[float],
        image_shape: Optional[Tuple[int, int]]
    ) -> Optional[Dict[str, Any]]:
        if image_shape is None or not bbox or len(bbox) < 4:
            return None
        try:
            h, w = image_shape
            x1, y1, x2, y2 = bbox
            x1 = int(np.floor(x1))
            y1 = int(np.floor(y1))
            x2 = int(np.ceil(x2))
            y2 = int(np.ceil(y2))
            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(x1 + 1, min(w, x2))
            y2 = max(y1 + 1, min(h, y2))
            mask = np.zeros((h, w), dtype=np.uint8)
            mask[y1:y2, x1:x2] = 1
            if mask.sum() == 0:
                return None
            rle = mask_utils.encode(np.asfortranarray(mask))
            counts = rle.get("counts")
            if isinstance(counts, bytes):
                counts = counts.decode("utf-8")
            return {
                "size": [int(h), int(w)],
                "counts": counts,
            }
        except Exception as e:
            print(f"[WARN] Failed to build fallback segmentation from bbox {bbox}: {e}")
            return None

    def _save_input_data(self, output_path: Path, rgb_image: str, depth_image: str, cam_params: Dict[str, Any]):
        """입력 데이터(RGB, Depth, 카메라 파라미터)를 output 디렉토리에 저장"""
        try:
            if SAVE_INPUT_IMAGES:
                # RGB 이미지 저장
                rgb_bytes = base64.b64decode(rgb_image)
                rgb_array = np.frombuffer(rgb_bytes, dtype=np.uint8)
                rgb_cv = cv2.imdecode(rgb_array, cv2.IMREAD_COLOR)
                if rgb_cv is not None:
                    cv2.imwrite(str(output_path / "input_rgb.png"), rgb_cv)
                    print(f"[INFO] RGB image saved: {output_path / 'input_rgb.png'}")
                
                # Depth 이미지 저장
                depth_bytes = base64.b64decode(depth_image)
                depth_array = np.frombuffer(depth_bytes, dtype=np.uint8)
                # 전달 포맷이 PNG이므로 이미지 디코드 사용 (16-bit 보존)
                depth_cv = cv2.imdecode(depth_array, cv2.IMREAD_UNCHANGED)
                if depth_cv is not None:
                    # 16-bit PNG로 저장
                    cv2.imwrite(str(output_path / "input_depth.png"), depth_cv)
                    print(f"[INFO] Depth image saved: {output_path / 'input_depth.png'}")
                else:
                    # 디코드 실패 시 원본 PNG 바이트를 그대로 기록 (fallback)
                    raw_path = output_path / "input_depth.png"
                    with open(raw_path, "wb") as f:
                        f.write(depth_bytes)
                    print(f"[WARN] Depth decode failed; wrote raw PNG bytes to: {raw_path}")
            else:
                print("[INFO] Skipping input image persistence (MAIN_SERVER_SAVE_INPUT_IMAGES != true)")
            
            if SAVE_CAMERA_PARAMS:
                # 카메라 파라미터 저장
                with open(output_path / "camera_params.json", "w", encoding="utf-8") as f:
                    json.dump(cam_params, f, indent=2, ensure_ascii=False)
                    print(f"[INFO] Camera parameters saved: {output_path / 'camera_params.json'}")
        except Exception as e:
            print(f"[WARN] Failed to save input data: {e}")
    
    def _create_metadata(
        self,
        class_name: str,
        object_name: str,
        cad_path: str,
        template_dir: str,
        template_existed: bool,
        cam_params: Dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        results: Dict[str, Any],
        success: bool,
        error: Optional[str] = None,
        request_tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """파이프라인 실행 메타데이터 생성"""
        duration = (end_time - start_time).total_seconds()
        
        metadata = {
            "pipeline_info": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": round(duration, 3),
                "success": success,
                "error": error
            },
            "request_info": {
                "class_name": class_name,
                "object_name": object_name,
                "cad_path": cad_path,
                "template_dir": template_dir,
                "template_existed": template_existed,
                "request_tag": request_tag
            },
            "camera_info": {
                "width": cam_params.get("width") or cam_params.get("depth_image_width"),
                "height": cam_params.get("height") or cam_params.get("depth_image_height"),
                "fx": cam_params.get("fx"),
                "fy": cam_params.get("fy"),
                "cx": cam_params.get("cx"),
                "cy": cam_params.get("cy"),
                "intrinsic": cam_params.get("intrinsic") or cam_params.get("cam_K"),
                "depth_scale": cam_params.get("depth_scale")
            },
            "pipeline_steps": {}
        }
        
        # 각 단계별 정보 추가
        if "render" in results:
            render_info = results["render"]
            metadata["pipeline_steps"]["render"] = {
                "skipped": render_info.get("skipped", False),
                "success": render_info.get("success", False) if not render_info.get("skipped") else True
            }
        
        if "ism" in results:
            ism_info = results["ism"]
            # 실제 감지 개수 계산 (ISM 응답 형식에 따라)
            num_detections = ism_info.get("num_detections", 0)
            print(f"[DEBUG] ISM metadata - num_detections from key: {num_detections}")
            print(f"[DEBUG] ISM metadata - has detections key: {'detections' in ism_info}")
            
            if num_detections == 0 and "detections" in ism_info:
                det = ism_info["detections"]
                print(f"[DEBUG] ISM metadata - detections type: {type(det)}")
                if isinstance(det, dict):
                    # masks, boxes, scores 등 중 가장 긴 것으로 계산
                    masks = det.get("masks", [])
                    boxes = det.get("boxes", [])
                    scores = det.get("scores", [])
                    num_detections = max(len(masks), len(boxes), len(scores))
                    print(f"[DEBUG] ISM metadata - calculated num_detections: {num_detections} (masks={len(masks)}, boxes={len(boxes)}, scores={len(scores)})")
                elif isinstance(det, list):
                    num_detections = len(det)
                    print(f"[DEBUG] ISM metadata - calculated num_detections (list): {num_detections}")
            
            metadata["pipeline_steps"]["ism"] = {
                "success": ism_info.get("success", False),
                "num_detections": num_detections,
                "inference_time": ism_info.get("inference_time", 0)
            }
            print(f"[DEBUG] ISM metadata - final num_detections: {num_detections}")
        
        if "pem" in results:
            pem_info = results["pem"]
            metadata["pipeline_steps"]["pem"] = {
                "success": pem_info.get("success", False),
                "num_detections": pem_info.get("num_detections", 0),
                "inference_time": pem_info.get("inference_time", 0)
            }
        
        return metadata
    
    def _extract_pose_summary(self, pem_result: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not isinstance(pem_result, dict):
            return []

        scores = pem_result.get("pose_scores") or []
        rotations = pem_result.get("pred_rot") or []
        translations = pem_result.get("pred_trans") or []

        summary: List[Dict[str, Any]] = []
        for idx, score in enumerate(scores):
            rot = rotations[idx] if idx < len(rotations) else None
            trans = translations[idx] if idx < len(translations) else None
            if rot is None or trans is None:
                continue
            summary.append({
                "index": idx,
                "score": float(score),
                "rotation": rot,
                "translation": trans,
            })
        return summary
    
    def _save_metadata(self, output_path: Path, metadata: Dict[str, Any]):
        """메타데이터를 JSON 파일로 저장"""
        try:
            metadata_file = output_path / "pipeline_metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Pipeline metadata saved to {metadata_file}")
        except Exception as e:
            print(f"[WARN] Failed to save metadata: {e}")

    def _save_pose_summary(self, output_path: Path, success: bool, poses: List[Dict[str, Any]], error: Optional[str]):
        try:
            summary_path = output_path / "pose_results.json"
            payload = {
                "success": success,
                "num_poses": len(poses),
                "pose_results": poses,
            }
            if error:
                payload["error"] = error
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Pose summary saved to {summary_path}")
        except Exception as e:
            print(f"[WARN] Failed to save pose summary: {e}")


# 전역 워크플로우 서비스 인스턴스
_workflow_service = None

def get_workflow_service() -> WorkflowService:
    """워크플로우 서비스 인스턴스 반환 (싱글톤)"""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowService()
    return _workflow_service


