"""
API Balance Checker - 查询WhaleCloud API余额
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def explore_whalecloud_api():
    """探索WhaleCloud的API接口"""
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = await browser.new_page()

        # 收集所有API请求
        api_calls = []

        async def handle_request(request):
            if "api" in request.url.lower() or "whalecloud" in request.url.lower():
                api_calls.append({
                    "url": request.url,
                    "method": request.method,
                    "resource_type": request.resource_type
                })

        page.on("request", handle_request)

        # 访问页面
        await page.goto("https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")
        await asyncio.sleep(5)

        print("=== 捕获到的API请求 ===")
        for call in api_calls:
            print(f"{call['method']} {call['url']}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(explore_whalecloud_api())
