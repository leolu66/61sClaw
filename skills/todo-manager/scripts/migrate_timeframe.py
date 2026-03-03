#!/usr/bin/env python3
"""
待办任务时限迁移脚本 v4 - 手动指定时限
"""
import json
from datetime import datetime

TASKS_FILE = r"C:\Users\luzhe\.openclaw\workspace-main\skills\todo-manager\data\tasks.json"

# 手动指定每个任务的时限
MANUAL_TIMEFRAMES = {
    3: ("weekly", "2026-03-07"),   # 编写运营商新闻采集Agent → 本周
    4: ("date", "2026-03-03"),    # 网上申报个人所得税 → 已完成，保留原日期
    5: ("monthly", None),          # 研究OpenClaw通信问题 → 本月
    6: ("weekly", "2026-03-14"),  # 软院出海合作伙伴交流 → 本周
    7: ("weekly", "2026-03-14"),   # 火山引擎方案整理 → 本周
    1: ("monthly", None),          # 研究调度特殊模型访问 → 本月
    8: ("date", "2026-03-03"),    # 去软院交流 → 已完成，保留原日期
    9: ("yearly", None),           # 写Paper → 长期
    10: ("yearly", None),          # 学习强化学习基础课程 → 长期
}

def get_deadline(timeframe, specific_date=None):
    """根据时限类型计算 deadline"""
    now = datetime.now()
    
    if timeframe == "today":
        return now.replace(hour=23, minute=59, second=59, microsecond=0)
    
    elif timeframe == "date":
        if specific_date:
            dt = datetime.strptime(specific_date, "%Y-%m-%d")
            return dt.replace(hour=23, minute=59, second=59, microsecond=0)
        return None
    
    elif timeframe == "weekly":
        days_until_sunday = 6 - now.weekday()
        if now.weekday() == 6:
            days_until_sunday = 7
        sunday = now + timedelta(days=days_until_sunday)
        return sunday.replace(hour=23, minute=59, second=59, microsecond=0)
    
    elif timeframe == "monthly":
        if now.month == 12:
            next_month = now.replace(year=now.year+1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month+1, day=1)
        last_day = next_month - timedelta(days=1)
        return last_day.replace(hour=23, minute=59, second=59, microsecond=0)
    
    elif timeframe == "yearly":
        return now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=0)
    
    return None

from datetime import timedelta

def main():
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    tasks = data["tasks"]
    
    for task in tasks:
        todo_num = task.get("todoNumber")
        if todo_num not in MANUAL_TIMEFRAMES:
            continue
            
        timeframe, specific_date = MANUAL_TIMEFRAMES[todo_num]
        
        task["timeframe"] = timeframe
        if specific_date:
            task["specificDate"] = specific_date
        
        # 对于已完成的任务，只更新 timeframe，不改变 deadline
        if task.get("status") == "completed":
            continue
        
        new_deadline = get_deadline(timeframe, specific_date)
        if new_deadline:
            task["deadline"] = new_deadline.strftime("%Y-%m-%dT%H:%M:%S.999+08:00")
    
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("Done!")
    print(f"Processed {len(tasks)} tasks")
    
    print("\n--- Timeframe Results ---")
    timeframe_names = {"today": "Today", "weekly": "Weekly", "monthly": "Monthly", "yearly": "Yearly", "date": "Date"}
    for task in tasks:
        tf = task.get("timeframe", "N/A")
        name = timeframe_names.get(tf, tf)
        status = "[DONE]" if task.get("status") == "completed" else ""
        print(f"[{name:^8}] #{task.get('todoNumber'):>2} {status} - {task['title']}")

if __name__ == "__main__":
    main()
