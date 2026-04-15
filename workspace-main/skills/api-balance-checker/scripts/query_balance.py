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
    
    # 如果今天有记录，返回今天最新的一条（对比基准）
    if today_records:
        record = today_records[0]  # 遍历是从新到旧，0 是最新的
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


def format_comparison_json(result):
    """格式化对比信息为 JSON"""
    # 使用保存时记录的对比基准（避免读到自己的情况）
    baseline = result.get("_baseline")
    
    comparison = {
        "time_diff_minutes": 0,
        "used_diff": "0",
        "requests_diff": 0,
        "is_first_query": False,
        "baseline_type": None
    }
    
    if baseline:
        last_remaining, last_used, last_requests, last_time, baseline_type = baseline
        try:
            last_time_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00').replace('+00:00', ''))
        except:
            last_time_dt = datetime.now()
        
        time_diff_minutes = (datetime.now() - last_time_dt).total_seconds() / 60
        comparison["time_diff_minutes"] = int(time_diff_minutes)
        comparison["baseline_type"] = baseline_type
        
        # 已使用费用差
        current_used = parse_amount(result.get("used", ""))
        last_used_val = parse_amount(last_used)
        if current_used is not None and last_used_val is not None:
            used_diff = current_used - last_used_val
            comparison["used_diff"] = f"+{used_diff:.2f}" if used_diff >= 0 else f"{used_diff:.2f}"
        
        # 调用次数差
        current_requests = result.get("requests", "未知")
        if current_requests != "未知" and last_requests != "未知" and last_requests is not None:
            try:
                diff_requests = int(current_requests) - int(last_requests)
                comparison["requests_diff"] = diff_requests
            except:
                pass
    else:
        comparison["is_first_query"] = True
    
    return comparison


def print_comparison(result):
    """打印对比 - 输出 JSON 格式供大模型格式化"""
    comparison = format_comparison_json(result)
    
    output = {
        "platform": result.get("platform", ""),
        "platform_key": result.get("platform_key", ""),
        "used": result.get("used", "未知"),
        "remaining": result.get("remaining", "未知"),
        "requests": result.get("requests", "未知"),
        "date": result.get("date", ""),
        "timestamp": result.get("timestamp", ""),
        "status": result.get("status", "error"),
        "last_query": comparison
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


def run_query(platform):
    """执行查询 - 进度输出到 stderr"""
    result = {
        "platform": f"WhaleCloud Lab ({platform})",
        "platform_key": platform,
        "used": "未知", "remaining": "未知", "requests": "未知",
        "date": datetime.now().strftime("%Y/%m/%d"),
        "timestamp": datetime.now().isoformat(),
        "status": "error"
    }
    
    # 进度输出到 stderr（不污染 JSON 输出）
    sys.stderr.write(f"Querying {platform}...\n")
    sys.stderr.flush()
    
    # 查询数据（内部自动检测/启动 Chrome）
    
    query_result = subprocess.run(
        [sys.executable, api_checker_script, platform],
        capture_output=True, text=True, timeout=60
    )
    
    # 显示查询进度（到 stderr）
    for line in query_result.stdout.strip().split('\n'):
        if line.strip():
            sys.stderr.write(f"  {line}\n")
            sys.stderr.flush()
    
    # 解析结果
    if "[成功]" in query_result.stdout or "success" in query_result.stdout:
        result["status"] = "success"
        import re
        match = re.search(r'剩余余额：￥([0-9.]+)', query_result.stdout)
        if match:
            result["remaining"] = match.group(1)  # 纯数字，去掉 ￥ 符号
        match = re.search(r'已用金额：￥([0-9.]+)', query_result.stdout)
        if match:
            result["used"] = match.group(1)  # 纯数字
        match = re.search(r'请求次数：(\d+)', query_result.stdout)
        if match:
            result["requests"] = match.group(1)
    
    # 先获取对比基准（保存之前）
    baseline = get_baseline_record(platform)
    result["_baseline"] = baseline
    
    # 保存结果
    save_result(result)
    sys.stderr.write(f"  Saved to {result_file}\n\n")
    sys.stderr.flush()
    
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
    
    # 输出 JSON 格式（供大模型格式化展示）
    success_results = [r for r in all_results if r["status"] == "success"]
    
    if success_results:
        # 输出第一个成功结果的完整 JSON
        print_comparison(success_results[0])
    else:
        # 全部失败
        print(json.dumps({
            "status": "error",
            "message": "All queries failed",
            "results": all_results
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
