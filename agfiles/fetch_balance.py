# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import re
import json
import os

# 从环境变量读取 API Key
api_key = os.environ.get("XTC_WHALECLOUD_API_KEY", "")
if not api_key:
    raise ValueError('请设置环境变量 XTC_WHALECLOUD_API_KEY')

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    
    page.goto('https://lab.iwhalecloud.com/gpt-proxy/console/dashboard')
    page.evaluate(f'localStorage.setItem("auth_token", "{api_key}")')
    page.reload()
    page.wait_for_timeout(3000)
    
    # 获取页面数据
    amounts = page.evaluate('''
        () => {
            const results = [];
            const elements = document.querySelectorAll('span, div, p');
            for (let el of elements) {
                const text = el.textContent;
                if (/\\d+\\.\\d{2}/.test(text) && (text.includes('¥') || text.includes('元'))) {
                    results.push(text.trim());
                }
            }
            return results;
        }
    ''')
    print("Amounts found:", amounts)
    
    # 尝试获取Alpine数据
    alpine_data = page.evaluate('''
        () => {
            const nav = document.querySelector('[x-data]');
            if (nav && nav.__x) {
                return JSON.stringify(nav.__x.$data);
            }
            return null;
        }
    ''')
    print("Alpine data:", alpine_data[:500] if alpine_data else "None")
    
    b.close()
