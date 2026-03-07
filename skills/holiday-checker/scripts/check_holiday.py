#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import sys
# 解决 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
判断某天是否为法定假日
用法: 
  python check_holiday.py <日期> [年份]
  python check_holiday.py --next                    # 查询下一个法定假日
  python check_holiday.py 2026-01-01
  python check_holiday.py 1月1日
"""
import json
import sys
import os
import re
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(SCRIPT_DIR, '..', 'data', 'holidays.json')

WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']


def get_weekday(date_str_or_date):
    """获取星期几"""
    if isinstance(date_str_or_date, str):
        d = datetime.strptime(date_str_or_date, '%Y-%m-%d').date()
    else:
        d = date_str_or_date
    return WEEKDAYS[d.weekday()]


def load_holidays():
    """加载假日数据"""
    if not os.path.exists(DATA_FILE):
        print(f"错误: 数据文件不存在 {DATA_FILE}", file=sys.stderr)
        print("请先运行: python fetch_holidays.py --save", file=sys.stderr)
        sys.exit(1)
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_date(date_str, default_year=2026):
    """解析日期字符串"""
    date_str = date_str.strip()
    
    # 尝试多种格式
    formats = [
        '%Y-%m-%d',    # 2026-01-01
        '%Y/%m/%d',    # 2026/01/01
        '%m月%d日',    # 1月1日
        '%Y年%m月%d日', # 2026年1月1日
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # 处理"X月X日"格式（需要补充年份）
    match = re.match(r'(\d+)月(\d+)日', date_str)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        return datetime(default_year, month, day).date()
    
    return None


def is_holiday(date_str, year=2026):
    """判断是否为假日"""
    data = load_holidays()
    
    target_date = parse_date(date_str, year)
    if not target_date:
        print(f"无法解析日期: {date_str}", file=sys.stderr)
        return None
    
    # 解析 holiday 中的日期范围
    for h in data.get('holidays', []):
        start_date_str = h['date']
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        days = h['days']
        
        # 计算结束日期
        end_date = start_date + timedelta(days=days - 1)
        
        if start_date <= target_date <= end_date:
            return {
                'is_holiday': True,
                'name': h['name'],
                'date': str(target_date),
                'start_date': str(start_date),
                'end_date': str(end_date),
                'total_days': days
            }
    
    return {
        'is_holiday': False,
        'date': str(target_date)
    }


def get_next_holiday(year=2026):
    """获取下一个法定假日"""
    from datetime import date
    data = load_holidays()
    today = date.today()
    
    next_holiday = None
    next_start_date = None
    
    for h in data.get('holidays', []):
        start_date = datetime.strptime(h['date'], '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=h['days'] - 1)
        
        # 跳过已结束的假期
        if end_date < today:
            continue
        
        # 今天是假期的第一天
        if start_date == today:
            return {
                'name': h['name'],
                'start_date': str(start_date),
                'end_date': str(end_date),
                'days': h['days'],
                'is_today': True,
                'days_until': 0
            }
        
        # 找到下一个最近的假期
        if next_start_date is None or start_date < next_start_date:
            next_start_date = start_date
            next_holiday = {
                'name': h['name'],
                'start_date': str(start_date),
                'end_date': str(end_date),
                'days': h['days'],
                'is_today': False,
                'days_until': (start_date - today).days
            }
    
    return next_holiday


def main():
    # 支持 --next 参数
    if len(sys.argv) > 1 and sys.argv[1] == '--next':
        year = int(sys.argv[2]) if len(sys.argv) > 2 else datetime.now().year
        result = get_next_holiday(year)
        if result:
            if result['is_today']:
                print(f"🎉 今天就是【{result['name']}】！")
                print(f"   假期: {result['start_date']} ({get_weekday(result['start_date'])}) 至 {result['end_date']} ({get_weekday(result['end_date'])}) (共{result['days']}天)")
            else:
                print(f"📅 下一个法定假日: 【{result['name']}】")
                print(f"   假期: {result['start_date']} ({get_weekday(result['start_date'])}) 至 {result['end_date']} ({get_weekday(result['end_date'])}) (共{result['days']}天)")
                print(f"   距今天还有 {result['days_until']} 天")
        else:
            print("今年没有更多的法定假日了")
        return 0
    
    if len(sys.argv) < 2:
        print("用法: python check_holiday.py <日期> [年份]")
        print("     python check_holiday.py --next [年份]  # 查询下一个法定假日")
        print("示例:")
        print("  python check_holiday.py 2026-01-01")
        print("  python check_holiday.py 1月1日 2026")
        print("  python check_holiday.py --next")
        sys.exit(1)
    
    date_str = sys.argv[1]
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    
    # 支持按名称查询
    data = load_holidays()
    for h in data.get('holidays', []):
        if h['name'] in date_str:
            start = datetime.strptime(h['date'], '%Y-%m-%d').date()
            end = start + timedelta(days=h['days'] - 1)
            print(f"【{h['name']}】")
            print(f"  假期: {h['date']} ({get_weekday(h['date'])}) 至 {end} ({get_weekday(end)}) (共{h['days']}天)")
            sys.exit(0)
    
    result = is_holiday(date_str, year)
    
    if result is None:
        sys.exit(1)
    
    if result['is_holiday']:
        print(f"✅ {result['date']} ({get_weekday(result['date'])}) 是【{result['name']}】假期")
        print(f"   假期范围: {result['start_date']} ({get_weekday(result['start_date'])}) 至 {result['end_date']} ({get_weekday(result['end_date'])}) (共{result['total_days']}天)")
    else:
        print(f"❌ {result['date']} ({get_weekday(result['date'])}) 不是假日")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
