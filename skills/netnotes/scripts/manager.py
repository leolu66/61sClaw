#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetNotes 管理工具 - 查询、搜索、统计、标签管理
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database import ArticleDatabase


def cmd_list(args):
    """列出文章"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    articles = db.list_articles(category=args.category, limit=args.limit)
    
    if not articles:
        print("没有找到文章")
        return
    
    print(f"\n[文章列表] 共 {len(articles)} 篇\n")
    print(f"{'ID':<6} {'分类':<10} {'标签':<20} {'标题':<30}")
    print("-" * 90)
    
    for article in articles:
        title = article['title'][:27] + "..." if len(article['title']) > 30 else article['title']
        tags_str = ', '.join(article['tags'])[:17] + "..." if article['tags'] and len(', '.join(article['tags'])) > 20 else ', '.join(article['tags']) if article['tags'] else '-'
        print(f"{article['id']:<6} {article['category']:<10} {tags_str:<20} {title:<30}")


def cmd_search(args):
    """搜索文章"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    articles = db.search_articles(args.keyword, limit=args.limit)
    
    if not articles:
        print(f"没有找到包含 '{args.keyword}' 的文章")
        return
    
    print(f"\n[搜索结果] '{args.keyword}' (共 {len(articles)} 篇)\n")
    print(f"{'ID':<6} {'分类':<10} {'标签':<20} {'标题':<30}")
    print("-" * 90)
    
    for article in articles:
        title = article['title'][:27] + "..." if len(article['title']) > 30 else article['title']
        tags_str = ', '.join(article['tags'])[:17] + "..." if article['tags'] and len(', '.join(article['tags'])) > 20 else ', '.join(article['tags']) if article['tags'] else '-'
        print(f"{article['id']:<6} {article['category']:<10} {tags_str:<20} {title:<30}")


def cmd_stats(args):
    """统计信息"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    stats = db.get_statistics()
    
    print("\n[NetNotes 统计]\n")
    print(f"总文章数: {stats['total']} 篇")
    print(f"总标签数: {stats['tag_count']} 个\n")
    
    if stats['categories']:
        print("分类分布:")
        for category, count in stats['categories'].items():
            bar = "#" * (count // 5 + 1)
            print(f"  {category:<10} {count:>3} 篇 {bar}")


def cmd_view(args):
    """查看文章详情"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    article = db.get_article_by_id(args.id)
    
    if not article:
        print(f"未找到 ID 为 {args.id} 的文章")
        return
    
    print(f"\n[文章详情]\n")
    print(f"ID:       {article['id']}")
    print(f"标题:     {article['title']}")
    print(f"分类:     {article['category']}")
    print(f"标签:     {', '.join(article['tags']) if article['tags'] else '无'}")
    print(f"URL:      {article['url']}")
    print(f"保存时间: {article['created_at']}")
    print(f"文件路径: {article['file_path']}")
    print(f"\n摘要:\n{article['summary']}")


def cmd_tags(args):
    """列出所有标签"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    tags = db.get_all_tags()
    
    if not tags:
        print("还没有标签")
        return
    
    print(f"\n[标签列表] 共 {len(tags)} 个\n")
    print(f"{'标签名':<20} {'文章数':<10}")
    print("-" * 35)
    
    for tag in tags:
        print(f"{tag['name']:<20} {tag['count']:<10}")


def cmd_tag_search(args):
    """按标签搜索文章"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    articles = db.search_by_tag(args.tag, limit=args.limit)
    
    if not articles:
        print(f"没有找到标签为 '{args.tag}' 的文章")
        return
    
    print(f"\n[标签搜索] '{args.tag}' (共 {len(articles)} 篇)\n")
    print(f"{'ID':<6} {'分类':<10} {'标签':<20} {'标题':<30}")
    print("-" * 90)
    
    for article in articles:
        title = article['title'][:27] + "..." if len(article['title']) > 30 else article['title']
        tags_str = ', '.join(article['tags'])[:17] + "..." if article['tags'] and len(', '.join(article['tags'])) > 20 else ', '.join(article['tags']) if article['tags'] else '-'
        print(f"{article['id']:<6} {article['category']:<10} {tags_str:<20} {title:<30}")


def cmd_add_tags(args):
    """为文章添加标签"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    # 检查文章是否存在
    article = db.get_article_by_id(args.id)
    if not article:
        print(f"未找到 ID 为 {args.id} 的文章")
        return
    
    # 解析标签
    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    
    # 添加标签
    db.add_tags_to_article(args.id, tags)
    
    print(f"[OK] 已为文章 '{article['title']}' 添加标签: {', '.join(tags)}")


def main():
    parser = argparse.ArgumentParser(description='NetNotes 管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出文章')
    list_parser.add_argument('-c', '--category', help='按分类筛选')
    list_parser.add_argument('-l', '--limit', type=int, default=100, help='限制数量')
    list_parser.set_defaults(func=cmd_list)
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索文章')
    search_parser.add_argument('keyword', help='搜索关键词')
    search_parser.add_argument('-l', '--limit', type=int, default=50, help='限制数量')
    search_parser.set_defaults(func=cmd_search)
    
    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='统计信息')
    stats_parser.set_defaults(func=cmd_stats)
    
    # view 命令
    view_parser = subparsers.add_parser('view', help='查看文章详情')
    view_parser.add_argument('id', type=int, help='文章ID')
    view_parser.set_defaults(func=cmd_view)
    
    # tags 命令
    tags_parser = subparsers.add_parser('tags', help='列出所有标签')
    tags_parser.set_defaults(func=cmd_tags)
    
    # tag 命令（按标签搜索）
    tag_parser = subparsers.add_parser('tag', help='按标签搜索文章')
    tag_parser.add_argument('tag', help='标签名')
    tag_parser.add_argument('-l', '--limit', type=int, default=50, help='限制数量')
    tag_parser.set_defaults(func=cmd_tag_search)
    
    # add-tags 命令
    add_tags_parser = subparsers.add_parser('add-tags', help='为文章添加标签')
    add_tags_parser.add_argument('id', type=int, help='文章ID')
    add_tags_parser.add_argument('tags', help='标签，多个用逗号分隔')
    add_tags_parser.set_defaults(func=cmd_add_tags)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
