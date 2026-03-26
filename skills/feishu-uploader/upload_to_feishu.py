#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书云盘文件上传实现
调用飞书 OpenAPI 上传文件
"""

import os
import sys
import io
import json
import base64
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 飞书 API 配置
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

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
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.token_expire_time = 0
        
    def get_access_token(self) -> str:
        """获取飞书访问令牌"""
        if self.access_token and self.token_expire_time > time.time():
            return self.access_token
            
        url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                print(f"[错误] 获取 token 失败: {result.get('msg')}")
                return None
                
            self.access_token = result["tenant_access_token"]
            self.token_expire_time = time.time() + result["expire"] - 60  # 提前60秒过期
            return self.access_token
            
        except Exception as e:
            print(f"[错误] 请求 token 失败: {e}")
            return None
    
    def get_root_folder_token(self) -> Optional[str]:
        """获取根目录 token"""
        token = self.get_access_token()
        if not token:
            return None
            
        url = f"{FEISHU_API_BASE}/drive/explorer/v2/root_folder/meta"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                print(f"[错误] 获取根目录失败: {result.get('msg')}")
                return None
                
            root_token = result.get("data", {}).get("token")
            print(f"[根目录] token: {root_token}")
            return root_token
            
        except Exception as e:
            print(f"[错误] 获取根目录异常: {e}")
            return None

    def get_or_create_folder(self, folder_name: str, parent_token: str = "") -> Optional[str]:
        """
        获取或创建文件夹
        
        Args:
            folder_name: 文件夹名称
            parent_token: 父文件夹 token（空表示根目录）
            
        Returns:
            文件夹 token
        """
        token = self.get_access_token()
        if not token:
            return None
            
        # 如果没有提供 parent_token，获取根目录 token
        if not parent_token:
            parent_token = self.get_root_folder_token()
            if not parent_token:
                return None
            
        # 先搜索文件夹是否存在
        url = f"{FEISHU_API_BASE}/drive/v1/files"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "page_size": 200,
            "folder_token": parent_token or None
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                print(f"[错误] 获取文件列表失败: {result.get('msg')}")
                return None
                
            # 查找同名文件夹
            for file in result.get("data", {}).get("files", []):
                if file.get("name") == folder_name and file.get("type") == "folder":
                    print(f"[找到文件夹] {folder_name}: {file['token']}")
                    return file["token"]
            
            # 不存在则创建
            return self.create_folder(folder_name, parent_token)
            
        except Exception as e:
            print(f"[错误] 搜索文件夹失败: {e}")
            return None
    
    def create_folder(self, folder_name: str, parent_token: str = "") -> Optional[str]:
        """创建文件夹"""
        token = self.get_access_token()
        if not token:
            return None
            
        url = f"{FEISHU_API_BASE}/drive/v1/files/create_folder"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "name": folder_name,
            "folder_token": parent_token
        }
            
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") != 0:
                print(f"[错误] 创建文件夹失败: {result.get('msg')}")
                print(f"[调试] 请求数据: {data}")
                print(f"[调试] 响应: {result}")
                return None
                
            folder_token = result["data"]["token"]
            print(f"[创建文件夹] {folder_name}: {folder_token}")
            return folder_token
            
        except Exception as e:
            print(f"[错误] 创建文件夹异常: {e}")
            return None
    
    def upload_file(self, file_path: str, folder_token: str) -> bool:
        """
        上传文件到飞书云盘
        
        Args:
            file_path: 本地文件路径
            folder_token: 目标文件夹 token
            
        Returns:
            是否成功
        """
        token = self.get_access_token()
        if not token:
            return False
            
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        print(f"[上传] {file_name} ({self.format_size(file_size)})")
        
        # 小文件直接上传（<20MB）
        if file_size < 20 * 1024 * 1024:
            return self._upload_small_file(file_path, folder_token, token)
        else:
            return self._upload_large_file(file_path, folder_token, token)
    
    def _upload_small_file(self, file_path: str, folder_token: str, token: str) -> bool:
        """上传小文件"""
        url = f"{FEISHU_API_BASE}/drive/v1/files/upload_all"
        headers = {"Authorization": f"Bearer {token}"}
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                # 使用 multipart/form-data 格式，按照飞书 API 要求
                files = {
                    'file': (file_name, f, 'application/octet-stream')
                }
                data = {
                    'file_name': file_name,
                    'parent_type': 'explorer',
                    'parent_node': folder_token,
                    'size': str(file_size)  # 添加文件大小
                }
                
                print(f"[调试] 上传参数: folder_token={folder_token}, size={file_size}")
                
                response = requests.post(url, headers=headers, files=files, data=data, timeout=300)
                result = response.json()
                
                if result.get("code") != 0:
                    print(f"[失败] {file_name}: {result.get('msg')}")
                    print(f"[调试] 响应: {result}")
                    return False
                    
                print(f"[成功] {file_name}: {result['data']['file_token']}")
                return True
                
        except Exception as e:
            print(f"[错误] 上传失败: {e}")
            return False
    
    def _upload_large_file(self, file_path: str, folder_token: str, token: str) -> bool:
        """分片上传大文件"""
        print(f"[大文件分片上传] 暂不支持，跳过")
        return False
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"


def load_config() -> Dict:
    """加载配置"""
    # 从环境变量或配置文件读取
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 默认配置（需要从飞书应用获取）
    return {
        "app_id": os.environ.get("FEISHU_APP_ID", ""),
        "app_secret": os.environ.get("FEISHU_APP_SECRET", "")
    }


def main():
    """主函数"""
    import time
    
    if len(sys.argv) < 2:
        print("用法: python upload_to_feishu.py <扫描结果json> [目标文件夹token]")
        print("示例: python upload_to_feishu.py scan_result.json")
        print("      python upload_to_feishu.py scan_result.json GPD4fUFKPlaiGoduXiRcpvXvnON")
        sys.exit(1)
    
    scan_file = sys.argv[1]
    target_folder_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(scan_file):
        print(f"错误: 文件不存在 - {scan_file}")
        sys.exit(1)
    
    # 加载扫描结果
    with open(scan_file, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)
    
    # 加载配置
    config = load_config()
    
    if not config.get("app_id") or not config.get("app_secret"):
        print("[错误] 请配置飞书 app_id 和 app_secret")
        print("方式1: 设置环境变量 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        print("方式2: 创建 config.json 文件")
        sys.exit(1)
    
    # 初始化上传器
    uploader = FeishuUploader(config["app_id"], config["app_secret"])
    
    # 获取或创建分类文件夹
    folder_tokens = {}
    
    if target_folder_token:
        # 使用指定的目标文件夹
        print(f"[使用指定文件夹] token: {target_folder_token}")
        for category in scan_data.get("categories", {}).keys():
            folder_tokens[category] = target_folder_token
    else:
        # 自动获取或创建分类文件夹
        for category in scan_data.get("categories", {}).keys():
            folder_name = FOLDER_NAMES.get(category, category)
            token = uploader.get_or_create_folder(folder_name)
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
