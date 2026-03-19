#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本摘要技能 - 使用 OpenClaw AI 模型
支持：文本、URL、文件、YouTube
"""

import sys
import os
import json
import argparse

# 添加 lib 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from extractor import WebContentExtractor
from document_reader import DocumentReader

class Summarizer:
    """文本摘要器 - 使用 OpenClaw AI 模型"""
    
    def __init__(self, length='medium'):
        """
        初始化摘要器
        
        Args:
            length: 摘要长度 (short/medium/long)
        """
        self.length = length
        self.length_config = {
            'short': {'max_chars': 200, 'desc': '简短摘要'},
            'medium': {'max_chars': 500, 'desc': '中等摘要'},
            'long': {'max_chars': 1000, 'desc': '详细摘要'}
        }
    
    def summarize_text(self, text, title=None):
        """
        总结纯文本
        
        Args:
            text: 要总结的文本
            title: 标题（可选）
            
        Returns:
            dict: 摘要结果
        """
        if not text or len(text.strip()) == 0:
            return {
                'success': False,
                'error': '文本内容为空'
            }
        
        # 构建提示词，让 OpenClaw AI 生成摘要
        prompt = self._build_prompt(text, title)
        
        # 返回结构化数据，由 OpenClaw 调用 AI 生成摘要
        return {
            'success': True,
            'type': 'text',
            'title': title,
            'original_length': len(text),
            'prompt': prompt,
            'length_config': self.length_config[self.length],
            'note': '请使用此 prompt 调用 OpenClaw AI 生成摘要'
        }
    
    def summarize_url(self, url):
        """
        总结网页内容
        
        Args:
            url: 网页 URL
            
        Returns:
            dict: 摘要结果
        """
        try:
            # 获取网页内容
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            html = response.text
            
            # 使用智能提取器
            extractor = WebContentExtractor()
            extracted = extractor.extract(html, url)
            
            if not extracted['success']:
                return {
                    'success': False,
                    'error': extracted.get('error', '提取失败')
                }
            
            # 生成摘要
            return self.summarize_text(
                extracted['content'], 
                extracted['title'] or url
            )
            
        except Exception as e:
            return {
                'success': False,
                'error': f'获取网页失败: {str(e)}'
            }
    
    def summarize_file(self, file_path):
        """
        总结文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 摘要结果
        """
        try:
            # 使用统一的文档读取器
            result = DocumentReader.read(file_path)
            
            if not result['success']:
                return result
            
            # 生成摘要
            return self.summarize_text(
                result['content'],
                result.get('title', os.path.basename(file_path))
            )
            
        except Exception as e:
            return {
                'success': False,
                'error': f'读取文件失败: {str(e)}'
            }
    
    def summarize_youtube(self, url):
        """
        总结 YouTube 视频（通过字幕）
        
        Args:
            url: YouTube URL
            
        Returns:
            dict: 摘要结果
        """
        try:
            # 提取视频 ID
            import re
            video_id = None
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^\&\s?]+)',
                r'youtube\.com/watch\?.*v=([^\&\s]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    break
            
            if not video_id:
                return {
                    'success': False,
                    'error': '无法解析 YouTube 视频 ID'
                }
            
            # 尝试获取字幕
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['zh', 'en'])
                transcript = ' '.join([item['text'] for item in transcript_list])
            except:
                transcript = None
            
            if not transcript:
                return {
                    'success': False,
                    'error': '无法获取视频字幕（可能无字幕或需要API）'
                }
            
            title = f"YouTube Video: {video_id}"
            return self.summarize_text(transcript, title)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'获取视频字幕失败: {str(e)}'
            }
    
    def _build_prompt(self, text, title=None):
        """
        构建摘要提示词
        
        Args:
            text: 原文
            title: 标题
            
        Returns:
            str: 提示词
        """
        length_desc = self.length_config[self.length]['desc']
        max_chars = self.length_config[self.length]['max_chars']
        
        # 截断过长的文本
        if len(text) > 8000:
            text = text[:8000] + "..."
        
        prompt = f"""请对以下内容生成{length_desc}（约{max_chars}字）：

{title if title else ''}

{text}

要求：
1. 提取核心观点和关键信息
2. 保持逻辑清晰，条理分明
3. 使用简洁的语言
4. 摘要长度控制在{max_chars}字以内

请直接输出摘要内容，不需要添加标题或格式标记。"""
        
        return prompt


def main():
    parser = argparse.ArgumentParser(description='文本摘要技能')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 文本摘要
    text_parser = subparsers.add_parser('text', help='总结文本')
    text_parser.add_argument('content', help='要总结的文本')
    text_parser.add_argument('--title', '-t', help='标题')
    
    # URL 摘要
    url_parser = subparsers.add_parser('url', help='总结网页')
    url_parser.add_argument('url', help='网页 URL')
    
    # 文件摘要
    file_parser = subparsers.add_parser('file', help='总结文件')
    file_parser.add_argument('path', help='文件路径')
    
    # YouTube 摘要
    youtube_parser = subparsers.add_parser('youtube', help='总结 YouTube 视频')
    youtube_parser.add_argument('url', help='YouTube URL')
    
    # 通用参数
    parser.add_argument('--length', '-l', choices=['short', 'medium', 'long'], 
                        default='medium', help='摘要长度')
    
    args = parser.parse_args()
    
    # 创建摘要器
    summarizer = Summarizer(length=args.length)
    
    if args.command == 'text':
        result = summarizer.summarize_text(args.content, args.title)
    elif args.command == 'url':
        result = summarizer.summarize_url(args.url)
    elif args.command == 'file':
        result = summarizer.summarize_file(args.path)
    elif args.command == 'youtube':
        result = summarizer.summarize_youtube(args.url)
    else:
        parser.print_help()
        return False
    
    # 输出结果
    try:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        # 如果控制台不支持 Unicode，使用 ensure_ascii=True
        print(json.dumps(result, ensure_ascii=True, indent=2))
    return result.get('success', False)


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
