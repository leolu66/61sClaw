"""
Debug - take screenshot and save page text
"""
import asyncio
from playwright.async_api import async_playwright

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = await browser.new_page()

        await page.goto("https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")
        await asyncio.sleep(3)

        # Take screenshot
        await page.screenshot(path="C:/Users/luzhe/Pictures/test_dashboard.png")

        # Get page text
        text = await page.evaluate("document.body.innerText")

        with open("C:/Users/luzhe/Pictures/test_dashboard.txt", "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Page text length: {len(text)}")
        print("Saved to file")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
