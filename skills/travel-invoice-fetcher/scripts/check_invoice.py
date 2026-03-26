#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查invoice.pdf文件内容和金额提取
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
    
    # 查找invoice.pdf文件
    invoice_file = None
    for file_path in trip_dir.rglob('*.pdf'):
        if file_path.name.lower() == 'invoice.pdf':
            invoice_file = file_path
            break
    
    if not invoice_file:
        print("❌ 未找到invoice.pdf文件")
        return
    
    print(f"找到文件: {invoice_file.name}")
    print("=" * 70)
    
    # 提取文本
    text = extract_text_from_pdf(invoice_file)
    print(f"文本长度: {len(text)}")
    
    if text:
        print("\n完整文本内容:")
        print('-' * 70)
        print(text)
        print('-' * 70)
        
        # 检查金额格式
        import re
        
        # 查找价税合计相关内容
        total_patterns = [
            r'价税合计.*?([¥￥]\d+\.\d{2})',
            r'合计.*?([¥￥]\d+\.\d{2})',
            r'金额.*?([¥￥]\d+\.\d{2})',
            r'([¥￥]\d+\.\d{2})',
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, text)
            if matches:
                print(f"\n找到金额模式 '{pattern}': {matches}")


if __name__ == "__main__":
    main()
