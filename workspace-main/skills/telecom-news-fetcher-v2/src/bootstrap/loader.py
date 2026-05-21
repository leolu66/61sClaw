"""
Bootstrap 知识库加载器
负责从YAML文件加载知识库
"""
import os
import yaml
from datetime import datetime
from typing import Dict, List, Optional

from common.models import (
    BootstrapKnowledgeBase,
    OperatorProfile,
    OfficialSite,
    ExecutiveInfo,
    SourceConfig,
    TaskTemplate,
    SourceType
)


class BootstrapLoader:
    """Bootstrap知识库加载器"""
    
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # 默认路径: 技能目录下的bootstrap/data
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(current_dir, '..', '..', 'bootstrap', 'data')
        else:
            self.data_dir = data_dir
    
    def load(self) -> BootstrapKnowledgeBase:
        """
        加载完整的知识库
        
        Returns:
            BootstrapKnowledgeBase: 知识库对象
        """
        kb_path = os.path.join(self.data_dir, 'knowledge_base.yaml')
        
        with open(kb_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return BootstrapKnowledgeBase(
            version=data.get('version', '1.0.0'),
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat())),
            update_frequency=data.get('update_frequency', 'daily'),
            operators=self._parse_operators(data.get('operators', {})),
            executives=self._parse_executives(data.get('executives', {})),
            keyword_graph=data.get('keyword_graph', {}),
            sources=self._parse_sources(data.get('sources', {})),
            task_templates=self._parse_templates(data.get('task_templates', {})),
            event_types=data.get('event_types', {})
        )
    
    def _parse_operators(self, data: Dict) -> Dict[str, OperatorProfile]:
        """解析运营商配置"""
        operators = {}
        
        for name, op_data in data.items():
            official_sites = []
            for site_data in op_data.get('official_sites', []):
                official_sites.append(OfficialSite(
                    name=site_data['name'],
                    url=site_data['url'],
                    news_url=site_data.get('news_url', site_data['url']),
                    encoding=site_data.get('encoding', 'utf-8'),
                    selectors=site_data.get('selectors', {}),
                    priority=site_data.get('priority', 3),
                    update_frequency=site_data.get('update_frequency', 'daily')
                ))
            
            operators[name] = OperatorProfile(
                name=name,
                aliases=op_data.get('aliases', []),
                english_name=op_data.get('english_name', ''),
                stock_code=op_data.get('stock_code', ''),
                official_sites=official_sites,
                official_wechat=op_data.get('official_wechat', []),
                official_weibo=op_data.get('official_weibo'),
                business_tags=op_data.get('business_tags', []),
                recent_focus=op_data.get('recent_focus', [])
            )
        
        return operators
    
    def _parse_executives(self, data: Dict) -> Dict[str, List[ExecutiveInfo]]:
        """解析高管配置"""
        executives = {}
        
        for operator, exec_list in data.items():
            executives[operator] = []
            for exec_data in exec_list:
                executives[operator].append(ExecutiveInfo(
                    name=exec_data['name'],
                    position=exec_data['position'],
                    operator=operator,
                    level=exec_data.get('level', '集团领导'),
                    responsibilities=exec_data.get('responsibilities', []),
                    name_aliases=exec_data.get('name_aliases', []),
                    recent_topics=exec_data.get('recent_topics', [])
                ))
        
        return executives
    
    def _parse_sources(self, data: Dict) -> Dict[str, SourceConfig]:
        """解析来源配置"""
        sources = {}
        
        for source_id, source_data in data.items():
            source_type_str = source_data.get('type', 'industry')
            try:
                source_type = SourceType(source_type_str)
            except ValueError:
                source_type = SourceType.INDUSTRY
            
            sources[source_id] = SourceConfig(
                id=source_id,
                name=source_data['name'],
                type=source_type,
                url=source_data['url'],
                priority=source_data.get('priority', 3),
                selectors=source_data.get('selectors'),
                encoding=source_data.get('encoding', 'utf-8'),
                enabled=source_data.get('enabled', True),
                anti_spider_level=source_data.get('anti_spider_level', 1),
                operator=source_data.get('operator'),
                news_url=source_data.get('news_url')
            )
        
        return sources
    
    def _parse_templates(self, data: Dict) -> Dict[str, TaskTemplate]:
        """解析任务模板"""
        templates = {}
        
        for template_id, template_data in data.items():
            templates[template_id] = TaskTemplate(
                id=template_id,
                name=template_data['name'],
                description=template_data['description'],
                applicable_scenarios=template_data.get('applicable_scenarios', []),
                trigger_conditions=template_data.get('trigger_conditions', {}),
                task_structure=template_data.get('task_structure', {}),
                parameters=template_data.get('parameters', []),
                expected_output=template_data.get('expected_output', '')
            )
        
        return templates
    
    def reload(self) -> BootstrapKnowledgeBase:
        """重新加载知识库"""
        return self.load()


# 单例模式，全局知识库实例
_knowledge_base: Optional[BootstrapKnowledgeBase] = None


def get_knowledge_base(force_reload: bool = False) -> BootstrapKnowledgeBase:
    """
    获取知识库实例（单例）
    
    Args:
        force_reload: 是否强制重新加载
        
    Returns:
        BootstrapKnowledgeBase: 知识库实例
    """
    global _knowledge_base
    
    if _knowledge_base is None or force_reload:
        loader = BootstrapLoader()
        _knowledge_base = loader.load()
    
    return _knowledge_base
