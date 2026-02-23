#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Brave Search API 搜索工具
"""
import requests
import json
import sys
import os
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置
API_KEY = 'BSAVcG_OLy94oPAQmb3ZpymklKZejXs'
BASE_URL = 'https://api.search.brave.com/res/v1/web/search'

def search(query, count=5, country='CN', search_lang='zh-hans'):
    """执行 Brave Search"""
    headers = {
        'X-Subscription-Token': API_KEY,
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'q': query,
        'count': count,
        'country': country,
        'search_lang': search_lang
    }
    
    try:
        r = requests.post(BASE_URL, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        results = data.get('web', {}).get('results', [])
        return results
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}", file=sys.stderr)
        print(f"响应内容: {r.text[:500]}", file=sys.stderr)
        return None

def format_results(results, verbose=False):
    """格式化搜索结果"""
    if not results:
        return "未找到结果"
    
    output = []
    for i, r in enumerate(results, 1):
        title = r.get('title', 'N/A')
        url = r.get('url', 'N/A')
        desc = r.get('description', '') if verbose else ''
        
        output.append(f"{i}. {title}")
        output.append(f"   {url}")
        if desc:
            output.append(f"   {desc[:100]}..." if len(desc) > 100 else f"   {desc}")
        output.append("")
    
    return "\n".join(output)

def main():
    # 解析参数
    args = sys.argv[1:]
    
    if not args or args[0] in ['-h', '--help', 'help']:
        print("Brave Search 搜索工具")
        print("")
        print("用法: python brave_search.py <关键词> [数量] [国家] [语言]")
        print("")
        print("参数:")
        print("  关键词    搜索内容 (必填)")
        print("  数量      返回结果数量，默认 5")
        print("  国家      国家代码，默认 CN")
        print("  语言      语言代码，默认 zh-hans")
        print("")
        print("示例:")
        print('  python brave_search.py "人工智能"')
        print('  python brave_search.py "AI news" 10 US en')
        print('  python brave_search.py "日本旅游" 5 JP ja')
        return
    
    query = args[0]
    count = int(args[1]) if len(args) > 1 else 5
    country = args[2] if len(args) > 2 else 'CN'
    search_lang = args[3] if len(args) > 3 else 'zh-hans'
    
    # 执行搜索
    results = search(query, count, country, search_lang)
    
    if results is None:
        print("搜索失败，请检查网络连接或 VPN", file=sys.stderr)
        sys.exit(1)
    
    # 输出结果
    print(format_results(results))

if __name__ == '__main__':
    main()
