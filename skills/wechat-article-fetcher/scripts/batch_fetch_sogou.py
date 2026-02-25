#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量获取微信公众号文章列表 - 搜狗搜索方案
"""

import json
import random
import sys
import time
from pathlib import Path
import re
import requests
from datetime import datetime
from typing import List, Dict

# 公众号列表
ACCOUNTS = [
    "究模智",
    "智猩猩AI",
    "架构师",
    "PaperAgent",
    "苏哲管理咨询",
    "AI寒武纪",
    "苍何",
    "腾讯研究院",
    "InfoQ",
    "逛逛GitHub",
    "熵衍AI",
    "AgenticAI",
    "AI产品阿颖"
]

# 输出目录
OUTPUT_DIR = Path(r"D:\anthropic\wechat\2025-02-20")

# 每个公众号获取的文章数量
ARTICLES_PER_ACCOUNT = 5


class WechatArticleFetcher:
    SOGOU_SEARCH_URL = "https://weixin.sogou.com/weixin"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://weixin.sogou.com/'
        })
    
    def get_articles(self, account_name: str, limit: int = 10) -> List[Dict]:
        params = {
            'type': '2',
            'query': account_name,
            'page': '1'
        }
        
        try:
            response = self.session.get(self.SOGOU_SEARCH_URL, params=params, timeout=10)
            response.encoding = 'utf-8'
            articles = self._parse_articles(response.text, account_name, limit)
            return articles
        except requests.RequestException as e:
            print(f"Error fetching articles: {e}")
            return []
    
    def _parse_articles(self, html: str, account_name: str, limit: int) -> List[Dict]:
        articles = []
        article_pattern = r'<li id="sogou_vr_[^"]*"[^>]*>.*?<div class="txt-box">.*?</li>'
        article_blocks = re.findall(article_pattern, html, re.DOTALL)
        
        for block in article_blocks[:limit]:
            article = {}
            
            # 提取标题
            title_match = re.search(r'<h3>.*?<a[^>]*>(.*?)</a>.*?</h3>', block, re.DOTALL)
            if title_match:
                title = re.sub(r'<[^>]+>', '', title_match.group(1))
                article['title'] = title.strip()
            
            # 提取链接
            link_match = re.search(r'<h3>.*?<a[^>]*href="([^"]*)"', block, re.DOTALL)
            if link_match:
                url = link_match.group(1)
                if url.startswith('/'):
                    url = 'https://weixin.sogou.com' + url
                article['url'] = url
            
            # 提取摘要
            summary_match = re.search(r'<p class="txt-info">(.*?)</p>', block, re.DOTALL)
            if summary_match:
                summary = re.sub(r'<[^>]+>', '', summary_match.group(1))
                article['summary'] = summary.strip()
            
            # 提取发布时间
            time_match = re.search(r'<span class="s2">[^<]*<script>[^<]*document\.write\(timeConvert\(\'([^\']*)\'\)\)', block)
            if time_match:
                timestamp = int(time_match.group(1))
                article['publish_time'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
            
            # 提取公众号名称
            account_match = re.search(r'<a id="weixin_account"[^>]*>([^<]*)</a>', block)
            if account_match:
                article['account_name'] = account_match.group(1).strip()
            else:
                article['account_name'] = account_name
            
            if article.get('title') and article.get('url'):
                articles.append(article)
        
        return articles


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 随机打乱公众号顺序
    shuffled_accounts = ACCOUNTS.copy()
    random.shuffle(shuffled_accounts)
    
    print(f"公众号获取顺序（随机）:")
    for i, account in enumerate(shuffled_accounts, 1):
        print(f"  {i}. {account}")
    print()
    
    fetcher = WechatArticleFetcher()
    summary = {}
    
    for idx, account_name in enumerate(shuffled_accounts, 1):
        print(f"\n[{idx}/{len(shuffled_accounts)}] 正在获取: {account_name}")
        
        try:
            articles = fetcher.get_articles(account_name, limit=ARTICLES_PER_ACCOUNT)
            
            # 构建结果
            result = {
                'account': {
                    'name': account_name,
                    'articles_count': len(articles)
                },
                'articles': articles
            }
            
            # 保存到文件
            filename = sanitize_filename(account_name) + ".json"
            output_path = OUTPUT_DIR / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            articles_count = len(articles)
            summary[account_name] = articles_count
            
            print(f"  获取到 {articles_count} 篇文章 -> {filename}")
            
        except Exception as e:
            print(f"  获取失败: {e}")
            summary[account_name] = 0
        
        # 随机延迟 3-5 秒（最后一个不延迟）
        if idx < len(shuffled_accounts):
            delay = random.uniform(3, 5)
            print(f"  等待 {delay:.1f} 秒...")
            time.sleep(delay)
    
    # 保存汇总
    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_accounts': len(ACCOUNTS),
            'total_articles': sum(summary.values()),
            'details': summary
        }, f, ensure_ascii=False, indent=2)
    
    # 输出汇总结果
    print(f"\n{'='*60}")
    print("获取结果汇总")
    print(f"{'='*60}")
    
    for account_name in ACCOUNTS:
        count = summary.get(account_name, 0)
        status = "OK" if count > 0 else "FAIL"
        print(f"[{status}] {account_name}: {count} 篇")
    
    print(f"{'='*60}")
    print(f"总计: {len(ACCOUNTS)} 个公众号, {sum(summary.values())} 篇文章")
    print(f"保存位置: {OUTPUT_DIR}")
    print(f"汇总文件: {summary_path}")


if __name__ == '__main__':
    main()
