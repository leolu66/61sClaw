# -*- coding: utf-8 -*-
"""
M3: 存储管理模块
实现数据持久化、标准化、去重和索引
"""
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any

from common.models import NewsItem, StorageResult, Reflection, Thought
from common.react import ReActModule, Observations


class StorageManager(ReActModule):
    """
    存储管理器
    
    功能:
    1. 保存原始数据
    2. 数据标准化
    3. 去重处理
    4. 构建索引
    """
    
    def __init__(self, data_dir: str = "data"):
        super().__init__("StorageManager")
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.processed_dir = os.path.join(data_dir, "processed")
        self.index_dir = os.path.join(data_dir, "index")
        
        # 确保目录存在
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)
        
    def think(self, input_data: List[NewsItem]) -> Thought:
        """思考阶段: 分析数据特征"""
        items = input_data
        
        considerations = [
            f"待存储数据: {len(items)} 条",
            f"数据来源: {len(set(item.source_name for item in items))} 个来源"
        ]
        
        # 检查数据质量
        incomplete = sum(1 for item in items if not item.title or len(item.content) < 50)
        if incomplete > 0:
            considerations.append(f"不完整数据: {incomplete} 条")
        
        return Thought(
            reasoning="\n".join(considerations),
            confidence=0.9 if incomplete / len(items) < 0.2 else 0.7,
            metadata={'items': items}
        )
    
    async def act(self, thought: Any) -> List[NewsItem]:
        """执行阶段: 存储数据"""
        items = thought.metadata.get('items', [])
        
        if not items:
            return []
        
        # 1. 保存原始数据
        await self._save_raw(items)
        
        # 2. 标准化
        normalized = self._normalize(items)
        
        # 3. 去重
        deduped = self._deduplicate(normalized)
        
        # 4. 保存处理后数据
        await self._save_processed(deduped)
        
        # 5. 更新索引
        self._update_index(deduped)
        
        return deduped
    
    def observe(self, output: List[NewsItem]) -> Observations:
        """观察阶段: 统计存储结果"""
        return Observations(
            success=True,
            metadata={
                'stored_count': len(output),
                'by_source': self._count_by_source(output)
            }
        )
    
    def reflect(self, observations: Observations) -> Reflection:
        """反思阶段: 评估存储质量"""
        metadata = observations.metadata or {}
        
        stored_count = metadata.get('stored_count', 0)
        
        if stored_count == 0:
            return Reflection(
                success=False,
                issues=["未存储任何数据"],
                needs_adjustment=False
            )
        
        return Reflection(
            success=True,
            issues=[],
            needs_adjustment=False
        )
    
    async def _save_raw(self, items: List[NewsItem]):
        """保存原始数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_{timestamp}.json"
        filepath = os.path.join(self.raw_dir, filename)
        
        data = [self._item_to_dict(item) for item in items]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[Storage] 原始数据已保存: {filepath}")
    
    async def _save_processed(self, items: List[NewsItem]):
        """保存处理后数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"processed_{timestamp}.json"
        filepath = os.path.join(self.processed_dir, filename)
        
        data = [self._item_to_dict(item) for item in items]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[Storage] 处理后数据已保存: {filepath}")
    
    def _normalize(self, items: List[NewsItem]) -> List[NewsItem]:
        """数据标准化"""
        normalized = []
        
        for item in items:
            # 生成内容指纹
            if not item.content_hash:
                item.content_hash = self._generate_content_hash(item.title, item.content)
            
            # 标准化时间
            if item.published_at is None:
                item.published_at = item.collected_at
            
            normalized.append(item)
        
        return normalized
    
    def _deduplicate(self, items: List[NewsItem]) -> List[NewsItem]:
        """去重处理"""
        seen_hashes = set()
        deduped = []
        
        for item in items:
            if item.content_hash not in seen_hashes:
                seen_hashes.add(item.content_hash)
                deduped.append(item)
            else:
                print(f"[Storage] 去重: {item.title[:30]}...")
        
        return deduped
    
    def _update_index(self, items: List[NewsItem]):
        """更新索引"""
        # 按来源索引
        by_source: Dict[str, List[str]] = {}
        for item in items:
            source = item.source_name
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(item.id)
        
        # 保存索引
        index_file = os.path.join(self.index_dir, "by_source.json")
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(by_source, f, ensure_ascii=False, indent=2)
    
    def _generate_content_hash(self, title: str, content: str) -> str:
        """生成内容指纹"""
        text = f"{title}{content[:200]}"
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def _item_to_dict(self, item: NewsItem) -> Dict:
        """转换为字典"""
        return {
            'id': item.id,
            'title': item.title,
            'url': item.url,
            'content': item.content[:500],  # 限制长度
            'source_name': item.source_name,
            'source_type': item.source_type.value if item.source_type else None,
            'published_at': item.published_at.isoformat() if item.published_at else None,
            'collected_at': item.collected_at.isoformat() if item.collected_at else None,
            'keywords': item.keywords,
            'content_hash': item.content_hash
        }
    
    def _count_by_source(self, items: List[NewsItem]) -> Dict[str, int]:
        """按来源统计"""
        counts = {}
        for item in items:
            source = item.source_name
            counts[source] = counts.get(source, 0) + 1
        return counts
