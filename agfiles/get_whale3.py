# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import re
import sys
import io
import os

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
    
    # 尝试获取金额
    pattern = r'(\d+\.\d{2})元'
    amounts = re.findall(pattern, full_text)
    
    print("=== 浩鲸Lab 余额 ===")
    print(f"找到的金额: {amounts}")
    
    # 打印相关行
    lines = full_text.split('\n')
    for line in lines:
        if '元' in line or '余额' in line or '剩余' in line or '已使用' in line:
            print(line)
    
    browser.close()
