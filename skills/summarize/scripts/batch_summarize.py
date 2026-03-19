#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量摘要处理器
支持：批量处理目录、批量处理文件列表
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 添加 lib 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from document_reader import DocumentReader

class BatchSummarizer:
    """批量摘要处理器"""
    
    def __init__(self, length='medium', recursive=False, output_dir=None):
        """
        初始化批量处理器
        
        Args:
            length: 摘要长度 (short/medium/long)
            recursive: 是否递归处理子目录
            output_dir: 输出目录（可选）
        """
        self.length = length
        self.recursive = recursive
        self.output_dir = output_dir
        self.length_config = {
            'short': {'max_chars': 200, 'desc': '简短摘要'},
            'medium': {'max_chars': 500, 'desc': '中等摘要'},
            'long': {'max_chars': 1000, 'desc': '详细摘要'}
        }
    
    def process_directory(self, directory, file_pattern=None):
        """
        批量处理目录中的所有文档
        
        Args:
            directory: 目录路径
            file_pattern: 文件匹配模式，如 "*.pdf" 或 "*.docx"
            
        Returns:
            dict: 处理结果
        """
        if not os.path.isdir(directory):
            return {
                'success': False,
                'error': f'目录不存在: {directory}'
            }
        
        # 收集所有支持的文件
        files = self._collect_files(directory, file_pattern)
        
        if not files:
            return {
                'success': False,
                'error': f'目录中没有找到支持的文档文件: {directory}'
            }
        
        print(f"找到 {len(files)} 个文件待处理...")
        
        # 批量处理
        return self._process_files(files)
    
    def process_file_list(self, file_list_path):
        """
        从文件列表批量处理
        
        Args:
            file_list_path: 文件列表路径（每行一个文件路径）
            
        Returns:
            dict: 处理结果
        """
        if not os.path.exists(file_list_path):
            return {
                'success': False,
                'error': f'文件列表不存在: {file_list_path}'
            }
        
        # 读取文件列表
        files = []
        with open(file_list_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                file_path = line.strip()
                if file_path and os.path.exists(file_path):
                    files.append(file_path)
                elif file_path:
                    print(f"警告: 文件不存在，已跳过: {file_path}")
        
        if not files:
            return {
                'success': False,
                'error': '文件列表中没有有效的文件路径'
            }
        
        print(f"从列表中加载了 {len(files)} 个文件...")
        
        # 批量处理
        return self._process_files(files)
    
    def _collect_files(self, directory, pattern=None):
        """收集目录中的文件"""
        files = []
        
        # 支持的扩展名
        supported_exts = list(DocumentReader.SUPPORTED_FORMATS.keys())
        
        if self.recursive:
            # 递归遍历
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    ext = os.path.splitext(filename)[1].lower()
                    
                    # 检查是否匹配模式
                    if pattern and not filename.endswith(pattern.replace('*', '')):
                        continue
                    
                    # 检查是否是支持的格式
                    if ext in supported_exts:
                        files.append(file_path)
        else:
            # 仅当前目录
            for item in os.listdir(directory):
                file_path = os.path.join(directory, item)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(item)[1].lower()
                    
                    # 检查是否匹配模式
                    if pattern and not item.endswith(pattern.replace('*', '')):
                        continue
                    
                    # 检查是否是支持的格式
                    if ext in supported_exts:
                        files.append(file_path)
        
        return sorted(files)
    
    def _process_files(self, files):
        """处理文件列表"""
        results = []
        success_count = 0
        failed_count = 0
        
        for idx, file_path in enumerate(files, 1):
            print(f"\n[{idx}/{len(files)}] 处理: {os.path.basename(file_path)}")
            
            # 读取文档
            doc_result = DocumentReader.read(file_path)
            
            if not doc_result['success']:
                print(f"  [FAIL] 读取失败: {doc_result.get('error', '未知错误')}")
                failed_count += 1
                results.append({
                    'file': file_path,
                    'success': False,
                    'error': doc_result.get('error', '读取失败')
                })
                continue
            
            # 生成摘要 prompt
            prompt = self._build_prompt(
                doc_result['content'],
                doc_result.get('title', os.path.basename(file_path))
            )
            
            result_item = {
                'file': file_path,
                'success': True,
                'title': doc_result.get('title'),
                'type': doc_result.get('type'),
                'format': doc_result.get('format'),
                'original_length': doc_result.get('length', 0),
                'prompt': prompt,
                'length_config': self.length_config[self.length]
            }
            
            results.append(result_item)
            success_count += 1
            print(f"  [OK] 成功 (原始长度: {result_item['original_length']} 字符)")
            
            # 如果指定了输出目录，保存单个结果
            if self.output_dir:
                self._save_single_result(result_item)
        
        # 汇总结果
        summary = {
            'success': True,
            'action': 'batch_process',
            'total_files': len(files),
            'success_count': success_count,
            'failed_count': failed_count,
            'length': self.length,
            'results': results
        }
        
        # 如果指定了输出目录，保存汇总结果
        if self.output_dir:
            self._save_summary(summary)
        
        return summary
    
    def _build_prompt(self, text, title=None):
        """构建摘要提示词"""
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
    
    def _save_single_result(self, result):
        """保存单个结果"""
        if not self.output_dir:
            return
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(result['file']))[0]
        output_file = os.path.join(self.output_dir, f"{base_name}.summary.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"  [SAVE] 已保存: {output_file}")
    
    def _save_summary(self, summary):
        """保存汇总结果"""
        if not self.output_dir:
            return
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        output_file = os.path.join(self.output_dir, 'batch_summary.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n[SUMMARY] 汇总结果已保存: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='批量摘要处理器')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 批量处理目录
    dir_parser = subparsers.add_parser('directory', help='批量处理目录')
    dir_parser.add_argument('path', help='目录路径')
    dir_parser.add_argument('--pattern', '-p', help='文件匹配模式，如 "*.pdf"')
    dir_parser.add_argument('--recursive', '-r', action='store_true', help='递归处理子目录')
    
    # 批量处理文件列表
    list_parser = subparsers.add_parser('list', help='从文件列表批量处理')
    list_parser.add_argument('file', help='文件列表路径（每行一个文件路径）')
    
    # 通用参数
    parser.add_argument('--length', '-l', choices=['short', 'medium', 'long'], 
                        default='medium', help='摘要长度')
    parser.add_argument('--output', '-o', help='输出目录（可选）')
    
    args = parser.parse_args()
    
    # 创建批量处理器
    batcher = BatchSummarizer(
        length=args.length,
        recursive=getattr(args, 'recursive', False),
        output_dir=args.output
    )
    
    if args.command == 'directory':
        result = batcher.process_directory(args.path, args.pattern)
    elif args.command == 'list':
        result = batcher.process_file_list(args.file)
    else:
        parser.print_help()
        return False
    
    # 输出结果
    try:
        print("\n" + "="*50)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print("\n" + "="*50)
        print(json.dumps(result, ensure_ascii=True, indent=2))
    
    return result.get('success', False)


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
