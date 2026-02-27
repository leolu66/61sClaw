import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 立即刷新输出
import functools
print = functools.partial(print, flush=True)

from playwright.async_api import async_playwright

async def main():
    print('开始执行...')
    async with async_playwright() as p:
        print('连接Chrome...')
        browser = await p.chromium.connect_over_cdp('http://127.0.0.1:9222')
        contexts = browser.contexts
        if contexts and contexts[0].pages:
            page = contexts[0].pages[0]
        else:
            context = await browser.new_context()
            page = await context.new_page()
        
        print('打开智谱AI资源包页面...')
        await page.goto('https://open.bigmodel.cn/finance-center/resource-package/package-mgmt')
        await asyncio.sleep(3)
        
        # 关闭广告弹窗
        try:
            close_buttons = await page.query_selector_all('button, div[role="button"]')
            for btn in close_buttons:
                try:
                    text = await btn.inner_text()
                    if text and ('×' in text or '关闭' in text or '知道了' in text):
                        await btn.click()
                        print('关闭弹窗')
                        await asyncio.sleep(1)
                        break
                except:
                    pass
        except:
            pass
        
        # 点击"我的资源包"
        print('查找页签...')
        all_elements = await page.query_selector_all('*')
        for elem in all_elements:
            try:
                text = await elem.inner_text()
                if text and '我的资源包' in text.strip() and len(text.strip()) < 10:
                    print(f'点击: {text.strip()}')
                    await elem.click()
                    await asyncio.sleep(2)
                    break
            except:
                pass
        
        content = await page.evaluate('''() => document.body.innerText''')
        print('页面内容:')
        print(content[:5000])
        
        print('等待60秒，请查看页面...')
        await asyncio.sleep(60)
        print('完成')

asyncio.run(main())
