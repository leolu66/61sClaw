#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能网页内容抓取工具
自动选择web_fetch或playwright模式抓取网页内容
"""
import argparse
import sys
import os
import json
import time
from pathlib import Path
import requests
from urllib.parse import urlparse

# 修复Windows控制台中文输出
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def try_web_fetch(url, format_type='markdown'):
    """尝试使用web_fetch工具获取内容"""
    try:
        # 调用openclaw的web_fetch工具
        import subprocess
        result = subprocess.run(
            ['openclaw', 'web', 'fetch', url, '--format', format_type],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            content = result.stdout.strip()
            # 检查内容是否有效（不是空的，也不是反爬提示）
            if content and len(content) > 100 and '反爬' not in content and '访问验证' not in content and '请输入验证码' not in content:
                return True, content
    except Exception as e:
        print(f"[web_fetch] 尝试失败: {str(e)}", file=sys.stderr)
    
    return False, None

def fetch_with_playwright(url, format_type='markdown', wait_time=3, cookie=None, click_selector=None, scroll=False):
    """使用playwright抓取网页内容"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 缺少playwright依赖，请先安装：pip install playwright && playwright install chromium", file=sys.stderr)
        return False, None
    
    try:
        with sync_playwright() as p:
            # 启动浏览器，无头模式
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # 设置Cookie
            if cookie:
                parsed_url = urlparse(url)
                context.add_cookies([{
                    'name': k.strip(),
                    'value': v.strip(),
                    'domain': parsed_url.netloc,
                    'path': '/'
                } for k, v in [c.split('=', 1) for c in cookie.split(';')]])
            
            page = context.new_page()
            
            # 访问页面
            page.goto(url, timeout=30000)
            
            # 等待加载
            time.sleep(wait_time)
            
            # 点击指定元素（比如接受Cookie、关闭弹窗等）
            if click_selector:
                try:
                    page.click(click_selector, timeout=5000)
                    time.sleep(1)
                except Exception as e:
                    print(f"⚠️ 点击元素失败: {str(e)}", file=sys.stderr)
            
            # 滚动到底部加载更多内容
            if scroll:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                # 多次滚动处理懒加载
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
            
            # 获取内容
            html_content = page.content()
            
            browser.close()
            
            # 转换格式
            if format_type == 'html':
                return True, html_content
            elif format_type == 'text':
                # 提取纯文本
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
                return True, text
            else: # markdown
                # 转换为markdown
                try:
                    import markdownify
                    markdown_content = markdownify.markdownify(html_content, heading_style="ATX")
                    return True, markdown_content
                except ImportError:
                    print("⚠️ 缺少markdownify依赖，返回HTML格式", file=sys.stderr)
                    return True, html_content
    
    except Exception as e:
        print(f"[playwright] 抓取失败: {str(e)}", file=sys.stderr)
        return False, None

def main():
    parser = argparse.ArgumentParser(description='智能网页内容抓取工具')
    parser.add_argument('url', help='要抓取的网页URL')
    parser.add_argument('--mode', choices=['auto', 'web_fetch', 'playwright'], default='auto', help='抓取模式，默认auto自动选择')
    parser.add_argument('--format', choices=['markdown', 'text', 'html'], default='markdown', help='输出格式，默认markdown')
    parser.add_argument('-o', '--output', help='输出文件路径，不指定则打印到控制台')
    parser.add_argument('--wait', type=int, default=3, help='playwright模式下页面等待时间（秒），默认3秒')
    parser.add_argument('--cookie', help='请求Cookie，格式："key1=value1; key2=value2"')
    parser.add_argument('--click-selector', help='页面加载后要点击的元素CSS选择器，用于关闭弹窗等')
    parser.add_argument('--scroll', action='store_true', help='是否自动滚动到底部加载全部内容')
    
    args = parser.parse_args()
    
    print(f"🚀 开始抓取网页: {args.url}", file=sys.stderr)
    
    content = None
    success = False
    
    # 按模式选择抓取方式
    if args.mode in ['auto', 'web_fetch']:
        if args.mode == 'web_fetch':
            print(f"🔧 使用web_fetch模式抓取", file=sys.stderr)
        else:
            print(f"🔧 尝试web_fetch模式...", file=sys.stderr)
        
        success, content = try_web_fetch(args.url, args.format)
        
        if success:
            print(f"✅ web_fetch模式抓取成功", file=sys.stderr)
    
    # 如果web_fetch失败或者强制playwright模式
    if not success and args.mode in ['auto', 'playwright']:
        if args.mode == 'playwright':
            print(f"🔧 使用playwright模式抓取", file=sys.stderr)
        else:
            print(f"🔧 web_fetch模式失败，切换到playwright模式...", file=sys.stderr)
        
        success, content = fetch_with_playwright(
            args.url, 
            args.format, 
            args.wait, 
            args.cookie, 
            args.click_selector, 
            args.scroll
        )
        
        if success:
            print(f"✅ playwright模式抓取成功", file=sys.stderr)
    
    if not success:
        print(f"❌ 所有抓取方式均失败", file=sys.stderr)
        sys.exit(1)
    
    # 输出结果
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📝 结果已保存到: {output_path.resolve()}", file=sys.stderr)
    else:
        print(content)

if __name__ == "__main__":
    main()
