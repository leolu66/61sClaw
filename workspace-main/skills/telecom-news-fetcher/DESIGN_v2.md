# 运营商新闻采集系统 - ReAct架构设计方案 v2.0

## 一、核心设计理念

基于 **ReAct (Reasoning + Acting)** 循环架构，每个模块执行后都进行**检验(Verify)**和**反思(Reflect)**，形成闭环优化。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ReAct 核心循环模式                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│   │ Thought │ →  │  Action │ →  │Observe  │ →  │ Reflect │                 │
│   │  思考   │    │  执行   │    │  观察   │    │  反思   │                 │
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘                 │
│        ↑                                          │                         │
│        └──────────────────────────────────────────┘                         │
│                                                                             │
│   每个模块都遵循: 计划 → 执行 → 检验 → 反思 → (必要时)重试/调整                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、系统整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    运营商新闻采集系统 - ReAct架构                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        主控循环 (Master Loop)                        │   │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌────────┐ │   │
│  │  │  M1任务 │ → │  M2采集 │ → │  M3存储 │ → │  M4汇编 │ → │ 完成   │ │   │
│  │  │  分解   │   │  引擎   │   │  管理   │   │  报告   │   │        │ │   │
│  │  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────────┘ │   │
│  │       ↓             ↓             ↓             ↓                    │   │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐              │   │
│  │  │Verify & │   │Verify & │   │Verify & │   │Verify & │              │   │
│  │  │Reflect  │   │Reflect  │   │Reflect  │   │Reflect  │              │   │
│  │  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘              │   │
│  │       └─────────────┴─────────────┴─────────────┘                    │   │
│  │                     ↓ (全局反思 & 迭代优化)                           │   │
│  │              ┌─────────────┐                                         │   │
│  │              │  全局状态机  │ ← 决定是否重试某模块/终止/降级            │   │
│  │              └─────────────┘                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        全局约束层                                    │   │
│  │  • 层次深度限制: max_depth = 3 (防止无限递归)                         │   │
│  │  • 子任务数量: max_tasks = 100 (广度限制)                            │   │
│  │  • 总耗时限制: max_duration = 10分钟                                 │   │
│  │  • 内存使用: max_memory = 500MB                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、模块详细设计

### M1: 任务分解模块 (Task Planner) - 支持分层递归

#### 3.1.1 ReAct循环实现

