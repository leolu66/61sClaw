#!/usr/bin/env python3
"""
日志清理脚本
功能：先归档日志，然后删除超过指定天数的日志文件
"""
import os
import json
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

# 配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
WORKSPACE_ROOT = r"C:\Users\luzhe\.openclaw\workspace-main"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_file_age_days(file_path):
    """获取文件年龄（天数）"""
    mtime = os.path.getmtime(file_path)
    file_date = datetime.fromtimestamp(mtime)
    age = datetime.now() - file_date
    return age.days

def archive_logs():
    """归档日志"""
    config = load_config()
    archive_config = config.get("log_archive", {})
    
    source_dir = os.path.join(WORKSPACE_ROOT, archive_config.get("source_dir", "logs"))
    archive_base = archive_config.get("archive_base", r"D:\openclaw\archive")
    create_date_subdir = archive_config.get("create_date_subdir", True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    archive_dir = os.path.join(archive_base, today) if create_date_subdir else archive_base
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    
    # 创建子目录
    subdirs = ["daily", "tasks", "errors", "summary", "stats"]
    for subdir in subdirs:
        os.makedirs(os.path.join(archive_dir, subdir), exist_ok=True)
    
    files_archived = 0
    total_size = 0
    
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, source_dir)
            dst_path = os.path.join(archive_dir, rel_path)
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            # 复制文件
            shutil.copy2(src_path, dst_path)
            size = os.path.getsize(src_path)
            total_size += size
            files_archived += 1
            print(f"  [OK] {rel_path}")
    
    return files_archived, total_size, archive_dir

def cleanup_old_logs(days_to_keep=3, dry_run=False):
    """清理超过天数的日志文件"""
    config = load_config()
    cleanup_config = config.get("log_cleanup", {})
    
    source_dir = os.path.join(WORKSPACE_ROOT, cleanup_config.get("source_dir", "logs"))
    days = cleanup_config.get("days_to_keep", days_to_keep)
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    files_deleted = 0
    total_size = 0
    
    print(f"\n------------------------------------------------------------")
    print(f"[INFO] 清理 {days} 天前的日志文件...")
    print(f"[INFO] 截止日期: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"------------------------------------------------------------")
    
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, source_dir)
            
            # 检查文件年龄
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            age_days = (datetime.now() - mtime).days
            
            if age_days > days:
                size = os.path.getsize(file_path)
                if dry_run:
                    print(f"  [DRY-RUN] 将删除: {rel_path} (年龄: {age_days} 天)")
                else:
                    os.remove(file_path)
                    print(f"  [DEL] {rel_path} (年龄: {age_days} 天)")
                total_size += size
                files_deleted += 1
    
    return files_deleted, total_size

def main():
    print("=" * 60)
    print("清理日志")
    print("=" * 60)
    print(f"工作区: {WORKSPACE_ROOT}")
    print(f"------------------------------------------------------------")
    
    # 步骤1: 归档日志
    print("\n[STEP 1] 归档日志...")
    archive_count, archive_size, archive_dir = archive_logs()
    
    print(f"\n[OK] 归档完成！")
    print(f"  归档文件: {archive_count}")
    print(f"  总大小: {archive_size / 1024:.1f} KB")
    print(f"  归档目录: {archive_dir}")
    
    # 步骤2: 清理旧日志
    print("\n[STEP 2] 清理旧日志...")
    delete_count, delete_size = cleanup_old_logs(days_to_keep=3, dry_run=False)
    
    print(f"\n------------------------------------------------------------")
    print(f"[OK] 清理完成！")
    print(f"  删除文件: {delete_count}")
    print(f"  释放空间: {delete_size / 1024:.1f} KB")
    print(f"============================================================")

if __name__ == "__main__":
    main()
