# -*- coding: utf-8 -*-
"""
通用新闻爬虫 - 支持多个新闻网站
基于配置文件动态抓取
"""

import requests
from bs4 import BeautifulSoup
import random
import time
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_random_ua(config):
    return random.choice(config['spider']['user_agents'])


def get_random_delay(config):
    delay = random.uniform(config['spider']['delay_min'], config['spider']['delay_max'])
    time.sleep(delay)


def extract_news(soup, base_url, source_name, limit=10):
    """从页面提取新闻链接"""
    all_news = []
    seen = set()
    
    # 尝试多种选择器
    selectors = [
        'a[href*=".html"]',
        'a[href*=".htm"]',
        'a[title]',
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
            # 过滤掉页内锚点链接
            if href.startswith('#'):
                continue
                
            seen.add(title)
            
            # 处理链接
            if href.startswith('//'):
                full_url = 'https:' + href
            elif href.startswith('/'):
                full_url = base_url + href
            elif href.startswith('http'):
                # 只保留同域名链接
                if base_url.replace('https://', '').replace('http://', '').split('/')[0] in href:
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
    config = load_config()
    sources = config.get('sources', {})
    source = sources.get(source_key)
    
    if not source or not source.get('enabled', False):
        return []
    
    base_url = source['base_url']
    news_paths = source.get('news_paths', ['/'])
    encoding = source.get('encoding', 'utf-8')
    source_name = source['name']
    
    headers = {
        'User-Agent': get_random_ua(config),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
    }
    
    all_news = []
    
    for path in news_paths:
        if len(all_news) >= limit:
            break
            
        url = base_url + path
        get_random_delay(config)
        
        try:
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.encoding = encoding
            
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news = extract_news(soup, base_url, source_name, limit)
            all_news.extend(news)
            
        except Exception as e:
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
    import sys
    source = sys.argv[1] if len(sys.argv) > 1 else 'c114'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print(f"🔍 正在获取 {source} 新闻...")
    news = fetch_news(source, limit)
    
    if not news:
        print("❌ 未获取到新闻")
        return
    
    print(f"\n✅ 获取到 {len(news)} 条新闻:\n")
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
        print(f"   🔗 {item['url']}\n")


if __name__ == '__main__':
    main()