```python
@dataclass
class TaskNode:
    """任务树节点"""
    id: str
    level: int                    # 层级深度 (0为根)
    parent_id: Optional[str]
    task_type: str                # 'search' | 'crawl' | 'analyze'
    description: str
    keywords: List[str]
    sources: List[str]
    status: str                   # 'pending' | 'running' | 'completed' | 'failed'
    
    # ReAct相关
    thought: str                  # 生成该任务的思考过程
    verification_result: Optional[VerificationResult]
    reflection: Optional[Reflection]
    
    # 子任务
    children: List['TaskNode']
    max_children: int = 10        # 单节点子任务上限


class TaskPlanner:
    """分层任务规划器 - 带ReAct循环"""
    
    def __init__(self, config: PlannerConfig):
        self.config = config
        self.max_depth = 3            # 最大递归深度
        self.max_total_tasks = 100    # 总任务数上限
        self.current_depth = 0
        
    async def plan(self, query: UserQuery) -> TaskTree:
        """
        主入口: 生成任务树
        遵循 ReAct: Thought → Action → Observe → Reflect
        """
        # === Thought: 分析用户需求 ===
        thought = self._analyze_requirements(query)
        
        # === Action: 生成第一层任务 ===
        root = TaskNode(
            id="root",
            level=0,
            parent_id=None,
            task_type="root",
            description=thought.summary,
            thought=thought.reasoning
        )
        
        # 递归分解任务
        await self._decompose_recursive(root, query)
        
        # === Observe: 统计任务树状态 ===
        stats = self._collect_tree_stats(root)
        
        # === Reflect: 验证任务合理性 ===
        reflection = self._reflect_on_tree(root, stats)
        
        # 根据反思结果调整
        if reflection.needs_adjustment:
            root = await self._adjust_tree(root, reflection)
            
        return TaskTree(root=root, stats=stats, reflection=reflection)
    
    async def _decompose_recursive(self, node: TaskNode, query: UserQuery):
        """
        递归分解任务
        约束: level < max_depth, total_tasks < max_total_tasks
        """
        if node.level >= self.max_depth:
            node.reflection = Reflection(
                conclusion="达到最大深度，停止分解",
                action="leaf_node"
            )
            return
            
        # 根据当前层级决定分解策略
        if node.level == 0:
            # L0: 按运营商分解
            children = self._decompose_by_operator(query)
        elif node.level == 1:
            # L1: 按来源类型分解
            children = self._decompose_by_source_type(node, query)
        elif node.level == 2:
            # L2: 按关键词细化
            children = self._decompose_by_keywords(node, query)
        else:
            return
        
        # 检查总数限制
        current_count = self._count_tasks(node)
        available_slots = self.max_total_tasks - current_count
        
        if available_slots <= 0:
            node.reflection = Reflection(
                conclusion="达到任务数上限，停止分解",
                action="limit_reached"
            )
            return
            
        # 截断到可用槽位
        children = children[:available_slots]
        
        # 为每个子任务进行ReAct验证
        for child in children:
            # Thought: 为什么需要这个子任务
            child.thought = self._think_child_task(child, node)
            
            # Observe: 预估该任务的价值
            child.expected_value = self._estimate_task_value(child)
            
            # Reflect: 是否值得执行
            reflection = self._reflect_on_task(child)
            
            if reflection.should_execute:
                node.children.append(child)
                # 递归分解
                await self._decompose_recursive(child, query)
            else:
                # 记录被过滤的任务及原因
                node.filtered_children.append({
                    'task': child,
                    'reason': reflection.skip_reason
                })
    
    def _reflect_on_tree(self, root: TaskNode, stats: TreeStats) -> Reflection:
        """
        对整棵任务树进行反思
        """
        issues = []
        suggestions = []
        
        # 检查1: 任务分布是否合理
        if stats.by_level[0] > 4:  # 根任务太多
            issues.append("顶层任务过多，建议合并相似运营商查询")
            suggestions.append("将相似运营商合并为'三大运营商'统一查询")
            
        # 检查2: 来源覆盖是否充分
        if stats.source_coverage < 0.5:
            issues.append("来源覆盖率低，可能遗漏重要信息")
            suggestions.append("增加高优先级官方来源")
            
        # 检查3: 任务粒度是否合适
        avg_keywords = stats.total_keywords / stats.total_tasks
        if avg_keywords > 10:
            issues.append("平均关键词过多，任务粒度可能过粗")
            suggestions.append("进一步细分任务，减少单任务关键词数")
            
        # 检查4: 预估耗时
        if stats.estimated_duration > 600:  # 超过10分钟
            issues.append("预估耗时过长")
            suggestions.append("减少低优先级任务，或增加并发")
        
        return Reflection(
            issues=issues,
            suggestions=suggestions,
            needs_adjustment=len(issues) > 0,
            confidence=1.0 - (len(issues) * 0.2)
        )
```

#### 3.1.2 分层分解策略

