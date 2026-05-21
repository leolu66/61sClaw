# -*- coding: utf-8 -*-
"""
M4: 报告汇编模块
生成结构化新闻报告
"""
from datetime import datetime
from typing import List, Dict, Any, Tuple

from common.models import NewsItem, Report, Reflection, Thought
from common.react import ReActModule, Observations


class ReportAssembler(ReActModule):
    """
    报告汇编器
    
    功能:
    1. 按模板汇总新闻
    2. 生成智能摘要
    3. 分类统计
    4. 多格式输出
    """
    
    def __init__(self):
        super().__init__("ReportAssembler")
        
    def think(self, input_data: Tuple[List[NewsItem], Any]) -> Thought:
        """思考阶段: 分析数据特征"""
        items, query = input_data
        
        considerations = [
            f"待生成报告数据: {len(items)} 条",
            f"查询: {query.text[:50]}..."
        ]
        
        # 分析数据分布
        by_source = {}
        for item in items:
            source = item.source_name
            by_source[source] = by_source.get(source, 0) + 1
        
        considerations.append(f"来源分布: {by_source}")
        
        return Thought(
            reasoning="\n".join(considerations),
            confidence=0.9,
            metadata={'items': items, 'query': query}
        )
    
    async def act(self, thought: Any) -> str:
        """执行阶段: 生成报告"""
        metadata = thought.metadata or {}
        items = metadata.get('items', [])
        query = metadata.get('query')
        
        if not items:
            return "未找到相关新闻"
        
        # 生成Markdown报告
        report = self._generate_markdown(items, query)
        
        return report
    
    def observe(self, output: str) -> Observations:
        """观察阶段"""
        return Observations(
            success=True,
            metadata={'report_length': len(output)}
        )
    
    def reflect(self, observations: Observations) -> Reflection:
        """反思阶段"""
        return Reflection(
            success=True,
            needs_adjustment=False
        )
    
    def _generate_markdown(self, items: List[NewsItem], query: Any) -> str:
        """生成Markdown格式报告"""
        lines = []
        
        # 标题
        lines.append("# 运营商新闻采集报告")
        lines.append("")
        
        # 元信息
        lines.append(f"**查询**: {query.text}")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**新闻总数**: {len(items)} 条")
        lines.append("")
        
        # 按来源分组
        by_source: Dict[str, List[NewsItem]] = {}
        for item in items:
            source = item.source_name
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(item)
        
        # 统计
        lines.append("## 统计概览")
        lines.append("")
        for source, source_items in by_source.items():
            lines.append(f"- **{source}**: {len(source_items)} 条")
        lines.append("")
        
        # 详细列表
        lines.append("## 新闻列表")
        lines.append("")
        
        for i, item in enumerate(items, 1):
            lines.append(f"### {i}. {item.title}")
            lines.append("")
            lines.append(f"- **来源**: {item.source_name}")
            if item.published_at:
                lines.append(f"- **时间**: {item.published_at.strftime('%Y-%m-%d')}")
            lines.append(f"- **链接**: {item.url}")
            if item.keywords:
                lines.append(f"- **关键词**: {', '.join(item.keywords[:5])}")
            if item.content and len(item.content) > 10:
                content_preview = item.content[:200] + "..." if len(item.content) > 200 else item.content
                lines.append(f"- **摘要**: {content_preview}")
            lines.append("")
        
        # 页脚
        lines.append("---")
        lines.append("")
        lines.append("*由运营商新闻采集系统自动生成*")
        
        return "\n".join(lines)
