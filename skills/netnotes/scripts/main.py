#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetNotes - 互联网笔记本主程序（交互式版本）
"""

import sys
import os
import argparse
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from crawler import WebCrawler
from classifier import ArticleClassifier
from database import ArticleDatabase


def init_directories():
    """初始化笔记本目录结构"""
    base_dir = Path(__file__).parent.parent
    notebooks_dir = base_dir / "notebooks"
    
    categories = ["AI", "运营商", "管理", "社会生活", "技术其他", "其他"]
    
    for category in categories:
        category_dir = notebooks_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建数据目录
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return notebooks_dir, data_dir


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


def save_article(content: str, title: str, category: str, notebooks_dir: Path) -> str:
    """保存文章到对应目录"""
    safe_title = sanitize_filename(title)
    filename = f"{safe_title}.md"
    
    category_dir = notebooks_dir / category
    file_path = category_dir / filename
    
    # 处理重名文件
    counter = 1
    original_file_path = file_path
    while file_path.exists():
        stem = original_file_path.stem
        file_path = category_dir / f"{stem}_{counter}.md"
        counter += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(file_path)


def interactive_confirm_category(classifier, title, content, summary):
    """交互式确认分类"""
    # 自动分类
    suggested_category = classifier.classify(title, content, summary)
    
    print(f"\n[INFO] 推荐分类: {suggested_category}")
    print("[INFO] 可选分类: AI, 运营商, 管理, 社会生活, 技术其他, 其他")
    
    # 询问确认
    user_input = input("确认分类请按回车，或输入新分类: ").strip()
    
    if user_input:
        # 验证输入的分类是否有效
        valid_categories = ["AI", "运营商", "管理", "社会生活", "技术其他", "其他"]
        if user_input in valid_categories:
            return user_input
        else:
            print(f"[WARN] 无效分类 '{user_input}'，使用推荐分类")
            return suggested_category
    
    return suggested_category


def interactive_input_tags():
    """交互式输入标签"""
    print("\n[INFO] 标签格式: 多个标签用逗号分隔，如: OpenClaw,架构解析,AI工具")
    user_input = input("需要添加什么标签? (直接回车跳过) ").strip()
    
    if not user_input:
        return []
    
    # 解析标签
    tags = [t.strip() for t in user_input.split(',') if t.strip()]
    return tags


def main():
    parser = argparse.ArgumentParser(description='NetNotes - 互联网笔记本')
    parser.add_argument('url', help='要保存的网页URL')
    parser.add_argument('--category', '-c', help='指定分类（跳过自动分类）')
    parser.add_argument('--tags', '-t', help='标签，多个标签用逗号分隔（非交互模式使用）')
    parser.add_argument('--non-interactive', '-n', action='store_true', help='非交互模式，自动保存')
    parser.add_argument('--force', '-f', action='store_true', help='强制重新保存已存在的文章')
    
    args = parser.parse_args()
    
    # 初始化目录
    notebooks_dir, data_dir = init_directories()
    
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
    # 清理emoji避免编码错误
    summary_clean = summary.encode('gbk', errors='ignore').decode('gbk')
    print(f"     摘要: {summary_clean}")
    
    # 处理分类
    if args.category:
        category = args.category
        print(f"[INFO] 使用指定分类: {category}")
    elif args.non_interactive:
        # 非交互模式，自动分类
        category = classifier.classify(article['title'], article['content'], summary)
        print(f"[INFO] 自动分类: {category}")
    else:
        # 交互式确认分类
        category = interactive_confirm_category(classifier, article['title'], article['content'], summary)
        print(f"[INFO] 确认分类: {category}")
    
    # 处理标签
    if args.tags:
        # 命令行指定标签
        tags = [t.strip() for t in args.tags.split(',') if t.strip()]
        print(f"[INFO] 使用标签: {', '.join(tags)}")
    elif args.non_interactive:
        # 非交互模式，无标签
        tags = []
    else:
        # 交互式输入标签
        tags = interactive_input_tags()
        if tags:
            print(f"[INFO] 添加标签: {', '.join(tags)}")
    
    # 构建Markdown内容
    tags_section = f"**标签**: {', '.join(tags)}  \n" if tags else ""
    md_content = f"""# {article['title']}

**来源**: [{url}]({url})  
**保存时间**: {article['fetch_time']}  
**分类**: {category}  
{tags_section}
---

## 摘要

{summary}

---

## 正文

{article['content']}
"""
    
    # 保存文件
    print(f"[INFO] 正在保存到 {category}...")
    file_path = save_article(md_content, article['title'], category, notebooks_dir)
    print(f"     保存路径: {file_path}")
    
    # 记录到数据库
    article_id = db.add_article(
        url=url,
        title=article['title'],
        category=category,
        summary=summary,
        file_path=file_path,
        tags=tags
    )
    
    print("\n[OK] 完成！")
    print(f"\n[INFO] 文章信息:")
    print(f"     标题: {article['title']}")
    print(f"     分类: {category}")
    print(f"     标签: {', '.join(tags) if tags else '无'}")
    print(f"     路径: {file_path}")


if __name__ == "__main__":
    main()
