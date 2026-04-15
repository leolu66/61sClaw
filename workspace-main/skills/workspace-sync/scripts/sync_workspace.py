#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workspace Sync - 同步工作目录到NAS
"""
import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

# 解决Windows中文编码问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# 工作目录：从 skills/workspace-sync/scripts 向上两级到 workspace-main
LOCAL_WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def load_config():
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "target_name": "小天才",
        "target_dir": r"Z:\61sOpenClaw"
    }

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_sync_dirs():
    """获取需要同步的目录"""
    return [
        "skills",        # 技能
        "memory",       # 记忆
        "gobang-game",  # 五子棋游戏
        "music-player", # 音乐播放器
        "agfiles",      # AI 生成的文件
    ]

def get_openclaw_logs():
    """获取OpenClaw日志目录"""
    openclaw_root = os.path.dirname(LOCAL_WORKSPACE)  # C:\Users\luzhe\.openclaw
    logs_dir = os.path.join(openclaw_root, "logs")
    return logs_dir

def sync_directory(source, target):
    """同步单个目录"""
    if not os.path.exists(source):
        return 0, 0
    
    os.makedirs(target, exist_ok=True)
    
    copied = 0
    skipped = 0
    
    for root, dirs, files in os.walk(source):
        # 跳过不需要的目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        rel_path = os.path.relpath(root, source)
        target_root = os.path.join(target, rel_path) if rel_path != '.' else target
        
        for file in files:
            if file.startswith('.') or file.endswith('.pyc'):
                skipped += 1
                continue
            
            source_file = os.path.join(root, file)
            target_file = os.path.join(target_root, file)
            
            # 检查是否需要复制
            if not os.path.exists(target_file):
                os.makedirs(target_root, exist_ok=True)
                shutil.copy2(source_file, target_file)
                copied += 1
            else:
                # 比较修改时间
                source_mtime = os.path.getmtime(source_file)
                target_mtime = os.path.getmtime(target_file)
                if source_mtime > target_mtime:
                    shutil.copy2(source_file, target_file)
                    copied += 1
                else:
                    skipped += 1
    
    return copied, skipped

def sync_workspace():
    """同步整个工作空间"""
    config = load_config()
    target_name = config.get("target_name", "unknown")
    target_base = config.get("target_dir", r"Z:\61sOpenClaw")
    target_dir = os.path.join(target_base, target_name)
    
    print(f"🔄 开始同步到: {target_dir}")
    print(f"📱 设备: {target_name}")
    print("-" * 40)
    
    total_copied = 0
    total_skipped = 0
    
    for dir_name in get_sync_dirs():
        source = os.path.join(LOCAL_WORKSPACE, dir_name)
        target = os.path.join(target_dir, dir_name)
        
        if os.path.exists(source):
            copied, skipped = sync_directory(source, target)
            total_copied += copied
            total_skipped += skipped
            if copied > 0:
                print(f"  ✅ {dir_name}: {copied} 个文件已更新")
            else:
                print(f"  ⏭️ {dir_name}: 无变化")
        else:
            print(f"  ⚠️ {dir_name}: 目录不存在")
    
    # 同步根目录的重要文件
    root_files = ["MEMORY.md", "AGENTS.md", "SOUL.md", "TOOLS.md", "USER.md"]
    for file_name in root_files:
        source = os.path.join(LOCAL_WORKSPACE, file_name)
        target = os.path.join(target_dir, file_name)
        
        if os.path.exists(source):
            if not os.path.exists(target) or os.path.getmtime(source) > os.path.getmtime(target):
                shutil.copy2(source, target)
                total_copied += 1
                print(f"  ✅ {file_name}: 已更新")
    
    # 同步OpenClaw日志
    logs_source = get_openclaw_logs()
    logs_target = os.path.join(target_dir, "openclaw_logs")
    if os.path.exists(logs_source):
        copied, skipped = sync_directory(logs_source, logs_target)
        total_copied += copied
        total_skipped += skipped
        if copied > 0:
            print(f"  ✅ openclaw_logs: {copied} 个文件已更新")
        else:
            print(f"  ⏭️ openclaw_logs: 无变化")
    
    # 同步数据库文件（从 datas 目录）
    db_files = ["zhipu_balance.db"]
    for db_file in db_files:
        source = os.path.join(LOCAL_WORKSPACE, "datas", db_file)
        target = os.path.join(target_dir, "datas", db_file)
        
        if os.path.exists(source):
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if not os.path.exists(target) or os.path.getmtime(source) > os.path.getmtime(target):
                shutil.copy2(source, target)
                total_copied += 1
                print(f"  ✅ {db_file}: 已更新")
    
    print("-" * 40)
    print(f"✨ 同步完成! 共更新 {total_copied} 个文件，跳过 {total_skipped} 个文件")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return total_copied

if __name__ == "__main__":
    sync_workspace()
