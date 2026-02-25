# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import os

# 从环境变量读取 API Key
api_key = os.environ.get("XTC_WHALECLOUD_API_KEY", "")
if not api_key:
    raise ValueError('请设置环境变量 XTC_WHALECLOUD_API_KEY')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # 用可见模式
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    
    page.goto('https://lab.iwhalecloud.com/gpt-proxy/console/dashboard')
    page.evaluate(f'localStorage.setItem("auth_token", "{api_key}")')
    page.reload()
    page.wait_for_timeout(5000)
    
    # 截图
    page.screenshot(path='C:/Users/luzhe/.openclaw/workspace-main/whale_page.png', full_page=True)
    print("截图保存到 whale_page.png")
    
    # 等待用户查看
    page.wait_for_timeout(30000)
    
    browser.close()
