#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成工作日志文件名
格式：YYYY-MM-DD-NNN-简短概述.md
"""

import os
import sys
import re
from datetime import datetime

def get_next_log_filename(summary="", log_dir=r"D:\anthropic\工作日志"):
    """生成下一个日志文件名

    Args:
        summary: 简短概述，如"修复MCP+邮件访问"
        log_dir: 日志保存目录

    Returns:
        (filepath, filename) 元组
    """
    # 确保目录存在
    os.makedirs(log_dir, exist_ok=True)

    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")

    # 扫描现有文件，找到当天的最大序号
    max_seq = 0
    for filename in os.listdir(log_dir):
        if filename.startswith(today) and filename.endswith('.md'):
            try:
                # 格式: 2026-02-13-001-描述.md 或 2026-02-13-001.md
                parts = filename.replace('.md', '').split('-')
                if len(parts) >= 4:
                    seq = int(parts[3])
                    max_seq = max(max_seq, seq)
            except (ValueError, IndexError):
                continue

    # 生成新序号
    next_seq = max_seq + 1

    # 清理概述字符串，确保文件名安全
    if summary:
        # 移除不安全的字符
        safe_summary = re.sub(r'[\\/*?:"<>|]', '', summary)
        safe_summary = safe_summary.replace(' ', '+')
        filename = f"{today}-{next_seq:03d}-{safe_summary}.md"
    else:
        filename = f"{today}-{next_seq:03d}.md"

    filepath = os.path.join(log_dir, filename)
    return filepath, filename

def main():
    # 从命令行参数获取概述
    summary = sys.argv[1] if len(sys.argv) > 1 else ""
    filepath, filename = get_next_log_filename(summary)
    print(filepath)

if __name__ == "__main__":
    main()
