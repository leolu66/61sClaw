"""
Take screenshot of WhaleCloud dashboard
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = await browser.new_page()

        await page.goto("https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")
        await asyncio.sleep(3)

        # Get page title
        title = await page.title()
        print(f"Page title: {title}")

        # Get page content
        content = await page.content()

        # Save screenshot
        await page.screenshot(path="C:/Users/luzhe/Pictures/whalecloud_dashboard.png")
        print("Screenshot saved!")

        # Try to extract visible text
        try:
            text = await page.evaluate("document.body.innerText")
            with open("C:/Users/luzhe/Pictures/whalecloud_text.txt", "w", encoding="utf-8") as f:
                f.write(text)
            print("Text saved!")
        except Exception as e:
            print(f"Error getting text: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
