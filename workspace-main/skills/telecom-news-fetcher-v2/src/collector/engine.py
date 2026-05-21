# -*- coding: utf-8 -*-
"""
M2: 采集引擎模块
实现自适应采集策略
"""
from typing import List, Dict, Optional, Any
import asyncio

from common.models import (
    TaskNode, NewsItem, CollectionResult,
    Thought, Reflection, SourceConfig
)
from common.react import ReActModule, Observations
from bootstrap.loader import get_knowledge_base
from collector.request_manager import RequestManager
from collector.spiders.base import BaseSpider, AntiSpiderDetected
from collector.spiders.c114 import C114Spider
from collector.spiders.official import OfficialSpider


class AdaptiveCollectionEngine(ReActModule):
    """
    自适应采集引擎
    
    功能:
    1. 根据任务选择合适的爬虫
    2. 实施反爬策略
    3. 失败重试和降级
    4. 质量评估
    """
    
    # 策略等级
    STRATEGIES = {
        'level_1_basic': {
            'name': '基础HTTP',
            'delay_min': 0.5,
            'delay_max': 1.5,
        },
        'level_2_standard': {
            'name': '标准爬虫',
            'delay_min': 1.0,
            'delay_max': 3.0,
        },
        'level_3_advanced': {
            'name': '高级爬虫',
            'delay_min': 2.0,
            'delay_max': 5.0,
        },
    }
    
    def __init__(self):
        super().__init__("CollectionEngine")
        self.kb = get_knowledge_base()
        self.spiders: Dict[str, BaseSpider] = {}
        self._init_spiders()
        
    def _init_spiders(self):
        """初始化爬虫"""
        for source_id, config in self.kb.sources.items():
            if not config.enabled:
                continue
                
            if source_id == 'c114':
                self.spiders[source_id] = C114Spider(config)
            elif source_id.endswith('_official'):
                self.spiders[source_id] = OfficialSpider(config)
            
    def think(self, input_data: TaskNode) -> Thought:
        """
        思考阶段: 选择采集策略
        """
        task = input_data
        considerations = []
        
        # 分析来源
        source_id = task.source_id
        if source_id and source_id in self.kb.sources:
            source_config = self.kb.sources[source_id]
            anti_spider_level = source_config.anti_spider_level
            considerations.append(f"来源反爬等级: {anti_spider_level}")
            
            # 根据反爬等级选择策略
            if anti_spider_level >= 3:
                suggested_strategy = 'level_3_advanced'
            elif anti_spider_level >= 2:
                suggested_strategy = 'level_2_standard'
            else:
                suggested_strategy = 'level_1_basic'
        else:
            suggested_strategy = 'level_2_standard'
            considerations.append("未知来源，使用保守策略")
        
        # 分析任务优先级
        if task.priority >= 5:
            considerations.append("高优先级任务，允许重试")
        
        return Thought(
            reasoning="\n".join(considerations),
            confidence=0.8 if source_id in self.spiders else 0.5,
            metadata={
                'task': task,
                'source_id': source_id,
                'strategy': suggested_strategy
            }
        )
    
    async def act(self, thought: Thought) -> List[NewsItem]:
        """
        执行阶段: 采集数据
        """
        metadata = thought.metadata or {}
        task = metadata.get('_input_data')
        source_id = metadata.get('source_id')
        strategy = metadata.get('strategy', 'level_2_standard')
        
        if not task:
            return []
        
        # 获取爬虫
        spider = self.spiders.get(source_id)
        if not spider:
            print(f"[Engine] 未找到爬虫: {source_id}")
            return []
        
        # 执行采集（带重试）
        items = []
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                print(f"[Engine] 尝试 {attempt + 1}/{max_attempts} 采集 {source_id}")
                
                items = await spider.fetch(
                    keywords=task.keywords,
                    limit=10
                )
                
                if items:
                    break
                    
            except AntiSpiderDetected as e:
                print(f"[Engine] 检测到反爬: {e}")
                if attempt < max_attempts - 1:
                    # 升级策略
                    strategy = self._escalate_strategy(strategy)
                    await asyncio.sleep(5)  # 等待后重试
                else:
                    raise
            except Exception as e:
                print(f"[Engine] 采集失败: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
        
        return items
    
    def observe(self, output: List[NewsItem]) -> Observations:
        """
        观察阶段: 评估采集结果
        """
        observations = Observations(
            success=True,
            metadata={}
        )
        
        if not output:
            observations.metadata['item_count'] = 0
            observations.metadata['quality_issues'] = ['未获取到任何数据']
        else:
            observations.metadata['item_count'] = len(output)
            
            # 检查内容完整性
            incomplete = sum(
                1 for item in output
                if len(item.content) < 50 or not item.title
            )
            observations.metadata['incomplete_ratio'] = incomplete / len(output)
        
        return observations
    
    def reflect(self, observations: Observations) -> Reflection:
        """
        反思阶段: 评估采集质量
        """
        metadata = observations.metadata or {}
        issues = []
        
        item_count = metadata.get('item_count', 0)
        if item_count == 0:
            issues.append("未获取到数据")
        elif item_count < 3:
            issues.append("获取数据量过少")
        
        incomplete_ratio = metadata.get('incomplete_ratio', 0)
        if incomplete_ratio > 0.5:
            issues.append("内容不完整率过高")
        
        return Reflection(
            success=len(issues) == 0 or item_count > 0,
            issues=issues,
            needs_adjustment=False
        )
    
    def _escalate_strategy(self, current: str) -> str:
        """升级策略"""
        levels = ['level_1_basic', 'level_2_standard', 'level_3_advanced']
        if current in levels:
            idx = levels.index(current)
            if idx < len(levels) - 1:
                return levels[idx + 1]
        return current