```python
class DecompositionStrategies:
    """分层分解策略"""
    
    @staticmethod
    def by_operator(query: UserQuery) -> List[TaskNode]:
        """
        L0分解: 按运营商
        输入: 用户查询
        输出: 各运营商独立任务
        """
        tasks = []
        for operator in query.operators:
            tasks.append(TaskNode(
                task_type="operator_scope",
                description=f"采集{operator}相关新闻",
                keywords=[operator] + get_operator_aliases(operator),
                max_children=20  # 每个运营商最多20个子任务
            ))
        return tasks
    
    @staticmethod
    def by_source_type(parent: TaskNode, query: UserQuery) -> List[TaskNode]:
        """
        L1分解: 按来源类型
        输入: 运营商任务
        输出: 官网/行业媒体/搜索引擎等子任务
        """
        sources = [
            ('official', '官方渠道', 5, 3),      # (类型, 名称, 优先级, 最大子任务)
            ('industry', '行业媒体', 3, 5),
            ('search', '搜索引擎', 2, 8),
            ('social', '社交媒体', 1, 4),
        ]
        
        tasks = []
        for source_type, name, priority, max_sub in sources:
            # 根据优先级和预估价值决定是否创建任务
            if priority >= query.min_priority:
                tasks.append(TaskNode(
                    task_type=f"source_{source_type}",
                    description=f"从{name}采集{parent.description}",
                    keywords=parent.keywords,
                    sources=[source_type],
                    priority=priority,
                    max_children=max_sub
                ))
        return tasks
    
    @staticmethod
    def by_keywords(parent: TaskNode, query: UserQuery) -> List[TaskNode]:
        """
        L2分解: 按关键词细化
        输入: 来源任务
        输出: 具体搜索任务
        """
        # 生成关键词组合
        keyword_groups = generate_keyword_combinations(
            parent.keywords,
            query.focus_areas,
            max_combinations=parent.max_children
        )
        
        tasks = []
        for i, kw_group in enumerate(keyword_groups):
            tasks.append(TaskNode(
                task_type="concrete_search",
                description=f"搜索: {' + '.join(kw_group)}",
                keywords=kw_group,
                sources=parent.sources,
                priority=parent.priority,
                max_children=0  # 叶子节点
            ))
        return tasks
```

#### 3.1.3 任务树可视化示例

```yaml
# 任务树示例 (max_depth=3, max_tasks=100)
task_tree:
  root:
    id: "root"
    level: 0
    description: "查询中国移动、中国电信最近7天新闻"
    
    children:
      # L1: 按运营商
      - id: "op_cm"
        level: 1
        operator: "中国移动"
        
        children:
          # L2: 按来源
          - id: "cm_official"
            level: 2
            source_type: "official"
            
            children:
              # L3: 具体任务 (叶子)
              - id: "cm_official_5g"
                level: 3
                keywords: ["中国移动", "5G-A"]
                source: "10086.cn"
                
              - id: "cm_official_cloud"
                level: 3
                keywords: ["中国移动", "算力网络"]
                source: "10086.cn"
                
          - id: "cm_c114"
            level: 2
            source_type: "industry"
            
            children:
              - id: "cm_c114_tech"
                level: 3
                keywords: ["中国移动", "技术创新"]
                source: "c114.com.cn"
                
              - id: "cm_c114_biz"
                level: 3
                keywords: ["中国移动", "业务动态"]
                source: "c114.com.cn"
                
          - id: "cm_search"
            level: 2
            source_type: "search"
            
            children:
              - id: "cm_brave_ceo"
                level: 3
                keywords: ["中国移动", "杨杰", "2026"]
                source: "brave_search"
                
      - id: "op_ct"
        level: 1
        operator: "中国电信"
        # ... 类似结构
        
  stats:
    total_tasks: 24      # < max_tasks=100
    max_depth: 3         # = max_depth
    by_level: {0: 1, 1: 2, 2: 6, 3: 15}
    by_source: {official: 4, industry: 8, search: 12}
    estimated_duration: "4分30秒"
    
  reflection:
    confidence: 0.85
    issues: []
    suggestions: ["可增加中国铁塔查询以完善覆盖"]
```

---

### M2: 采集引擎模块 (Collection Engine) - 自适应策略

#### 3.2.1 ReAct循环实现

