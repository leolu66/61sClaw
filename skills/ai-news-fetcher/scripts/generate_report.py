#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI新闻汇总报告生成器
获取各来源AI新闻并生成一份格式化的汇总报告
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
    """生成AI新闻汇总报告"""

    # 创建新闻获取器
    fetcher = NewsFetcher(limit=limit)

    # 获取所有来源的新闻
    all_articles = {}
    print("开始获取各来源AI新闻...\n")

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

    # 生成报告内容
    total_count = sum(len(articles) for articles in all_articles.values())
    today = datetime.now().strftime('%Y年%m月%d日')
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    lines = []

    # 报告标题
    lines.append(f"# AI新闻日报")
    lines.append(f"\n**日期**: {today}")
    lines.append(f"**更新时间**: {update_time}")
    lines.append(f"**新闻来源**: {len(all_articles)} 个")
    lines.append(f"**文章总数**: {total_count} 篇")
    lines.append("")

    # 目录
    lines.append("## 目录")
    lines.append("")
    for i, source_name in enumerate(all_articles.keys(), 1):
        count = len(all_articles[source_name])
        lines.append(f"{i}. [{source_name}](#{source_name.lower().replace(' ', '-')}) - {count}篇")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 各来源新闻
    for source_name, articles in all_articles.items():
        # 章节标题
        lines.append(f"## {source_name}")
        lines.append("")

        # 新闻表格
        lines.append("| 序号 | 标题 | 时间 | 原文 |")
        lines.append("|------|------|------|------|")

        # 根据来源设置标题长度限制
        title_limit = 80 if source_name == "AiBase" else 50

        for idx, article in enumerate(articles, 1):
            # 处理标题长度，过长则截断
            title = article['title']
            if len(title) > title_limit:
                title = title[:title_limit-3] + "..."

            # 处理时间
            time_str = article['time'] if article['time'] != "未知时间" else "-"

            # 生成表格行
            lines.append(f"| {idx} | {title} | {time_str} | [链接]({article['link']}) |")

        lines.append("")
        lines.append("---")
        lines.append("")

    # 页脚
    lines.append("## 说明")
    lines.append("")
    lines.append("本报告由AI新闻获取工具自动生成，内容来源于国内主流AI科技媒体。")
    lines.append("如需更详细信息，请点击各文章链接阅读原文。")
    lines.append("")
    lines.append("---")
    lines.append(f"\n*报告生成时间: {update_time}*")

    # 合并内容
    content = "\n".join(lines)

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_path


def main():
    """主函数"""
    # 输出目录
    output_dir = r"D:\anthropic\AI新闻"

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名
    output_path = generate_filename(output_dir)

    print("=" * 60)
    print("AI新闻日报生成器")
    print("=" * 60)
    print(f"\n输出目录: {output_dir}")
    print(f"目标文件: {os.path.basename(output_path)}")
    print()

    # 生成报告
    result = generate_report(output_path, limit=8)

    if result:
        print(f"\n{'=' * 60}")
        print("[成功] 报告生成成功!")
        print(f"{'=' * 60}")
        print(f"文件路径: {result}")
        print(f"文件大小: {os.path.getsize(result) / 1024:.2f} KB")
        return 0
    else:
        print(f"\n{'=' * 60}")
        print("[失败] 报告生成失败")
        print(f"{'=' * 60}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
