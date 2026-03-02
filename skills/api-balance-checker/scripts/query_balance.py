#!/usr/bin/env python3
"""
余额查询主脚本 - 负责完整流程：启动 Chrome -> 查询 -> 关闭 Chrome
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

# 脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
api_checker_script = os.path.join(script_dir, "api_balance_checker.py")

# 结果保存路径
result_file = Path.home() / "Pictures" / "api_balances.json"


def load_history():
    """加载历史记录"""
    if result_file.exists():
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_result(result):
    """保存查询结果"""
    history = load_history()
    history.insert(0, result)
    history = history[:100]
    result_file.parent.mkdir(parents=True, exist_ok=True)
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_last_record(platform_key):
    """获取上次记录"""
    history = load_history()
    for record in history:
        if record.get("platform_key") == platform_key:
            return (record.get("remaining"), record.get("used"), 
                    record.get("requests"), record.get("timestamp"))
    return None


def get_baseline_record(platform_key):
    """
    获取对比基准记录
    - 如果今天有记录，返回今天第一条
    - 如果今天没记录（跨天），返回昨天最后一条
    """
    history = load_history()
    today = datetime.now().date()
    yesterday = today.replace(day=today.day - 1) if today.day > 1 else today
    
    today_records = []
    yesterday_records = []
    
    for record in history:
        if record.get("platform_key") != platform_key:
            continue
        try:
            record_date = datetime.fromisoformat(record.get("timestamp", "").replace('Z', '+00:00').replace('+00:00', '')).date()
            if record_date == today:
                today_records.append(record)
            elif record_date == yesterday:
                yesterday_records.append(record)
        except:
            continue
    
    # 如果今天有记录，返回今天第一条（最早的）
    if today_records:
        record = today_records[-1]  # 最后一条是最近的，第一条是最早的
        return (record.get("remaining"), record.get("used"), 
                record.get("requests"), record.get("timestamp"), "today")
    
    # 如果今天没记录但昨天有，返回昨天最后一条
    if yesterday_records:
        record = yesterday_records[0]  # 第一条是最早的，最后一条是最近的
        return (record.get("remaining"), record.get("used"), 
                record.get("requests"), record.get("timestamp"), "yesterday")
    
    return None


def parse_amount(amount_str):
    """解析金额"""
    if not amount_str or amount_str == "未知":
        return None
    try:
        return float(str(amount_str).replace("￥", ""))
    except:
        return None


def format_time_diff(minutes):
    """格式化时间差"""
    if minutes < 60:
        return f"{int(minutes)}分钟前"
    elif minutes < 1440:
        return f"{int(minutes/60)}小时前"
    else:
        return f"{int(minutes/1440)}天前"


def format_time_diff_detailed(minutes):
    """格式化时间差（详细）"""
    if minutes < 1:
        seconds = int(minutes * 60)
        return f"{seconds}秒"
    elif minutes < 60:
        return f"{int(minutes)}分钟"
    else:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        if mins > 0:
            return f"{hours}小时{mins}分钟"
        else:
            return f"{hours}小时"


def print_comparison(result):
    """打印对比"""
    platform_key = result.get("platform_key", "")
    baseline = get_baseline_record(platform_key)
    
    if baseline:
        last_remaining, last_used, last_requests, last_time, baseline_type = baseline
        try:
            last_time_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00').replace('+00:00', ''))
        except:
            last_time_dt = datetime.now()
        
        time_diff_minutes = (datetime.now() - last_time_dt).total_seconds() / 60
        
        # ========== 当前余额 ==========
        current_remaining = result.get("remaining", "未知")
        current_used = result.get("used", "未知")
        current_requests = result.get("requests", "未知")
        
        # 解析金额
        remaining_val = parse_amount(current_remaining)
        used_val = parse_amount(current_used)
        
        print("## 当前余额")
        print("| 已使用费用 | 剩余额度 | 请求次数 |")
        print("| ---------- | -------- | -------- |")
        print(f"| **${used_val}** | **${remaining_val}** | **{current_requests}** |")
        
        # ========== 与上次对比 ==========
        is_yesterday = baseline_type == "yesterday"
        
        # 余额基准
        if is_yesterday and platform_key == "whalecloud":
            # 跨天：使用系统基准 100 元
            balance_baseline = 100.0
            baseline_label = "（昨日重置）"
        else:
            # 同一天或非 whalecloud：使用上次剩余金额
            balance_baseline = parse_amount(last_remaining) or 100.0
            baseline_label = ""
        
        print()
        print("## 与上次对比")
        
        # 时间间隔
        time_str = format_time_diff_detailed(time_diff_minutes)
        print(f"- **时间间隔**：{time_str}")
        
        if is_yesterday and platform_key == "whalecloud":
            # 跨天：计算实际重置金额 = 已使用 + 剩余
            reset_amount = (used_val or 0) + (remaining_val or 0)
            print(f"- **基准重置**：跨天已重置，基准 ¥{reset_amount:.2f}")
        
        # 已使用费用差（只显示这个，余额变化与已使用是此消彼长的关系）
        last_used_val = parse_amount(last_used)
        if used_val is not None and last_used_val is not None:
            used_diff = used_val - last_used_val
            if used_diff > 0:
                print(f"- **已使用**：+{used_diff:.2f}")
            elif used_diff < 0:
                print(f"- **已使用**：-{abs(used_diff):.2f}")
            else:
                print(f"- **已使用**：不变")
        
        # 调用次数差
        current_requests_num = current_requests
        last_requests_num = last_requests
        if current_requests_num != "未知" and last_requests_num != "未知" and last_requests_num is not None:
            try:
                diff_requests = int(current_requests_num) - int(last_requests_num)
                if diff_requests > 0:
                    print(f"- **调用次数**：+ {diff_requests} 次")
                elif diff_requests < 0:
                    print(f"- **调用次数**：{diff_requests} 次")
                else:
                    print(f"- **调用次数**：不变")
            except:
                pass
    else:
        # 首次查询
        current_remaining = result.get("remaining", "未知")
        current_used = result.get("used", "未知")
        current_requests = result.get("requests", "未知")
        
        remaining_val = parse_amount(current_remaining)
        used_val = parse_amount(current_used)
        
        print("## 当前余额")
        print("| 已使用费用 | 剩余额度 | 请求次数 |")
        print("| ---------- | -------- | -------- |")
        print(f"| **\${used_val}** | **\${remaining_val}** | **{current_requests}** |")
        print()
        print("## 与上次对比")
        print("- **时间间隔**：首次查询")
        print("- **余额**：-")
        print("- **调用**：-")


def run_query(platform):
    """执行查询 - 带进度反馈"""
    result = {
        "platform": f"WhaleCloud Lab ({platform})",
        "platform_key": platform,
        "used": "未知", "remaining": "未知", "requests": "未知",
        "date": datetime.now().strftime("%Y/%m/%d"),
        "timestamp": datetime.now().isoformat(),
        "status": "error"
    }
    
    print("=" * 60)
    print(f"查询 {platform} 余额")
    print("=" * 60)
    print()
    
    # 查询数据（内部自动检测/启动 Chrome）
    print("[查询] 正在查询余额数据...")
    
    query_result = subprocess.run(
        [sys.executable, api_checker_script, platform],
        capture_output=True, text=True, timeout=60
    )
    
    # 显示查询进度
    for line in query_result.stdout.strip().split('\n'):
        if line.strip():
            print(f"     {line}")
    
    # 解析结果
    if "[成功]" in query_result.stdout or "success" in query_result.stdout:
        result["status"] = "success"
        import re
        match = re.search(r'剩余余额：￥([0-9.]+)', query_result.stdout)
        if match:
            result["remaining"] = f"￥{match.group(1)}"
        match = re.search(r'已用金额：￥([0-9.]+)', query_result.stdout)
        if match:
            result["used"] = f"￥{match.group(1)}"
        match = re.search(r'请求次数：(\d+)', query_result.stdout)
        if match:
            result["requests"] = match.group(1)
    
    # 保存结果
    save_result(result)
    print(f"     [完成] 已保存至：{result_file}")
    print()
    
    return result


def main():
    if len(sys.argv) < 2:
        print("用法：python query_balance.py <platform> [platform2] [platform3] ...")
        print("示例：python query_balance.py whalecloud")
        print("      python query_balance.py whalecloud zhipu moonshot")
        sys.exit(1)
    
    platforms = sys.argv[1:]
    all_results = []
    
    for platform in platforms:
        result = run_query(platform)
        all_results.append(result)
    
    # 汇总结果
    success_count = sum(1 for r in all_results if r["status"] == "success")
    
    print("=" * 60)
    if success_count == len(all_results):
        print("[成功] 全部查询完成")
    elif success_count > 0:
        print(f"[部分成功] {success_count}/{len(all_results)} 查询成功")
    else:
        print("[失败] 全部查询失败")
    print("=" * 60)
    
    for result in all_results:
        if result["status"] == "success":
            print(f"   [{result['platform_key']}] 剩余：{result['remaining']} | 已用：{result['used']} | 请求：{result['requests']}次")
        else:
            print(f"   [{result['platform_key']}] 查询失败")
    
    # 对比第一个成功的结果
    first_success = next((r for r in all_results if r["status"] == "success"), None)
    if first_success:
        print()
        print_comparison(first_success)


if __name__ == "__main__":
    main()
