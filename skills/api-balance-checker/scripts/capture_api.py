"""
API Balance Checker - 捕获API响应
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def capture_api_responses():
    """捕获API响应"""
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = await browser.new_page()

        api_responses = []

        async def handle_response(response):
            url = response.url
            if "/api/" in url or "/v1/" in url:
                try:
                    if response.status < 400:
                        body = await response.text()
                        api_responses.append({
                            "url": url,
                            "status": response.status,
                            "body": body[:500] if body else ""
                        })
                except:
                    pass

        page.on("response", handle_response)

        # 访问页面
        print("正在访问页面...")
        await page.goto("https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")

        # 等待一段时间让API调用完成
        await asyncio.sleep(8)

        print("\n=== 捕获到的API响应 ===")
        for resp in api_responses:
            print(f"\n{resp['status']} {resp['url']}")
            if resp['body']:
                print(f"  Body: {resp['body'][:200]}...")

        # 获取页面可见文本
        print("\n=== 页面内容 ===")
        content = await page.evaluate("document.body.innerText")
        print(content[:1000])

        await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_api_responses())