```python
@dataclass
class CollectionResult:
    """采集结果"""
    task_id: str
    success: bool
    items: List[NewsItem]
    raw_response: Optional[str]
    
    # ReAct相关
    thought: str                  # 采集策略思考
    observations: Observations    # 观察结果
    reflection: Reflection        # 反思结论
    
    # 质量指标
    quality_metrics: QualityMetrics
    
    # 自适应信息
    antispider_detected: bool
    strategy_used: str            # 实际使用的策略
    fallback_used: bool


class AdaptiveCollectionEngine:
    """自适应采集引擎 - 带ReAct循环"""
    
    def __init__(self):
        self.strategies = StrategyRegistry()
        self.playwright_manager = PlaywrightManager()
        self.request_manager = RequestManager()
        
    async def collect(self, task: TaskNode) -> CollectionResult:
        """
        主入口: 自适应采集
        ReAct: Thought → Action → Observe → Reflect → (必要时)Adapt
        """
        # === Thought: 分析任务特征，选择初始策略 ===
        thought = self._think_strategy(task)
        
        # 选择初始策略
        strategy = self._select_initial_strategy(task, thought)
        
        # === Action: 执行采集 ===
        attempt = 0
        max_attempts = 3
        
        while attempt < max_attempts:
            attempt += 1
            
            try:
                result = await self._execute_with_strategy(task, strategy)
                
                # === Observe: 观察执行结果 ===
                observations = self._observe_result(result, task)
                
                # === Reflect: 反思结果质量 ===
                reflection = self._reflect_on_collection(result, observations)
                
                if reflection.success:
                    return CollectionResult(
                        task_id=task.id,
                        success=True,
                        items=result.items,
                        thought=thought.reasoning,
                        observations=observations,
                        reflection=reflection,
                        quality_metrics=reflection.quality_metrics,
                        antispider_detected=observations.antispider_signals,
                        strategy_used=strategy.name,
                        fallback_used=attempt > 1
                    )
                
                # 需要调整策略
                if reflection.needs_strategy_change:
                    strategy = self._adapt_strategy(strategy, reflection)
                    continue
                    
                # 无法继续，返回部分结果
                if reflection.critical_failure:
                    break
                    
            except AntiSpiderDetected as e:
                # 被反爬，升级策略
                strategy = self._escalate_strategy(strategy, e)
                continue
                
            except Exception as e:
                # 其他错误，记录并尝试降级
                strategy = self._fallback_strategy(strategy, e)
                continue
        
        # 所有尝试失败
        return CollectionResult(
            task_id=task.id,
            success=False,
            items=[],
            thought=thought.reasoning,
            reflection=Reflection(
                success=False,
                conclusion=f"{max_attempts}次尝试后仍失败",
                action="abort"
            )
        )
    
    def _think_strategy(self, task: TaskNode) -> Thought:
        """
        Thought: 分析任务，生成策略选择思考
        """
        considerations = []
        
        # 分析来源特征
        source = task.sources[0] if task.sources else 'unknown'
        
        if source in ['c114', 'cnii', 'cfyys']:
            considerations.append(f"{source}是行业媒体，可能有基础反爬")
            
        if source in ['official']:
            considerations.append("官方站点通常限制较松，但需尊重robots.txt")
            
        if 'search' in task.task_type:
            considerations.append("搜索API需要控制速率，避免配额耗尽")
        
        # 分析关键词复杂度
        kw_complexity = len(task.keywords)
        if kw_complexity > 5:
            considerations.append(f"关键词较多({kw_complexity}个)，可能需要分批次查询")
        
        # 生成策略建议
        suggested_strategy = self._recommend_strategy(source, considerations)
        
        return Thought(
            reasoning="\n".join(considerations),
            suggested_strategy=suggested_strategy,
            confidence=0.8 if considerations else 0.6
        )
    
    def _observe_result(self, result: RawResult, task: TaskNode) -> Observations:
        """
        Observe: 观察采集结果，提取关键信号
        """
        observations = Observations()
        
        # 1. 反爬信号检测
        if result.status_code in [403, 429, 503]:
            observations.antispider_signals = True
            observations.block_type = result.status_code
            
        if result.response_time > 10:  # 响应过慢可能是限速
            observations.slow_response = True
            
        if 'captcha' in result.content.lower() or '验证' in result.content:
            observations.captcha_detected = True
            observations.antispider_signals = True
            
        # 2. 内容质量观察
        if result.items:
            observations.items_collected = len(result.items)
            observations.avg_content_length = sum(
                len(item.content) for item in result.items
            ) / len(result.items)
            
            # 检查内容完整性
            incomplete = sum(
                1 for item in result.items 
                if len(item.content) < 50 or not item.title
            )
            observations.incomplete_ratio = incomplete / len(result.items)
            
        # 3. 结构变化检测
        if result.items and all(
            item.title == result.items[0].title 
            for item in result.items[:3]
        ):
            observations.possible_structure_change = True
            
        return observations
    
    def _reflect_on_collection(
        self, 
        result: RawResult, 
        observations: Observations
    ) -> Reflection:
        """
        Reflect: 反思采集结果，决定下一步行动
        """
        issues = []
        metrics = QualityMetrics()
        
        # 评估1: 反爬对抗结果
        if observations.antispider_signals:
            if observations.captcha_detected:
                issues.append("检测到验证码，当前策略无法绕过")
                metrics.accessibility = 0.0
            else:
                issues.append("检测到反爬机制")
                metrics.accessibility = 0.3
        else:
            metrics.accessibility = 1.0
            
        # 评估2: 数据丰富度
        if not result.items:
            issues.append("未获取到任何数据")
            metrics.completeness = 0.0
        else:
            metrics.completeness = min(1.0, len(result.items) / 10)
            
        # 评估3: 内容质量
        if observations.incomplete_ratio > 0.5:
            issues.append(f"内容不完整率过高({observations.incomplete_ratio:.0%})")
            metrics.quality = 0.3
        elif observations.incomplete_ratio > 0.2:
            metrics.quality = 0.7
        else:
            metrics.quality = 0.9
            
        # 评估4: 时效性
        if result.items:
            recent_items = sum(
                1 for item in result.items
                if item.published_at and 
                (datetime.now() - item.published_at).days <= 7
            )
            metrics.freshness = recent_items / len(result.items)
        
        # 综合判断
        overall_score = (
            metrics.accessibility * 0.3 +
            metrics.completeness * 0.3 +
            metrics.quality * 0.25 +
            metrics.freshness * 0.15
        )
        
        # 决定下一步
        needs_change = False
        critical_failure = False
        
        if overall_score < 0.3:
            needs_change = True
            if metrics.accessibility == 0:
                critical_failure = True
        elif overall_score < 0.6:
            needs_change = True
            
        return Reflection(
            success=overall_score >= 0.6,
            quality_metrics=metrics,
            issues=issues,
            needs_strategy_change=needs_change,
            critical_failure=critical_failure,
            conclusion=f"综合得分: {overall_score:.2f}",
            action="adapt" if needs_change else "complete"
        )
```

