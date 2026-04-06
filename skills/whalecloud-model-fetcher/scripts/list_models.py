#!/usr/bin/env python3
"""
WhaleCloud 模型列表查询器
实时爬取并模糊匹配模型列表，支持选择后查询详情
"""

import asyncio
import json
import os
import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, Page

# 设置控制台编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

API_KEY = "ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo="
MODEL_INFO_URL = "https://lab.iwhalecloud.com/gpt-proxy/console/model-info"
USER_DATA_DIR = os.path.expandvars(r"%LOCALAPPDATA%\ChromeDebugProfile")
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output"


def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        print(f"[{timestamp}] [{level}] {message}")
    except:
        print(f"[{timestamp}] [{level}] {message.encode('ascii', 'ignore').decode()}")


def safe_print(text: str):
    """安全打印，处理编码问题"""
    try:
        sys.stdout.buffer.write(text.encode('utf-8'))
    except:
        print(text.encode('ascii', 'ignore').decode())


async def fetch_model_list(page: Page, query: str) -> List[Dict]:
    """使用网页搜索框获取匹配的模型列表"""
    
    # 等待搜索框和卡片加载
    await page.wait_for_selector('input[type="text"]', timeout=30000)
    await page.wait_for_selector('.card-hover', timeout=30000)
    await asyncio.sleep(2)
    
    # 找到搜索框并输入关键词
    # 选择器: body > main > div.mb-6.flex.flex-col.sm\:flex-row.gap-4 > div > input
    try:
        search_input = await page.query_selector('main input[type="text"]')
        if not search_input:
            # 尝试其他可能的选择器
            search_input = await page.query_selector('input[placeholder*="搜索"], input[placeholder*="search"], .search-input')
        
        if search_input:
            log(f"使用搜索框搜索: {query}")
            await search_input.fill(query)
            await asyncio.sleep(2)  # 等待过滤生效
        else:
            log("未找到搜索框，使用页面内过滤")
    except Exception as e:
        log(f"搜索框操作失败: {e}", "WARN")
    
    # 获取过滤后的模型卡片
    cards = await page.query_selector_all('.card-hover')
    log(f"找到 {len(cards)} 个模型卡片")
    
    matches = []
    
    for i, card in enumerate(cards):
        try:
            card_text = await card.evaluate('el => el.textContent')
            lines = [line.strip() for line in card_text.split('\n') if line.strip()]
            
            if len(lines) >= 2:
                model_name = lines[1].strip()
            else:
                continue
            
            # 提取简介
            desc_match = re.search(r'对应模型【.*', card_text, re.S)
            description = desc_match.group().split('\n')[0].strip() if desc_match else ''
            
            matches.append({
                'index': i,
                'name': model_name,
                'description': description
            })
        except Exception as e:
            continue
    
    return matches


def format_model_list(matches: List[Dict], query: str) -> str:
    """格式化模型列表"""
    lines = [f"\n找到 {len(matches)} 个匹配 \"{query}\" 的模型：\n"]
    
    for i, model in enumerate(matches, 1):
        lines.append(f"[{i}] {model['name']}")
        if model.get('description'):
            # 截取简介前50字符
            desc = model['description'][:50] + '...' if len(model['description']) > 50 else model['description']
            lines.append(f"    {desc}")
    
    lines.append("\n输入编号查询详情 (1-{}), 或输入 0 取消:".format(len(matches)))
    return '\n'.join(lines)


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='查询 WhaleCloud 模型列表')
    parser.add_argument('query', help='模型名称关键词')
    parser.add_argument('--select', type=int, help='直接选择指定编号')
    args = parser.parse_args()
    
    query = args.query
    log(f"搜索模型: {query}")
    
    # 启动浏览器
    log("启动浏览器进行实时查询...")
    
    async with async_playwright() as p:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            args=["--start-maximized"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 访问页面
        log(f"访问 {MODEL_INFO_URL}")
        await page.goto(MODEL_INFO_URL, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)
        
        # 检查登录
        text = await page.evaluate('() => document.body.innerText')
        if '需要登录' in text:
            log("需要登录")
            login_btn = await page.query_selector('button:has-text("前往登录")')
            if login_btn:
                await login_btn.click()
                await asyncio.sleep(2)
                await page.fill('input[type="password"]', API_KEY)
                await page.click('button[type="submit"]')
                log("已登录")
                await asyncio.sleep(3)
                await page.goto(MODEL_INFO_URL, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(3)
        
        # 获取模型列表
        matches = await fetch_model_list(page, query)
        await context.close()
        
        if not matches:
            log(f"未找到匹配 \"{query}\" 的模型", "WARN")
            return
        
        # 显示列表
        list_text = format_model_list(matches, query)
        safe_print(list_text)
        
        # 如果指定了直接选择
        if args.select and 1 <= args.select <= len(matches):
            selected = matches[args.select - 1]
            log(f"\n已选择 [{args.select}] {selected['name']}")
            # 调用 query_model.py 查询详情
            script_path = SCRIPT_DIR / "query_model.py"
            subprocess.run([sys.executable, str(script_path), selected['name']])
            return
        
        # 输出结果供上层处理
        # 将匹配列表保存到临时文件，方便上层读取
        result_file = OUTPUT_DIR / "last_model_list.json"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'query': query,
                'matches': matches,
                'timestamp': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        log(f"\n匹配结果已保存: {result_file}")
        log("请使用 --select <编号> 参数查询详情，或在交互模式下输入编号")


if __name__ == "__main__":
    asyncio.run(main())
