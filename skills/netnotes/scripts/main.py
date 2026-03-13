#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetNotes - 互联网笔记本主程序（预览确认版）
"""

import sys
import os
import argparse
import shutil
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from crawler import WebCrawler
from classifier import ArticleClassifier
from database import ArticleDatabase


def init_directories():
    """初始化笔记本目录结构"""
    base_dir = Path(__file__).parent.parent
    notebooks_dir = base_dir / "notebooks"
    temp_dir = base_dir / "temp"
    
    categories = ["AI", "运营商", "管理", "社会生活", "技术其他", "其他"]
    
    for category in categories:
        category_dir = notebooks_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建临时目录（用于预览）
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建数据目录
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return notebooks_dir, temp_dir, data_dir


def sanitize_filename(title: str) -> str:
    """清理文件名中的非法字符"""
    import re
    
    # Windows 非法字符: < > : " / \ | ? *
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        title = title.replace(char, '_')
    
    # 移除换行符和控制字符
    title = re.sub(r'[\n\r\t]', ' ', title)
    title = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', title)
    
    # 移除emoji
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    title = emoji_pattern.sub('', title)
    
    # 清理多余空格
    title = ' '.join(title.split())
    
    # 限制长度
    if len(title) > 80:
        title = title[:80]
    
    # 去除首尾空格和点
    title = title.strip('. ')
    
    return title.strip() or "未命名文章"


def generate_preview_content(article, url, category, tags, summary):
    """生成预览页面内容"""
    tags_section = f"**标签**: {', '.join(tags)}  \n" if tags else ""
    
    content = f"""# {article['title']}

**来源**: [{url}]({url})  
**抓取时间**: {article['fetch_time']}  
**建议分类**: {category}  
{tags_section}
---

## 摘要

{summary}

---

## 正文

{article['content']}
"""
    return content


def generate_preview_html(article, url, category, suggested_tags, summary):
    """生成HTML格式的预览页面"""
    # 转义HTML特殊字符
    title = article['title'].replace('<', '&lt;').replace('>', '&gt;')
    summary_html = summary.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
    
    tags_html = ""
    for tag in suggested_tags:
        tags_html += f'<span class="tag">{tag}</span> '
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NetNotes - 文章预览</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .info-table td {{
            padding: 10px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        .info-table td:first-child {{
            font-weight: bold;
            color: #495057;
            width: 120px;
        }}
        .summary {{
            background: #e7f3ff;
            padding: 15px;
            border-left: 4px solid #007acc;
            margin: 20px 0;
            border-radius: 0 4px 4px 0;
        }}
        .tag {{
            display: inline-block;
            background: #007acc;
            color: white;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 14px;
            margin-right: 8px;
        }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .section h2 {{
            margin-top: 0;
            color: #007acc;
        }}
        .category-option {{
            padding: 8px 12px;
            margin: 5px;
            background: #e9ecef;
            border-radius: 4px;
            display: inline-block;
            cursor: pointer;
        }}
        .category-option.recommended {{
            background: #d4edda;
            border: 2px solid #28a745;
        }}
        .confirm-btn {{
            background: #28a745;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
        }}
        .confirm-btn:hover {{
            background: #218838;
        }}
        hr {{
            border: none;
            border-top: 1px solid #dee2e6;
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NetNotes - 文章预览</h1>
        
        <table class="info-table">
            <tr><td>标题</td><td>{title}</td></tr>
            <tr><td>来源</td><td><a href="{url}" target="_blank">{url}</a></td></tr>
            <tr><td>建议分类</td><td><strong>{category}</strong></td></tr>
            <tr><td>字数</td><td>{len(article['content'])}</td></tr>
        </table>
        
        <div class="summary">
            <h3>文章摘要</h3>
            <p>{summary_html}</p>
        </div>
        
        <hr>
        
        <div class="section">
            <h2>建议标签</h2>
            {tags_html if tags_html else '<p style="color: #666;">暂无建议标签</p>'}
        </div>
        
        <hr>
        
        <div class="section">
            <h2>文章正文预览</h2>
            <p style="color: #666;">（前500字符）</p>
            <pre style="white-space: pre-wrap; word-wrap: break-word; background: #f4f4f4; padding: 15px; border-radius: 4px;">{article['content'][:500].replace('<', '&lt;').replace('>', '&gt;')}...</pre>
        </div>
        
        <hr>
        
        <p style="color: #666; font-size: 14px;">
            提示：请在下方命令行中确认分类和标签，然后保存。
        </p>
    </div>
</body>
</html>"""
    return html


def save_preview_file(content, html_content, title, temp_dir):
    """保存预览文件到临时目录"""
    safe_title = sanitize_filename(title)
    
    # 保存Markdown预览
    md_path = temp_dir / f"{safe_title}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 保存HTML预览
    html_path = temp_dir / f"{safe_title}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return md_path, html_path


def move_to_category(md_path, category, notebooks_dir):
    """将文件从临时目录移动到分类目录"""
    category_dir = notebooks_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    dest_path = category_dir / md_path.name
    
    # 处理重名
    counter = 1
    original_dest = dest_path
    while dest_path.exists():
        stem = original_dest.stem
        dest_path = category_dir / f"{stem}_{counter}.md"
        counter += 1
    
    shutil.move(str(md_path), str(dest_path))
    return dest_path


