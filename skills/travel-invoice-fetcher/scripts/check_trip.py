#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查trip.pdf文件内容和解析结果
"""

import sys
import io
from pathlib import Path

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def extract_text_from_pdf(file_path):
    """从PDF文件提取文本"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"   ⚠️ 提取文本失败 {file_path.name}: {e}")
        return ""


def main():
    """主函数"""
    # 设置测试目录
    trip_dir = Path(r'D:\Users\luzhe\报销凭证\南京-北京-0225-0311')
    
    if not trip_dir.exists():
        print(f"❌ 目录不存在: {trip_dir}")
        return
    
    # 查找trip.pdf文件
    trip_file = None
    for file_path in trip_dir.rglob('*.pdf'):
        if file_path.name.lower() == 'trip.pdf':
            trip_file = file_path
            break
    
    if not trip_file:
        print("❌ 未找到trip.pdf文件")
        return
    
    print(f"找到文件: {trip_file.name}")
    print("=" * 70)
    
    # 提取文本
    text = extract_text_from_pdf(trip_file)
    print(f"文本长度: {len(text)}")
    
    if text:
        print("\n完整文本内容:")
        print('-' * 70)
        print(text)
        print('-' * 70)
        
        # 检查是否包含地铁出行相关内容
        if '地铁出行' in text:
            print("\n✅ 检测到地铁出行行程单")
        
        # 检查日期格式
        import re
        date_pattern = r'(\d{4}年\d{1,2}月\d{1,2}日)'
        date_matches = re.findall(date_pattern, text)
        if date_matches:
            print(f"\n找到日期: {date_matches}")
        
        # 检查时间格式
        time_pattern = r'(\d{2}:\d{2})-(\d{2}:\d{2})'
        time_matches = re.findall(time_pattern, text)
        if time_matches:
            print(f"找到时间: {time_matches}")
        
        # 检查行程站点
        route_pattern = r'([^ ]+?-[^ ]+?)'
        route_matches = re.findall(route_pattern, text)
        if route_matches:
            print(f"找到行程站点: {route_matches}")


if __name__ == "__main__":
    main()
