# -*- coding: utf-8 -*-
"""
C114通信网爬虫
支持获取移动、联通、电信等运营商行业新闻
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
import random
import time
import json
import os

# 添加项目根目录到路径
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')


def load_config():
    """加载配置文件"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_random_ua(config):
    """随机获取User-Agent"""
    return random.choice(config['spider']['user_agents'])


def get_random_delay(config):
    """随机延迟"""
    delay = random.uniform(
        config['spider']['delay_min'],
        config['spider']['delay_max']
    )
    time.sleep(delay)


def fetch_c114_news(source_key='c114', limit=10):
    """
    获取C114新闻
    
    Args:
        source_key: 来源标识
        limit: 每个分类获取的新闻数
    
    Returns:
        list: 新闻列表
    """
    config = load_config()
    source = config['sources'].get(source_key)
    
    if not source or not source.get('enabled', False):
        return []
    
    base_url = source['base_url']
    
    headers = {
        'User-Agent': get_random_ua(config),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': base_url
    }
    
    all_news = []
    
    # 获取滚动新闻页面
    url = base_url + '/news/roll.asp'
    get_random_delay(config)
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"⚠️ 获取失败: {url} - 状态码: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有新闻链接
        # C114 滚动新闻页面的链接通常在 ul 或 div 中
        articles = soup.select('div.news_list a') or soup.select('ul.news_list a')
        
        # 如果没找到，尝试更宽泛的选择器
        if not articles:
            articles = soup.select('a[href*="/news/"]')
        
        seen = set()
        
        for a_tag in articles:
            if len(all_news) >= limit:
                break
                
            title = a_tag.get_text(strip=True)
            href = a_tag.get('href', '')
            
            # 过滤：需要是文章链接，不是列表页
            if not title or len(title) < 5:
                continue
            if '/news/' not in href and '/a' not in href:
                continue
            if 'roll.asp' in href or 'index' in href:
                continue
                
            if title in seen:
                continue
            seen.add(title)
            
            # 处理相对链接
            if href.startswith('/'):
                full_url = base_url + href
            elif href.startswith('http'):
                full_url = href
            else:
                continue
            
            # 尝试获取日期
            date_text = ""
            parent = a_tag.find_parent(['div', 'li', 'tr'])
            if parent:
                # 尝试多种日期选择器
                date_span = (parent.find('span', class_='date') or 
                           parent.find('span', class_='time') or
                           parent.find('span', class_='pub_time'))
                if date_span:
                    date_text = date_span.get_text(strip=True)
            
            all_news.append({
                'title': title,
                'url': full_url,
                'date': date_text,
                'source': source['name']
            })
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {url} - {str(e)}")
    except Exception as e:
        print(f"❌ 解析异常: {url} - {str(e)}")
    
    return all_news[:limit]


def fetch_article_content(url):
    """
    获取单篇文章详细内容
    
    Args:
        url: 文章链接
    
    Returns:
        dict: 包含标题、发布时间、正文摘要
    """
    config = load_config()
    
    headers = {
        'User-Agent': get_random_ua(config),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    
    get_random_delay(config)
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取标题
        title = ""
        title_tag = soup.find('h1') or soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # 提取发布时间
        pub_time = ""
        time_tag = soup.find('span', class_='pub_time') or soup.find('span', class_='time')
        if time_tag:
            pub_time = time_tag.get_text(strip=True)
        
        # 提取正文内容（取前500字）
        content = ""
        article_div = soup.find('div', class_='content') or soup.find('div', class_='article_content')
        if article_div:
            # 移除脚本和样式
            for tag in article_div(['script', 'style']):
                tag.decompose()
            content = article_div.get_text(strip=True)[:500]
        
        return {
            'title': title,
            'pub_time': pub_time,
            'content': content,
            'url': url
        }
        
    except Exception as e:
        print(f"❌ 获取文章内容失败: {url} - {str(e)}")
        return None


def main():
    """测试入口"""
    print("🔍 正在获取 C114 通信网新闻...")
    
    news = fetch_c114_news('c114', limit=5)
    
    if not news:
        print("❌ 未获取到新闻")
        return
    
    print(f"\n✅ 获取到 {len(news)} 条新闻:\n")
    
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
        print(f"   📅 {item['date']} | 🔗 {item['url']}")
        print()


if __name__ == '__main__':
    main()
