#!/usr/bin/env python3
"""
YCB 객체를 원본 백업에서 복원하고 다시 mm 단위로 변환
"""
from pathlib import Path
import shutil
from tqdm import tqdm

ycb_dir = Path("static/meshes/ycb")
backup_patterns = ["*_backup.obj", "*_mm_backup.obj"]

def find_backup_files():
    """백업 파일 찾기"""
    backups = {}
    for pattern in backup_patterns:
        for backup_file in ycb_dir.glob(pattern):
            # 원본 이름 추출
            if "_backup" in backup_file.name:
                original_name = backup_file.name.replace("_backup", "").replace("_mm_backup", "")
            else:
                continue
            
            backups[original_name] = backup_file
    return backups

def restore_and_convert():
    """백업 파일 복원 및 mm 변환"""
    # 1. 현재 YCB 파일들 확인
    current_files = list(ycb_dir.glob("*.obj"))
    current_objs = [f for f in current_files if "backup" not in f.name]
    print(f"[INFO] 현재 YCB 객체 파일: {len(current_objs)}개")
    
    # 2. 백업 파일 찾기
    backups = find_backup_files()
    print(f"[INFO] 찾은 백업 파일: {len(backups)}개")
    
    if len(backups) == 0:
        print("[ERROR] 백업 파일을 찾을 수 없습니다!")
        print("[INFO] 대신 현재 파일들을 m 단위로 변환합니다...")
        
        # 현재 파일들이 mm 단위라고 가정하고 1000으로 나눔
        from convert_ycb_to_mm_safe import parse_obj_file, write_obj_file
        import numpy as np
        
        for obj_file in tqdm(current_objs, desc="m 단위로 변환"):
            data = parse_obj_file(obj_file)
            vertices = data['vertices']
            
            # 이미 mm 단위인지 확인
            if vertices.max() > 100:
                # mm -> m 변환 (1000으로 나눔)
                vertices_scaled = vertices / 1000.0
                write_obj_file(obj_file, data, vertices_scaled)
                print(f"  [OK] {obj_file.name}: mm -> m 변환 완료")
        
        # 다시 m -> mm 변환
        print("\n[INFO] 이제 m -> mm 변환 시작...")
        from convert_ycb_to_mm_safe import convert_obj_to_mm
        
        for obj_file in tqdm(current_objs, desc="mm 단위로 변환"):
            try:
                convert_obj_to_mm(obj_file, create_backup=False)
            except Exception as e:
                print(f"  [ERROR] {obj_file.name}: {e}")
        
        return
    
    # 3. 현재 파일 삭제 (백업이 아닌 것만)
    print(f"\n[INFO] 현재 파일 삭제 중...")
    for obj_file in current_objs:
        obj_file.unlink()
        print(f"  [DEL] {obj_file.name}")
    
    # 4. 백업 파일 복원
    print(f"\n[INFO] 백업 파일 복원 중...")
    for original_name, backup_file in tqdm(backups.items(), desc="복원"):
        restored_path = ycb_dir / original_name
        shutil.copy2(backup_file, restored_path)
        print(f"  [OK] {original_name}")
    
    # 5. mm 단위로 변환
    print(f"\n[INFO] mm 단위로 변환 시작...")
    from convert_ycb_to_mm_safe import convert_obj_to_mm
    
    restored_files = list(ycb_dir.glob("*.obj"))
    restored_objs = [f for f in restored_files if "backup" not in f.name]
    
    for obj_file in tqdm(restored_objs, desc="mm 변환"):
        try:
            convert_obj_to_mm(obj_file, create_backup=False)
            print(f"  [OK] {obj_file.name}")
        except Exception as e:
            print(f"  [ERROR] {obj_file.name}: {e}")

if __name__ == "__main__":
    restore_and_convert()

