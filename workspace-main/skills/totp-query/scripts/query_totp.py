#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态口令查询工具
根据坐标从密码本中查询对应的密码
"""

import sys
import io
import re
import subprocess

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def copy_to_clipboard(text):
    """将文本复制到剪贴板"""
    try:
        # 使用 PowerShell 的 Set-Clipboard 命令
        subprocess.run(
            ['powershell', '-command', f'Set-Clipboard -Value "{text}"'],
            check=True,
            capture_output=True
        )
        return True
    except Exception:
        return False

# 密码本数据
PASSWORD_GRID = {
    'A': ['MGZ', 'ZKA', 'QPF', 'HFT', 'G3N', 'YEA', 'HAD', '6AL'],
    'B': ['GND', 'BJD', 'LEE', '5GB', '9RJ', 'YE9', 'PQ4', 'KY9'],
    'C': ['WSG', 'VEX', 'CVK', 'KKH', 'Q7P', 'JGJ', 'YXH', 'NFE'],
    'D': ['SXL', 'WB9', '873', 'BQZ', '75H', 'ZX5', 'EL4', 'JDL'],
    'E': ['K9G', 'KDA', '5SZ', 'UDZ', 'ZJ7', 'ARX', 'M2X', 'TE4'],
    'F': ['E79', '3VZ', '6SN', 'SPR', 'AJX', 'NU7', 'MSP', 'BS6'],
    'G': ['77Y', 'QU4', 'D7Z', 'H9V', 'LID', '8TX', 'CUT', '9Q5'],
    'H': ['86L', 'VNR', 'WNN', 'VPQ', 'URB', 'NPA', '5KV', 'FSL']
}

ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
COLUMNS = list(range(1, 9))  # 1-8


def parse_coordinate(coord_str):
    """
    解析坐标字符串，如 'A1' 或 'C7'
    
    Args:
        coord_str: 坐标字符串，如 'A1', 'C7'
    
    Returns:
        tuple: (行, 列) 如 ('A', 1)
    """
    coord_str = coord_str.strip().upper()
    match = re.match(r'^([A-H])([1-8])$', coord_str)
    if not match:
        raise ValueError(f"无效的坐标格式: {coord_str}，正确格式如 A1, C7")
    
    row = match.group(1)
    col = int(match.group(2))
    return row, col


def get_password(row, col):
    """
    根据行和列获取密码
    
    Args:
        row: 行字母 A-H
        col: 列数字 1-8
    
    Returns:
        str: 三位数密码
    """
    if row not in ROWS:
        raise ValueError(f"无效的行: {row}，必须是 A-H")
    if col not in COLUMNS:
        raise ValueError(f"无效的列: {col}，必须是 1-8")
    
    return PASSWORD_GRID[row][col - 1]  # 列从1开始，索引从0开始


def query_totp(coord_pair):
    """
    查询动态口令
    
    Args:
        coord_pair: 坐标对字符串，如 'A1:C7' 或 'A1：C7'
    
    Returns:
        str: 拼接后的动态口令
    """
    # 支持中文冒号和英文冒号
    coord_pair = coord_pair.replace('：', ':')
    coords = coord_pair.split(':')
    
    if len(coords) != 2:
        raise ValueError(f"无效的坐标对格式: {coord_pair}，正确格式如 A1:C7 或 A1：C7")
    
    coord1 = coords[0].strip()
    coord2 = coords[1].strip()
    
    row1, col1 = parse_coordinate(coord1)
    row2, col2 = parse_coordinate(coord2)
    
    pwd1 = get_password(row1, col1)
    pwd2 = get_password(row2, col2)
    
    return pwd1 + pwd2


def print_grid():
    """打印密码本表格"""
    print("密码本：")
    print("| 行 \\ 列 | 1    | 2    | 3    | 4    | 5    | 6    | 7    | 8    |")
    print("| ------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |")
    for row in ROWS:
        row_data = PASSWORD_GRID[row]
        print(f"| {row}       | {' | '.join(row_data)} |")


def main():
    if len(sys.argv) < 2:
        print("用法: python query_totp.py <坐标对>")
        print("示例: python query_totp.py A1:C7")
        print("      python query_totp.py A1：C7")
        print()
        print_grid()
        sys.exit(1)
    
    coord_pair = sys.argv[1]
    
    try:
        result = query_totp(coord_pair)
        print(result)
        
        # 复制到剪贴板
        if copy_to_clipboard(result):
            print("(已复制到剪贴板)", file=sys.stderr)
        else:
            print("(复制到剪贴板失败，请手动复制)", file=sys.stderr)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
