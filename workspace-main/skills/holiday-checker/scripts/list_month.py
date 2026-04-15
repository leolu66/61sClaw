#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
列出某月的所有假日
用法: python list_month.py <月份> [年份]
     python list_month.py 1      # 列出1月假日
     python list_month.py 2 2026 # 列出2026年2月假日
"""
import json
import sys
import os
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(SCRIPT_DIR, '..', 'data', 'holidays.json')


def load_holidays():
    """加载假日数据"""
    if not os.path.exists(DATA_FILE):
        print(f"错误: 数据文件不存在 {DATA_FILE}", file=sys.stderr)
        sys.exit(1)
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_month_holidays(month, year=2026):
    """列出某月的所有假日"""
    data = load_holidays()
    results = []
    
    for h in data.get('holidays', []):
        start_date = datetime.strptime(h['date'], '%Y-%m-%d').date()
        days = h['days']
        
        # 生成假期内的所有日期
        for i in range(days):
            current = start_date + timedelta(days=i)
            if current.month == month and current.year == year:
                results.append({
                    'date': str(current),
                    'name': h['name'],
                    'day_of_week': current.strftime('%A'),
                    'is_first_day': i == 0
                })
    
    return sorted(results, key=lambda x: x['date'])


def format_day_of_week(day_str):
    """格式化星期"""
    mapping = {
        'Monday': '周一',
        'Tuesday': '周二',
        'Wednesday': '周三',
        'Thursday': '周四',
        'Friday': '周五',
        'Saturday': '周六',
        'Sunday': '周日'
    }
    return mapping.get(day_str, day_str)


def main():
    if len(sys.argv) < 2:
        print("用法: python list_month.py <月份> [年份]")
        print("示例:")
        print("  python list_month.py 1       # 列出1月假日")
        print("  python list_month.py 2 2026  # 列出2026年2月假日")
        sys.exit(1)
    
    month = int(sys.argv[1])
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    
    if month < 1 or month > 12:
        print("错误: 月份必须在1-12之间", file=sys.stderr)
        sys.exit(1)
    
    holidays = list_month_holidays(month, year)
    
    print(f"=== {year}年{month}月假日 ===\n")
    
    if not holidays:
        print(f"{month}月没有假日")
        return 0
    
    # 按假期分组显示
    current_name = None
    for h in holidays:
        if h['name'] != current_name:
            current_name = h['name']
            print(f"【{h['name']}】")
        
        dow = format_day_of_week(h['day_of_week'])
        first_day_marker = " (首日)" if h['is_first_day'] else ""
        print(f"  {h['date']} {dow}{first_day_marker}")
    
    print(f"\n共 {len(holidays)} 天")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
