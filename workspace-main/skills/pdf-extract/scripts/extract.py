#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Extract - 提取 PDF 文本内容
使用 pdfplumber 库，纯本地处理
"""

import sys
import argparse
import io

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import pdfplumber
except ImportError:
    print("错误：pdfplumber 未安装")
    print("安装方法：pip install pdfplumber")
    sys.exit(1)


def extract_text(pdf_path, pages=None):
    """
    提取 PDF 文本内容
    
    Args:
        pdf_path: PDF 文件路径
        pages: 页面范围，如 "1-5" 或 "1,3,5"，None 表示全部
    
    Returns:
        提取的文本内容
    """
    text_parts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        
        # 解析页面范围
        if pages:
            page_numbers = parse_pages(pages, total_pages)
        else:
            page_numbers = range(1, total_pages + 1)
        
        for page_num in page_numbers:
            if 1 <= page_num <= total_pages:
                page = pdf.pages[page_num - 1]  # pdfplumber 使用 0-based 索引
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"\n--- 第 {page_num} 页 ---\n")
                    text_parts.append(page_text)
    
    return "\n".join(text_parts)


def parse_pages(pages_str, total_pages):
    """
    解析页面范围字符串
    
    Args:
        pages_str: 如 "1-5" 或 "1,3,5"
        total_pages: 总页数
    
    Returns:
        页面编号列表（1-based）
    """
    page_numbers = set()
    
    for part in pages_str.split(','):
        part = part.strip()
        if '-' in part:
            # 范围，如 "1-5"
            start, end = part.split('-', 1)
            start = int(start.strip())
            end = int(end.strip())
            page_numbers.update(range(start, end + 1))
        else:
            # 单页，如 "3"
            page_numbers.add(int(part))
    
    # 过滤有效页面
    return sorted([p for p in page_numbers if 1 <= p <= total_pages])


def main():
    parser = argparse.ArgumentParser(description='提取 PDF 文本内容')
    parser.add_argument('pdf_path', help='PDF 文件路径')
    parser.add_argument('--pages', '-p', help='页面范围，如 "1-5" 或 "1,3,5"')
    
    args = parser.parse_args()
    
    try:
        text = extract_text(args.pdf_path, args.pages)
        print(text)
    except FileNotFoundError:
        print(f"错误：找不到文件 '{args.pdf_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