def interactive_confirm(category, suggested_tags, article, temp_dir):
    """交互式确认分类和标签"""
    categories = ["AI", "运营商", "管理", "社会生活", "技术其他", "其他"]
    
    print("\n" + "="*60)
    print("文章预览已生成，请确认以下信息:")
    print("="*60)
    
    print(f"\n[分类]")
    print(f"  建议分类: {category}")
    print(f"  可选分类: {', '.join(categories)}")
    
    user_category = input("  确认分类请按回车，或输入新分类: ").strip()
    if user_category and user_category in categories:
        category = user_category
    
    print(f"\n[标签]")
    if suggested_tags:
        print(f"  建议标签: {', '.join(suggested_tags)}")
    print(f"  格式: 多个标签用逗号分隔")
    
    user_tags = input("  请输入标签（直接回车跳过）: ").strip()
    
    if user_tags:
        tags = [t.strip() for t in user_tags.split(',') if t.strip()]
    else:
        tags = []
    
    # 询问是否保存
    print(f"\n[确认保存]")
    print(f"  分类: {category}")
    print(f"  标签: {', '.join(tags) if tags else '无'}")
    
    confirm = input("  确认保存? (y/n): ").strip().lower()
    
    if confirm == 'y':
        return category, tags, True
    else:
        return category, tags, False


def main():
    parser = argparse.ArgumentParser(description='NetNotes - 互联网笔记本')
    parser.add_argument('url', help='要保存的网页URL')
    parser.add_argument('--category', '-c', help='指定分类（跳过交互）')
    parser.add_argument('--tags', '-t', help='标签，多个标签用逗号分隔')
    parser.add_argument('--non-interactive', '-n', action='store_true', help='非交互模式，自动保存')
    parser.add_argument('--force', '-f', action='store_true', help='强制重新保存已存在的文章')
    
    args = parser.parse_args()
    
    # 初始化目录
    notebooks_dir, temp_dir, data_dir = init_directories()
    
    # 初始化组件
    crawler = WebCrawler()
    classifier = ArticleClassifier()
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    url = args.url
    
    # 检查是否已存在
    if not args.force:
        existing = db.get_article_by_url(url)
        if existing:
            print(f"[!] 文章已存在: {existing['title']}")
            print(f"    分类: {existing['category']}")
            print(f"    标签: {', '.join(existing['tags']) if existing['tags'] else '无'}")
            print(f"    路径: {existing['file_path']}")
            print(f"    使用 --force 可强制重新保存")
            return
    
    print(f"[INFO] 正在抓取: {url}")
    
    # 抓取网页
    try:
        article = crawler.fetch(url)
        if not article:
            print("[ERROR] 抓取失败，无法获取文章内容")
            return
    except Exception as e:
        print(f"[ERROR] 抓取出错: {e}")
        return
    
    print(f"[OK] 抓取成功: {article['title']}")
    print(f"     字数: {len(article['content'])}")
    
    # 生成摘要
    print("[INFO] 正在生成摘要...")
    summary = classifier.generate_summary(article['title'], article['content'])
    summary_clean = summary.encode('gbk', errors='ignore').decode('gbk')
    print(f"     摘要: {summary_clean[:100]}...")
    
    # 自动分类
    suggested_category = classifier.classify(article['title'], article['content'], summary)
    
    # 生成建议标签（从分类关键词中提取）
    suggested_tags = []
    if suggested_category == "AI":
        suggested_tags = ["AI", "人工智能", "OpenClaw"]
    elif suggested_category == "技术其他":
        suggested_tags = ["技术", "开发", "编程"]
    
    # 生成预览内容
    preview_content = generate_preview_content(article, url, suggested_category, suggested_tags, summary)
    preview_html = generate_preview_html(article, url, suggested_category, suggested_tags, summary)
    
    # 保存预览文件到临时目录
    md_path, html_path = save_preview_file(preview_content, preview_html, article['title'], temp_dir)
    
    print(f"\n[INFO] 预览文件已生成:")
    print(f"     Markdown: {md_path}")
    print(f"     HTML: {html_path}")
    
    # 处理分类和标签
    if args.non_interactive:
        # 非交互模式
        category = args.category or suggested_category
        tags = [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else []
        confirmed = True
    elif args.category and args.tags is not None:
        # 命令行指定了所有参数
        category = args.category
        tags = [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else []
        confirmed = True
    else:
        # 交互式确认
        category, tags, confirmed = interactive_confirm(suggested_category, suggested_tags, article, temp_dir)
    
    if not confirmed:
        print("\n[INFO] 已取消保存")
        print(f"[INFO] 预览文件保留在: {temp_dir}")
        return
    
    # 移动文件到分类目录
    print(f"\n[INFO] 正在保存到 {category}...")
    final_path = move_to_category(md_path, category, notebooks_dir)
    print(f"     保存路径: {final_path}")
    
    # 删除HTML预览文件
    if html_path.exists():
        html_path.unlink()
    
    # 记录到数据库
    article_id = db.add_article(
        url=url,
        title=article['title'],
        category=category,
        summary=summary,
        file_path=str(final_path),
        tags=tags
    )
    
    print("\n[OK] 完成！")
    print(f"\n[INFO] 文章信息:")
    print(f"     标题: {article['title']}")
    print(f"     分类: {category}")
    print(f"     标签: {', '.join(tags) if tags else '无'}")
    print(f"     路径: {final_path}")


if __name__ == "__main__":
    main()
