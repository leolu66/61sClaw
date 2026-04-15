#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章工具 - 文章保存模块
将文章保存为 Markdown 文件
"""

import os
import re
from datetime import datetime
from typing import Dict


class ArticleSaver:
    """文章保存器"""
    
    def __init__(self, output_dir: str, naming_pattern: str = "{account}_{title}.md", 
                 use_date_subdir: bool = True):
        """
        初始化
        
        Args:
            output_dir: 基础输出目录
            naming_pattern: 文件名格式模板
            use_date_subdir: 是否使用日期子目录
        """
        self.base_dir = output_dir
        self.naming_pattern = naming_pattern
        self.use_date_subdir = use_date_subdir
        
        # 确定最终输出目录
        if use_date_subdir:
            today = datetime.now().strftime("%Y%m%d")
            self.output_dir = os.path.join(output_dir, today)
        else:
            self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"[输出] 目录: {self.output_dir}")
    
    def save(self, article: Dict, account_name: str = None) -> str:
        """
        保存文章为 Markdown
        
        Args:
            article: 文章信息字典
            account_name: 公众号名称（可选，优先使用 article 中的 account）
            
        Returns:
            保存的文件路径
        """
        # 获取公众号名称
        account = account_name or article.get('account', 'Unknown')
        
        # 为每个公众号创建子目录
        account_dir = os.path.join(self.output_dir, self._sanitize(account))
        os.makedirs(account_dir, exist_ok=True)
        
        # 生成文件名（不包含公众号前缀，因为已经在子目录中）
        title = article.get('title', 'Unknown')
        safe_title = self._sanitize(title)
        filename = f"{safe_title}.md"
        
        filepath = os.path.join(account_dir, filename)
        
        # 构建 Markdown 内容
        content = self._build_markdown(article)
        
        # 保存文件（直接覆盖）
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def _generate_filename(self, article: Dict, account: str) -> str:
        """生成文件名"""
        title = article.get('title', 'Unknown')
        
        # 清理非法字符
        safe_account = self._sanitize(account)
        safe_title = self._sanitize(title)
        
        # 应用命名模式
        filename = self.naming_pattern.format(
            account=safe_account,
            title=safe_title
        )
        
        # 确保有 .md 扩展名
        if not filename.endswith('.md'):
            filename += '.md'
        
        return filename
    
    def _sanitize(self, name: str) -> str:
        """清理文件名中的非法字符"""
        # 替换 Windows 非法字符
        name = re.sub(r'[\\/*?:"<>|]', '_', name)
        # 移除多余空格
        name = re.sub(r'\s+', ' ', name).strip()
        # 限制长度
        if len(name) > 80:
            name = name[:80]
        return name
    
    def _build_markdown(self, article: Dict) -> str:
        """构建 Markdown 内容"""
        title = article.get('title', 'Unknown')
        account = article.get('account', 'Unknown')
        publish_time = article.get('publish_time', '')
        url = article.get('url', '')
        content = article.get('content', '')
        
        md = f"""# {title}

**公众号**: {account}  
**发布时间**: {publish_time or 'Unknown'}  
**原文链接**: {url}

---

{content}

---

*Generated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        return md
    
    def get_saved_files(self) -> list:
        """获取已保存的文件列表"""
        files = []
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f.endswith('.md'):
                    files.append(os.path.join(self.output_dir, f))
        return sorted(files)
    
    def save_account_summary(self, account_name: str, summary_content: str) -> str:
        """
        保存公众号文章总结报告
        
        Args:
            account_name: 公众号名称
            summary_content: 总结内容
            
        Returns:
            保存的文件路径
        """
        filename = f"{self._sanitize(account_name)}_总结.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        return filepath
