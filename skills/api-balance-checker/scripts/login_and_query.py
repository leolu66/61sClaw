"""
Login with API Key and query balance
"""
import asyncio
from playwright.async_api import async_playwright

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="

async def login_and_query():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = await browser.new_page()

        # Go to login page
        await page.goto("https://lab.iwhalecloud.com/gpt-proxy/console/dashboard")
        await asyncio.sleep(3)

        # Take screenshot to see the login form
        await page.screenshot(path="C:/Users/luzhe/Pictures/login_page.png")
        print("Login page screenshot saved!")

        # Try to find API key input field
        # Look for input fields
        inputs = await page.query_selector_all("input")
        print(f"Found {len(inputs)} input fields")

        for i, inp in enumerate(inputs):
            try:
                placeholder = await inp.get_attribute("placeholder")
                id_val = await inp.get_attribute("id")
                name_val = await inp.get_attribute("name")
                type_val = await inp.get_attribute("type")
                print(f"Input {i}: placeholder={placeholder}, id={id_val}, name={name_val}, type={type_val}")
            except:
                pass

        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_and_query())
