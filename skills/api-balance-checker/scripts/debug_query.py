"""
Debug query
"""
import asyncio
from playwright.async_api import async_playwright

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = await browser.new_page()

        await page.goto("https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")
        await asyncio.sleep(2)

        title = await page.title()
        print(f"Title: {title}")

        await page.screenshot(path="C:/Users/luzhe/Pictures/debug.png")

        # Login if needed
        if "登录" in title:
            print("Need to login")
            await page.fill('input[type="password"]', API_KEY)
            label = await page.query_selector('label')
            if label:
                await label.click()
            await asyncio.sleep(0.5)
            buttons = await page.query_selector_all("button")
            if buttons:
                await buttons[-1].click()
            await asyncio.sleep(5)

        await page.screenshot(path="C:/Users/luzhe/Pictures/debug2.png")

        # Get page text
        text = await page.evaluate("document.body.innerText")
        with open("C:/Users/luzhe/Pictures/debug.txt", "w", encoding="utf-8") as f:
            f.write(text)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
