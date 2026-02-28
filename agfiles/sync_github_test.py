#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub Sync - Simplified version with better error handling
"""
import os
import sys
import base64
import requests

# Configuration
TOKEN = os.environ.get('XTC_GITHUB_TOKEN', '')
if not TOKEN:
    raise ValueError('Please set XTC_GITHUB_TOKEN environment variable')

REPO_OWNER = 'leolu66'
REPO_NAME = '61sClaw'
BASE_PATH = r'C:\Users\luzhe\.openclaw\workspace-main'
SYNC_DIRS = ['skills', 'agfiles']

# Ignore patterns
IGNORE_PATTERNS = ['__pycache__', '.git', '.pyc', '.pyo', '.exe', '.dll', '.so', 'logs']

# agfiles allowed extensions
AGFILES_ALLOWED = ['.py', '.ps1', '.bat']

API_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}'
HEADERS = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def should_ignore(filepath, parent_dir=''):
    for pattern in IGNORE_PATTERNS:
        if pattern in filepath:
            return True
    # Special handling for agfiles
    if parent_dir == 'agfiles':
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in AGFILES_ALLOWED:
            return True
    return False

def get_files(base_dir, parent_dir=''):
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not should_ignore(d, parent_dir)]
        for filename in filenames:
            if should_ignore(filename, parent_dir):
                continue
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, base_dir).replace('\\', '/')
            files.append({'path': rel_path, 'full_path': full_path})
    return files

def upload_file(filepath, content):
    url = f'{API_URL}/contents/{filepath}'
    # Handle binary content
    if isinstance(content, bytes):
        b64 = base64.b64encode(content).decode('utf-8')
    else:
        b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    data = {
        'message': 'Sync via OpenClaw',
        'content': b64
    }
    
    # Check if exists
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code == 200:
        data['sha'] = r.json()['sha']
    
    r = requests.put(url, headers=HEADERS, json=data, timeout=30)
    return r.status_code in [200, 201], r.status_code

def main():
    print(f'GitHub Sync - {REPO_OWNER}/{REPO_NAME}')
    print('=' * 50)
    
    # Test connection
    r = requests.get(f'{API_URL}', headers=HEADERS, timeout=10)
    if r.status_code != 200:
        print(f'ERROR: Cannot access repository (status: {r.status_code})')
        return False
    print('Connection: OK')
    
    # Collect files
    all_files = []
    for sync_dir in SYNC_DIRS:
        dir_path = os.path.join(BASE_PATH, sync_dir)
        if os.path.exists(dir_path):
            files = get_files(dir_path, parent_dir=sync_dir)
            for f in files:
                f['path'] = f'{sync_dir}/{f["path"]}'
            all_files.extend(files)
            print(f'{sync_dir}: {len(files)} files')
    
    print(f'Total: {len(all_files)} files')
    print('=' * 50)
    
    # Sync files
    success = failed = 0
    for i, f in enumerate(all_files, 1):
        try:
            # Try to read as text first, fallback to binary
            ext = os.path.splitext(f['full_path'])[1].lower()
            binary_exts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.svg']
            
            if ext in binary_exts:
                with open(f['full_path'], 'rb') as fp:
                    content = fp.read()
            else:
                with open(f['full_path'], 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
            
            ok, status = upload_file(f['path'], content)
            if ok:
                success += 1
                print(f'[{i}/{len(all_files)}] OK: {f["path"]}')
            else:
                failed += 1
                print(f'[{i}/{len(all_files)}] FAILED ({status}): {f["path"]}')
        except Exception as e:
            failed += 1
            print(f'[{i}/{len(all_files)}] ERROR: {f["path"]} - {e}')
    
    print('=' * 50)
    print(f'Done! Success: {success}, Failed: {failed}')
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
