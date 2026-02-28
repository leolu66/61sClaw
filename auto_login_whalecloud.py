# -*- coding: utf-8 -*-
"""
自动登录鲸云实验室
- 如果已登录，直接查询余额
- 如果在登录界面，自动填入API Key并登录
"""
import asyncio
import sys
import io
from playwright.async_api import async_playwright

# 设置UTF-8编码输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="

async def check_and_login():
    """检查登录状态并自动登录"""
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
                await page.screenshot(path="C:/Users/luzhe/Pictures/whalecloud_after_login.png")
                print("[INFO] 截图已保存")
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

        if data:
            print("\n" + "="*60)
            print("[DATA] 鲸云实验室余额")
            print("="*60)
            print(f"已使用费用: ¥{data.get('used', '未知')}")
            print(f"剩余额度: ¥{data.get('remaining', '未知')}")
            print(f"请求次数: {data.get('requests', '未知')}")
            print("="*60)
        else:
            print("[WARN] 未能提取到余额数据")

        # 保持页面打开，方便查看
        print("\n[INFO] 页面已保持打开状态")
        print("   如需继续查询其他平台，请保持此标签页登录状态")

        # 不关闭浏览器，保持连接
        # await browser.close()

if __name__ == "__main__":
    asyncio.run(check_and_login())
