#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
判断某天是否因调休而上班
用法: python check_workday.py <日期> [年份]
     python check_workday.py 2026-01-04
     python check_workday.py 1月4日 2026
"""
import json
import sys
import os
import re
from datetime import datetime

SCRIPT_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(SCRIPT_DIR, '..', 'data', 'holidays.json')


def load_holidays():
    """加载假日数据"""
    if not os.path.exists(DATA_FILE):
        print(f"错误: 数据文件不存在 {DATA_FILE}", file=sys.stderr)
        sys.exit(1)
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_date(date_str, default_year=2026):
    """解析日期字符串"""
    date_str = date_str.strip()
    
    formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%m月%d日',
        '%Y年%m月%d日',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    match = re.match(r'(\d+)月(\d+)日', date_str)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        return datetime(default_year, month, day).date()
    
    return None


def is_workday(date_str, year=2026):
    """判断是否为调休上班日"""
    data = load_holidays()
    
    target_date = parse_date(date_str, year)
    if not target_date:
        print(f"无法解析日期: {date_str}", file=sys.stderr)
        return None
    
    target_str = str(target_date)
    
    for w in data.get('workdays', []):
        if w['date'] == target_str:
            return {
                'is_workday': True,
                'date': target_str,
                'note': w['note']
            }
    
    return {
        'is_workday': False,
        'date': target_str
    }


def format_day_of_week(date_obj):
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
    return mapping.get(date_obj.strftime('%A'), date_obj.strftime('%A'))


def main():
    if len(sys.argv) < 2:
        print("用法: python check_workday.py <日期> [年份]")
        print("示例:")
        print("  python check_workday.py 2026-01-04")
        print("  python check_workday.py 1月4日 2026")
        sys.exit(1)
    
    date_str = sys.argv[1]
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    
    result = is_workday(date_str, year)
    
    if result is None:
        sys.exit(1)
    
    if result['is_workday']:
        date_obj = datetime.strptime(result['date'], '%Y-%m-%d').date()
        dow = format_day_of_week(date_obj)
        print(f"⚠️  {result['date']} {dow} 需要上班！")
        print(f"   原因: {result['note']}")
    else:
        print(f"✅ {result['date']} 不需要上班（正常休息日）")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