#### 3.2.2 自适应策略选择

```python
class StrategyRegistry:
    """策略注册表 - 支持动态升级"""
    
    STRATEGIES = {
        # Level 1: 基础请求
        'basic_http': {
            'level': 1,
            'tools': ['requests'],
            'features': ['static_ua', 'no_delay'],
            'use_when': '简单站点，无反爬',
        },
        
        # Level 2: 标准爬虫
        'standard_crawl': {
            'level': 2,
            'tools': ['requests', 'bs4'],
            'features': ['ua_rotation', 'random_delay', 'cookie_persist'],
            'use_when': '一般站点，基础反爬',
        },
        
        # Level 3: 高级爬虫
        'advanced_crawl': {
            'level': 3,
            'tools': ['requests', 'bs4', 'proxy_pool'],
            'features': ['ua_rotation', 'request_fingerprint', 'proxy_rotation', 
                        'retry_backoff', 'session_management'],
            'use_when': '有较强反爬的站点',
        },
        
        # Level 4: 浏览器模拟
        'playwright_sim': {
            'level': 4,
            'tools': ['playwright'],
            'features': ['real_browser', 'js_execution', 'human_like_behavior',
                        'stealth_mode', 'viewport_rotation'],
            'use_when': '重度反爬，需要JS渲染',
        },
        
        # Level 5: 智能对抗
        'intelligent_bypass': {
            'level': 5,
            'tools': ['playwright', 'ml_detection'],
            'features': ['all_level4', 'captcha_solving', 'behavior_learning',
                        'fingerprint_randomization', 'residential_proxy'],
            'use_when': '极端反爬场景',
        },
    }
    
    def escalate(self, current: str, reason: str) -> str:
        """策略升级"""
        levels = {k: v['level'] for k, v in self.STRATEGIES.items()}
        current_level = levels.get(current, 1)
        
        for name, config in self.STRATEGIES.items():
            if config['level'] == current_level + 1:
                return name
        return current  # 已经是最高级
        
    def fallback(self, current: str) -> str:
        """策略降级"""
        levels = {k: v['level'] for k, v in self.STRATEGIES.items()}
        current_level = levels.get(current, 1)
        
        for name, config in self.STRATEGIES.items():
            if config['level'] == current_level - 1:
                return name
        return current  # 已经是最低级


class AdaptiveExecutor:
    """自适应执行器"""
    
    async def execute_with_strategy(self, task: TaskNode, strategy: str) -> RawResult:
        """根据策略类型选择执行方式"""
        
        if strategy in ['basic_http', 'standard_crawl', 'advanced_crawl']:
            return await self._http_crawl(task, strategy)
            
        elif strategy in ['playwright_sim', 'intelligent_bypass']:
            return await self._playwright_crawl(task, strategy)
            
        elif strategy == 'search_api':
            return await self._api_search(task)
            
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    async def _http_crawl(self, task: TaskNode, strategy: str) -> RawResult:
        """HTTP爬虫实现"""
        config = StrategyRegistry.STRATEGIES[strategy]
        
        headers = self._build_headers(config['features'])
        proxies = self._get_proxies(config['features'])
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                task.url,
                headers=headers,
                proxy=proxies,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                content = await resp.text()
                return RawResult(
                    status_code=resp.status,
                    content=content,
                    response_time=resp.elapsed.total_seconds()
                )
    
    async def _playwright_crawl(self, task: TaskNode, strategy: str) -> RawResult:
        """Playwright浏览器模拟"""
        config = StrategyRegistry.STRATEGIES[strategy]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self._get_random_ua(),
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            # 注入stealth脚本
            if 'stealth_mode' in config['features']:
                await context.add_init_script(self._get_stealth_script())
            
            page = await context.new_page()
            
            # 模拟人类行为
            await page.goto(task.url, wait_until='networkidle')
            await asyncio.sleep(random.uniform(2, 5))
            
            # 随机滚动
            if 'human_like_behavior' in config['features']:
                await self._human_like_scroll(page)
            
            content = await page.content()
            await browser.close()
            
            return RawResult(
                status_code=200,
                content=content,
                response_time=0  # Playwright不直接提供
            )
```

