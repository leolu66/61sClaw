#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetNotes 高级查询工具 - 支持多条件组合查询
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from database import ArticleDatabase


def format_article_line(article: Dict, index: int = None) -> str:
    """格式化文章列表行"""
    idx = f"[{index}]" if index else f"[{article['id']}]"
    title = article['title'][:35] + "..." if len(article['title']) > 38 else article['title']
    tags_str = ', '.join(article['tags'])[:15] + "..." if article['tags'] and len(', '.join(article['tags'])) > 18 else ', '.join(article['tags']) if article['tags'] else '-'
    date = article['created_at'][:10] if article['created_at'] else '-'
    
    return f"{idx:<6} {date:<12} {article['category']:<10} {tags_str:<20} {title}"


def cmd_search(args):
    """高级组合查询"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    # 构建查询条件
    conditions = []
    
    if args.keyword:
        conditions.append(f"关键词: '{args.keyword}'")
    if args.tag:
        conditions.append(f"标签: '{args.tag}'")
    if args.category:
        conditions.append(f"分类: '{args.category}'")
    if args.date_from:
        conditions.append(f"日期从: {args.date_from}")
    if args.date_to:
        conditions.append(f"日期到: {args.date_to}")
    
    if not conditions:
        print("请至少指定一个查询条件")
        print("使用 --help 查看可用条件")
        return
    
    print(f"\n[组合查询] {' | '.join(conditions)}\n")
    
    # 执行查询
    articles = db.advanced_search(
        keyword=args.keyword,
        tag=args.tag,
        category=args.category,
        date_from=args.date_from,
        date_to=args.date_to,
        limit=args.limit
    )
    
    if not articles:
        print("没有找到符合条件的文章")
        return
    
    print(f"找到 {len(articles)} 篇文章:\n")
    print(f"{'编号':<6} {'日期':<12} {'分类':<10} {'标签':<20} {'标题'}")
    print("-" * 100)
    
    for i, article in enumerate(articles, 1):
        print(format_article_line(article, i))
    
    # 保存结果供后续操作
    global last_search_results
    last_search_results = {i: article for i, article in enumerate(articles, 1)}
    
    print(f"\n提示: 使用 'open <编号>' 查看文章，如: python scripts/query.py open 1")


def cmd_open(args):
    """打开指定文章"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    # 获取文章
    if args.id.isdigit():
        article_id = int(args.id)
        article = db.get_article_by_id(article_id)
    else:
        # 尝试从上次搜索结果获取
        idx = int(args.id)
        if 'last_search_results' in globals() and idx in last_search_results:
            article = last_search_results[idx]
        else:
            print(f"未找到编号为 {args.id} 的文章")
            print("请先执行查询，或使用文章ID")
            return
    
    if not article:
        print(f"未找到编号为 {args.id} 的文章")
        return
    
    file_path = Path(article['file_path'])
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return
    
    print(f"\n[打开文章] {article['title']}\n")
    
    # 显示文章信息
    print(f"ID:       {article['id']}")
    print(f"标题:     {article['title']}")
    print(f"分类:     {article['category']}")
    print(f"标签:     {', '.join(article['tags']) if article['tags'] else '无'}")
    print(f"保存时间: {article['created_at']}")
    print(f"文件路径: {file_path}")
    print()
    
    # 读取并显示内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 显示前2000字符
        preview_len = min(2000, len(content))
        print("="*60)
        print(content[:preview_len])
        if len(content) > preview_len:
            print(f"\n... (共 {len(content)} 字符，使用系统编辑器查看完整内容)")
        print("="*60)
        
        # 询问是否用系统编辑器打开
        if not args.no_editor:
            user_input = input("\n是否用系统编辑器打开? (y/n): ").strip().lower()
            if user_input == 'y':
                try:
                    if sys.platform == 'win32':
                        subprocess.run(['notepad', str(file_path)], check=True)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', str(file_path)], check=True)
                    else:
                        subprocess.run(['xdg-open', str(file_path)], check=True)
                except Exception as e:
                    print(f"无法打开编辑器: {e}")
                    print(f"文件路径: {file_path}")
        
    except Exception as e:
        print(f"读取文件失败: {e}")


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
    print(f"{'编号':<6} {'日期':<12} {'分类':<10} {'标签':<20} {'标题'}")
    print("-" * 100)
    
    for i, article in enumerate(articles, 1):
        print(format_article_line(article, i))


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


def cmd_recent(args):
    """查看最近保存的文章"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db = ArticleDatabase(data_dir / "netnotes.db")
    
    days = args.days
    date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    articles = db.advanced_search(date_from=date_from, limit=args.limit)
    
    if not articles:
        print(f"最近 {days} 天内没有文章")
        return
    
    print(f"\n[最近 {days} 天] 共 {len(articles)} 篇\n")
    print(f"{'编号':<6} {'日期':<12} {'分类':<10} {'标签':<20} {'标题'}")
    print("-" * 100)
    
    for i, article in enumerate(articles, 1):
        print(format_article_line(article, i))


def main():
    parser = argparse.ArgumentParser(description='NetNotes 高级查询工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # search 命令 - 高级组合查询
    search_parser = subparsers.add_parser('search', help='高级组合查询')
    search_parser.add_argument('-k', '--keyword', help='关键词（搜索标题和摘要）')
    search_parser.add_argument('-t', '--tag', help='标签')
    search_parser.add_argument('-c', '--category', help='分类')
    search_parser.add_argument('--from', dest='date_from', help='日期从 (YYYY-MM-DD)')
    search_parser.add_argument('--to', dest='date_to', help='日期到 (YYYY-MM-DD)')
    search_parser.add_argument('-l', '--limit', type=int, default=50, help='限制数量')
    search_parser.set_defaults(func=cmd_search)
    
    # open 命令 - 打开文章
    open_parser = subparsers.add_parser('open', help='打开文章查看')
    open_parser.add_argument('id', help='文章编号（从查询结果）或文章ID')
    open_parser.add_argument('--no-editor', action='store_true', help='不使用系统编辑器')
    open_parser.set_defaults(func=cmd_open)
    
    # list 命令 - 列出文章
    list_parser = subparsers.add_parser('list', help='列出文章')
    list_parser.add_argument('-c', '--category', help='按分类筛选')
    list_parser.add_argument('-l', '--limit', type=int, default=100, help='限制数量')
    list_parser.set_defaults(func=cmd_list)
    
    # tags 命令 - 列出标签
    tags_parser = subparsers.add_parser('tags', help='列出所有标签')
    tags_parser.set_defaults(func=cmd_tags)
    
    # stats 命令 - 统计信息
    stats_parser = subparsers.add_parser('stats', help='统计信息')
    stats_parser.set_defaults(func=cmd_stats)
    
    # recent 命令 - 最近文章
    recent_parser = subparsers.add_parser('recent', help='查看最近文章')
    recent_parser.add_argument('-d', '--days', type=int, default=7, help='最近N天')
    recent_parser.add_argument('-l', '--limit', type=int, default=20, help='限制数量')
    recent_parser.set_defaults(func=cmd_recent)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print("\n使用示例:")
        print("  python scripts/query.py search -t OpenClaw          # 按标签查询")
        print("  python scripts/query.py search -k AI -c 技术其他     # 关键词+分类")
        print("  python scripts/query.py search --from 2026-03-01    # 日期范围")
        print("  python scripts/query.py open 1                      # 打开编号1的文章")
        print("  python scripts/query.py recent -d 3                 # 最近3天")
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
