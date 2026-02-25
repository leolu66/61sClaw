#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章工具 - 报告生成模块
生成读取结果的汇总报告
"""

import json
from datetime import datetime
from typing import List, Dict


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.results = []
    
    def add_result(self, account_name: str, article_title: str, 
                   status: str, filepath: str = None, error: str = None):
        """添加一条结果记录"""
        self.results.append({
            'account': account_name,
            'title': article_title,
            'status': status,  # 'success' 或 'failed'
            'filepath': filepath,
            'error': error,
            'time': datetime.now().isoformat()
        })
    
    def generate_console_report(self) -> str:
        """生成控制台报告"""
        total = len(self.results)
        success = sum(1 for r in self.results if r['status'] == 'success')
        failed = total - success
        
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("执行报告")
        lines.append("=" * 60)
        lines.append(f"总计: {total} 篇")
        lines.append(f"成功: {success} 篇")
        lines.append(f"失败: {failed} 篇")
        
        if failed > 0:
            lines.append("\n失败列表:")
            for r in self.results:
                if r['status'] == 'failed':
                    lines.append(f"  - [{r['account']}] {r['title'][:40]}...")
                    if r['error']:
                        lines.append(f"    原因: {r['error'][:50]}")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def generate_json_report(self) -> str:
        """生成 JSON 格式报告"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total': len(self.results),
                'success': sum(1 for r in self.results if r['status'] == 'success'),
                'failed': sum(1 for r in self.results if r['status'] == 'failed')
            },
            'results': self.results
        }
        return json.dumps(report, ensure_ascii=False, indent=2)
    
    def save_json_report(self, filepath: str):
        """保存 JSON 报告到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_json_report())
    
    def get_failed_items(self) -> List[Dict]:
        """获取失败的条目"""
        return [r for r in self.results if r['status'] == 'failed']
