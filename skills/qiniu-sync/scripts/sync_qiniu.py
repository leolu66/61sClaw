#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七牛云同步 - 将workspace同步到七牛云
"""
import os
import sys
import json
from datetime import datetime

# 解决Windows中文编码问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加七牛云SDK路径
QINIU_SDK_PATH = r"C:\Users\luzhe\AppData\Roaming\npm\node_modules\openclaw\skills\qiniu-cloud\scripts"
sys.path.insert(0, QINIU_SDK_PATH)

try:
    from qiniu_ops import upload_file, list_files
except ImportError:
    print("Error: Cannot import qiniu_ops. Please ensure qiniu-cloud skill is installed.")
    sys.exit(1)

# 配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
LOCAL_WORKSPACE = r"C:\Users\luzhe\.openclaw\workspace-main"

def load_config():
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "workspace_path": LOCAL_WORKSPACE
    }

def get_sync_mapping():
    """获取同步映射关系"""
    return {
        "skills": "skills/",
        "memory": "logs/",
        "data": "data/",
    }

def sync_directory(local_dir, remote_prefix, extensions=None):
    """同步目录到七牛云"""
    if not os.path.exists(local_dir):
        return 0, 0
    
    uploaded = 0
    skipped = 0
    
    for root, dirs, files in os.walk(local_dir):
        # 跳过不需要的目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        rel_path = os.path.relpath(root, local_dir)
        remote_dir = remote_prefix + "/" + rel_path.replace("\\", "/") if rel_path != '.' else remote_prefix
        
        for file in files:
            # 跳过隐藏文件和编译文件
            if file.startswith('.') or file.endswith('.pyc'):
                skipped += 1
                continue
            
            # 检查扩展名
            if extensions:
                ext = os.path.splitext(file)[1]
                if ext not in extensions:
                    skipped += 1
                    continue
            
            local_file = os.path.join(root, file)
            remote_key = (remote_dir + "/" + file) if not remote_dir.endswith("/") else (remote_dir + file)
            
            try:
                result = upload_file(local_file, remote_key)
                uploaded += 1
                print(f"  ✅ {remote_key}")
            except Exception as e:
                skipped += 1
                print(f"  ⏭️ {remote_key} (skip: {e})")
    
    return uploaded, skipped

def sync_file(local_file, remote_key):
    """同步单个文件到七牛云"""
    try:
        result = upload_file(local_file, remote_key)
        return True
    except Exception as e:
        print(f"  ❌ {local_file} -> {remote_key}: {e}")
        return False

def sync_to_qiniu():
    """同步整个工作空间到七牛云"""
    config = load_config()
    workspace = config.get("workspace_path", LOCAL_WORKSPACE)
    
    print(f"🔄 开始同步到七牛云: 61sopenclaw")
    print(f"📁 工作目录: {workspace}")
    print("-" * 50)
    
    total_uploaded = 0
    total_skipped = 0
    
    # 1. 同步 skills/ -> /skills/
    skills_dir = os.path.join(workspace, "skills")
    if os.path.exists(skills_dir):
        uploaded, skipped = sync_directory(skills_dir, "skills")
        total_uploaded += uploaded
        total_skipped += skipped
        print(f"  📦 skills: {uploaded} 上传, {skipped} 跳过")
    
    # 2. 同步 gobang-game/ -> /skills/gobang-game
    gobang_dir = os.path.join(workspace, "gobang-game")
    if os.path.exists(gobang_dir):
        uploaded, skipped = sync_directory(gobang_dir, "skills/gobang-game")
        total_uploaded += uploaded
        total_skipped += skipped
        print(f"  📦 gobang-game: {uploaded} 上传, {skipped} 跳过")
    
    # 3. 同步 music-player/ -> /skills/music-player
    music_dir = os.path.join(workspace, "music-player")
    if os.path.exists(music_dir):
        uploaded, skipped = sync_directory(music_dir, "skills/music-player")
        total_uploaded += uploaded
        total_skipped += skipped
        print(f"  📦 music-player: {uploaded} 上传, {skipped} 跳过")
    
    # 4. 同步 memory/ -> /logs/
    memory_dir = os.path.join(workspace, "memory")
    if os.path.exists(memory_dir):
        uploaded, skipped = sync_directory(memory_dir, "logs")
        total_uploaded += uploaded
        total_skipped += skipped
        print(f"  📝 memory: {uploaded} 上传, {skipped} 跳过")
    
    # 5. 同步 *.db -> /data/
    data_files = []
    for file in os.listdir(workspace):
        if file.endswith('.db'):
            data_files.append(file)
    
    for db_file in data_files:
        local_path = os.path.join(workspace, db_file)
        remote_key = f"data/{db_file}"
        if sync_file(local_path, remote_key):
            total_uploaded += 1
            print(f"  💾 {db_file} -> /data/{db_file}")
        else:
            total_skipped += 1
    
    # 6. 同步根目录配置文件 -> /
    root_files = ["MEMORY.md", "AGENTS.md", "TOOLS.md"]
    for file_name in root_files:
        local_path = os.path.join(workspace, file_name)
        if os.path.exists(local_path):
            if sync_file(local_path, file_name):
                total_uploaded += 1
                print(f"  📄 {file_name}")
    
    print("-" * 50)
    print(f"✨ 同步完成! 共上传 {total_uploaded} 个文件，跳过 {total_skipped} 个文件")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 访问地址: https://s3.61sopenclaw.z0.glb.clouddn.com/")
    
    return total_uploaded

if __name__ == "__main__":
    sync_to_qiniu()
