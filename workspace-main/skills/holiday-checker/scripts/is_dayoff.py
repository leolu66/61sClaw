#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合查询某天是否休息日
结合法定假日、调休安排、周末综合判断
用法: python is_dayoff.py <日期>
     python is_dayoff.py 2026-01-01
     python is_dayoff.py 今天
     python is_dayoff.py 明天
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import os
import re
from datetime import datetime, timedelta, date

SCRIPT_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(SCRIPT_DIR, '..', 'data', 'holidays.json')


def load_holidays():
    """加载假日数据"""
    if not os.path.exists(DATA_FILE):
        print(f"错误: 数据文件不存在 {DATA_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_date_input(date_str):
    """解析日期输入，支持今天、明天、后天等"""
    date_str = date_str.strip().lower()
    today = date.today()
    
    # 处理相对日期
    if date_str in ['今天', 'today']:
        return today
    elif date_str in ['明天', 'tomorrow']:
        return today + timedelta(days=1)
    elif date_str in ['后天']:
        return today + timedelta(days=2)
    elif date_str in ['大后天']:
        return today + timedelta(days=3)
    
    # 处理 "X月X日" 格式
    match = re.match(r'(\d+)月(\d+)日', date_str)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        return datetime(today.year, month, day).date()
    
    # 处理标准日期格式
    formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None


def is_holiday_range(target_date, holidays):
    """检查是否在法定假日范围内"""
    for h in holidays:
        start_date = datetime.strptime(h['date'], '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=h['days'] - 1)
        
        if start_date <= target_date <= end_date:
            return {
                'is_holiday': True,
                'name': h['name'],
                'start': str(start_date),
                'end': str(end_date),
                'days': h['days']
            }
    return None


def is_workday(target_date, workdays):
    """检查是否是调休上班日"""
    target_str = str(target_date)
    for w in workdays:
        if w['date'] == target_str:
            return {
                'is_workday': True,
                'note': w.get('note', '')
            }
    return None


def is_weekend(target_date):
    """检查是否是周末"""
    # weekday(): Monday=0, Sunday=6
    return target_date.weekday() >= 5  # 5=Saturday, 6=Sunday


def get_dayoff_reason(target_date, holidays, workdays):
    """
    综合判断是否休息日
    返回: (is_dayoff: bool, reasons: list)
    """
    reasons = []
    
    # 1. 检查是否法定假日
    holiday_info = is_holiday_range(target_date, holidays)
    if holiday_info:
        return True, [f"法定假日: {holiday_info['name']}"]
    
    # 2. 检查是否调休上班日
    workday_info = is_workday(target_date, workdays)
    if workday_info:
        return False, [f"调休上班: {workday_info['note']}"]
    
    # 3. 检查是否是周末
    if is_weekend(target_date):
        return True, ["周末休息"]
    
    # 4. 普通工作日
    return False, ["正常工作日"]


def main():
    if len(sys.argv) < 2:
        print("用法: python is_dayoff.py <日期>")
        print("示例:")
        print("  python is_dayoff.py 2026-01-01")
        print("  python is_dayoff.py 今天")
        print("  python is_dayoff.py 明天")
        print("  python is_dayoff.py 4月4日")
        sys.exit(1)
    
    date_str = sys.argv[1]
    target_date = parse_date_input(date_str)
    
    if not target_date:
        print(f"无法解析日期: {date_str}", file=sys.stderr)
        sys.exit(1)
    
    # 加载数据
    data = load_holidays()
    holidays = data.get('holidays', [])
    workdays = data.get('workdays', [])
    
    # 综合判断
    is_dayoff, reasons = get_dayoff_reason(target_date, holidays, workdays)
    
    # 输出结果
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday = weekday_names[target_date.weekday()]
    
    print(f"📅 {target_date} ({weekday})")
    
    if is_dayoff:
        print(f"✅ 休息")
    else:
        print(f"💼 上班")
    
    for reason in reasons:
        print(f"   原因: {reason}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
