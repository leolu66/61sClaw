"""
Debug - check page state
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

        # Check for login form
        password_input = await page.query_selector('input[type="password"]')
        if password_input:
            print("Found password input - need to login")

            # Fill password
            await password_input.fill(API_KEY)
            print("Filled API key")

            # Check checkbox
            checkbox = await page.query_selector('input[type="checkbox"]')
            if checkbox:
                await checkbox.click()
                print("Clicked checkbox")

            # Wait a bit
            await asyncio.sleep(1)

            # Find and click submit button
            # Try different selectors
            button = await page.query_selector('button.ant-btn-primary')
            if not button:
                button = await page.query_selector('button[type="submit"]')
            if not button:
                buttons = await page.query_selector_all('button')
                button = buttons[-1] if buttons else None

            if button:
                await button.click()
                print("Clicked submit button")

            # Wait for navigation
            await asyncio.sleep(8)

        # Take screenshot
        await page.screenshot(path="C:/Users/luzhe/Pictures/final_debug.png")

        # Get page text
        text = await page.evaluate("document.body.innerText")
        with open("C:/Users/luzhe/Pictures/final_debug.txt", "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Page text length: {len(text)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
