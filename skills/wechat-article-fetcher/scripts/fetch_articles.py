#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章获取工具
通过公众号名称搜索并获取近期文章列表
"""

import argparse
import json
import re
import sys
import time
import io
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    import requests
except ImportError:
    print("Error: requests library is required. Install with: pip install requests")
    sys.exit(1)


class WechatArticleFetcher:
    """微信公众号文章获取器"""
    
    # 微信搜狗搜索接口
    SOGOU_SEARCH_URL = "https://weixin.sogou.com/weixin"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://weixin.sogou.com/'
        })
    
    def search_official_account(self, account_name: str) -> List[Dict]:
        """
        搜索公众号
        
        Args:
            account_name: 公众号名称
            
        Returns:
            公众号列表，包含名称、微信号、简介等信息
        """
        params = {
            'type': '1',  # 1=公众号搜索
            'query': account_name,
            'page': '1'
        }
        
        try:
            response = self.session.get(self.SOGOU_SEARCH_URL, params=params, timeout=10)
            response.encoding = 'utf-8'
            
            # 解析搜索结果
            accounts = self._parse_account_search(response.text)
            return accounts
            
        except requests.RequestException as e:
            print(f"Error searching account: {e}")
            return []
    
    def _parse_account_search(self, html: str) -> List[Dict]:
        """解析公众号搜索结果"""
        accounts = []
        
        # 匹配公众号信息块
        account_pattern = r'<li id="sogou_vr_[^"]*"[^>]*>.*?<div class="txt-box">.*?</li>'
        account_blocks = re.findall(account_pattern, html, re.DOTALL)
        
        for block in account_blocks[:5]:  # 只取前5个结果
            account = {}
            
            # 提取公众号名称
            name_match = re.search(r'<p class="tit">.*?<em>([^<]*)</em>.*?</p>', block)
            if name_match:
                account['name'] = re.sub(r'<[^>]+>', '', name_match.group(1)).strip()
            
            # 提取微信号
            wechat_id_match = re.search(r'微信号：<label[^>]*>([^<]*)</label>', block)
            if wechat_id_match:
                account['wechat_id'] = wechat_id_match.group(1).strip()
            
            # 提取简介
            intro_match = re.search(r'<p class="info">([^<]*)</p>', block)
            if intro_match:
                account['intro'] = intro_match.group(1).strip()
            
            # 提取链接
            link_match = re.search(r'<p class="tit"><a href="([^"]*)"', block)
            if link_match:
                account['url'] = 'https://weixin.sogou.com' + link_match.group(1)
            
            if account.get('name'):
                accounts.append(account)
        
        return accounts
    
    def get_articles(self, account_name: str, limit: int = 10) -> List[Dict]:
        """
        获取公众号近期文章
        
        Args:
            account_name: 公众号名称
            limit: 获取文章数量（默认10篇）
            
        Returns:
            文章列表，包含标题、链接、发布时间等
        """
        # 先搜索文章
        params = {
            'type': '2',  # 2=文章搜索
            'query': f"{account_name}",
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
        """解析文章列表"""
        articles = []
        
        # 匹配文章信息块
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
    
    def get_article_detail(self, article_url: str) -> Dict:
        """
        获取文章详情（需要处理跳转）
        
        Args:
            article_url: 文章链接
            
        Returns:
            文章详情
        """
        try:
            # 搜狗链接需要跳转
            if 'weixin.sogou.com' in article_url:
                response = self.session.get(article_url, allow_redirects=False, timeout=10)
                if response.status_code == 302:
                    article_url = response.headers.get('Location', article_url)
            
            # 获取微信文章页面
            response = self.session.get(article_url, timeout=10)
            response.encoding = 'utf-8'
            
            detail = {
                'url': article_url,
                'title': '',
                'content': '',
                'publish_time': '',
                'read_count': '',
                'like_count': ''
            }
            
            # 提取标题
            title_match = re.search(r'<h1[^>]*class="rich_media_title[^"]*"[^>]*>(.*?)</h1>', response.text, re.DOTALL)
            if title_match:
                detail['title'] = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            
            # 提取发布时间
            time_match = re.search(r'var s="(\d{4}-\d{2}-\d{2})"', response.text)
            if time_match:
                detail['publish_time'] = time_match.group(1)
            
            # 提取内容
            content_match = re.search(r'<div id="js_content"[^>]*>(.*?)</div>\s*<script', response.text, re.DOTALL)
            if content_match:
                content = content_match.group(1)
                # 清理HTML标签但保留文本
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()
                detail['content'] = content[:500] + '...' if len(content) > 500 else content
            
            return detail
            
        except requests.RequestException as e:
            print(f"Error fetching article detail: {e}")
            return {'url': article_url, 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='获取微信公众号文章')
    parser.add_argument('account', help='公众号名称')
    parser.add_argument('-n', '--num', type=int, default=10, help='获取文章数量（默认10篇）')
    parser.add_argument('-d', '--detail', action='store_true', help='获取文章详情')
    parser.add_argument('-o', '--output', help='输出文件路径（JSON格式）')
    parser.add_argument('--search-only', action='store_true', help='仅搜索公众号，不获取文章')
    
    args = parser.parse_args()
    
    fetcher = WechatArticleFetcher()
    
    print(f"🔍 正在搜索公众号: {args.account}\n")
    
    if args.search_only:
        # 仅搜索公众号
        accounts = fetcher.search_official_account(args.account)
        if not accounts:
            print("❌ 未找到相关公众号")
            return
        
        print(f"✅ 找到 {len(accounts)} 个相关公众号:\n")
        for i, account in enumerate(accounts, 1):
            print(f"{i}. {account.get('name', 'Unknown')}")
            print(f"   微信号: {account.get('wechat_id', 'N/A')}")
            print(f"   简介: {account.get('intro', 'N/A')}")
            print()
        
        result = {'accounts': accounts}
    else:
        # 获取文章
        print(f"📰 正在获取文章列表...\n")
        articles = fetcher.get_articles(args.account, args.num)
        
        if not articles:
            print("❌ 未找到相关文章")
            return
        
        print(f"✅ 找到 {len(articles)} 篇文章:\n")
        
        result = {'account': args.account, 'articles': []}
        
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.get('title', 'Unknown')}")
            print(f"   公众号: {article.get('account_name', 'N/A')}")
            print(f"   时间: {article.get('publish_time', 'N/A')}")
            print(f"   链接: {article.get('url', 'N/A')}")
            
            article_data = {
                'index': i,
                'title': article.get('title'),
                'account': article.get('account_name'),
                'publish_time': article.get('publish_time'),
                'url': article.get('url'),
                'summary': article.get('summary', '')
            }
            
            # 获取详情
            if args.detail:
                print(f"   📄 正在获取详情...")
                detail = fetcher.get_article_detail(article['url'])
                article_data['detail'] = detail
                if detail.get('content'):
                    print(f"   内容预览: {detail['content'][:100]}...")
            
            result['articles'].append(article_data)
            print()
            
            # 避免请求过快
            if args.detail and i < len(articles):
                time.sleep(1)
    
    # 保存到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 结果已保存到: {args.output}")
    
    # 输出JSON到stdout
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
