import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import functools
print = functools.partial(print, flush=True)

from playwright.async_api import async_playwright

async def main():
    print('开始...')
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://127.0.0.1:9222')
        contexts = browser.contexts
        if contexts and contexts[0].pages:
            page = contexts[0].pages[0]
        else:
            context = await browser.new_context()
            page = await context.new_page()
        
        await page.goto('https://open.bigmodel.cn/finance-center/resource-package/package-mgmt')
        await asyncio.sleep(3)
        
        # 关闭弹窗
        try:
            close_buttons = await page.query_selector_all('button, div[role="button"]')
            for btn in close_buttons:
                try:
                    text = await btn.inner_text()
                    if text and ('×' in text or '关闭' in text or '知道了' in text):
                        await btn.click()
                        await asyncio.sleep(1)
                        break
                except:
                    pass
        except:
            pass
        
        # 点击"我的资源包"
        all_elements = await page.query_selector_all('*')
        for elem in all_elements:
            try:
                text = await elem.inner_text()
                if text and '我的资源包' in text.strip() and len(text.strip()) < 10:
                    await elem.click()
                    await asyncio.sleep(2)
                    break
            except:
                pass
        
        # 获取表格数据
        content = await page.evaluate('''() => {
            const result = [];
            
            // 查找所有表格行
            const rows = document.querySelectorAll('tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td, th');
                if (cells.length > 0) {
                    let rowData = [];
                    cells.forEach(cell => rowData.push(cell.innerText.trim()));
                    if (rowData.some(t => t.includes('资源包') || t.includes('tokens') || t.includes('次'))) {
                        result.push('Row: ' + rowData.join(' | '));
                    }
                }
            });
            
            return result.join('\\n');
        }''')
        print('表格内容:')
        print(content[:6000])
        
        print('等待20秒...')
        await asyncio.sleep(20)

asyncio.run(main())
