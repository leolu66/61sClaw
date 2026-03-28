#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书云盘文件上传实现 - 使用 lark-drive skill
调用 lark-cli drive +upload 上传文件
"""

import os
import sys
import io
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 获取 lark-cli 路径
LARK_CLI = os.path.expandvars(r'%APPDATA%\npm\lark-cli.cmd')
if not os.path.exists(LARK_CLI):
    # 尝试使用 PATH 中的 lark-cli
    LARK_CLI = 'lark-cli'

# 文件夹名称映射
FOLDER_NAMES = {
    'src': 'src',
    'videos': 'videos',
    'recordings': 'recordings',
    'images': 'images',
    'documents': 'documents',
    'appdatas': 'appdatas',
    'temp': 'temp'
}


class FeishuUploader:
    """使用 lark-drive skill 上传文件"""
    
    def __init__(self):
        self.folder_tokens = {}
    
    def run_lark_cli(self, *args) -> tuple[bool, str]:
        """执行 lark-cli 命令"""
        cmd = ['lark-cli'] + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300
            )
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, f"执行错误: {e}"
    
    def get_root_folder_token(self) -> Optional[str]:
        """获取根目录 token"""
        # 使用 API 获取根文件夹
        try:
            result = subprocess.run(
                [LARK_CLI, 'api', 'GET', '/open-apis/drive/explorer/v2/root_folder/meta'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30,
                shell=True
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get('data', {}).get('token')
        except Exception as e:
            print(f"[错误] 获取根文件夹失败: {e}")
        return None
    
    def _find_folder(self, folder_name: str, parent_token: str) -> Optional[str]:
        """查找文件夹 token"""
        try:
            result = subprocess.run(
                [LARK_CLI, 'api', 'GET', '/open-apis/drive/v1/files',
                 '--params', json.dumps({"page_size": 200, "folder_token": parent_token})],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30,
                shell=True
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for file in data.get('data', {}).get('files', []):
                    if file.get('name') == folder_name and file.get('type') == 'folder':
                        return file['token']
        except:
            pass
        return None
    
    def get_or_create_folder(self, folder_name: str, parent_token: str = None) -> Optional[str]:
        """获取或创建文件夹"""
        parent = parent_token or self.get_root_folder_token()
        if not parent:
            print("[错误] 无法获取父文件夹 token")
            return None
        
        # 先尝试查找
        token = self._find_folder(folder_name, parent)
        if token:
            print(f"[找到文件夹] {folder_name}: {token}")
            return token
        
        # 创建文件夹 - 使用原生 API
        try:
            result = subprocess.run(
                [LARK_CLI, 'api', 'POST', '/open-apis/drive/v1/files/create_folder',
                 '--data', json.dumps({"name": folder_name, "folder_token": parent})],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30,
                shell=True
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                token = data.get('data', {}).get('token')
                print(f"[创建文件夹] {folder_name}: {token}")
                return token
            else:
                print(f"[错误] 创建文件夹失败: {result.stderr}")
        except Exception as e:
            print(f"[错误] 创建文件夹异常: {e}")
        return None
    
    def upload_file(self, file_path: str, folder_token: str, custom_name: str = None) -> bool:
        """使用 lark-drive +upload 上传文件"""
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            print(f"[错误] 文件不存在: {file_path}")
            return False
        
        file_name = custom_name or os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        print(f"[上传] {file_name} ({format_size(file_size)})")
        
        # lark-cli 要求使用相对路径，需要切换到文件所在目录执行
        file_dir = os.path.dirname(file_path)
        rel_path = os.path.basename(file_path)
        
        # 使用 lark-drive +upload 快捷命令
        cmd_args = [
            LARK_CLI, 'drive', '+upload',
            '--file', f"./{rel_path}",
            '--folder-token', folder_token
        ]
        
        if custom_name:
            cmd_args.extend(['--name', custom_name])
        
        # 在文件所在目录执行命令
        try:
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300,
                cwd=file_dir,
                shell=True
            )
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
        except Exception as e:
            success = False
            output = f"执行错误: {e}"
        
        if success:
            print(f"[成功] {file_name}")
            return True
        else:
            print(f"[失败] {file_name}: {output}")
            return False
    
    def download_file(self, file_token: str, output_path: str) -> bool:
        """使用 lark-drive +download 下载文件"""
        print(f"[下载] file_token: {file_token} -> {output_path}")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 获取输出文件名
        output_file = os.path.basename(output_path)
        
        # 在输出目录执行下载命令，使用相对路径
        try:
            result = subprocess.run(
                [LARK_CLI, 'drive', '+download',
                 '--file-token', file_token,
                 '--output', f"./{output_file}"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300,
                cwd=output_dir or '.',
                shell=True
            )
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
        except Exception as e:
            success = False
            output = f"执行错误: {e}"
        
        if success:
            print(f"[成功] 已下载到: {output_path}")
            return True
        else:
            print(f"[失败]: {output}")
            return False


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python upload_to_feishu.py <扫描结果json> [目标文件夹token]")
        print("示例: python upload_to_feishu.py scan_result.json")
        print("      python upload_to_feishu.py scan_result.json fldbc_xxx")
        sys.exit(1)
    
    scan_file = sys.argv[1]
    target_folder_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(scan_file):
        print(f"错误: 文件不存在 - {scan_file}")
        sys.exit(1)
    
    # 加载扫描结果
    with open(scan_file, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)
    
    # 初始化上传器
    uploader = FeishuUploader()
    
    # 获取或创建分类文件夹
    folder_tokens = {}
    
    # 检查扫描结果中是否已包含 folder_tokens
    if "folder_tokens" in scan_data:
        folder_tokens = scan_data["folder_tokens"]
        print(f"[使用扫描结果中的文件夹配置]")
    elif target_folder_token:
        # 使用指定的目标文件夹
        print(f"[使用指定文件夹] token: {target_folder_token}")
        for category in scan_data.get("categories", {}).keys():
            folder_tokens[category] = target_folder_token
    else:
        # 自动获取或创建分类文件夹
        print("[准备文件夹]")
        root_token = uploader.get_root_folder_token()
        if not root_token:
            print("[错误] 无法获取根文件夹，请检查 lark-cli 是否已认证")
            sys.exit(1)
        
        for category in scan_data.get("categories", {}).keys():
            folder_name = FOLDER_NAMES.get(category, category)
            token = uploader.get_or_create_folder(folder_name, root_token)
            if token:
                folder_tokens[category] = token
    
    # 上传文件
    total_files = 0
    success_files = 0
    
    for category, files in scan_data.get("categories", {}).items():
        if category not in folder_tokens:
            print(f"[跳过] {category}: 文件夹未找到")
            continue
            
        folder_token = folder_tokens[category]
        print(f"\n[上传分类] {category}")
        
        for file_info in files:
            total_files += 1
            if uploader.upload_file(file_info["path"], folder_token):
                success_files += 1
    
    print(f"\n[上传完成] 成功: {success_files}/{total_files}")


if __name__ == '__main__':
    main()
