#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章工具 - 主程序 (重构版)
支持单公众号处理和批次调度
"""

import os
import sys
import random
import time
import json
from typing import List, Dict, Optional
from datetime import datetime

# 添加当前目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from config import get_config
from article_list_fetcher import ArticleListFetcher
from article_content_reader import ArticleContentReader
from article_saver import ArticleSaver
from article_summarizer import ArticleSummarizer
from report_generator import ReportGenerator


class WechatArticleTool:
    """微信公众号文章工具主类"""
    
    def __init__(self, config_path: str = None):
        """初始化"""
        self.config = get_config(config_path)
        self.report = ReportGenerator()
        self.summarizer = ArticleSummarizer()
        
        # 初始化各模块
        self.list_fetcher = ArticleListFetcher(
            cookie=self.config.cookie,
            token=self.config.token
        )
        
        # 初始化保存器（使用日期子目录）
        self.saver = ArticleSaver(
            output_dir=self.config.get("output.base_dir", r"D:\anthropic\wechat"),
            naming_pattern=self.config.get("output.naming_pattern", "{account}_{title}.md"),
            use_date_subdir=self.config.get("output.use_date_subdir", True)
        )
        
        # 加载进度文件
        self.progress_file = os.path.join(self.saver.output_dir, ".progress.json")
        self.progress = self._load_progress()
    
    def _load_progress(self) -> Dict:
        """加载处理进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            'completed': [],  # 已完成的公众号
            'failed': [],     # 失败的公众号
            'last_run': None  # 上次运行时间
        }
    
    def _save_progress(self):
        """保存处理进度"""
        self.progress['last_run'] = datetime.now().isoformat()
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
    
    def process_single_account(self, account_name: str, interactive: bool = True) -> List[dict]:
        """
        处理单个公众号
        
        Args:
            account_name: 公众号名称
            interactive: 是否交互式（出错时提示用户）
            
        Returns:
            处理的文章列表
        """
        print(f"\n{'='*60}")
        print(f"[处理] 公众号: {account_name}")
        print('='*60)
        
        # 1. 获取文章列表（智能数量）
        result = self.list_fetcher.fetch_account_articles(
            account_name,
            limit=self.config.get("fetch.max_articles", 10),
            min_articles=self.config.get("fetch.min_articles", 3),
            days_threshold=self.config.get("fetch.days_threshold", 3)
        )
        
        # 检查是否出现错误
        error = result.get('error')
        if error:
            print(f"\n[错误] 获取公众号失败: {error}")
            print("[暂停] 可能是以下原因：")
            print("       1. Cookie/Token 过期")
            print("       2. 触发腾讯限制")
            print("       3. 网络问题")
            
            if interactive:
                print("\n[建议] 请检查：")
                print("       - 访问 https://mp.weixin.qq.com 确认是否需要重新登录")
                print("       - 检查 Cookie 和 Token 是否有效")
                response = input("\n请选择: (c[继续]/r[重试]/s[跳过]/q[退出]): ").strip().lower()
                if response == 'r':
                    return self.process_single_account(account_name, interactive)
                elif response == 's':
                    self.progress['failed'].append(account_name)
                    self._save_progress()
                    return []
                elif response == 'q':
                    print("[退出] 程序已终止")
                    sys.exit(0)
                else:
                    self.progress['failed'].append(account_name)
                    self._save_progress()
                    return []
            else:
                self.progress['failed'].append(account_name)
                self._save_progress()
                return []
        
        articles = result.get('articles', [])
        if not articles:
            print(f"[警告] 未获取到文章")
            self.progress['completed'].append(account_name)
            self._save_progress()
            return []
        
        # 2. 读取每篇文章内容
        processed_articles = []
        min_delay = self.config.get("fetch.min_delay", 2)
        max_delay = self.config.get("fetch.max_delay", 5)
        
        with ArticleContentReader(headless=True) as reader:
            for i, article in enumerate(articles, 1):
                title = article.get('title', 'Unknown')
                url = article.get('link', '')
                
                print(f"\n[{i}/{len(articles)}] {title[:50]}...")
                
                try:
                    content_data = reader.read(url, timeout=self.config.get("fetch.timeout", 30))
                    
                    if 'error' in content_data:
                        self.report.add_result(account_name, title, 'failed', error=content_data['error'])
                        continue
                    
                    full_article = {
                        'title': title,
                        'account': account_name,
                        'publish_time': content_data.get('publish_time', ''),
                        'url': url,
                        'content': content_data.get('content', ''),
                        'create_time': article.get('create_time', 0)
                    }
                    
                    filepath = self.saver.save(full_article, account_name)
                    self.report.add_result(account_name, title, 'success', filepath)
                    processed_articles.append(full_article)
                    
                except Exception as e:
                    self.report.add_result(account_name, title, 'failed', error=str(e))
                
                if i < len(articles):
                    time.sleep(random.uniform(min_delay, max_delay))
        
        # 3. 生成公众号总结报告
        if processed_articles:
            self._generate_account_summary(account_name, processed_articles)
        
        # 4. 记录完成
        self.progress['completed'].append(account_name)
        if account_name in self.progress['failed']:
            self.progress['failed'].remove(account_name)
        self._save_progress()
        
        return processed_articles
    
    def generate_summary_for_account(self, account_name: str, interactive: bool = True) -> bool:
        """
        为指定公众号生成总结报告（基于已保存的文章）
        
        Args:
            account_name: 公众号名称
            interactive: 是否交互式
            
        Returns:
            是否成功生成
        """
        print(f"\n{'='*60}")
        print(f"[生成总结] 公众号: {account_name}")
        print('='*60)
        
        # 检查公众号目录是否存在
        account_dir = os.path.join(self.saver.output_dir, account_name)
        if not os.path.exists(account_dir):
            print(f"[错误] 未找到公众号目录: {account_dir}")
            if interactive:
                response = input("是否跳过？(y/n): ").strip().lower()
                if response == 'n':
                    return False
            return False
        
        # 读取所有文章文件
        articles = []
        for filename in os.listdir(account_dir):
            if filename.endswith('.md') and not filename.endswith('_总结.md'):
                filepath = os.path.join(account_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 解析文章信息
                    title = self._extract_title(content, filename)
                    url = self._extract_url(content)
                    publish_time = self._extract_publish_time(content)
                    
                    articles.append({
                        'title': title,
                        'account': account_name,
                        'link': url,  # 使用 'link' 而不是 'url'
                        'content': content,
                        'create_time': publish_time
                    })
                except Exception as e:
                    print(f"[警告] 读取文件失败 {filename}: {e}")
        
        if not articles:
            print(f"[警告] 未找到文章")
            return False
        
        print(f"[信息] 找到 {len(articles)} 篇文章")
        
        # 生成总结报告
        self._generate_account_summary(account_name, articles)
        
        return True
    
    def _generate_account_summary(self, account_name: str, articles: List[dict]):
        """生成公众号文章总结报告"""
        print(f"\n[总结] 正在生成 {account_name} 的文章总结报告...")
        
        summary_content = self.summarizer.generate_account_summary(account_name, articles)
        summary_path = self.saver.save_account_summary(account_name, summary_content)
        
        print(f"[完成] 总结报告已保存: {os.path.basename(summary_path)}")
    
    def _extract_title(self, content: str, filename: str) -> str:
        """从文章内容或文件名提取标题"""
        import re
        
        # 尝试从 Markdown 标题提取（支持 # 或 ## 开头的标题）
        lines = content.split('\n')
        content_title = None
        for line in lines[:10]:  # 只检查前10行
            line = line.strip()
            # 匹配 # 标题 或 ## 标题
            if line.startswith('# ') or line.startswith('## '):
                title = re.sub(r'^#+\s*', '', line).strip()
                # 排除常见的非标题行（如公众号名称）
                if title and len(title) > 3:
                    content_title = title
                    break
        
        # 如果内容中的标题有效且不是 "Unknown"，使用内容标题
        if content_title and content_title != 'Unknown':
            return content_title
        
        # 否则尝试从文件名提取（移除 .md 后缀）
        file_title = filename.replace('.md', '')
        # 检查文件名是否有意义（长度足够且不只是字母数字）
        if len(file_title) >= 5:
            return file_title
        
        # 如果文件名无效，返回内容标题（即使是 Unknown）
        return content_title if content_title else 'Unknown'
    
    def _extract_url(self, content: str) -> str:
        """从文章内容提取原文链接"""
        for line in content.split('\n'):
            if '原文链接' in line:
                # 提取 URL
                import re
                match = re.search(r'https?://[^\s\n]+', line)
                if match:
                    return match.group(0)
        return ''
    
    def _extract_publish_time(self, content: str) -> str:
        """从文章内容提取发布时间"""
        for line in content.split('\n'):
            if '发布时间' in line:
                return line.split(':', 1)[-1].strip()
        return ''
    
    def _extract_articles_from_summary(self, summary_content: str) -> list:
        """
        从公众号总结报告中提取文章列表
        
        Returns:
            文章列表，每项包含 title, url, time
        """
        import re
        articles = []
        
        # 查找文章清单部分
        in_article_list = False
        current_article = {}
        
        for line in summary_content.split('\n'):
            line = line.strip()
            
            # 文章清单开始
            if '## 文章清单' in line:
                in_article_list = True
                continue
            
            # 文章清单结束（遇到下一个 ## 标题）
            if in_article_list and line.startswith('## '):
                break
            
            if in_article_list:
                # 匹配文章标题行: 1. [标题](链接)
                title_match = re.match(r'^\d+\.\s*\[([^\]]+)\]\(([^)]+)\)', line)
                if title_match:
                    current_article = {
                        'title': title_match.group(1),
                        'url': title_match.group(2),
                        'time': ''
                    }
                
                # 匹配发布时间行: - 发布时间: xxx
                time_match = re.search(r'发布时间[:：]\s*(.+)', line)
                if time_match and current_article:
                    current_article['time'] = time_match.group(1).strip()
                    articles.append(current_article)
                    current_article = {}
        
        return articles
    
    def generate_master_summary(self):
        """
        生成主汇总报告，包含所有公众号的文章列表
        文件名格式: Summary_YYYYMMDD_HHMM.md
        """
        print("\n" + "="*60)
        print("[生成] 主汇总报告")
        print("="*60)
        
        # 获取所有公众号目录
        accounts = []
        for item in os.listdir(self.saver.output_dir):
            item_path = os.path.join(self.saver.output_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                accounts.append(item)
        
        if not accounts:
            print("[错误] 未找到公众号目录")
            return
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"Summary_{timestamp}.md"
        filepath = os.path.join(self.saver.output_dir, filename)
        
        # 构建汇总报告内容
        lines = []
        lines.append(f"# 微信公众号文章汇总报告")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**公众号数量**: {len(accounts)} 个")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 公众号列表表格
        lines.append("## 公众号列表")
        lines.append("")
        lines.append("| 序号 | 公众号 | 文章数 | 总结报告 |")
        lines.append("|------|--------|--------|----------|")
        
        total_articles = 0
        for i, account in enumerate(sorted(accounts), 1):
            account_dir = os.path.join(self.saver.output_dir, account)
            
            # 统计文章数量
            article_count = 0
            for f in os.listdir(account_dir):
                if f.endswith('.md') and not f.endswith('_总结.md'):
                    article_count += 1
            
            total_articles += article_count
            
            # 总结报告文件名
            summary_file = f"{account}_总结.md"
            summary_path = os.path.join(self.saver.output_dir, summary_file)
            
            # 如果总结文件存在，创建链接
            if os.path.exists(summary_path):
                # 使用相对路径链接
                summary_link = f"[{account}_总结.md](./{summary_file})"
            else:
                summary_link = "未生成"
            
            lines.append(f"| {i} | {account} | {article_count} | {summary_link} |")
        
        lines.append("")
        lines.append(f"**总计**: {total_articles} 篇文章")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 每个公众号的文章列表
        lines.append("## 文章详情")
        lines.append("")
        
        for account in sorted(accounts):
            account_dir = os.path.join(self.saver.output_dir, account)
            
            lines.append(f"### {account}")
            lines.append("")
            
            # 获取该公众号的所有文章
            articles = []
            for filename in os.listdir(account_dir):
                if filename.endswith('.md') and not filename.endswith('_总结.md'):
                    article_filepath = os.path.join(account_dir, filename)
                    try:
                        with open(article_filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        title = self._extract_title(content, filename)
                        url = self._extract_url(content)
                        publish_time = self._extract_publish_time(content)
                        
                        articles.append({
                            'title': title,
                            'url': url,
                            'time': publish_time
                        })
                    except Exception as e:
                        print(f"[警告] 读取文件失败 {filename}: {e}")
            
            # 如果没有找到文章文件，尝试从总结报告中提取
            if not articles:
                summary_file = os.path.join(self.saver.output_dir, f"{account}_总结.md")
                if os.path.exists(summary_file):
                    try:
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary_content = f.read()
                        
                        # 从总结报告中提取文章清单部分
                        articles = self._extract_articles_from_summary(summary_content)
                    except Exception as e:
                        print(f"[警告] 读取总结报告失败 {account}: {e}")
            
            if articles:
                lines.append(f"**文章数**: {len(articles)} 篇")
                lines.append("")
                lines.append("| 序号 | 文章标题 | 发布时间 |")
                lines.append("|------|----------|----------|")
                
                for i, article in enumerate(articles, 1):
                    title = article['title']
                    url = article['url']
                    time = article['time']
                    
                    # 对标题中的 | 进行转义，避免破坏 Markdown 表格
                    title = title.replace('|', '\\|')
                    
                    # 如果URL存在，创建链接
                    if url:
                        title_link = f"[{title}]({url})"
                    else:
                        title_link = title
                    
                    lines.append(f"| {i} | {title_link} | {time} |")
                
                lines.append("")
            else:
                lines.append("*暂无文章*")
                lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("*本报告由自动化工具生成*")
        
        # 保存汇总报告
        content = "\n".join(lines)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[完成] 主汇总报告已保存: {filename}")
        print(f"       路径: {filepath}")
        print(f"       公众号: {len(accounts)} 个")
        print(f"       总文章: {total_articles} 篇")
        
        return filepath
    
    def generate_all_summaries(self, interactive: bool = True):
        """
        为所有已处理的公众号生成总结报告
        
        Args:
            interactive: 是否交互式
        """
        print("=" * 60)
        print("批量生成公众号总结报告")
        print("=" * 60)
        
        # 获取所有公众号目录
        accounts = []
        for item in os.listdir(self.saver.output_dir):
            item_path = os.path.join(self.saver.output_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                accounts.append(item)
        
        if not accounts:
            print("[错误] 未找到公众号目录")
            return
        
        print(f"\n[信息] 找到 {len(accounts)} 个公众号")
        
        success_count = 0
        for i, account in enumerate(accounts, 1):
            print(f"\n[{i}/{len(accounts)}] 处理: {account}")
            if self.generate_summary_for_account(account, interactive=False):
                success_count += 1
        
        print(f"\n[完成] 成功生成 {success_count}/{len(accounts)} 个总结报告")
    
    def run_batch(self, batch_size: int = 3, mode: str = 'auto'):
        """
        批次处理模式
        
        Args:
            batch_size: 每批处理的公众号数量
            mode: 'auto' 自动调度, 'manual' 手动调度
        """
        accounts = self.config.enabled_accounts
        if not accounts:
            print("[错误] 没有启用的公众号，请在配置文件中添加")
            return
        
        # 过滤已完成的公众号
        pending_accounts = [a for a in accounts if a not in self.progress['completed']]
        
        print("=" * 60)
        print("微信公众号文章获取工具 v2.0")
        print("=" * 60)
        print(f"\n[配置] 全部公众号: {len(accounts)} 个")
        print(f"[配置] 已完成: {len(self.progress['completed'])} 个")
        print(f"[配置] 待处理: {len(pending_accounts)} 个")
        print(f"[配置] 失败: {len(self.progress['failed'])} 个")
        print(f"[配置] 批次大小: {batch_size} 个")
        print(f"[配置] 调度模式: {'自动' if mode == 'auto' else '手动'}")
        
        if not pending_accounts:
            print("\n[完成] 所有公众号已处理完毕！")
            return
        
        # 随机打乱（反爬）
        if self.config.get("fetch.random_order", True):
            random.shuffle(pending_accounts)
        
        # 分批处理
        all_articles = []
        total_batches = (len(pending_accounts) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(pending_accounts))
            batch_accounts = pending_accounts[start_idx:end_idx]
            
            print(f"\n{'='*60}")
            print(f"[批次 {batch_idx + 1}/{total_batches}] 公众号: {', '.join(batch_accounts)}")
            print('='*60)
            
            if mode == 'manual':
                response = input("\n是否处理该批次？(y[是]/n[跳过]/q[退出]): ").strip().lower()
                if response == 'n':
                    continue
                elif response == 'q':
                    print("[退出] 程序已终止")
                    break
            
            # 处理当前批次
            for account in batch_accounts:
                articles = self.process_single_account(account, interactive=True)
                all_articles.extend(articles)
                time.sleep(random.uniform(2, 4))
            
            # 批次间暂停
            if batch_idx < total_batches - 1:
                if mode == 'auto':
                    print(f"\n[批次完成] 自动模式下 10秒后继续...")
                    time.sleep(10)
                else:
                    response = input("\n[批次完成] 按回车继续下一批次，或输入 q 退出: ").strip().lower()
                    if response == 'q':
                        break
        
        # 生成总报告
        print(f"\n[汇总] 共处理 {len(all_articles)} 篇文章")
        print(self.report.generate_console_report())
        
        report_path = os.path.join(self.saver.output_dir, "report.json")
        self.report.save_json_report(report_path)
        print(f"\n[报告] 总报告已保存: {report_path}")
    
    def run_single(self, account_name: str):
        """处理单个公众号（命令行直接调用）"""
        print("=" * 60)
        print("微信公众号文章获取工具 v2.0 - 单公众号模式")
        print("=" * 60)
        
        articles = self.process_single_account(account_name, interactive=True)
        
        print(f"\n[完成] 共处理 {len(articles)} 篇文章")
        
        # 保存报告
        report_path = os.path.join(self.saver.output_dir, "report.json")
        self.report.save_json_report(report_path)


def prompt_for_credentials():
    """交互式提示用户输入 Cookie 和 Token"""
    print("\n" + "=" * 60)
    print("微信凭证输入")
    print("=" * 60)
    print("提示: Cookie 和 Token 有效期较短，过期后需要重新获取")
    print("获取方式: 访问 https://mp.weixin.qq.com -> 扫码登录 -> F12开发者工具")
    print("=" * 60 + "\n")
    
    cookie = input("请输入 Cookie (直接回车使用配置文件中的值): ").strip()
    token = input("请输入 Token (直接回车使用配置文件中的值): ").strip()
    
    return cookie if cookie else None, token if token else None


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='微信公众号文章获取工具')
    parser.add_argument('-c', '--config', help='配置文件路径')
    parser.add_argument('--cookie', help='微信 Cookie（覆盖配置）')
    parser.add_argument('--token', help='微信 Token（覆盖配置）')
    parser.add_argument('--prompt', '-p', action='store_true', help='交互式提示输入 Cookie 和 Token')
    
    # 模式选择
    parser.add_argument('--mode', '-m', 
                       choices=['batch', 'single', 'summary', 'summary-all', 'master-summary'], 
                       default='batch',
                       help='运行模式: batch=批次处理, single=单公众号, summary=生成单个总结, summary-all=生成所有总结, master-summary=生成主汇总报告')
    
    # 批次处理参数
    parser.add_argument('--batch-size', '-b', type=int, default=3, help='每批处理的公众号数量')
    parser.add_argument('--schedule', '-s', choices=['auto', 'manual'], default='auto',
                       help='调度模式: auto=自动, manual=手动')
    
    # 单公众号参数
    parser.add_argument('--account', '-a', help='指定公众号名称（用于 single 或 summary 模式）')
    
    args = parser.parse_args()
    
    # 如果命令行提供了 cookie/token，设置环境变量
    if args.cookie:
        os.environ['WECHAT_COOKIE'] = args.cookie
    if args.token:
        os.environ['WECHAT_TOKEN'] = args.token
    
    # 如果指定了 --prompt 参数，交互式提示输入
    if args.prompt:
        cookie, token = prompt_for_credentials()
        if cookie:
            os.environ['WECHAT_COOKIE'] = cookie
        if token:
            os.environ['WECHAT_TOKEN'] = token
    
    # 运行工具
    tool = WechatArticleTool(args.config)
    
    if args.mode == 'single' and args.account:
        # 单公众号模式
        tool.run_single(args.account)
    elif args.mode == 'summary' and args.account:
        # 生成单个公众号总结
        tool.generate_summary_for_account(args.account, interactive=True)
    elif args.mode == 'summary-all':
        # 生成所有公众号总结
        tool.generate_all_summaries(interactive=True)
    elif args.mode == 'master-summary':
        # 生成主汇总报告
        tool.generate_master_summary()
    else:
        # 批次处理模式
        tool.run_batch(batch_size=args.batch_size, mode=args.schedule)


if __name__ == '__main__':
    main()
