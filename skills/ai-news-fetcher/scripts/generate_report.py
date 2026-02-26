#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 新闻汇总报告生成器
获取各来源 AI 新闻并生成一份格式化的汇总报告
"""

import os
import sys
from datetime import datetime
from fetch_ai_news import NewsFetcher


def generate_filename(output_dir: str, prefix: str = "ainews_") -> str:
    """生成报告文件名，处理重名情况"""
    date_str = datetime.now().strftime('%Y%m%d')
    base_name = f"{prefix}{date_str}.md"
    file_path = os.path.join(output_dir, base_name)

    # 如果文件已存在，添加序号
    if os.path.exists(file_path):
        counter = 1
        while True:
            new_name = f"{prefix}{date_str}_{counter}.md"
            new_path = os.path.join(output_dir, new_name)
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    return file_path


def generate_report(output_path: str, limit: int = 8) -> str:
    """生成 AI 新闻汇总报告"""
    fetcher = NewsFetcher(limit=limit)
    all_articles = {}
    print("开始获取各来源 AI 新闻...\n")

    for source_name in fetcher.SOURCES.keys():
        articles = fetcher.fetch_source(source_name)
        if articles:
            all_articles[source_name] = articles
            print(f"  [OK] {source_name}: {len(articles)}条")
        else:
            print(f"  [FAIL] {source_name}: 未获取到新闻")

    if not all_articles:
        print("\n错误：未能从任何来源获取到新闻")
        return None

    total_count = sum(len(articles) for articles in all_articles.values())
    today = datetime.now().strftime('%Y年%m月%d日')
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    lines = []
    lines.append(f"# AI 新闻日报")
    lines.append(f"\n**日期**: {today}")
    lines.append(f"**更新时间**: {update_time}")
    lines.append(f"**新闻来源**: {len(all_articles)} 个")
    lines.append(f"**文章总数**: {total_count} 篇")
    lines.append("")
    lines.append("## 目录")
    lines.append("")
    for i, source_name in enumerate(all_articles.keys(), 1):
        count = len(all_articles[source_name])
        anchor = source_name.lower().replace(' ', '-')
        lines.append(f"{i}. [{source_name}](#{anchor}) - {count}篇")
    lines.append("")
    lines.append("---")
    lines.append("")

    for source_name, articles in all_articles.items():
        lines.append(f"## {source_name}")
        lines.append("")
        lines.append("| 序号 | 标题 | 时间 | 原文 |")
        lines.append("|------|------|------|------|")
        for i, article in enumerate(articles[:8], 1):
            title = article.get('title', '无标题')[:50]
            if len(article.get('title', '')) > 50:
                title += "..."
            time_ago = article.get('time_ago', '-')
            url = article.get('url', '#')
            lines.append(f"| {i} | {title} | {time_ago} | [阅读]({url}) |")
        lines.append("")

    lines.append("## 说明")
    lines.append("")
    lines.append("本日报由 AI 新闻自动抓取生成，新闻来源为公开网络 AI 科技媒体。")
    lines.append("如需更多信息，请点击链接阅读原文。")
    lines.append("")
    lines.append(f"*最后更新时间：{update_time}*")

    content = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_path


if __name__ == "__main__":
    output_dir = r"D:\anthropic\AI_News"
    os.makedirs(output_dir, exist_ok=True)
    output_path = generate_filename(output_dir)

    print("=" * 60)
    print("AI 新闻日报生成器")
    print("=" * 60)
    print(f"\n输出目录：{output_dir}")
    print(f"目标文件：{os.path.basename(output_path)}")
    print()

    result = generate_report(output_path, limit=8)

    if result:
        print(f"\n{'=' * 60}")
        print("[成功] 报告生成成功!")
        print(f"{'=' * 60}")
        print(f"文件路径：{result}")
        print(f"文件大小：{os.path.getsize(result) / 1024:.2f} KB")
        sys.exit(0)
    else:
        print(f"\n{'=' * 60}")
        print("[失败] 报告生成失败")
        print(f"{'=' * 60}")
        sys.exit(1)
