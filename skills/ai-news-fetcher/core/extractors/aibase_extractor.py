#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义提取器 - AiBase
"""

from typing import List, Dict
from bs4 import BeautifulSoup
from extractor import BaseExtractor


class AibaseExtractor(BaseExtractor):
    """AiBase专用提取器"""
    
    def extract(self, html: str) -> List[Dict]:
        """提取AiBase新闻"""
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # 查找所有新闻链接
        links = soup.find_all('a', href=lambda x: x and x.startswith('/news/'))
        
        for link in links:
            try:
                # 获取标题 - 第一个div的文本
                title_div = link.find('div')
                title = title_div.get_text(strip=True) if title_div else ''
                
                # 获取链接
                href = link.get('href', '')
                if href.startswith('/'):
                    href = 'https://news.aibase.cn' + href
                
                if title and href:
                    articles.append({
                        'title': title,
                        'link': href,
                        'summary': '',
                        'author': '',
                        'time': ''
                    })
            except Exception as e:
                continue
        
        return articles
