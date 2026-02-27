# -*- coding: utf-8 -*-
"""
通用新闻爬虫 - 支持多个新闻网站
使用 Playwright 浏览器自动化，更难被反爬检测
"""

import asyncio
import random
import json
import os
import sys
import io

# Fix stdout encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Playwright
from playwright.async_api import async_playwright

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_random_delay():
    """随机延迟"""
    config = load_config()
    delay = random.uniform(
        config['spider'].get('delay_min', 2),
        config['spider'].get('delay_max', 5)
    )
    return delay


async def fetch_with_playwright(url, encoding='utf-8'):
    """使用 Playwright 获取页面"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        page = await browser.new_page()
        
        try:
            await page.goto(url, timeout=30000, wait_until='networkidle')
            
            # 等待页面加载完成
            await asyncio.sleep(2)
            
            # 获取页面内容
            content = await page.content()
            
            await browser.close()
            return content
            
        except Exception as e:
            await browser.close()
            raise e


def extract_news(soup, base_url, source_name, limit=10):
    """从页面提取新闻链接"""
    from bs4 import BeautifulSoup
    
    all_news = []
    seen = set()
    
    # 尝试多种选择器
    selectors = [
        'a[href*=".html"]',
        'a[href*=".htm"]',
        'a[title]',
        '.news_list a',
        '.article_list a',
        'ul li a',
    ]
    
    for selector in selectors:
        if len(all_news) >= limit:
            break
            
        articles = soup.select(selector)
        
        for a_tag in articles:
            if len(all_news) >= limit:
                break
            
            title = a_tag.get_text(strip=True)
            href = a_tag.get('href', '')
            
            # 严格过滤
            if not title or len(title) < 6:
                continue
            if title in seen:
                continue
            if any(x in href.lower() for x in ['javascript', 'mailto', '#', 'null', 'undefined']):
                continue
            if href.startswith('#'):
                continue
                
            seen.add(title)
            
            # 处理链接
            if href.startswith('//'):
                full_url = 'https:' + href
            elif href.startswith('/'):
                full_url = base_url + href
            elif href.startswith('http'):
                domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
                if domain in href:
                    full_url = href
                else:
                    continue
            else:
                continue
            
            all_news.append({
                'title': title,
                'url': full_url,
                'date': '',
                'source': source_name
            })
    
    return all_news


async def fetch_news_async(source_key, limit=10):
    """异步获取指定新闻源"""
    from bs4 import BeautifulSoup
    
    config = load_config()
    sources = config.get('sources', {})
    source = sources.get(source_key)
    
    if not source or not source.get('enabled', False):
        return []
    
    base_url = source['base_url']
    news_paths = source.get('news_paths', ['/'])
    encoding = source.get('encoding', 'utf-8')
    source_name = source['name']
    
    all_news = []
    
    for path in news_paths:
        if len(all_news) >= limit:
            break
            
        url = base_url + path
        
        # 随机延迟
        await asyncio.sleep(get_random_delay())
        
        try:
            content = await fetch_with_playwright(url, encoding)
            soup = BeautifulSoup(content, 'html.parser')
            news = extract_news(soup, base_url, source_name, limit)
            all_news.extend(news)
            print(f"   ✅ {source_name}: 获取到 {len(news)} 条")
            
        except Exception as e:
            print(f"   ❌ {source_name}: {str(e)[:50]}")
            continue
    
    # 去重并返回
    seen = set()
    result = []
    for news in all_news:
        if news['title'] not in seen:
            seen.add(news['title'])
            result.append(news)
    
    return result[:limit]


def fetch_news(source_key, limit=10):
    """同步包装"""
    return asyncio.run(fetch_news_async(source_key, limit))


# 为每个源创建函数
def fetch_c114_news(source_key='c114', limit=10):
    return fetch_news('c114', limit)

def fetch_cnii_news(source_key='cnii', limit=10):
    return fetch_news('cnii', limit)

def fetch_cfyys_news(source_key='cfyys', limit=10):
    return fetch_news('cfyys', limit)

def fetch_cww_news(source_key='cww', limit=10):
    return fetch_news('cww', limit)

def fetch_ccidcom_news(source_key='ccidcom', limit=10):
    return fetch_news('ccidcom', limit)


async def main_async():
    source = sys.argv[1] if len(sys.argv) > 1 else 'cnii'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print(f"🔍 正在获取 {source} 新闻 (使用 Playwright)...")
    news = await fetch_news_async(source, limit)
    
    if not news:
        print("❌ 未获取到新闻")
        return
    
    print(f"\n✅ 获取到 {len(news)} 条新闻:\n")
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
        print(f"   🔗 {item['url']}\n")


def main():
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
