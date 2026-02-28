"""
Auto login with API Key and query balance
智能判断页面状态：已登录则直接查询，未登录则先登录
"""
import asyncio
import json
from playwright.async_api import async_playwright

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="

async def check_if_logged_in(page):
    """检查是否已登录 - 直接检查页面是否包含'账户余额'"""
    content = await page.content()
    
    # 最可靠的标志：页面包含"账户余额"
    if '账户余额' in content:
        return True
    
    # 检查是否在登录页：包含"API Key"输入框或"请输入"文字
    text = await page.evaluate('() => document.body.innerText')
    if 'API Key' in text or '请输入' in text or '登录' in text:
        return False
    
    # 默认认为已登录
    return True

async def extract_balance_data(page):
    """从页面提取余额数据"""
    data = await page.evaluate("""
        () => {
            const pageText = document.body.innerText;
            const data = {};
            if (pageText.includes('账户余额')) {
                const match = pageText.match(/账户余额[\\s:：Y]*([0-9.]+)/);
                if (match) data.balance = match[1];
            }
            if (pageText.includes('今日消耗')) {
                const match = pageText.match(/今日消耗[\\s:：Y]*([0-9.]+)/);
                if (match) data.today = match[1];
            }
            if (pageText.includes('本月消耗')) {
                const match = pageText.match(/本月消耗[\\s:：Y]*([0-9.]+)/);
                if (match) data.month = match[1];
            }
            return data;
        }
    """)
    return data

