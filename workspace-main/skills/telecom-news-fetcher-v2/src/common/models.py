"""
公共数据模型
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# ============ 枚举类型 ============

class SourceType(Enum):
    OFFICIAL = "official"
    INDUSTRY = "industry"
    MEDIA = "media"
    FINANCE = "finance"
    SEARCH = "search"
    SOCIAL = "social"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NewsCategory(Enum):
    BUSINESS = "业务动态"
    TECHNOLOGY = "技术创新"
    COOPERATION = "战略合作"
    FINANCIAL = "财务数据"
    POLICY = "政策公告"
    SOCIAL = "社会责任"


# ============ Bootstrap 数据模型 ============

@dataclass
class OfficialSite:
    """官方网站配置"""
    name: str
    url: str
    news_url: str
    encoding: str
    selectors: Dict[str, str]
    priority: int
    update_frequency: str


@dataclass
class OperatorProfile:
    """运营商档案"""
    name: str
    aliases: List[str]
    english_name: str
    stock_code: str
    official_sites: List[OfficialSite]
    official_wechat: List[str]
    official_weibo: Optional[str]
    business_tags: List[str]
    recent_focus: List[str]


@dataclass
class ExecutiveInfo:
    """高管信息"""
    name: str
    position: str
    operator: str
    level: str
    responsibilities: List[str]
    name_aliases: List[str]
    recent_topics: List[str]


@dataclass
class KeywordNode:
    """关键词节点"""
    keyword: str
    aliases: List[str]
    related: List[str]
    priority: int
    category: str


@dataclass
class SourceConfig:
    """来源配置"""
    id: str
    name: str
    type: SourceType
    url: str
    priority: int
    selectors: Optional[Dict[str, str]] = None
    encoding: str = "utf-8"
    enabled: bool = True
    anti_spider_level: int = 1
    operator: Optional[str] = None
    news_url: Optional[str] = None


@dataclass
class TaskTemplate:
    """任务模板"""
    id: str
    name: str
    description: str
    applicable_scenarios: List[str]
    trigger_conditions: Dict[str, Any]
    task_structure: Dict[str, Any]
    parameters: List[Dict[str, Any]]
    expected_output: str


@dataclass
class BootstrapKnowledgeBase:
    """Bootstrap知识库"""
    version: str
    last_updated: datetime
    update_frequency: str
    operators: Dict[str, OperatorProfile]
    executives: Dict[str, List[ExecutiveInfo]]
    keyword_graph: Dict[str, Any]
    sources: Dict[str, SourceConfig]
    task_templates: Dict[str, TaskTemplate]
    event_types: Dict[str, Any]


# ============ 运行时数据模型 ============

@dataclass
class UserQuery:
    """用户查询"""
    text: str
    operators: Optional[List[str]] = None
    date_range: Optional[Dict[str, str]] = None
    focus_areas: Optional[List[str]] = None
    output_format: str = "markdown"


@dataclass
class TaskNode:
    """任务树节点"""
    id: str
    level: int
    type: str
    description: str
    parent_id: Optional[str] = None
    operator: Optional[str] = None
    source_type: Optional[SourceType] = None
    source_id: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    url: Optional[str] = None
    priority: int = 3
    status: TaskStatus = TaskStatus.PENDING
    thought: Optional[str] = None
    reflection: Optional['Reflection'] = None
    children: List['TaskNode'] = field(default_factory=list)


@dataclass
class TaskTree:
    """任务树"""
    root: TaskNode
    stats: Optional['TreeStats'] = None
    reflection: Optional['Reflection'] = None


@dataclass
class TreeStats:
    """任务树统计"""
    total_tasks: int
    max_depth: int
    by_level: Dict[int, int]
    by_source: Dict[str, int]
    estimated_duration: float


@dataclass
class NewsItem:
    """新闻条目"""
    id: str
    title: str
    url: str
    content: str
    source_name: str
    collected_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    source_type: SourceType = SourceType.INDUSTRY
    source_url: Optional[str] = None
    summary: Optional[str] = None
    operators: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    quality_score: Optional['QualityScore'] = None
    credibility_score: float = 0.0
    content_hash: Optional[str] = None
    similar_to: List[str] = field(default_factory=list)


@dataclass
class QualityScore:
    """质量评分"""
    overall: float
    dimensions: Dict[str, float]
    passed: bool


# ============ ReAct 相关模型 ============

@dataclass
class Thought:
    """思考过程"""
    reasoning: str
    confidence: float = 0.8
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Reflection:
    """反思结果"""
    success: bool
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    needs_adjustment: bool = False
    confidence: float = 0.8
    action: str = "complete"  # complete | adapt | retry | abort


@dataclass
class ModuleResult:
    """模块执行结果"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    reflection: Optional[Reflection] = None


@dataclass
class CollectionResult:
    """采集结果"""
    success: bool
    task_id: str
    items: List[NewsItem] = field(default_factory=list)
    strategy_used: str = ""
    attempt_count: int = 1
    error: Optional[str] = None


@dataclass
class StorageResult:
    """存储结果"""
    success: bool
    processed_items: List[NewsItem] = field(default_factory=list)
    observations: Optional[Dict[str, Any]] = None
    reflection: Optional[Reflection] = None
    error: Optional[str] = None


@dataclass
class Report:
    """报告"""
    content: str
    quality_observations: Optional[Dict[str, Any]] = None
    reflection: Optional[Reflection] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemResult:
    """系统结果"""
    success: bool
    report: Optional[Report] = None
    statistics: Optional[Dict[str, Any]] = None
    global_reflection: Optional[Reflection] = None
    execution_time: float = 0.0
    error: Optional[str] = None


# ============ 模板匹配相关 ============

@dataclass
class TemplateMatch:
    """模板匹配结果"""
    template: TaskTemplate
    confidence: float
    reasons: List[str] = field(default_factory=list)


# ============ 约束相关 ============

@dataclass
class GlobalConstraints:
    """全局约束"""
    max_depth: int = 3
    max_tasks: int = 100
    max_duration: float = 600
    max_memory: int = 524288000
    max_retries: int = 3
    min_quality_score: float = 0.6