#### 3.2.3 质量评估与筛选

```python
class QualityAssessor:
    """质量评估器"""
    
    def assess(self, item: NewsItem) -> QualityScore:
        """
        多维度质量评估
        """
        scores = {}
        
        # 1. 完整性评分
        completeness_checks = [
            (item.title and len(item.title) >= 10, 0.3),
            (item.content and len(item.content) >= 100, 0.3),
            (item.published_at is not None, 0.2),
            (item.source_name is not None, 0.2),
        ]
        scores['completeness'] = sum(
            weight for check, weight in completeness_checks if check
        )
        
        # 2. 可信度评分
        source_scores = {
            '中国移动官网': 1.0,
            '中国电信官网': 1.0,
            'C114通信网': 0.8,
            '通信世界网': 0.8,
            '新浪财经': 0.6,
            '百度新闻': 0.5,
        }
        scores['credibility'] = source_scores.get(item.source_name, 0.4)
        
        # 3. 相关性评分
        keyword_matches = sum(
            1 for kw in item.keywords 
            if kw in item.title or kw in item.content[:500]
        )
        scores['relevance'] = min(1.0, keyword_matches / 3)
        
        # 4. 时效性评分
        if item.published_at:
            days_old = (datetime.now() - item.published_at).days
            if days_old <= 1:
                scores['freshness'] = 1.0
            elif days_old <= 3:
                scores['freshness'] = 0.8
            elif days_old <= 7:
                scores['freshness'] = 0.6
            elif days_old <= 30:
                scores['freshness'] = 0.4
            else:
                scores['freshness'] = 0.2
        else:
            scores['freshness'] = 0.0
        
        # 5. 内容丰富度
        content_features = [
            (len(item.content) >= 500, 0.2),
            (item.has_image, 0.1),
            ('。' in item.content or '；' in item.content, 0.1),  # 有完整句子
            (any(c.isdigit() for c in item.content), 0.1),  # 包含数字/数据
        ]
        scores['richness'] = sum(
            weight for check, weight in content_features if check
        )
        
        # 综合得分
        weights = {
            'completeness': 0.25,
            'credibility': 0.25,
            'relevance': 0.20,
            'freshness': 0.15,
            'richness': 0.15,
        }
        
        overall = sum(scores[k] * weights[k] for k in weights)
        
        return QualityScore(
            overall=overall,
            dimensions=scores,
            passed=overall >= 0.6  # 及格线
        )
    
    def filter_items(self, items: List[NewsItem], min_score: float = 0.6) -> List[NewsItem]:
        """筛选高质量条目"""
        results = []
        for item in items:
            score = self.assess(item)
            item.quality_score = score
            if score.passed:
                results.append(item)
        return results
```

