#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub 同步工具
将本地 skills 和 agfiles 同步到 GitHub 仓库
"""
import os
import sys
import base64
import requests
import json
from datetime import datetime

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置 - 必须从环境变量读取
TOKEN = os.environ.get('XTC_GITHUB_TOKEN', '')
if not TOKEN:
    raise ValueError('请设置环境变量 XTC_GITHUB_TOKEN')
REPO_OWNER = 'leolu66'
REPO_NAME = '61sClaw'
BASE_PATH = r'C:\Users\luzhe\.openclaw\workspace-main'

# 要同步的目录
SYNC_DIRS = ['skills', 'agfiles']

# 要忽略的文件/目录
IGNORE_PATTERNS = [
    '__pycache__', '.git', '.pyc', 
    'passwords.json.encrypted', 'master.key',
    'MEMORY.md', 'TOOLS.md', 'USER.md', 'IDENTITY.md'
]

API_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}'


def get_headers():
    return {
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }


def should_ignore(filepath):
    """检查是否应该忽略该文件"""
    for pattern in IGNORE_PATTERNS:
        if pattern in filepath:
            return True
    return False


def get_local_files(base_dir):
    """获取本地所有要同步的文件"""
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        # 跳过忽略的目录
        dirs[:] = [d for d in dirs if not should_ignore(d)]
        
        for filename in filenames:
            if should_ignore(filename):
                continue
            
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, base_dir)
            # 修复 Windows 路径分隔符 -> GitHub 用 /
            rel_path = rel_path.replace('\\', '/')
            files.append({
                'path': rel_path,
                'full_path': full_path
            })
    return files


def get_remote_files():
    """获取远程仓库当前文件"""
    r = requests.get(f'{API_URL}/contents', headers=get_headers())
    if r.status_code != 200:
        print(f'获取远程文件失败: {r.status_code}')
        return {}
    
    files = {}
    for item in r.json():
        if item['type'] == 'file':
            files[item['name']] = item['sha']
    return files


def upload_file(filepath, content, message='Update via GitHub API'):
    """上传文件到 GitHub"""
    url = f'{API_URL}/contents/{filepath}'
    data = {
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode('utf-8')
    }
    
    # 检查文件是否已存在
    r = requests.get(url, headers=get_headers())
    if r.status_code == 200:
        data['sha'] = r.json()['sha']
    
    r = requests.put(url, headers=get_headers(), json=data)
    return r.status_code in [200, 201]


def sync_to_github():
    """同步到 GitHub"""
    if not TOKEN:
        print('❌ 请设置环境变量 XTC_GITHUB_TOKEN')
        return False
    
    print(f'🔄 开始同步到 GitHub...')
    print(f'📁 仓库: {REPO_OWNER}/{REPO_NAME}')
    
    # 获取本地文件
    all_files = []
    for sync_dir in SYNC_DIRS:
        dir_path = os.path.join(BASE_PATH, sync_dir)
        if os.path.exists(dir_path):
            files = get_local_files(dir_path)
            for f in files:
                f['path'] = f"{sync_dir}/{f['path']}"
            all_files.extend(files)
            print(f'  📂 {sync_dir}: {len(files)} 个文件')
    
    print(f'  共 {len(all_files)} 个文件待同步')
    
    # 同步每个文件
    success = 0
    failed = 0
    
    for f in all_files:
        try:
            with open(f['full_path'], 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
            
            if upload_file(f['path'], content):
                success += 1
                print(f'  ✅ {f["path"]}')
            else:
                failed += 1
                print(f'  ❌ {f["path"]}')
        except Exception as e:
            failed += 1
            print(f'  ❌ {f["path"]}: {e}')
    
    print(f'\n✨ 同步完成! 成功: {success}, 失败: {failed}')
    return failed == 0


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        # 只检查不上传
        for sync_dir in SYNC_DIRS:
            dir_path = os.path.join(BASE_PATH, sync_dir)
            if os.path.exists(dir_path):
                files = get_local_files(dir_path)
                print(f'📂 {sync_dir}: {len(files)} 个文件')
    else:
        sync_to_github()
