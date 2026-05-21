# -*- coding: utf-8 -*-
"""
爬虫基类
所有具体爬虫都应继承此类
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime

from common.models import NewsItem, SourceConfig


class BaseSpider(ABC):
    """爬虫基类"""
    
    def __init__(self, config: SourceConfig):
        self.config = config
        self.name = config.name
        self.source_id = config.id
        
    @abstractmethod
    async def fetch(
        self,
        keywords: List[str],
        limit: int = 10,
        **kwargs
    ) -> List[NewsItem]:
        """获取新闻"""
        pass
    
    def create_news_item(
        self,
        title: str,
        url: str,
        content: str = "",
        published_at: Optional[datetime] = None,
        **kwargs
    ) -> NewsItem:
        """创建新闻条目"""
        return NewsItem(
            id=self._generate_id(url),
            title=title,
            url=url,
            content=content,
            source_name=self.config.name,
            published_at=published_at,
            **kwargs
        )
    
    def _generate_id(self, url: str) -> str:
        """生成唯一ID"""
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:12]
    
    def _extract_date(self, date_str: str) -> Optional[datetime]:
        """从字符串提取日期"""
        import re
        
        if not date_str:
            return None
        
        patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
            (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),
            (r'(\d{1,2})-(\d{1,2})', '%m-%d'),
            (r'(\d{1,2})月(\d{1,2})日', '%m月%d日'),
        ]
        
        for pattern, fmt in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if fmt == '%m-%d' or fmt == '%m月%d日':
                        year = datetime.now().year
                        date_str_full = f"{year}-{match.group(1)}-{match.group(2)}"
                        return datetime.strptime(date_str_full, '%Y-%m-%d')
                    else:
                        return datetime.strptime(match.group(0), fmt)
                except ValueError:
                    continue
        
        return None


class AntiSpiderDetected(Exception):
    """反爬检测异常"""
    pass
