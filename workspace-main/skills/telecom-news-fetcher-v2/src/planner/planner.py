"""
M1: 任务分解模块
实现Bootstrap感知 + ReAct循环的任务规划器
"""
import re
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from common.models import (
    UserQuery, TaskNode, TaskTree, TaskStatus, SourceType,
    Thought, Reflection, TreeStats, TemplateMatch,
    BootstrapKnowledgeBase
)
from common.react import ReActModule, Observations
from bootstrap.loader import get_knowledge_base


class TaskPlanner(ReActModule):
    """
    任务规划器
    
    功能:
    1. 分析用户查询，匹配最佳模板
    2. 如模板不匹配，进行动态任务分解
    3. 使用Bootstrap知识库丰富任务
    4. 支持3层递归分解，100任务上限
    """
    
    def __init__(self, knowledge_base: Optional[BootstrapKnowledgeBase] = None):
        super().__init__("TaskPlanner")
        self.kb = knowledge_base or get_knowledge_base()
        self.max_depth = 3
        self.max_tasks = 100
        self.task_count = 0
        
    def think(self, input_data: UserQuery) -> Thought:
        """
        思考阶段: 分析查询特征
        """
        considerations = []
        
        # 1. 检测运营商
        detected_operators = self._detect_operators(input_data.text)
        considerations.append(f"检测到运营商: {detected_operators}")
        
        # 2. 解析时间范围
        date_range = self._parse_date_range(input_data.text)
        considerations.append(f"时间范围: {date_range}")
        
        # 3. 提取关键词
        keywords = self._extract_keywords(input_data.text)
        considerations.append(f"关键词: {keywords}")
        
        # 4. 判断场景
        scenario = self._detect_scenario(input_data.text)
        considerations.append(f"场景判断: {scenario}")
        
        # 5. 尝试模板匹配
        template_match = self._match_template(input_data)
        if template_match:
            considerations.append(f"匹配模板: {template_match.template.name} (置信度: {template_match.confidence:.2f})")
        
        return Thought(
            reasoning="\n".join(considerations),
            confidence=0.8 if template_match else 0.6,
            metadata={
                'detected_operators': detected_operators,
                'date_range': date_range,
                'keywords': keywords,
                'scenario': scenario,
                'template_match': template_match
            }
        )
    
    async def act(self, thought: Thought) -> TaskTree:
        """
        执行阶段: 生成任务树
        """
        metadata = thought.metadata or {}
        # 从metadata中获取原始查询
        query = metadata.get('_input_data')
        if query is None:
            # 如果没有，从reasoning中重建
            query = UserQuery(text="查询")
        template_match = metadata.get('template_match')
        
        # 如果模板匹配成功且置信度高，使用模板
        if template_match and template_match.confidence > 0.7:
            task_tree = self._instantiate_template(template_match.template, query)
        else:
            # 否则动态分解
            task_tree = self._dynamic_decompose(query)
        
        # 使用Bootstrap知识丰富任务树
        task_tree = self._enrich_with_bootstrap(task_tree)
        
        return task_tree
    
    def observe(self, output: TaskTree) -> Observations:
        """
        观察阶段: 统计任务树
        """
        stats = self._calculate_stats(output.root)
        output.stats = stats
        
        return Observations(
            success=True,
            metadata={
                'total_tasks': stats.total_tasks,
                'max_depth': stats.max_depth,
                'by_level': stats.by_level,
                'by_source': stats.by_source,
                'estimated_duration': stats.estimated_duration
            }
        )
    
    def reflect(self, observations: Observations) -> Reflection:
        """
        反思阶段: 评估任务树质量
        """
        metadata = observations.metadata or {}
        issues = []
        suggestions = []
        
        # 检查1: 任务数是否超限
        total_tasks = metadata.get('total_tasks', 0)
        if total_tasks > self.max_tasks:
            issues.append(f"任务数超限: {total_tasks} > {self.max_tasks}")
            suggestions.append("减少分解深度或合并相似任务")
        
        # 检查2: 深度是否合理
        max_depth = metadata.get('max_depth', 0)
        if max_depth > self.max_depth:
            issues.append(f"深度超限: {max_depth} > {self.max_depth}")
            suggestions.append("限制递归深度")
        
        # 检查3: 来源覆盖
        by_source = metadata.get('by_source', {})
        if 'official' not in by_source:
            issues.append("缺少官方来源")
            suggestions.append("添加官网新闻采集任务")
        
        # 检查4: 预估耗时
        estimated_duration = metadata.get('estimated_duration', 0)
        if estimated_duration > 300:  # 5分钟
            issues.append(f"预估耗时过长: {estimated_duration:.0f}秒")
            suggestions.append("减少低优先级任务或增加并发")
        
        # 检查5: 任务数过少
        if total_tasks < 3:
            issues.append("任务数过少，可能覆盖不足")
            suggestions.append("检查查询条件，扩展关键词")
        
        return Reflection(
            success=len(issues) == 0,
            issues=issues,
            suggestions=suggestions,
            needs_adjustment=len(issues) > 0 and total_tasks > self.max_tasks,
            confidence=1.0 - len(issues) * 0.15
        )
    
    async def adapt(self, output: TaskTree, reflection: Reflection) -> TaskTree:
        """
        调整阶段: 优化任务树
        """
        # 如果任务过多，进行剪枝
        if output.stats and output.stats.total_tasks > self.max_tasks:
            output.root = self._prune_tree(output.root)
            output.stats = self._calculate_stats(output.root)
        
        return output
    
    # ============ 辅助方法 ============
    
    def _detect_operators(self, text: str) -> List[str]:
        """检测查询中的运营商"""
        detected = []
        text_lower = text.lower()
        
        for name, profile in self.kb.operators.items():
            # 检查主名称
            if name in text:
                detected.append(name)
                continue
            
            # 检查别名
            for alias in profile.aliases:
                if alias.lower() in text_lower:
                    detected.append(name)
                    break
        
        return detected if detected else list(self.kb.operators.keys())
    
    def _parse_date_range(self, text: str) -> Dict[str, str]:
        """解析时间范围"""
        # 默认最近7天
        end = datetime.now()
        start = end - timedelta(days=7)
        
        # 检查特定关键词
        if '今天' in text or '今日' in text:
            start = end
        elif '昨天' in text:
            start = end - timedelta(days=1)
            end = start
        elif '最近3天' in text or '近3天' in text:
            start = end - timedelta(days=3)
        elif '最近7天' in text or '近7天' in text or '最近一周' in text:
            start = end - timedelta(days=7)
        elif '最近30天' in text or '近30天' in text or '最近一个月' in text:
            start = end - timedelta(days=30)
        
        return {
            'start': start.strftime('%Y-%m-%d'),
            'end': end.strftime('%Y-%m-%d')
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 从关键词图谱匹配
        for category, kw_list in self.kb.keyword_graph.get('business_keywords', {}).items():
            for kw_data in kw_list:
                keyword = kw_data['keyword']
                if keyword in text:
                    keywords.append(keyword)
                else:
                    # 检查别名
                    for alias in kw_data.get('aliases', []):
                        if alias in text:
                            keywords.append(keyword)
                            break
        
        return keywords
    
    def _detect_scenario(self, text: str) -> str:
        """检测场景类型"""
        # 检查事件关键词
        for event_type, event_data in self.kb.event_types.items():
            for kw in event_data.get('keywords', []):
                if kw in text:
                    return event_type
        
        return 'general'
    
    def _match_template(self, query: UserQuery) -> Optional[TemplateMatch]:
        """匹配最佳模板"""
        matches = []
        
        for template in self.kb.task_templates.values():
            score = 0.0
            reasons = []
            
            # 检查触发关键词
            trigger_keywords = template.trigger_conditions.get('keywords', [])
            for kw in trigger_keywords:
                if kw in query.text:
                    score += 0.3
                    reasons.append(f"触发词: {kw}")
            
            # 检查必需实体
            required_entities = template.trigger_conditions.get('required_entities', [])
            for entity in required_entities:
                if entity == 'operator':
                    operators = self._detect_operators(query.text)
                    if operators:
                        score += 0.4
                        reasons.append(f"实体: operator ({operators})")
            
            if score > 0.5:
                matches.append(TemplateMatch(
                    template=template,
                    confidence=min(score, 1.0),
                    reasons=reasons
                ))
        
        if matches:
            matches.sort(key=lambda x: x.confidence, reverse=True)
            return matches[0]
        
        return None
    
    def _instantiate_template(self, template: Any, query: UserQuery) -> TaskTree:
        """实例化模板"""
        root = TaskNode(
            id=str(uuid.uuid4())[:8],
            level=0,
            type='root',
            description=f"模板: {template.name}"
        )
        
        # 根据模板结构生成任务
        structure = template.task_structure
        
        # L1: 按来源类型或运营商分解
        level_1 = structure.get('level_1', {})
        if level_1.get('type') == 'by_source_type':
            for child_config in level_1.get('children', []):
                child = self._create_source_type_node(child_config, root, query)
                root.children.append(child)
                
                # L2: 按关键词组分解
                level_2 = structure.get('level_2', {})
                if level_2.get('type') == 'by_keyword_group':
                    for grandchild in self._create_keyword_group_nodes(level_2, child, query):
                        child.children.append(grandchild)
        
        return TaskTree(root=root)
    
    def _dynamic_decompose(self, query: UserQuery) -> TaskTree:
        """动态任务分解"""
        root = TaskNode(
            id=str(uuid.uuid4())[:8],
            level=0,
            type='root',
            description=query.text
        )
        
        # L1: 按运营商分解
        operators = self._detect_operators(query.text)
        for op in operators[:4]:  # 最多4个运营商
            if self._check_task_limit():
                break
            child = self._create_operator_node(op, root)
            root.children.append(child)
            
            # L2: 按来源类型分解
            for source_child in self._create_source_nodes(child, query):
                if self._check_task_limit():
                    break
                child.children.append(source_child)
                
                # L3: 按关键词细化
                for kw_child in self._create_keyword_nodes(source_child, query):
                    if self._check_task_limit():
                        break
                    source_child.children.append(kw_child)
        
        return TaskTree(root=root)
    
    def _create_operator_node(self, operator: str, parent: TaskNode) -> TaskNode:
        """创建运营商节点"""
        profile = self.kb.operators.get(operator)
        aliases = profile.aliases if profile else []
        
        return TaskNode(
            id=str(uuid.uuid4())[:8],
            level=parent.level + 1,
            type='operator',
            description=f"采集{operator}相关新闻",
            parent_id=parent.id,
            operator=operator,
            keywords=[operator] + aliases,
            priority=4
        )
    
    def _create_source_type_node(self, config: Dict, parent: TaskNode, query: UserQuery) -> TaskNode:
        """创建来源类型节点"""
        source_type = config.get('source_type', 'industry')
        priority = config.get('priority', 3)
        
        # 根据source_type确定source_id
        source_id = None
        if source_type == 'official':
            # 官方来源：尝试从parent获取operator，如果没有则使用默认
            operator = parent.operator if parent else None
            if operator:
                source_id_map = {
                    '中国移动': 'cm_official',
                    '中国电信': 'ct_official',
                    '中国联通': 'cu_official',
                    '中国铁塔': 'tower_official'
                }
                source_id = source_id_map.get(operator)
            else:
                # 默认使用中国移动
                source_id = 'cm_official'
        elif source_type == 'industry':
            source_id = 'c114'
        
        return TaskNode(
            id=str(uuid.uuid4())[:8],
            level=parent.level + 1,
            type='source_type',
            description=f"从{source_type}采集",
            parent_id=parent.id,
            source_type=SourceType(source_type) if source_type in [t.value for t in SourceType] else SourceType.INDUSTRY,
            source_id=source_id,
            keywords=parent.keywords if parent else [],
            priority=priority
        )
    
    def _create_source_nodes(self, parent: TaskNode, query: UserQuery) -> List[TaskNode]:
        """创建来源节点"""
        nodes = []
        operator = parent.operator
        
        # 添加官方来源
        if operator:
            official_sources = [
                (f"{operator}_official", 5),
            ]
            for source_id, priority in official_sources:
                if source_id in self.kb.sources:
                    nodes.append(TaskNode(
                        id=str(uuid.uuid4())[:8],
                        level=parent.level + 1,
                        type='source',
                        description=f"官方来源: {source_id}",
                        parent_id=parent.id,
                        operator=operator,
                        source_id=source_id,
                        keywords=parent.keywords,
                        priority=priority
                    ))
        
        # 添加行业媒体
        industry_sources = ['c114']
        for source_id in industry_sources:
            if source_id in self.kb.sources:
                nodes.append(TaskNode(
                    id=str(uuid.uuid4())[:8],
                    level=parent.level + 1,
                    type='source',
                    description=f"行业媒体: {source_id}",
                    parent_id=parent.id,
                    operator=operator,
                    source_id=source_id,
                    keywords=parent.keywords,
                    priority=3
                ))
        
        return nodes
    
    def _create_keyword_group_nodes(self, config: Dict, parent: TaskNode, query: UserQuery) -> List[TaskNode]:
        """创建关键词组节点"""
        nodes = []
        groups = config.get('groups', [])
        
        # 确定source_id
        source_id = parent.source_id
        if not source_id and parent.operator:
            # 根据运营商和source_type推断source_id
            if parent.source_type == SourceType.OFFICIAL:
                source_id_map = {
                    '中国移动': 'cm_official',
                    '中国电信': 'ct_official',
                    '中国联通': 'cu_official',
                    '中国铁塔': 'tower_official'
                }
                source_id = source_id_map.get(parent.operator)
            elif parent.source_type == SourceType.INDUSTRY:
                source_id = 'c114'
        
        for group_name in groups:
            # 从知识库获取该组关键词
            group_keywords = self.kb.keyword_graph.get('business_keywords', {}).get(group_name, [])
            for kw_data in group_keywords[:3]:  # 每组最多3个关键词
                nodes.append(TaskNode(
                    id=str(uuid.uuid4())[:8],
                    level=parent.level + 1,
                    type='keyword_group',
                    description=f"关键词: {kw_data['keyword']}",
                    parent_id=parent.id,
                    operator=parent.operator,
                    source_id=source_id,
                    keywords=parent.keywords + [kw_data['keyword']],
                    priority=parent.priority
                ))
        
        return nodes
    
    def _create_keyword_nodes(self, parent: TaskNode, query: UserQuery) -> List[TaskNode]:
        """创建关键词节点"""
        nodes = []
        
        # 提取查询中的关键词
        keywords = self._extract_keywords(query.text)
        
        # 如果没有提取到，使用默认关键词
        if not keywords:
            keywords = ['5G', 'AI', '云']
        
        for kw in keywords[:3]:  # 最多3个关键词
            nodes.append(TaskNode(
                id=str(uuid.uuid4())[:8],
                level=parent.level + 1,
                type='concrete',
                description=f"搜索: {kw}",
                parent_id=parent.id,
                operator=parent.operator,
                source_id=parent.source_id,
                keywords=parent.keywords + [kw],
                priority=parent.priority
            ))
        
        return nodes
    
    def _enrich_with_bootstrap(self, tree: TaskTree) -> TaskTree:
        """使用Bootstrap知识丰富任务树"""
        
        def enrich_node(node: TaskNode):
            # 注入运营商别名
            if node.operator and node.operator in self.kb.operators:
                profile = self.kb.operators[node.operator]
                node.keywords = list(set(node.keywords + profile.aliases))
            
            # 注入高管别名
            if node.operator and node.operator in self.kb.executives:
                for exec in self.kb.executives[node.operator]:
                    if exec.name in node.keywords or any(alias in node.keywords for alias in exec.name_aliases):
                        node.keywords = list(set(node.keywords + exec.name_aliases))
            
            # 注入关键词关联
            for kw in node.keywords[:]:
                # 查找相关关键词
                for category, kw_list in self.kb.keyword_graph.get('business_keywords', {}).items():
                    for kw_data in kw_list:
                        if kw_data['keyword'] == kw:
                            node.keywords = list(set(node.keywords + kw_data.get('related', [])))
            
            # 递归处理子节点
            for child in node.children:
                enrich_node(child)
        
        enrich_node(tree.root)
        return tree
    
    def _calculate_stats(self, root: TaskNode) -> TreeStats:
        """计算任务树统计"""
        total_tasks = 0
        max_depth = 0
        by_level: Dict[int, int] = {}
        by_source: Dict[str, int] = {}
        
        def traverse(node: TaskNode, depth: int):
            nonlocal total_tasks, max_depth
            
            total_tasks += 1
            max_depth = max(max_depth, depth)
            by_level[depth] = by_level.get(depth, 0) + 1
            
            if node.source_id:
                by_source[node.source_id] = by_source.get(node.source_id, 0) + 1
            elif node.source_type:
                by_source[node.source_type.value] = by_source.get(node.source_type.value, 0) + 1
            
            for child in node.children:
                traverse(child, depth + 1)
        
        traverse(root, 0)
        
        # 预估耗时（每任务约3秒）
        estimated_duration = total_tasks * 3
        
        return TreeStats(
            total_tasks=total_tasks,
            max_depth=max_depth,
            by_level=by_level,
            by_source=by_source,
            estimated_duration=estimated_duration
        )
    
    def _check_task_limit(self) -> bool:
        """检查是否超过任务数限制"""
        self.task_count += 1
        return self.task_count > self.max_tasks
    
    def _prune_tree(self, node: TaskNode, max_children: int = 5) -> TaskNode:
        """剪枝：限制子节点数量"""
        if len(node.children) > max_children:
            # 按优先级排序，保留高优先级任务
            node.children.sort(key=lambda x: x.priority, reverse=True)
            node.children = node.children[:max_children]
        
        # 递归处理子节点
        for child in node.children:
            self._prune_tree(child, max_children)
        
        return node
