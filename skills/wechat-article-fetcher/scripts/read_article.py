#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章内容读取工具
使用 Playwright 绕过反爬限制，读取文章完整内容并保存为 Markdown
"""

import argparse
import json
import re
import sys
import time
import os
from datetime import datetime
from typing import Optional
from urllib.parse import unquote

# 修复 Windows 控制台编码问题 - 仅在非测试环境
if sys.platform == 'win32' and sys.stdout.isatty():
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except:
        pass

try:
    from playwright.sync_api import sync_playwright, Page
except ImportError:
    print("请先安装 Playwright: pip install playwright")
    print("然后安装浏览器: playwright install chromium")
    sys.exit(1)


class WechatArticleReader:
    """微信公众号文章读取器"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        
    def __enter__(self):
        """上下文管理器入口"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
    
    def read_article(self, url: str, timeout: int = 30) -> dict:
        """
        读取单篇文章
        
        Args:
            url: 文章链接
            timeout: 等待超时时间（秒）
            
        Returns:
            包含文章信息的字典
        """
        page = self.context.new_page()
        
        try:
            print(f"正在访问: {url[:80]}...")
            
            # 访问文章页面
            page.goto(url, wait_until='networkidle', timeout=timeout * 1000)
            
            # 等待页面加载完成
            page.wait_for_load_state('domcontentloaded')
            time.sleep(2)  # 额外等待确保内容加载
            
            # 提取文章信息
            result = self._extract_article_info(page)
            
            print(f"成功读取: {result.get('title', 'Unknown')[:50]}...")
            
            return result
            
        except Exception as e:
            print(f"读取失败: {e}")
            return {'error': str(e), 'url': url}
        finally:
            page.close()
    
    def _extract_article_info(self, page: Page) -> dict:
        """提取文章信息"""
        
        # 获取标题
        title = page.locator('h1#activity_name, h2.rich_media_title, #js_article_title').first
        title_text = title.inner_text().strip() if title.count() > 0 else 'Unknown'
        
        # 获取公众号名称
        account = page.locator('a#js_name, #js_profile_qrcode .profile_nickname, #js_author_name').first
        account_text = account.inner_text().strip() if account.count() > 0 else 'Unknown'
        
        # 获取发布时间
        publish_time = page.locator('#publish_time, #js_publish_time, .publish_time').first
        time_text = publish_time.inner_text().strip() if publish_time.count() > 0 else ''
        
        # 获取正文内容
        content_html = page.locator('#js_content, .rich_media_content').first
        
        if content_html.count() > 0:
            # 获取 HTML 内容
            html_content = content_html.inner_html()
            # 转换为 Markdown
            markdown_content = self._html_to_markdown(html_content)
        else:
            markdown_content = ''
        
        return {
            'title': title_text,
            'account': account_text,
            'publish_time': time_text,
            'content': markdown_content,
            'url': page.url
        }
    
    def _html_to_markdown(self, html: str) -> str:
        """将 HTML 转换为 Markdown"""
        # 移除 script 和 style 标签
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        
        # 处理图片
        html = re.sub(r'<img[^>]+data-src=["\']([^"\']+)["\'][^>]*>', r'![图片](\1)', html)
        html = re.sub(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', r'![图片](\1)', html)
        
        # 处理标题
        html = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n\n', html, flags=re.DOTALL)
        html = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n\n', html, flags=re.DOTALL)
        html = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n\n', html, flags=re.DOTALL)
        html = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1\n\n', html, flags=re.DOTALL)
        
        # 处理段落
        html = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', html, flags=re.DOTALL)
        
        # 处理换行
        html = re.sub(r'<br\s*/?>', '\n', html)
        
        # 处理加粗
        html = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', html, flags=re.DOTALL)
        html = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', html, flags=re.DOTALL)
        
        # 处理斜体
        html = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', html, flags=re.DOTALL)
        html = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', html, flags=re.DOTALL)
        
        # 处理链接
        html = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'[\2](\1)', html, flags=re.DOTALL)
        
        # 处理列表
        html = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', html, flags=re.DOTALL)
        html = re.sub(r'<ul[^>]*>|</ul>|<ol[^>]*>|</ol>', '', html)
        
        # 处理代码块
        html = re.sub(r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```\n\n', html, flags=re.DOTALL)
        html = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', html, flags=re.DOTALL)
        
        # 移除其他标签
        html = re.sub(r'<[^>]+>', '', html)
        
        # 解码 HTML 实体
        html = html.replace('&nbsp;', ' ')
        html = html.replace('&lt;', '<')
        html = html.replace('&gt;', '>')
        html = html.replace('&amp;', '&')
        html = html.replace('&quot;', '"')
        html = html.replace('&#39;', "'")
        
        # 清理多余空白
        html = re.sub(r'\n{3,}', '\n\n', html)
        html = html.strip()
        
        return html
    
    def save_article(self, article: dict, output_dir: str, filename: str = None) -> str:
        """
        保存文章为 Markdown 文件
        
        Args:
            article: 文章信息字典
            output_dir: 输出目录
            filename: 文件名（可选，默认使用文章标题）
            
        Returns:
            保存的文件路径
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        if not filename:
            safe_title = re.sub(r'[\\/*?:"<>|]', '_', article.get('title', 'Unknown'))
            filename = f"{safe_title}.md"
        
        filepath = os.path.join(output_dir, filename)
        
        # 构建 Markdown 内容
        md_content = f"""# {article.get('title', 'Unknown')}

**公众号**: {article.get('account', 'Unknown')}  
**发布时间**: {article.get('publish_time', 'Unknown')}  
**原文链接**: {article.get('url', '')}

---

{article.get('content', '')}

---

*本文档由自动化工具生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"已保存到: {filepath}")
        return filepath


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    # 替换 Windows 文件名非法字符
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    # 移除多余空格
    name = re.sub(r'\s+', ' ', name).strip()
    # 限制长度
    if len(name) > 100:
        name = name[:100]
    return name


def main():
    parser = argparse.ArgumentParser(description='微信公众号文章读取工具')
    parser.add_argument('url', help='文章链接')
    parser.add_argument('-o', '--output', default='.', help='输出目录（默认当前目录）')
    parser.add_argument('-n', '--name', help='自定义文件名（不含扩展名）')
    parser.add_argument('--headless', action='store_true', default=True, help='无头模式（默认开启）')
    parser.add_argument('--no-headless', dest='headless', action='store_false', help='显示浏览器窗口')
    parser.add_argument('-p', '--prefix', help='文件名前缀')
    
    args = parser.parse_args()
    
    # 读取文章
    with WechatArticleReader(headless=args.headless) as reader:
        article = reader.read_article(args.url)
        
        if 'error' in article:
            print(f"❌ 读取失败: {article['error']}")
            sys.exit(1)
        
        # 生成文件名
        if args.name:
            filename = f"{sanitize_filename(args.name)}.md"
        elif args.prefix:
            safe_title = sanitize_filename(article['title'])
            filename = f"{args.prefix}_{safe_title}.md"
        else:
            safe_title = sanitize_filename(article['title'])
            filename = f"{safe_title}.md"
        
        # 保存文章
        reader.save_article(article, args.output, filename)


if __name__ == '__main__':
    main()
