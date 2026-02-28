"""
API Balance Checker - 带截图和API Key查询
"""
import asyncio
import json
from playwright.async_api import async_playwright

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="

async def check_balance_with_key():
    """使用API Key查询余额"""
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = await browser.new_page()

        # 访问页面
        await page.goto("https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")
        await asyncio.sleep(3)

        # 截图
        await page.screenshot(path="C:/Users/luzhe/Pictures/whalecloud_status.png")
        print("截图已保存")

        # 获取cookies
        cookies = await context.cookies() if 'context' in locals() else []
        print(f"Cookies: {len(cookies)}")

        await browser.close()

async def try_api_endpoints():
    """尝试不同的API端点"""
    import requests

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    endpoints = [
        "https://lab.iwhalecloud.com/gpt-proxy/api/user/info",
        "https://lab.iwhalecloud.com/gpt-proxy/api/v1/user/info",
        "https://lab.iwhalecloud.com/gpt-proxy/api/v1/balance",
        "https://lab.iwhalecloud.com/gpt-proxy/api/account/info",
        "https://lab.iwhalecloud.com/gpt-proxy/api/balance",
        "https://lab.iwhalecloud.com/gpt-proxy/console/api/user/info",
        "https://lab.iwhalecloud.com/api/user/info",
    ]

    for url in endpoints:
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            print(f"{resp.status_code} {url}")
            if resp.status_code == 200:
                print(f"  Response: {resp.text[:200]}")
        except Exception as e:
            print(f"Error {url}: {e}")

if __name__ == "__main__":
    # 先尝试API端点
    print("=== 尝试API端点 ===")
    try:
        asyncio.run(try_api_endpoints())
    except:
        pass

    # 然后获取截图
    print("\n=== 获取页面截图 ===")
    asyncio.run(check_balance_with_key())
