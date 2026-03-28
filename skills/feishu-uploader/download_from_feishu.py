#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书云盘文件下载工具 - 使用 lark-drive skill
"""

import os
import sys
import io
import json
import subprocess
from pathlib import Path
from typing import Optional

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 获取 lark-cli 路径
LARK_CLI = os.path.expandvars(r'%APPDATA%\npm\lark-cli.cmd')
if not os.path.exists(LARK_CLI):
    LARK_CLI = 'lark-cli'


class FeishuDownloader:
    """使用 lark-drive skill 下载文件"""
    
    def download_by_token(self, file_token: str, output_path: str) -> bool:
        """
        使用 file_token 下载文件
        
        Args:
            file_token: 飞书文件 token (如 boxbc_xxx, doxcn_xxx)
            output_path: 本地保存路径
        """
        print(f"[下载] file_token: {file_token}")
        print(f"[保存到] {output_path}")
        
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
            print(f"[成功] 已下载: {output_path}")
            return True
        else:
            print(f"[失败]: {output}")
            return False
    
    def download_by_url(self, file_url: str, output_path: str) -> bool:
        """
        从飞书 URL 下载文件
        
        支持的 URL 格式:
        - https://xxx.feishu.cn/drive/file/boxbc_xxx
        - https://xxx.larksuite.com/docx/doxcn_xxx
        """
        # 从 URL 提取 file_token
        file_token = self._extract_token_from_url(file_url)
        if not file_token:
            print(f"[错误] 无法从 URL 提取 file_token: {file_url}")
            return False
        
        print(f"[解析 URL] 提取到 token: {file_token}")
        return self.download_by_token(file_token, output_path)
    
    def _extract_token_from_url(self, url: str) -> Optional[str]:
        """从飞书 URL 中提取 file_token"""
        import re
        
        # 匹配各种飞书 URL 格式
        patterns = [
            r'/drive/file/(\w+)',  # 云盘文件
            r'/docx/(\w+)',        # 新版文档
            r'/doc/(\w+)',         # 旧版文档
            r'/sheets/(\w+)',      # 表格
            r'/wiki/(\w+)',        # 知识库 (需要额外处理)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='下载飞书云盘文件')
    parser.add_argument('source', help='文件 token 或 URL')
    parser.add_argument('output', help='本地保存路径')
    parser.add_argument('--url', action='store_true', help='source 是 URL 而非 token')
    
    args = parser.parse_args()
    
    downloader = FeishuDownloader()
    
    if args.url:
        success = downloader.download_by_url(args.source, args.output)
    else:
        success = downloader.download_by_token(args.source, args.output)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