---

### M3 & M4: 存储与报告模块的ReAct设计

#### 3.3.1 存储管理ReAct

```python
class StorageManagerWithReAct:
    """带反思的存储管理"""
    
    async def store(self, items: List[NewsItem]) -> StorageResult:
        # Thought: 分析数据特征
        thought = self._think_storage_strategy(items)
        
        # Action: 执行存储
        try:
            # 保存原始数据
            raw_path = await self._save_raw(items)
            
            # 标准化处理
            normalized = self._normalize(items)
            
            # 去重
            deduped = self._deduplicate(normalized)
            
            # 保存处理后的数据
            processed_path = await self._save_processed(deduped)
            
            # Observe: 观察存储结果
            observations = StorageObservations(
                raw_count=len(items),
                normalized_count=len(normalized),
                deduped_count=len(deduped),
                duplicate_rate=(len(normalized) - len(deduped)) / len(normalized)
            )
            
            # Reflect: 反思存储质量
            reflection = self._reflect_on_storage(observations)
            
            if reflection.needs_reprocess:
                # 调整参数重新处理
                deduped = await self._reprocess_with_adjustment(normalized, reflection)
            
            return StorageResult(
                success=True,
                raw_path=raw_path,
                processed_path=processed_path,
                stats=observations,
                reflection=reflection
            )
            
        except Exception as e:
            return StorageResult(success=False, error=str(e))
```

#### 3.3.2 报告汇编ReAct

```python
class ReportAssemblerWithReAct:
    """带反思的报告汇编"""
    
    async def assemble(self, items: List[NewsItem], template: str) -> Report:
        # Thought: 分析数据特征，选择报告结构
        thought = self._think_report_structure(items, template)
        
        # Action: 生成报告初稿
        draft = await self._generate_draft(items, thought.structure)
        
        # Observe: 检查报告质量
        observations = ReportObservations(
            coverage=self._check_coverage(draft, items),
            balance=self._check_operator_balance(draft),
            redundancy=self._check_redundancy(draft),
            readability=self._assess_readability(draft)
        )
        
        # Reflect: 反思报告质量
        reflection = self._reflect_on_report(draft, observations)
        
        # 根据反思优化
        if reflection.needs_improvement:
            draft = await self._improve_report(draft, reflection)
        
        return Report(
            content=draft,
            quality_observations=observations,
            reflection=reflection
        )
```

