# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import os
import re

# 从环境变量读取 API Key
api_key = os.environ.get("XTC_WHALECLOUD_API_KEY", "")
if not api_key:
    raise ValueError('请设置环境变量 XTC_WHALECLOUD_API_KEY')

p = sync_playwright().start()
b = p.chromium.launch(headless=True)
page = b.new_page()

page.goto('https://lab.iwhalecloud.com/gpt-proxy/console/dashboard')

# 设置localStorage
page.evaluate(f'localStorage.setItem("auth_token", "{api_key}")')
page.reload()

# 等待页面加载
page.wait_for_timeout(2000)

content = page.content()

# 写入文件
with open('whale_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
p.stop()
