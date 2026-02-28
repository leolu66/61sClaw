"""
Debug login - check checkbox state
"""
import asyncio
from playwright.async_api import async_playwright

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="

async def debug_login():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = await browser.new_page()

        await page.goto("https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")
        await asyncio.sleep(3)

        # Fill API key
        await page.fill('input[type="password"]', API_KEY)
        print("API Key filled")

        # Get checkbox element
        checkbox = await page.query_selector('input[type="checkbox"]')
        print(f"Checkbox element: {checkbox}")

        # Check if checkbox is checked before
        is_checked_before = await checkbox.is_checked() if checkbox else False
        print(f"Checked before: {is_checked_before}")

        # Try clicking the label
        label = await page.query_selector('label')
        if label:
            await label.click()
            print("Clicked label")
            await asyncio.sleep(1)

        # Check again
        is_checked_after = await checkbox.is_checked() if checkbox else False
        print(f"Checked after: {is_checked_after}")

        # Take screenshot
        await page.screenshot(path="C:/Users/luzhe/Pictures/debug_checkbox.png")

        # Try clicking directly on the checkbox
        await checkbox.click(force=True)
        print("Clicked checkbox with force")
        await asyncio.sleep(1)

        is_checked_final = await checkbox.is_checked() if checkbox else False
        print(f"Checked final: {is_checked_final}")

        await page.screenshot(path="C:/Users/luzhe/Pictures/debug_checkbox2.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_login())
