#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页内容提取器 - 智能提取正文内容
"""

import re
import json
from urllib.parse import urlparse

class WebContentExtractor:
    """智能网页内容提取器"""
    
    def __init__(self):
        # 需要移除的标签
        self.remove_tags = [
            'script', 'style', 'nav', 'header', 'footer', 
            'aside', 'advertisement', 'ad', 'sidebar',
            'comment', 'social', 'share', 'related'
        ]
        
        # 可能包含正文的标签
        self.content_tags = [
            'article', 'main', 'content', 'post', 'entry',
            'div[class*="content"]', 'div[class*="article"]',
            'div[class*="post"]', 'div[class*="main"]'
        ]
    
    def extract(self, html, url=None):
        """
        从 HTML 提取正文内容
        
        Args:
            html: HTML 内容
            url: 网页 URL（用于参考）
            
        Returns:
            dict: 提取结果
        """
        if not html:
            return {'success': False, 'error': 'HTML 内容为空'}
        
        try:
            # 提取标题
            title = self._extract_title(html)
            
            # 提取正文
            text = self._extract_main_content(html)
            
            # 提取元数据
            metadata = self._extract_metadata(html, url)
            
            return {
                'success': True,
                'title': title,
                'content': text,
                'metadata': metadata,
                'content_length': len(text),
                'url': url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'提取失败: {str(e)}'
            }
    
    def _extract_title(self, html):
        """提取页面标题"""
        # 尝试多种方式提取标题
        patterns = [
            r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']twitter:title["\'][^>]*content=["\']([^"\']+)["\']',
            r'<title>([^<]+)</title>',
            r'<h1[^>]*>([^<]+)</h1>'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # 清理标题（移除网站名等）
                title = re.sub(r'[\|\-–—].*$', '', title).strip()
                if title:
                    return title
        
        return None
    
    def _extract_main_content(self, html):
        """提取主要内容"""
        # 移除 script 和 style 标签及其内容
        text = html
        for tag in ['script', 'style', 'noscript']:
            text = re.sub(rf'<{tag}[^>]*>[^]*?</{tag}>', ' ', text, flags=re.IGNORECASE)
        
        # 尝试找到文章主体
        # 策略1: 查找 article 标签
        article_match = re.search(r'<article[^>]*>([^]*?)</article>', text, re.IGNORECASE)
        if article_match:
            text = article_match.group(1)
        else:
            # 策略2: 查找 main 标签
            main_match = re.search(r'<main[^>]*>([^]*?)</main>', text, re.IGNORECASE)
            if main_match:
                text = main_match.group(1)
            else:
                # 策略3: 查找包含最多文本的 div
                text = self._find_largest_text_block(text)
        
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 清理文本
        text = self._clean_text(text)
        
        return text
    
    def _find_largest_text_block(self, html):
        """查找包含最多文本的 div 块"""
        # 简单的启发式算法：找包含最多中文或英文单词的 div
        div_pattern = r'<div[^>]*>([^]*?)</div>'
        divs = re.findall(div_pattern, html, re.IGNORECASE)
        
        best_div = html  # 默认使用整个 HTML
        max_score = 0
        
        for div in divs:
            # 计算文本密度分数
            text_content = re.sub(r'<[^>]+>', ' ', div)
            
            # 统计文本长度作为分数
            score = len(text_content.strip())
            
            # 惩罚包含导航、广告等关键词的 div
            lower_div = div.lower()
            penalty_keywords = ['nav', 'menu', 'sidebar', 'ad', 'comment', 'footer', 'header']
            for keyword in penalty_keywords:
                if keyword in lower_div:
                    score *= 0.5
            
            if score > max_score:
                max_score = score
                best_div = div
        
        return best_div
    
    def _clean_text(self, text):
        """清理文本"""
        # 解码 HTML 实体
        try:
            import html
            text = html.unescape(text)
        except:
            pass
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        
        # 移除广告、分享等常见文本
        ad_patterns = [
            r'分享.*?:?\s*\n',
            r'相关阅读.*?:?\s*\n',
            r'推荐阅读.*?:?\s*\n',
            r'版权声明.*?:?\s*\n',
            r'免责声明.*?:?\s*\n',
        ]
        for pattern in ad_patterns:
            text = re.sub(pattern, '\n', text, flags=re.IGNORECASE)
        
        # 移除空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _extract_metadata(self, html, url):
        """提取元数据"""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc if url else None
        }
        
        # 提取描述
        desc_match = re.search(
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if desc_match:
            metadata['description'] = desc_match.group(1)
        
        # 提取作者
        author_match = re.search(
            r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if author_match:
            metadata['author'] = author_match.group(1)
        
        # 提取发布日期
        date_patterns = [
            r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']publishdate["\'][^>]*content=["\']([^"\']+)["\']',
            r'<time[^>]*datetime=["\']([^"\']+)["\']'
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, html, re.IGNORECASE)
            if date_match:
                metadata['published_date'] = date_match.group(1)
                break
        
        return metadata


if __name__ == '__main__':
    # 测试
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>测试文章 - 示例网站</title>
        <meta name="description" content="这是一个测试文章的描述">
    </head>
    <body>
        <header>网站导航</header>
        <article>
            <h1>人工智能的发展趋势</h1>
            <p>人工智能正在快速发展，深度学习技术取得了突破性进展。</p>
            <p>未来，AI 将在更多领域发挥重要作用。</p>
        </article>
        <aside>相关推荐</aside>
        <footer>版权所有</footer>
    </body>
    </html>
    """
    
    extractor = WebContentExtractor()
    result = extractor.extract(test_html, 'https://example.com/article')
    print(json.dumps(result, ensure_ascii=False, indent=2))
