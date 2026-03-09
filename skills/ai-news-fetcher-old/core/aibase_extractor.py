#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AiBase 专用提取器
"""

from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class AibaseExtractor:
    """AiBase专用提取器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config.get('site', {}).get('base_url', 'https://news.aibase.cn')
    
    def extract(self, html: str) -> List[Dict]:
        """提取AiBase新闻"""
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # 查找所有新闻链接
        links = soup.find_all('a', href=lambda x: x and str(x).startswith('/news/'))
        
        for link in links:
            try:
                # 获取第一个div（包含标题和摘要）
                div = link.find('div', recursive=False)
                if not div:
                    continue
                
                # 获取完整文本
                full_text = div.get_text(strip=True)
                
                # 标题通常是前半部分（在第一个句号或特定标点之前）
                # 根据示例，标题和摘要连在一起，需要分割
                title = ''
                summary = ''
                
                # 尝试找到标题和摘要的分界点
                # 标题通常较短，摘要以"近日"、"全球"等词开头
                markers = ['高德纳惊叹', '近日，', '全球', '国产', '腾讯', '火山', '联想', 'MiniMax']
                for marker in markers:
                    if marker in full_text:
                        idx = full_text.find(marker)
                        title = full_text[:idx].strip()
                        summary = full_text[idx:].strip()
                        break
                
                if not title:
                    # 如果没有找到标记，取前50个字符作为标题
                    title = full_text[:50] + '...' if len(full_text) > 50 else full_text
                    summary = full_text[50:200] if len(full_text) > 50 else ''
                
                # 获取链接
                href = link.get('href', '')
                if href.startswith('/'):
                    href = 'https://news.aibase.cn' + href
                
                if title and href:
                    articles.append({
                        'title': title,
                        'link': href,
                        'summary': summary,
                        'author': '',
                        'time': ''
                    })
            except Exception as e:
                continue
        
        return articles
