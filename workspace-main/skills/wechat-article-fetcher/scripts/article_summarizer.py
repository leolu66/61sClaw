#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章工具 - 文章总结模块
为每篇文章生成简单总结
"""

import re
from typing import Dict, List
from datetime import datetime


class ArticleSummarizer:
    """文章总结器"""
    
    def __init__(self):
        pass
    
    def summarize(self, content: str, max_length: int = 200) -> str:
        """
        生成文章总结
        
        Args:
            content: 文章内容
            max_length: 总结最大长度
            
        Returns:
            总结文本
        """
        if not content:
            return "暂无内容"
        
        # 清理内容
        text = self._clean_content(content)
        
        # 提取关键句子
        sentences = self._extract_key_sentences(text)
        
        # 组合总结
        summary = " ".join(sentences)
        
        # 限制长度
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary if summary else "内容暂无法总结"
    
    def _clean_content(self, content: str) -> str:
        """清理内容"""
        # 移除 Markdown 标记
        text = re.sub(r'!\[.*?\]\(.*?\)', '', content)  # 图片
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # 链接
        text = re.sub(r'[#*`]', '', text)  # 标记符号
        text = re.sub(r'\n+', ' ', text)  # 换行转空格
        text = re.sub(r'\s+', ' ', text).strip()  # 多余空格
        return text
    
    def _extract_key_sentences(self, text: str, max_sentences: int = 3) -> List[str]:
        """提取关键句子"""
        # 按句号、问号、感叹号分割
        sentences = re.split(r'[。！？\.\!\?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return [text[:100] + "..."] if len(text) > 100 else [text]
        
        # 简单的关键词权重排序
        keywords = ['AI', '人工智能', '模型', '技术', '发布', '推出', '宣布', 
                   '研究', '报告', '分析', '显示', '表示', '认为', '预测']
        
        scored_sentences = []
        for sent in sentences[:10]:  # 只考虑前10句
            score = sum(1 for kw in keywords if kw in sent)
            # 优先选择长度适中的句子
            if 30 < len(sent) < 150:
                score += 1
            scored_sentences.append((score, sent))
        
        # 按分数排序
        scored_sentences.sort(reverse=True)
        
        # 返回前 N 句
        return [s[1] for s in scored_sentences[:max_sentences]]
    
    def generate_account_summary(self, account_name: str, articles: List[Dict]) -> str:
        """
        生成公众号文章总结报告
        
        Args:
            account_name: 公众号名称
            articles: 文章列表，每项包含 title, link, content, create_time 等
            
        Returns:
            Markdown 格式的总结报告
        """
        lines = []
        
        # 标题
        lines.append(f"# {account_name} - 文章总结报告")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**文章数量**: {len(articles)} 篇")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 文章清单
        lines.append("## 文章清单")
        lines.append("")
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Unknown')
            link = article.get('link', '')
            create_time = article.get('create_time', '')
            
            # 格式化时间
            if isinstance(create_time, int):
                create_time = datetime.fromtimestamp(create_time).strftime('%m-%d %H:%M')
            
            lines.append(f"{i}. [{title}]({link})")
            if create_time:
                lines.append(f"   - 发布时间: {create_time}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 每篇文章的总结
        lines.append("## 文章摘要")
        lines.append("")
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Unknown')
            content = article.get('content', '')
            
            lines.append(f"### {i}. {title}")
            lines.append("")
            
            # 生成总结
            summary = self.summarize(content, max_length=300)
            lines.append(summary)
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("*本报告由自动化工具生成*")
        
        return "\n".join(lines)
