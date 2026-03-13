#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页抓取模块 - 支持静态和动态网页
"""

import re
import time
from datetime import datetime
from typing import Optional, Dict
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
except ImportError:
    print("请先安装依赖: pip install requests beautifulsoup4 markdownify")
    raise


class WebCrawler:
    """网页抓取器"""
    
    # 需要Playwright的动态网站域名列表
    DYNAMIC_SITES = [
        '36kr.com',
        'infoq.cn',
        'zhihu.com',
        'juejin.cn',
        'csdn.net',
        'sspai.com',
        'ifanr.com',
        'geekpark.net',
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _is_dynamic_site(self, url: str) -> bool:
        """判断是否为需要动态渲染的网站"""
        domain = urlparse(url).netloc.lower()
        for site in self.DYNAMIC_SITES:
            if site in domain:
                return True
        return False
    
    def _fetch_with_requests(self, url: str) -> Optional[str]:
        """使用requests获取静态页面"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text
        except Exception as e:
            print(f"   requests获取失败: {e}")
            return None
    
    def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """使用Playwright获取动态页面"""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_viewport_size({"width": 1920, "height": 1080})
                
                # 设置User-Agent
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                print("   使用Playwright渲染页面...")
                page.goto(url, wait_until='networkidle', timeout=60000)
                
                # 等待页面加载
                time.sleep(2)
                
                # 获取内容
                html = page.content()
                browser.close()
                return html
        except ImportError:
            print("   Playwright未安装，尝试使用requests")
            return None
        except Exception as e:
            print(f"   Playwright获取失败: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取文章标题"""
        # 尝试多种方式获取标题
        selectors = [
            'h1.article-title',
            'h1.post-title',
            'h1.entry-title',
            'article h1',
            '.article-title',
            '.post-title',
            'h1',
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                return elem.get_text(strip=True)
        
        # 从title标签获取
        if soup.title:
            return soup.title.get_text(strip=True)
        
        return "未命名文章"
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> str:
        """提取文章正文"""
        # 常见文章容器选择器
        content_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '.article-body',
            '.post-body',
            '[class*="article"]',
            '[class*="content"]',
            'main',
        ]
        
        content_elem = None
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                # 检查内容长度，避免选到太短的元素
                text_length = len(elem.get_text(strip=True))
                if text_length > 200:  # 至少200字符
                    content_elem = elem
                    break
        
        if not content_elem:
            # 如果没有找到合适的容器，尝试从body提取
            content_elem = soup.body
        
        if not content_elem:
            return ""
        
        # 移除不需要的元素
        for elem in content_elem.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            elem.decompose()
        
        # 转换为Markdown
        html_str = str(content_elem)
        markdown = md(html_str, heading_style="ATX")
        
        # 清理
        markdown = self._clean_markdown(markdown)
        
        return markdown
    
    def _clean_markdown(self, text: str) -> str:
        """清理Markdown文本"""
        # 移除过多的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 移除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # 再次清理空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def fetch(self, url: str) -> Optional[Dict]:
        """
        抓取网页内容
        
        Returns:
            dict: {
                'title': str,
                'content': str,
                'url': str,
                'fetch_time': str
            }
        """
        # 判断使用哪种方式获取
        if self._is_dynamic_site(url):
            html = self._fetch_with_playwright(url)
        else:
            html = self._fetch_with_requests(url)
            if not html:
                # 如果requests失败，尝试playwright
                html = self._fetch_with_playwright(url)
        
        if not html:
            return None
        
        # 解析HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取标题和内容
        title = self._extract_title(soup)
        content = self._extract_content(soup, url)
        
        if not content or len(content) < 100:
            # 内容太短，可能抓取失败
            return None
        
        return {
            'title': title,
            'content': content,
            'url': url,
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