---

## 四、全局状态机与协调

```python
class GlobalCoordinator:
    """全局协调器 - 管理整个ReAct流程"""
    
    def __init__(self):
        self.constraints = GlobalConstraints(
            max_depth=3,
            max_tasks=100,
            max_duration=600,  # 10分钟
            max_memory=500*1024*1024  # 500MB
        )
        self.state = SystemState()
        
    async def run(self, query: UserQuery) -> SystemResult:
        """主协调循环"""
        start_time = time.time()
        
        # M1: 任务分解
        plan_result = await self._run_module_with_react(
            'planner',
            lambda: self.planner.plan(query)
        )
        
        if not plan_result.success:
            return SystemResult(success=False, stage='planning', error=plan_result.error)
        
        # M2: 采集执行
        collection_result = await self._run_module_with_react(
            'collector',
            lambda: self._execute_collection_plan(plan_result.output)
        )
        
        if collection_result.items:
            # M3: 存储管理
            storage_result = await self._run_module_with_react(
                'storage',
                lambda: self.storage.store(collection_result.items)
            )
            
            # M4: 报告生成
            report_result = await self._run_module_with_react(
                'assembler',
                lambda: self.assembler.assemble(
                    storage_result.processed_items,
                    query.template
                )
            )
        
        # 全局反思
        global_reflection = self._global_reflect(
            plan_result, collection_result, storage_result, report_result
        )
        
        return SystemResult(
            success=True,
            report=report_result.output,
            global_reflection=global_reflection,
            execution_time=time.time() - start_time
        )
    
    async def _run_module_with_react(self, name: str, executor) -> ModuleResult:
        """运行单个模块，带ReAct循环"""
        # 检查约束
        if not self._check_constraints():
            return ModuleResult(success=False, error="约束违反")
        
        # 执行
        try:
            output = await executor()
            return ModuleResult(success=True, output=output)
        except Exception as e:
            return ModuleResult(success=False, error=str(e))
    
    def _check_constraints(self) -> bool:
        """检查全局约束"""
        # 时间约束
        if self.state.elapsed_time > self.constraints.max_duration:
            return False
        
        # 任务数约束
        if self.state.task_count > self.constraints.max_tasks:
            return False
        
        # 内存约束
        if self.state.memory_usage > self.constraints.max_memory:
            return False
        
        return True
```

---

## 五、关键约束总结

| 约束项 | 值 | 说明 |
|-------|-----|------|
| **层次深度** | max_depth = 3 | 任务分解最多3层，防止无限递归 |
| **子任务数** | max_tasks = 100 | 单查询最多100个子任务 |
| **总耗时** | max_duration = 10分钟 | 整体超时限制 |
| **内存使用** | max_memory = 500MB | 内存上限 |
| **单节点子任务** | max_children = 10 | 每层最多10个子任务 |
| **采集重试** | max_attempts = 3 | 单任务最多3次尝试 |
| **质量及格线** | min_score = 0.6 | 数据质量及格分数 |

---

## 六、与v1设计的对比

| 特性 | v1设计 | v2 ReAct设计 |
|-----|--------|-------------|
| **架构模式** | 线性流水线 | ReAct循环 |
| **任务分解** | 单层分解 | 分层递归 + 深度/广度限制 |
| **错误处理** | 简单重试 | 反思驱动的自适应策略 |
| **采集策略** | 固定策略 | 动态升级(HTTP→Playwright) |
| **质量评估** | 简单过滤 | 多维度评分 + 反思优化 |
| **可观测性** | 基础日志 | 完整Thought/Observe/Reflect链 |
| **约束保障** | 无 | 全局约束 + 状态机 |

---

*设计文档版本: v2.0 (ReAct架构)*
*最后更新: 2026-04-30*
