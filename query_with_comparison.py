# -*- coding: utf-8 -*-
"""
查询鲸云实验室余额，包含跨天对比
- 如果已登录，直接查询
- 如果在登录界面，自动登录
- 展示与上次记录的对比（含跨天判断）
"""
import asyncio
import sys
import io
import sqlite3
import os
from datetime import datetime
from playwright.async_api import async_playwright

# 设置UTF-8编码输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="
DB_PATH = os.path.expanduser("~/.api_balance_history.db")

# ==================== 数据库操作 ====================

def init_database():
    """初始化SQLite数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            platform_name TEXT,
            remaining REAL,
            used REAL,
            requests INTEGER,
            packages TEXT,
            query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_record(platform, platform_name, remaining, used, requests=None, packages=None):
    """保存查询记录到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    beijing_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO balance_history (platform, platform_name, remaining, used, requests, packages, query_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (platform, platform_name, remaining, used, requests, None, beijing_time))
    conn.commit()
    conn.close()

def get_last_record(platform):
    """获取指定平台的上次查询记录（倒数第2条）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT remaining, used, requests, query_time
        FROM balance_history
        WHERE platform = ?
        ORDER BY query_time DESC
        LIMIT 1 OFFSET 1
    ''', (platform,))
    result = cursor.fetchone()
    conn.close()
    return result

def parse_amount(amount_str):
    """解析金额字符串为数值"""
    if not amount_str or amount_str == '未知':
        return None
    try:
        cleaned = str(amount_str).replace('¥', '').replace('￥', '').replace(',', '').strip()
        return float(cleaned)
    except:
        return None

def format_time_diff(minutes):
    """格式化时间差"""
    if minutes < 1:
        return "刚刚"
    elif minutes < 60:
        return f"{int(minutes)}分钟前"
    elif minutes < 1440:
        hours = minutes / 60
        return f"{int(hours)}小时前"
    else:
        days = minutes / 1440
        return f"{int(days)}天前"

def print_comparison(result):
    """打印与上次查询的对比（考虑鲸云实验室每日0点自动充值到100）"""
    platform_key = "whalecloud"

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
        current_remaining = result.get("remaining")
        current_used = result.get("used")

        # 判断是否跨天（上次记录的日期与当前日期不同）
        last_date = last_time_dt.date()
        current_date = current_time.date()
        is_different_day = (last_date != current_date)

        # 鲸云实验室特殊逻辑：每日0点后自动充值到100
        # 如果上次记录是前一天，则基准余额应为100（自动充值）
        baseline_remaining = 100.0 if is_different_day else last_remaining

        print(f"\n  [DATA] 与上次对比 ({time_diff_str}):")

        # 如果是鲸云实验室且跨天，说明系统已自动充值
        if is_different_day:
            print(f"     [INFO] 系统自动充值: 前一日记录，基准余额 ¥100")

        # 余额变化（相对于基准余额）
        if current_remaining is not None and baseline_remaining is not None:
            remaining_diff = current_remaining - baseline_remaining
            if remaining_diff < 0:
                print(f"     余额减少: ¥{abs(remaining_diff):.2f} (¥{baseline_remaining:.2f} → ¥{current_remaining:.2f})")
            elif remaining_diff > 0:
                print(f"     余额增加: ¥{remaining_diff:.2f} (¥{baseline_remaining:.2f} → ¥{current_remaining:.2f})")
            else:
                print(f"     余额不变: ¥{current_remaining:.2f}")

        # 使用量变化
        if current_used is not None and last_used is not None:
            used_diff = current_used - last_used
            if used_diff > 0:
                if is_different_day:
                    print(f"     今日消耗: ¥{used_diff:.2f} (系统充值后)")
                else:
                    print(f"     使用增加: ¥{used_diff:.2f} (¥{last_used:.2f} → ¥{current_used:.2f})")
            elif used_diff < 0:
                if is_different_day:
                    print(f"     余额重置: 系统已自动充值")
                else:
                    print(f"     使用减少: ¥{abs(used_diff):.2f}")

        # 请求次数变化
        current_requests = result.get("requests")
        if current_requests and last_requests is not None:
            req_diff = current_requests - last_requests
            if req_diff > 0:
                if is_different_day:
                    print(f"     今日请求: {req_diff}次 (系统充值后)")
                else:
                    print(f"     请求增加: {req_diff}次 ({last_requests} → {current_requests})")
    else:
        print(f"\n  [INFO] 首次查询，无历史记录对比")

# ==================== 主函数 ====================

async def check_and_login():
    """检查登录状态并自动登录"""
    # 初始化数据库
    init_database()

    async with async_playwright() as p:
        # 连接到已有的Chrome
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            print("[OK] 已连接到Chrome浏览器")
        except Exception as e:
            print(f"[ERROR] 无法连接到Chrome: {e}")
            return

        # 创建新页面
        context = browser.contexts[0]
        page = await context.new_page()

        # 访问鲸云实验室
        print("[INFO] 正在访问鲸云实验室...")
        await page.goto("https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")
        await asyncio.sleep(3)

        # 检查页面状态
        page_text = await page.evaluate("() => document.body.innerText")

        # 判断是否需要登录
        if '密码' in page_text or 'API Key' in page_text or 'ailab' in page_text:
            print("[INFO] 检测到登录界面，开始自动登录...")

            # 填入API Key
            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(API_KEY)
                print("[OK] API Key已填入")

            # 勾选同意协议
            checkbox = await page.query_selector('input[type="checkbox"]')
            if checkbox:
                is_checked = await checkbox.is_checked()
                if not is_checked:
                    await checkbox.click()
                    print("[OK] 已勾选同意协议")

            # 点击登录按钮
            await asyncio.sleep(1)
            buttons = await page.query_selector_all('button')
            if buttons:
                await buttons[-1].click()
                print("[OK] 登录按钮已点击")

            # 等待登录完成
            await asyncio.sleep(5)
            print("[INFO] 等待登录完成...")

            # 验证登录状态
            page_text = await page.evaluate("() => document.body.innerText")
            if '已使用费用' in page_text or '剩余额度' in page_text or '余额' in page_text:
                print("[OK] 登录成功！")
            else:
                print("[WARN] 登录状态不明确，请手动检查")
        else:
            print("[OK] 已登录，无需重复登录")

        # 提取余额数据
        data = await page.evaluate("""
            () => {
                const pageText = document.body.innerText;
                const data = {};

                if (pageText.includes('已使用费用')) {
                    const match = pageText.match(/已使用费用[\\s:：¥]*([0-9.]+)/);
                    if (match) data.used = match[1];
                }

                if (pageText.includes('剩余额度')) {
                    const match = pageText.match(/剩余额度[\\s:：¥]*([0-9.]+)/);
                    if (match) data.remaining = match[1];
                }

                if (pageText.includes('请求次数')) {
                    const match = pageText.match(/请求次数[\\s:：]*(\\d+)/);
                    if (match) data.requests = match[1];
                }

                return data;
            }
        """)

        result = {
            "remaining": float(data.get('remaining', 0)) if data.get('remaining') else None,
            "used": float(data.get('used', 0)) if data.get('used') else None,
            "requests": int(data.get('requests', 0)) if data.get('requests') else None
        }

        if result["remaining"] is not None:
            # 保存记录
            save_record("whalecloud", "浩鲸Lab (WhaleCloud)",
                      result["remaining"], result["used"], result["requests"])

            print("\n" + "="*60)
            print("[DATA] 鲸云实验室余额")
            print("="*60)
            print(f"已使用费用: ¥{result['used']:.2f}")
            print(f"剩余额度: ¥{result['remaining']:.2f}")
            print(f"请求次数: {result['requests']}")

            # 打印对比
            print_comparison(result)

            print("="*60)
            print(f"[INFO] 数据已保存到: {DB_PATH}")
        else:
            print("[WARN] 未能提取到余额数据")

        # 不关闭浏览器，保持连接
        # await browser.close()

if __name__ == "__main__":
    asyncio.run(check_and_login())
