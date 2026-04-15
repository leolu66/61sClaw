#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章工具 - 文章内容读取模块
使用 Playwright 绕过反爬限制，读取文章完整内容
"""

import re
import time
from typing import Dict, Optional
from playwright.sync_api import sync_playwright, Page


class ArticleContentReader:
    """公众号文章内容读取器"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.playwright = None
        
    def __enter__(self):
        """上下文管理器入口"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def read(self, url: str, timeout: int = 30) -> Dict:
        """
        读取单篇文章内容
        
        Args:
            url: 文章链接
            timeout: 超时时间（秒）
            
        Returns:
            文章信息字典
        """
        page = self.context.new_page()
        
        try:
            print(f"  [访问] {url[:60]}...")
            
            # 访问页面
            page.goto(url, wait_until='networkidle', timeout=timeout * 1000)
            page.wait_for_load_state('domcontentloaded')
            time.sleep(2)  # 等待动态内容加载
            
            # 提取信息
            result = self._extract(page)
            print(f"  [成功] {result.get('title', 'Unknown')[:40]}...")
            
            return result
            
        except Exception as e:
            print(f"  [失败] {e}")
            return {'error': str(e), 'url': url}
        finally:
            page.close()
    
    def _extract(self, page: Page) -> Dict:
        """提取文章信息"""
        # 标题
        title_selectors = [
            'h1#activity_name',
            'h2.rich_media_title',
            '#js_article_title',
            '.rich_media_title'
        ]
        title = self._get_text(page, title_selectors)
        
        # 公众号名称
        account_selectors = [
            '#js_name',
            '#js_profile_qrcode .profile_nickname',
            '#js_author_name',
            '.profile_nickname'
        ]
        account = self._get_text(page, account_selectors)
        
        # 发布时间
        time_selectors = [
            '#publish_time',
            '#js_publish_time',
            '.publish_time',
            '#post-date'
        ]
        publish_time = self._get_text(page, time_selectors)
        
        # 正文内容
        content_selectors = [
            '#js_content',
            '.rich_media_content'
        ]
        content = self._get_html(page, content_selectors)
        
        return {
            'title': title or 'Unknown',
            'account': account or 'Unknown',
            'publish_time': publish_time or '',
            'content': self._html_to_markdown(content) if content else '',
            'url': page.url
        }
    
    def _get_text(self, page: Page, selectors: list) -> str:
        """尝试多个选择器获取文本"""
        for selector in selectors:
            try:
                element = page.locator(selector).first
                if element.count() > 0:
                    text = element.inner_text().strip()
                    if text:
                        return text
            except:
                continue
        return ''
    
    def _get_html(self, page: Page, selectors: list) -> str:
        """尝试多个选择器获取 HTML"""
        for selector in selectors:
            try:
                element = page.locator(selector).first
                if element.count() > 0:
                    return element.inner_html()
            except:
                continue
        return ''
    
    def _html_to_markdown(self, html: str) -> str:
        """HTML 转 Markdown"""
        # 移除 script/style
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        
        # 图片
        html = re.sub(r'<img[^\u003e]+data-src=["\']([^"\']+)["\'][^\u003e]*>', r'![图片](\1)', html)
        html = re.sub(r'<img[^\u003e]+src=["\']([^"\']+)["\'][^\u003e]*>', r'![图片](\1)', html)
        
        # 标题
        html = re.sub(r'<h1[^\u003e]*>(.*?)</h1>', r'# \1\n\n', html, flags=re.DOTALL)
        html = re.sub(r'<h2[^\u003e]*>(.*?)</h2>', r'## \1\n\n', html, flags=re.DOTALL)
        html = re.sub(r'<h3[^\u003e]*>(.*?)</h3>', r'### \1\n\n', html, flags=re.DOTALL)
        
        # 段落
        html = re.sub(r'<p[^\u003e]*>(.*?)</p>', r'\1\n\n', html, flags=re.DOTALL)
        
        # 换行
        html = re.sub(r'<br\s*/?>', '\n', html)
        
        # 加粗/斜体
        html = re.sub(r'<(strong|b)[^\u003e]*>(.*?)</\1>', r'**\2**', html, flags=re.DOTALL)
        html = re.sub(r'<(em|i)[^\u003e]*>(.*?)</\1>', r'*\2*', html, flags=re.DOTALL)
        
        # 链接
        html = re.sub(r'<a[^\u003e]+href=["\']([^"\']+)["\'][^\u003e]*>(.*?)</a>', r'[\2](\1)', html, flags=re.DOTALL)
        
        # 列表
        html = re.sub(r'<li[^\u003e]*>(.*?)</li>', r'- \1\n', html, flags=re.DOTALL)
        html = re.sub(r'<[ou]l[^\u003e]*>|</[ou]l>', '', html)
        
        # 代码
        html = re.sub(r'<pre[^\u003e]*>(.*?)</pre>', r'```\n\1\n```\n\n', html, flags=re.DOTALL)
        html = re.sub(r'<code[^\u003e]*>(.*?)</code>', r'`\1`', html, flags=re.DOTALL)
        
        # 移除其他标签
        html = re.sub(r'<[^\u003e]+>', '', html)
        
        # 解码实体
        html = html.replace('&nbsp;', ' ').replace('&lt;', '<')
        html = html.replace('&gt;', '>').replace('&amp;', '&')
        html = html.replace('&quot;', '"').replace('&#39;', "'")
        
        # 清理空白
        html = re.sub(r'\n{3,}', '\n\n', html).strip()
        
        return html
