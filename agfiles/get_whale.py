# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import os
import re

# 先用token登录（从环境变量读取）
api_key = os.environ.get("XTC_WHALECLOUD_API_KEY", "")
if not api_key:
    raise ValueError('请设置环境变量 XTC_WHALECLOUD_API_KEY')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    # 直接设置localStorage模拟登录
    page.goto('https://lab.iwhalecloud.com/gpt-proxy/console/dashboard')
    page.evaluate(f'localStorage.setItem("auth_token", "{api_key}")')
    page.reload()
    page.wait_for_timeout(3000)
    
    # 获取页面中所有包含金额的元素
    text = page.content()
    
    # 提取金额
    pattern = r'(\d+\.\d{2})'
    amounts = re.findall(pattern, text)
    
    # 找包含"剩余"或"余额"附近的金额
    import re
    # 查找"剩余"后面的金额
    remaining_match = re.search(r'剩余[：:]\s*(\d+\.\d{2})', text)
    used_match = re.search(r'已使用[：:]\s*(\d+\.\d{2})', text)
    
    print("=== 浩鲸Lab 余额查询 ===")
    if used_match:
        print(f"已使用: ¥{used_match.group(1)}")
    if remaining_match:
        print(f"剩余: ¥{remaining_match.group(1)}")
    
    # 打印所有找到的金额（去重）
    unique_amounts = sorted(set(amounts), key=lambda x: float(x), reverse=True)
    print(f"\n页面中的金额: {unique_amounts[:10]}")
    
    browser.close()
