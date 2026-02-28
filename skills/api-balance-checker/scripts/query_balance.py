def print_comparison(result):
    """打印与上次查询的对比（考虑鲸云实验室每日0点自动充值到100）"""
    platform_key = result.get("platform_key", "")
    platform_name = result.get("platform", "")

    # 获取上次记录
    last_record = get_last_record(platform_key)

    if last_record:
        last_remaining, last_used, last_requests, last_time = last_record
        current_time = datetime.now()
        last_time_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00').replace('+00:00', ''))

        # 计算时间差（分钟）
        time_diff_minutes = (current_time - last_time_dt).total_seconds() / 60
        time_diff_str = format_time_diff(time_diff_minutes)

        # 解析当前值
        current_remaining = parse_amount(result.get("remaining"))
        current_used = parse_amount(result.get("used"))

        # 判断是否跨天（上次记录的日期与当前日期不同）
        last_date = last_time_dt.date()
        current_date = current_time.date()
        is_different_day = (last_date != current_date)

        # 鲸云实验室特殊逻辑：每日0点后自动充值到100
        # 如果上次记录是前一天，则基准余额应为100（自动充值）
        baseline_remaining = 100.0 if is_different_day and platform_key == "whalecloud" else last_remaining

        print(f"\n  📊 与上次对比 ({time_diff_str}):")

        # 如果是鲸云实验室且跨天，说明系统已自动充值
        if platform_key == "whalecloud" and is_different_day:
            print(f"     [系统自动充值: 前一日记录，基准余额 ¥100]")

        # 余额变化（相对于基准余额）
        if current_remaining is not None and baseline_remaining is not None:
            remaining_diff = current_remaining - baseline_remaining
            if remaining_diff < 0:
                print(f"     余额减少: ¥{abs(remaining_diff):.2f} (¥{baseline_remaining:.2f} → ¥{current_remaining:.2f})")
            elif remaining_diff > 0:
                print(f"     余额增加: ¥{remaining_diff:.2f} (¥{baseline_remaining:.2f} → ¥{current_remaining:.2f})")
            else:
                print(f"     余额不变: ¥{current_remaining:.2f}")

        # 使用量变化（如果是跨天，显示累计消耗）
        if current_used is not None and last_used is not None:
            used_diff = current_used - last_used
            if used_diff > 0:
                if is_different_day and platform_key == "whalecloud":
                    print(f"     今日消耗: ¥{used_diff:.2f} (系统充值后)")
                else:
                    print(f"     使用增加: ¥{used_diff:.2f} (¥{last_used:.2f} → ¥{current_used:.2f})")
            elif used_diff < 0:
                if is_different_day and platform_key == "whalecloud":
                    print(f"     余额重置: 系统已自动充值")
                else:
                    print(f"     使用减少: ¥{abs(used_diff):.2f}")

        # 请求次数变化
        current_requests = result.get("requests")
        if current_requests != '未知' and last_requests is not None:
            try:
                current_req_val = int(current_requests)
                req_diff = current_req_val - last_requests
                if req_diff > 0:
                    if is_different_day and platform_key == "whalecloud":
                        print(f"     今日请求: {req_diff}次 (系统充值后)")
                    else:
                        print(f"     请求增加: {req_diff}次 ({last_requests} → {current_req_val})")
            except:
                pass
    else:
        print(f"\n  📊 首次查询，无历史记录对比")




