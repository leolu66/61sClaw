# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import os
import re

# 从环境变量读取 API Key
api_key = os.environ.get("XTC_WHALECLOUD_API_KEY", "")
if not api_key:
    raise ValueError('请设置环境变量 XTC_WHALECLOUD_API_KEY')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    page.goto('https://lab.iwhalecloud.com/gpt-proxy/console/dashboard')
    page.evaluate(f'localStorage.setItem("auth_token", "{api_key}")')
    page.reload()
    page.wait_for_timeout(5000)
    
    # 等待页面完全加载
    page.wait_for_load_state('networkidle')
    
    # 获取完整页面文本
    full_text = page.evaluate('document.body.innerText')
    
    print("=== 页面文本内容 ===")
    print(full_text[:3000])
    
    # 尝试获取金额
    pattern = r'(\d+\.\d{2})元'
    amounts = re.findall(pattern, full_text)
    print(f"\n找到的金额: {amounts}")
    
    browser.close()
