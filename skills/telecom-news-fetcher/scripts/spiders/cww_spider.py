# -*- coding: utf-8 -*-
"""
通信世界网爬虫 (cww.net.cn)
"""

import requests
from bs4 import BeautifulSoup
import random
import time
import json
import os

# 配置文件路径 (与 c114_spider.py 保持一致)
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


def fetch_cww_news(source_key='cww', limit=10):
    """获取通信世界网新闻"""
    config = load_config()
    source = config['sources'].get(source_key)
    
    if not source or not source.get('enabled', False):
        return []
    
    base_url = source['base_url']
    
    headers = {
        'User-Agent': get_random_ua(config),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    # 尝试多个可能的新闻页面
    news_urls = [
        '/newscenter/',
        '/news/',
        '/xwzx/',
        '/html/xwzx/',
    ]
    
    all_news = []
    
    for path in news_urls:
        if len(all_news) >= limit:
            break
            
        url = base_url + path
        get_random_delay(config)
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找新闻链接 - 通用选择器
            articles = soup.select('a[href*=".html"]')
            
            seen = set()
            for a_tag in articles:
                if len(all_news) >= limit:
                    break
                
                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                
                # 过滤条件
                if not title or len(title) < 8:
                    continue
                if title in seen:
                    continue
                if any(x in href for x in ['javascript', 'mailto', '#']):
                    continue
                    
                seen.add(title)
                
                # 处理链接
                if href.startswith('/'):
                    full_url = base_url + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                # 只保留本网站的链接
                if 'cww.net.cn' not in full_url and not full_url.startswith('/'):
                    continue
                
                all_news.append({
                    'title': title,
                    'url': full_url,
                    'date': '',
                    'source': source['name']
                })
                
        except Exception as e:
            continue
    
    return all_news[:limit]


def main():
    print("🔍 正在获取通信世界网新闻...")
    news = fetch_cww_news('cww', limit=5)
    
    if not news:
        print("❌ 未获取到新闻")
        return
    
    print(f"\n✅ 获取到 {len(news)} 条新闻:\n")
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
        print(f"   🔗 {item['url']}\n")


if __name__ == '__main__':
    main()
