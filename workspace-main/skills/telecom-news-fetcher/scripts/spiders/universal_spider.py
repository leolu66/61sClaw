# -*- coding: utf-8 -*-
"""
通用新闻爬虫 - 支持多个新闻网站
使用 Playwright 浏览器自动化，更难被反爬检测
"""

import random
import json
import os
import sys
import io
import time

# Fix stdout encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Playwright - 使用同步版本，更简单
from playwright.sync_api import sync_playwright

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


class BrowserFetcher:
    """浏览器爬虫类 - 复用 Playwright"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        return self
        
    def __exit__(self, *args):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def fetch(self, url, timeout=30):
        """获取页面内容"""
        page = self.context.new_page()
        try:
            page.goto(url, wait_until='networkidle', timeout=timeout * 1000)
            time.sleep(2)  # 等待动态内容
            content = page.content()
            page.close()
            return content
        except Exception as e:
            page.close()
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
        '.list a',
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


def fetch_news(source_key, limit=10):
    """获取指定新闻源"""
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
    
    with BrowserFetcher(headless=True) as fetcher:
        for path in news_paths:
            if len(all_news) >= limit:
                break
                
            url = base_url + path
            
            # 随机延迟
            time.sleep(get_random_delay())
            
            try:
                content = fetcher.fetch(url, timeout=30)
                soup = BeautifulSoup(content, 'html.parser')
                news = extract_news(soup, base_url, source_name, limit)
                all_news.extend(news)
                print(f"   [OK] {source_name}: {len(news)} 条")
                
            except Exception as e:
                print(f"   [X] {source_name}: {str(e)[:40]}")
                continue
    
    # 去重并返回
    seen = set()
    result = []
    for news in all_news:
        if news['title'] not in seen:
            seen.add(news['title'])
            result.append(news)
    
    return result[:limit]


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


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else 'c114'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print(f"[+] 获取 {source} 新闻 (Playwright)...")
    news = fetch_news(source, limit)
    
    if not news:
        print("[-] 未获取到新闻")
        return
    
    print(f"\n[OK] 共 {len(news)} 条:\n")
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
        print(f"   {item['url']}\n")


if __name__ == '__main__':
    main()