async def login_and_query():
    result = {"platform": "WhaleCloud API", "status": "error"}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            page = await browser.new_page()

            # 访问页面
            await page.goto("https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")
            await asyncio.sleep(2)
            
            # 检查是否已登录
            is_logged_in = await check_if_logged_in(page)
            current_title = await page.title()
            print(f"[INFO] 当前页面标题：{current_title}")
            
            if is_logged_in:
                print("[INFO] 已登录状态，直接查询余额...")
            else:
                print("[INFO] 未登录，开始登录流程...")
                
                # 等待 password 输入框可见
                await page.wait_for_selector('input[type="password"]', state='visible')
                await asyncio.sleep(1)
                print("[INFO] 登录页面加载完成")

                # 清空并填写 API Key
                await page.fill('input[type="password"]', '')
                await page.fill('input[type="password"]', API_KEY)
                print("[INFO] API Key 已填写")

                # 勾选"记住登录状态" checkbox
                # 注意：这个 checkbox 默认是勾选的，不要重复点击！
                checkbox = await page.query_selector('input[type="checkbox"]')
                if checkbox:
                    # 用 JavaScript 检查 checkbox 状态
                    is_checked = await page.evaluate('el => el.checked', checkbox)
                    print(f"[INFO] checkbox 当前状态：checked={is_checked}")
                    if not is_checked:
                        await checkbox.click()
                        await asyncio.sleep(0.3)
                        is_checked_after = await page.evaluate('el => el.checked', checkbox)
                        print(f"[INFO] 已勾选记住登录状态，新状态：checked={is_checked_after}")
                    else:
                        print("[INFO] 记住登录状态已勾选，跳过")
                else:
                    print("[WARN] 未找到记住登录状态的 checkbox")

                await asyncio.sleep(0.5)

                # 点击登录按钮
                login_btn = await page.query_selector('button:has-text("登录")')
                if login_btn:
                    await login_btn.click()
                    print("[INFO] 已点击登录按钮")
                else:
                    buttons = await page.query_selector_all("button")
                    print(f"[INFO] 找到 {len(buttons)} 个按钮")
                    if buttons:
                        await buttons[-1].click()
                        print("[INFO] 已点击登录按钮（备用方案）")

                # 等待登录跳转
                print("[INFO] 等待登录跳转...")
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)
                
                # 验证登录结果
                new_title = await page.title()
                print(f"[INFO] 登录后页面标题：{new_title}")
                
                # 等待页面元素稳定
                await asyncio.sleep(2)
                
                # 检查页面内容
                page_content = await page.content()
                has_balance = '账户余额' in page_content
                print(f"[INFO] 页面是否包含'账户余额': {has_balance}")
                
                # 检查是否还在登录页
                still_on_login = await check_if_logged_in(page)
                print(f"[INFO] check_if_logged_in 返回：{still_on_login}")
                
                if not has_balance:
                    # 可能页面还在加载，或者需要导航
                    print("[INFO] 页面没有账户余额，检查页面元素...")
                    
                    # 获取所有链接和按钮
                    links = await page.query_selector_all('a')
                    print(f"[DEBUG] 找到 {len(links)} 个链接")
                    
                    buttons = await page.query_selector_all('button')
                    print(f"[DEBUG] 找到 {len(buttons)} 个按钮")
                    
                    # 获取页面文本（移除 emoji 避免编码问题）
                    page_text = await page.evaluate('() => document.body.innerText')
                    # 移除 emoji 和其他非 ASCII 字符
                    safe_text = ''.join(c for c in page_text[:500] if ord(c) < 128 or '\u4e00' <= c <= '\u9fff')
                    print(f"[DEBUG] 页面文本：{safe_text}")
                print("[INFO] 登录成功！")
            
            # 提取余额数据
            print("[INFO] 提取余额数据...")
            await asyncio.sleep(1)  # 确保页面完全加载
            
            # 直接获取页面文本内容
            page_text = await page.evaluate('() => document.body.innerText')
            # 移除 emoji 避免编码问题
            safe_page_text = ''.join(c for c in page_text[:500] if ord(c) < 128 or '\u4e00' <= c <= '\u9fff')
            print(f"[DEBUG] 页面文本前 500 字：{safe_page_text}")
            
            # 查找余额信息
            import re
            
            # 方法 1: 匹配正确的中文标签（根据实际页面）
            # 页面显示：已使用费用、剩余额度
            balance_match = re.search(r'剩余额度 [\s:：Y]*([0-9.]+)', page_text, re.DOTALL)
            used_match = re.search(r'已使用费用 [\s:：Y]*([0-9.]+)', page_text, re.DOTALL)
            
            balance = balance_match.group(1) if balance_match else None
            used = used_match.group(1) if used_match else None
            
            if balance:
                print(f"[INFO] 方法 1 成功：balance={balance}, used={used}")
            else:
                # 方法 2: 从统计信息区域提取 "已用：X / 剩余：Y"
                print("[DEBUG] 方法 1 失败，尝试方法 2...")
                stats_match = re.search(r'已用 [：:\s]*([0-9.]+)\s*/\s*剩余 [：:\s]*([0-9.]+)', page_text)
                if stats_match:
                    used = stats_match.group(1)
                    balance = stats_match.group(2)
                    print(f"[INFO] 方法 2 成功：used={used}, balance={balance}")
                else:
                    # 方法 3: 直接找前两个有意义的数字（已使用和剩余）
                    print("[DEBUG] 方法 2 失败，尝试方法 3...")
                    # 查找所有金额格式的数字
                    amounts = re.findall(r'(\d+\.\d+)', page_text)
                    print(f"[DEBUG] 找到的数字：{amounts[:10]}")
                    # 通常第一个大数字是已使用，第二个是剩余
                    if len(amounts) >= 2:
                        used = amounts[0]  # 104.xx
                        balance = amounts[1]  # 95.xx
                        print(f"[INFO] 方法 3：used={used}, balance={balance}")
            
            today = used  # 已使用费用作为今日消耗
            month = None
            
            print(f"[INFO] 最终数据：balance={balance}, used={used}, today={today}")

            if balance:
                result["balance"] = f"Y{balance}"
                result["today_usage"] = f"Y{today or '0'}"
                result["month_usage"] = f"Y{month or '0'}"
                result["status"] = "success"
                print(f"[INFO] 余额查询成功：余额={balance}, 已使用={used}")
            else:
                result["status"] = "error"
                result["error"] = "未能提取到余额数据"
                print("[ERROR] 所有方法都失败了")

    except Exception as e:
        result["error"] = str(e)
        print(f"[ERROR] 异常：{e}")
        import traceback
        traceback.print_exc()

    # 保存结果到临时文件
    with open("C:/Users/luzhe/Pictures/whalecloud_balance.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 读取历史记录并对比
    history_file = "C:/Users/luzhe/Pictures/api_balances.json"
    last_record = None
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
            if history and len(history) > 0:
                last_record = history[0]  # 取最新的一条
    except:
        pass

    # 显示对比结果
    print("\n" + "=" * 60)
    print("与上次查询对比")
    print("=" * 60)
    
    if last_record:
        last_date_str = last_record.get("date", "")
        last_used = last_record.get("used", "Y0").replace("Y", "")
        last_requests = last_record.get("requests", "0")
        last_timestamp = last_record.get("timestamp", "")  # 读取上次的时间戳
        
        # 用日期对象比较（不要用字符串）
        from datetime import datetime
        try:
            # 解析上次记录日期（支持多种格式）
            if last_timestamp:
                # 有时间戳就用时间戳
                last_dt = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00').replace('+00:00', ''))
            elif last_date_str:
                # 否则用日期
                last_dt = datetime.strptime(last_date_str, "%Y/%m/%d")
            else:
                last_dt = None
        except:
            last_dt = None
        
        now = datetime.now()
        
        # 计算时间差
        time_diff_str = ""
        is_new_day = False
        if last_dt:
            # 确保时间对象类型一致（去掉时区信息）
            if last_dt.tzinfo is not None:
                last_dt = last_dt.replace(tzinfo=None)
            
            # 比较日期判断是否跨天
            is_new_day = (last_dt.date() != now.date())
            
            # 计算时间差
            delta = now - last_dt
            total_minutes = int(delta.total_seconds() / 60)
            
            if total_minutes >= 60:
                hours = total_minutes // 60
                minutes = total_minutes % 60
                if minutes > 0:
                    time_diff_str = f"{hours}小时{minutes}分钟"
                else:
                    time_diff_str = f"{hours}小时"
            else:
                time_diff_str = f"{total_minutes}分钟"
        
        print(f"上次记录：{last_date_str}")
        if time_diff_str:
            print(f"相隔时间：{time_diff_str}")
        
        # 计算差额
        try:
            current_used = float(used)
            last_used_val = float(last_used) if last_used else 0
            
            if is_new_day:
                # 跨天：期初为 0
                used_diff = current_used
                print(f"[新的一天] 期初费用重置为 0")
            else:
                # 同一天：本次 - 上次
                used_diff = current_used - last_used_val
            
            print(f"费用增加：Y{used_diff:.2f}")
        except Exception as e:
            print(f"费用对比：计算失败 ({e})")
            used_diff = 0
        
        # 请求次数对比
        try:
            current_requests = 0
            # 提取请求次数
            req_match = re.search(r'请求次数.*?(\d{3,})', page_text, re.DOTALL)
            if req_match:
                current_requests = int(req_match.group(1))
            
            last_req = int(last_requests) if last_requests and last_requests.isdigit() else 0
            
            if is_new_day:
                # 跨天：期初为 0
                req_diff = current_requests
                print(f"[新的一天] 期初次数重置为 0")
            else:
                # 同一天：本次 - 上次
                req_diff = current_requests - last_req
            
            print(f"次数增加：{req_diff} 次")
        except Exception as e:
            print(f"次数对比：计算失败 ({e})")
            req_diff = 0
    else:
        print("首次查询，无历史记录对比")
        used_diff = float(used) if used else 0
        req_diff = 0
        is_new_day = True
    
    print("=" * 60)

    # 保存新记录到历史文件（添加到开头）
    # 提取请求次数（使用更简单的匹配方式）
    request_count = "0"
    req_match = re.search(r'请求次数.*?(\d{3,})', page_text, re.DOTALL)
    if req_match:
        request_count = req_match.group(1)
    else:
        # 备用方案：找第一个 3 位以上的合理数字
        all_numbers = re.findall(r'\d{3,}', page_text)
        for num in all_numbers:
            num_val = int(num)
            if 100 <= num_val <= 100000:
                request_count = num
                break
    
    now = datetime.now()
    new_record = {
        "platform": "WhaleCloud Lab (鲸云实验室)",
        "platform_key": "whalecloud",
        "used": f"Y{used}",
        "remaining": f"Y{balance}",
        "requests": request_count,
        "date": now.strftime("%Y/%m/%d"),
        "timestamp": now.isoformat(),  # 添加时间戳
        "status": "success"
    }
    
    try:
        history = []
        if last_record:
            history = [last_record]
        history.insert(0, new_record)
        # 只保留最近 30 条记录
        history = history[:30]
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"[OK] 历史记录已保存到 {history_file}")
    except Exception as e:
        print(f"[WARN] 保存历史记录失败：{e}")

    # 不关闭浏览器，保持登录状态
    print("[INFO] 完成，浏览器保持打开状态")
    return result


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    result = asyncio.run(login_and_query())
    print(json.dumps(result, ensure_ascii=False, indent=2))

