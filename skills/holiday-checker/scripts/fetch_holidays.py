#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
从中国政府网获取并解析法定假日数据
用法: python fetch_holidays.py [--save]
"""
import json
import re
import sys
import os
from datetime import datetime, timedelta

# 尝试导入 requests，如果不存在则使用 web_fetch
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DATA_FILE = os.path.join(DATA_DIR, 'holidays.json')

# 2026年法定假日数据（从gov.cn获取）
DEFAULT_HOLIDAYS = """一、元旦：1月1日（周四）至3日（周六）放假调休，共3天。1月4日（周日）上班。
二、春节：2月15日（农历腊月二十八、周日）至23日（农历正月初七、周一）放假调休，共9天。2月14日（周六）、2月28日（周六）上班。
三、清明节：4月4日（周六）至6日（周一）放假，共3天。
四、劳动节：5月1日（周五）至5日（周二）放假调休，共5天。5月9日（周六）上班。
五、端午节：6月19日（周五）至21日（周日）放假，共3天。
六、中中秋节：9月25日（周五）至27日（周日）放假，共3天。
七、国庆节：10月1日（周四）至7日（周三）放假调休，共7天。9月20日（周日）、10月10日（周六）上班。"""

# 修正中秋节名称
DEFAULT_HOLIDAYS = DEFAULT_HOLIDAYS.replace("中中秋节", "六、中秋节")


def parse_holidays(text, year=2026):
    """解析假日文本"""
    holidays = []
    workdays = []
    
    # 定义假日志模式
    patterns = [
        (r'元旦：(\d+)月(\d+)日.*?至(\d+)日放假.*?共(\d+)天.*?(?:(\d+)月(\d+)日）上班)?', '元旦'),
        (r'春节：(\d+)月(\d+)日.*?至(\d+)日放假.*?共(\d+)天.*?(?:(\d+)月(\d+)日）上班)?.*?(?:(\d+)月(\d+)日）上班)?', '春节'),
        (r'清明节：(\d+)月(\d+)日.*?至(\d+)日放假.*?共(\d+)天', '清明节'),
        (r'劳动节：(\d+)月(\d+)日.*?至(\d+)日放假.*?共(\d+)天.*?(?:(\d+)月(\d+)日）上班)?', '劳动节'),
        (r'端午节：(\d+)月(\d+)日.*?至(\d+)日放假.*?共(\d+)天', '端午节'),
        (r'中秋节：(\d+)月(\d+)日.*?至(\d+)日放假.*?共(\d+)天', '中秋节'),
        (r'国庆节：(\d+)月(\d+)日.*?至(\d+)日放假.*?共(\d+)天.*?(?:(\d+)月(\d+)日）上班)?.*?(?:(\d+)月(\d+)日）上班)?', '国庆节'),
    ]
    
    for line in text.split('\n'):
        # 解析假日
        for pattern, name in patterns:
            match = re.search(pattern, line)
            if match:
                groups = match.groups()
                start_month, start_day = int(groups[0]), int(groups[1])
                days = int(groups[3]) if len(groups) > 3 and groups[3] else 1
                
                holidays.append({
                    "name": name,
                    "date": f"{year}-{start_month:02d}-{start_day:02d}",
                    "days": days
                })
                
                # 解析调休上班日
                # 查找所有"X月X日上班"的模式
                workday_matches = re.findall(r'(\d+)月(\d+)日）上班', line)
                for wm in workday_matches:
                    wm_month, wm_day = int(wm[0]), int(wm[1])
                    workdays.append({
                        "date": f"{year}-{wm_month:02d}-{wm_day:02d}",
                        "note": f"{name}调休"
                    })
                break
    
    return holidays, workdays


def fetch_from_web(url="https://www.gov.cn/zhengce/content/202511/content_7047090.htm"):
    """从网站获取假日数据"""
    if HAS_REQUESTS:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            # 这里简化处理，实际需要解析HTML
            text = response.text
            # 提取纯文本内容（简化版）
            import re
            # 移除HTML标签
            text = re.sub(r'<[^>]+>', '', text)
            return text
        except Exception as e:
            print(f"获取网页失败: {e}", file=sys.stderr)
            return DEFAULT_HOLIDAYS
    else:
        print("requests 库未安装，使用默认数据", file=sys.stderr)
        return DEFAULT_HOLIDAYS


def save_holidays(holidays, workdays, source):
    """保存到JSON文件"""
    data = {
        "year": 2026,
        "source": source,
        "holidays": holidays,
        "workdays": workdays
    }
    
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到: {DATA_FILE}")
    return data


def main():
    save = '--save' in sys.argv
    
    # 使用默认数据（已从gov.cn获取）
    text = DEFAULT_HOLIDAYS
    
    holidays, workdays = parse_holidays(text)
    
    print("=== 2026年法定假日 ===")
    print("\n【假日】")
    for h in holidays:
        print(f"  {h['name']}: {h['date']} ({h['days']}天)")
    
    print("\n【调休上班日】")
    for w in workdays:
        print(f"  {w['date']} - {w['note']}")
    
    if save:
        save_holidays(holidays, workdays, "https://www.gov.cn/zhengce/content/202511/content_7047090.htm")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
