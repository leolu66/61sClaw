# 运营商新闻采集系统 - ReAct + Bootstrap架构设计方案 v3.0

## 一、核心设计理念

在ReAct架构基础上，增加**Bootstrap机制**——系统启动时预先检索和维护关键领域知识，形成可复用的**子任务模板库**，提升任务分解的效率和准确性。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Bootstrap + ReAct 双循环架构                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                        Bootstrap 循环 (预加载)                        │  │
│   │                                                                     │  │
│   │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │  │
│   │   │ 知识发现 │ →  │ 信息提取 │ →  │ 模板生成 │ →  │ 持续更新 │     │  │
│   │   │ Discover │    │ Extract  │    │ Template │    │ Refresh  │     │  │
│   │   └──────────┘    └──────────┘    └──────────┘    └──────────┘     │  │
│   │         ↑                                            │              │  │
│   │         └────────────────────────────────────────────┘              │  │
│   │                                                                     │  │
│   │   输出: 运营商知识库 + 高管数据库 + 关键词图谱 + 子任务模板库           │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      主流程 ReAct 循环 (运行时)                        │  │
│   │                                                                     │  │
│   │   M1任务分解 ──→ M2采集引擎 ──→ M3存储管理 ──→ M4报告汇编            │  │
│   │      ↑              ↑              ↑              ↑                │  │
│   │      └──────────────┴──────────────┴──────────────┘                │  │
│   │                    Bootstrap知识库注入                              │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、Bootstrap机制详解

### 2.1 Bootstrap数据模型

```python
@dataclass
class BootstrapKnowledgeBase:
    """Bootstrap知识库 - 系统预加载的核心数据"""
    
    # 1. 运营商元数据
    operators: Dict[str, OperatorProfile]
    
    # 2. 高管数据库
    executives: Dict[str, List[ExecutiveInfo]]
    
    # 3. 关键词图谱
    keyword_graph: KeywordGraph
    
    # 4. 来源配置库
    sources: Dict[str, SourceConfig]
    
    # 5. 子任务模板库
    task_templates: TaskTemplateLibrary
    
    # 6. 事件类型映射
    event_types: Dict[str, EventTypeConfig]
    
    # 元数据
    version: str
    last_updated: datetime
    update_frequency: str  # 'daily' | 'weekly' | 'monthly'


@dataclass
class OperatorProfile:
    """运营商档案"""
    name: str                          # 中文名
    aliases: List[str]                 # 别名列表
    english_name: str                  # 英文名
    stock_code: str                    # 股票代码
    
    # 官方渠道
    official_sites: List[OfficialSite]
    official_wechat: List[str]         # 官方公众号
    official_weibo: str                # 官方微博
    
    # 业务领域标签
    business_tags: List[str]
    
    # 近期热点（动态更新）
    recent_focus: List[str]


@dataclass
class OfficialSite:
    """官方网站配置"""
    name: str                          # 站点名称
    url: str                           # 首页URL
    news_url: str                      # 新闻列表页
    news_pattern: str                  # 新闻链接正则
    encoding: str                      # 页面编码
    update_frequency: str              # 更新频率
    priority: int                      # 采集优先级
    
    # 选择器配置（用于爬虫）
    selectors: Dict[str, str]          # title/date/content/link


@dataclass
class ExecutiveInfo:
    """高管信息"""
    name: str                          # 姓名
    position: str                      # 职位
    operator: str                      # 所属运营商
    
    # 职务详情
    level: str                         # 级别: '集团领导' | '省公司' | '专业公司'
    responsibilities: List[str]        # 分管领域
    
    # 近期动态关键词
    recent_topics: List[str]
    
    # 媒体引用别名
    name_aliases: List[str]            # 如: "杨董事长"、"柯总"


@dataclass
class KeywordGraph:
    """关键词图谱 - 语义关联网络"""
    
    # 核心关键词
    core_keywords: List[str]           # 运营商名称等
    
    # 业务关键词（分层）
    business_keywords: Dict[str, List[str]]
    # {
    #   'network': ['5G-A', '6G', '算力网络', '光网络'],
    #   'technology': ['AI', '大模型', '物联网', '边缘计算'],
    #   ...
    # }
    
    # 事件关键词
    event_keywords: Dict[str, List[str]]
    # {
    #   'financial': ['财报', '年报', '营收', '利润'],
    #   'conference': ['合作伙伴大会', '生态大会', '峰会'],
    #   ...
    # }
    
    # 关联关系
    relations: List[KeywordRelation]   # 关键词间的关联强度


@dataclass
class TaskTemplate:
    """子任务模板"""
    template_id: str
    name: str                          # 模板名称
    description: str                   # 描述
    
    # 适用条件
    applicable_when: TemplateCondition
    
    # 任务结构
    task_structure: Dict[str, Any]     # 任务树结构模板
    
    # 参数占位符
    parameters: List[TemplateParam]    # 可替换参数
    
    # 预期输出
    expected_output: str
    
    # 使用统计
    usage_count: int
    success_rate: float


@dataclass
class EventTypeConfig:
    """事件类型配置"""
    name: str                          # 事件类型名
    keywords: List[str]                # 识别关键词
    priority: int                      # 优先级
    
    # 关联模板
    template_id: str                   # 使用的任务模板
    
    # 特殊处理
    requires_cross_verify: bool        # 是否需要交叉验证
    alert_threshold: int               # 告警阈值
```

---

### 2.2 Bootstrap启动流程

```python
class BootstrapEngine:
    """Bootstrap引擎 - 知识预加载"""
    
    def __init__(self, config: BootstrapConfig):
        self.config = config
        self.knowledge_base = None
        
    async def bootstrap(self, force_refresh: bool = False) -> BootstrapKnowledgeBase:
        """
        执行Bootstrap流程
        
        1. 检查本地缓存
        2. 如过期或强制刷新，执行全量更新
        3. 返回知识库
        """
        # 检查缓存
        if not force_refresh and self._is_cache_valid():
            return self._load_from_cache()
        
        # 执行全量Bootstrap
        kb = BootstrapKnowledgeBase()
        
        # Step 1: 发现运营商信息
        kb.operators = await self._discover_operators()
        
        # Step 2: 提取高管信息
        kb.executives = await self._discover_executives(kb.operators)
        
        # Step 3: 构建关键词图谱
        kb.keyword_graph = await self._build_keyword_graph()
        
        # Step 4: 发现来源配置
        kb.sources = await self._discover_sources(kb.operators)
        
        # Step 5: 生成任务模板
        kb.task_templates = await self._generate_templates(
            kb.operators, kb.keyword_graph, kb.event_types
        )
        
        # Step 6: 加载事件类型配置
        kb.event_types = self._load_event_types()
        
        # 保存缓存
        self._save_to_cache(kb)
        
        return kb
    
    # ============ 各步骤详细实现 ============
    
    async def _discover_operators(self) -> Dict[str, OperatorProfile]:
        """
        发现运营商基本信息
        来源: 官网验证、百科、财报
        """
        operators = {}
        
        # 预定义四大运营商基础信息
        base_info = {
            '中国移动': {
                'aliases': ['中移动', 'China Mobile', 'CMCC'],
                'stock_code': '600941.SH / 0941.HK',
                'official_domains': ['10086.cn', 'chinamobileltd.com'],
            },
            '中国电信': {
                'aliases': ['中电信', 'China Telecom'],
                'stock_code': '601728.SH / 0728.HK',
                'official_domains': ['chinatelecom.com.cn', '189.cn'],
            },
            '中国联通': {
                'aliases': ['中联通', 'China Unicom'],
                'stock_code': '600050.SH / 0762.HK',
                'official_domains': ['chinaunicom.com.cn', '10010.com'],
            },
            '中国铁塔': {
                'aliases': ['中铁塔', 'China Tower'],
                'stock_code': '00788.HK',
                'official_domains': ['chinatowercom.cn'],
            },
        }
        
        for name, info in base_info.items():
            # 验证官网可访问性
            official_sites = await self._verify_official_sites(info['official_domains'])
            
            # 发现新闻页面
            news_sites = await self._discover_news_pages(official_sites)
            
            operators[name] = OperatorProfile(
                name=name,
                aliases=info['aliases'],
                english_name=info['aliases'][1],
                stock_code=info['stock_code'],
                official_sites=news_sites,
                business_tags=await self._discover_business_tags(name),
                recent_focus=[]  # 运行时动态填充
            )
        
        return operators
    
    async def _discover_executives(self, operators: Dict[str, OperatorProfile]) -> Dict[str, List[ExecutiveInfo]]:
        """
        发现高管信息
        来源: 官网领导介绍页、财报、新闻报道
        """
        executives = {}
        
        for op_name, op_profile in operators.items():
            op_executives = []
            
            # 从官网提取
            for site in op_profile.official_sites:
                if '领导' in site.name or 'about' in site.url:
                    leaders = await self._extract_leaders_from_page(site.url)
                    op_executives.extend(leaders)
            
            # 从近期新闻补充
            news_leaders = await self._extract_leaders_from_news(op_name)
            op_executives = self._merge_executive_lists(op_executives, news_leaders)
            
            # 预定义关键高管（作为fallback）
            fallback_leaders = self._get_fallback_executives(op_name)
            op_executives = self._merge_executive_lists(op_executives, fallback_leaders)
            
            executives[op_name] = op_executives
        
        return executives
    
    async def _build_keyword_graph(self) -> KeywordGraph:
        """
        构建关键词图谱
        包含: 业务关键词、技术关键词、事件关键词
        """
        graph = KeywordGraph(
            core_keywords=['中国移动', '中国电信', '中国联通', '中国铁塔'],
            business_keywords={},
            event_keywords={},
            relations=[]
        )
        
        # 业务关键词（技术领域）
        graph.business_keywords['network'] = [
            '5G-A', '5G-Advanced', '6G', '算力网络', '光网络',
            '千兆宽带', '万兆光网', '全光网', 'SPN', 'OTN'
        ]
        graph.business_keywords['technology'] = [
            'AI', '人工智能', '大模型', 'LLM', '机器学习',
            '物联网', 'IoT', '边缘计算', 'MEC', '区块链',
            '数字孪生', 'XR', 'VR', 'AR', '元宇宙'
        ]
        graph.business_keywords['service'] = [
            '云服务', '云计算', '天翼云', '移动云', '联通云',
            '大数据', '数据中心', 'IDC', 'CDN', '安全服务'
        ]
        graph.business_keywords['terminal'] = [
            '5G手机', '5G套餐', '云手机', '云电脑',
            '智能家居', '智能穿戴', '车联网', 'V2X'
        ]
        
        # 新兴领域
        graph.business_keywords['emerging'] = [
            '低空经济', '低空网络', '无人机', 'eVTOL',
            '卫星通信', '卫星互联网', '天通卫星', '北斗',
            '量子通信', '量子计算', '6G研发'
        ]
        
        # 事件关键词
        graph.event_keywords['financial'] = [
            '财报', '年报', '半年报', '季报',
            '营收', '利润', '净利润', 'EBITDA',
            '派息', '分红', '股息', '投资者关系'
        ]
        graph.event_keywords['conference'] = [
            '合作伙伴大会', '生态大会', '创新大会',
            '世界移动通信大会', 'MWC', 'PT展',
            '峰会', '论坛', '发布会'
        ]
        graph.event_keywords['cooperation'] = [
            '战略合作', '签约', '合作协议', '联合',
            '共建', '合资公司', '生态合作', '产学研'
        ]
        graph.event_keywords['investment'] = [
            '投资', '并购', '收购', '入股',
            '资本合作', '融资', 'IPO', '上市'
        ]
        graph.event_keywords['policy'] = [
            '政策', '监管', '工信部', '通管局',
            '牌照', '频谱', '牌照发放', '新规'
        ]
        graph.event_keywords['social'] = [
            '社会责任', 'ESG', '乡村振兴', '数字乡村',
            '双碳', '节能减排', '应急通信', '重保'
        ]
        
        # 构建关联关系
        graph.relations = self._build_keyword_relations(graph)
        
        return graph
    
    async def _discover_sources(self, operators: Dict[str, OperatorProfile]) -> Dict[str, SourceConfig]:
        """
        发现并验证信息来源
        """
        sources = {}
        
        # 官方来源
        for op_name, op in operators.items():
            for site in op.official_sites:
                source_id = f"{op_name}_official_{site.name}"
                sources[source_id] = SourceConfig(
                    id=source_id,
                    name=f"{op_name}-{site.name}",
                    type='official',
                    url=site.news_url,
                    priority=5,
                    selectors=site.selectors,
                    enabled=True
                )
        
        # 行业媒体
        industry_sites = [
            ('c114', 'C114通信网', 'https://www.c114.com.cn', 3),
            ('cnii', '中国信息产业网', 'https://www.cnii.com.cn', 3),
            ('cfyys', '通信产业网', 'https://www.ccidcom.com', 3),
            ('cww', '通信世界网', 'https://www.cww.net.cn', 3),
        ]
        for site_id, name, url, priority in industry_sites:
            sources[site_id] = SourceConfig(
                id=site_id,
                name=name,
                type='industry',
                url=url,
                priority=priority,
                enabled=True
            )
        
        # 央媒财经
        media_sites = [
            ('xinhua_telecom', '新华社通信', 'http://www.news.cn/tech/', 4),
            ('people_telecom', '人民网通信', 'http://telecom.people.com.cn/', 4),
        ]
        for site_id, name, url, priority in media_sites:
            sources[site_id] = SourceConfig(
                id=site_id,
                name=name,
                type='media',
                url=url,
                priority=priority,
                enabled=True
            )
        
        return sources
    
    async def _generate_templates(
        self,
        operators: Dict[str, OperatorProfile],
        keyword_graph: KeywordGraph,
        event_types: Dict[str, EventTypeConfig]
    ) -> TaskTemplateLibrary:
        """
        生成子任务模板库
        """
        library = TaskTemplateLibrary()
        
        # 模板1: 运营商日常监测
        library.add_template(TaskTemplate(
            template_id='operator_daily_monitor',
            name='运营商日常新闻监测',
            description='监测指定运营商的官网和行业媒体新闻',
            applicable_when=TemplateCondition(
                trigger_keywords=['最新', '最近', '今天', '本周'],
                required_entities=['operator']
            ),
            task_structure={
                'level_1': {
                    'type': 'by_source_type',
                    'children': [
                        {'source_type': 'official', 'priority': 5, 'limit': 10},
                        {'source_type': 'industry', 'priority': 3, 'limit': 15},
                    ]
                },
                'level_2': {
                    'type': 'by_keyword_group',
                    'keyword_groups': ['business', 'technology']
                }
            },
            parameters=[
                TemplateParam(name='operator', type='str', required=True),
                TemplateParam(name='days', type='int', default=7),
                TemplateParam(name='focus_areas', type='List[str]', default=[]),
            ]
        ))
        
        # 模板2: 财报季专题
        library.add_template(TaskTemplate(
            template_id='financial_report_focus',
            name='财报季深度追踪',
            description='财报发布期间的全方位信息采集',
            applicable_when=TemplateCondition(
                trigger_keywords=['财报', '年报', '业绩', '营收', '利润'],
                time_sensitive=True
            ),
            task_structure={
                'level_1': {
                    'type': 'by_operator',
                    'all_operators': True
                },
                'level_2': {
                    'type': 'by_content_type',
                    'children': [
                        {'type': 'official_report', 'priority': 5},
                        {'type': 'analyst_review', 'priority': 4},
                        {'type': 'market_reaction', 'priority': 3},
                    ]
                }
            },
            parameters=[
                TemplateParam(name='quarter', type='str', required=True),  # Q1/Q2/Q3/Q4
                TemplateParam(name='year', type='int', required=True),
            ]
        ))
        
        # 模板3: 高管动态追踪
        library.add_template(TaskTemplate(
            template_id='executive_tracking',
            name='高管动态追踪',
            description='追踪指定高管的公开活动和发言',
            applicable_when=TemplateCondition(
                trigger_keywords=['董事长', '总经理', 'CEO', '总裁'],
                required_entities=['executive_name']
            ),
            task_structure={
                'level_1': {
                    'type': 'by_search_engine',
                    'engines': ['brave', 'bing'],
                    'keyword_pattern': '{executive_name} {operator} {time_range}'
                }
            },
            parameters=[
                TemplateParam(name='executive_name', type='str', required=True),
                TemplateParam(name='operator', type='str', required=True),
                TemplateParam(name='days', type='int', default=30),
            ]
        ))
        
        # 模板4: 技术热点追踪
        library.add_template(TaskTemplate(
            template_id='tech_trend_tracking',
            name='技术热点追踪',
            description='追踪特定技术领域的最新进展',
            applicable_when=TemplateCondition(
                trigger_keywords=['AI', '5G-A', '6G', '低空', '卫星', '量子'],
                required_entities=['tech_keyword']
            ),
            task_structure={
                'level_1': {
                    'type': 'by_tech_area',
                    'cross_operators': True
                },
                'level_2': {
                    'type': 'by_content_depth',
                    'children': [
                        {'type': 'announcement', 'priority': 5},
                        {'type': 'deployment', 'priority': 4},
                        {'type': 'pilot_project', 'priority': 3},
                    ]
                }
            },
            parameters=[
                TemplateParam(name='tech_keyword', type='str', required=True),
                TemplateParam(name='operators', type='List[str]', default='all'),
            ]
        ))
        
        # 模板5: 重大事件应急响应
        library.add_template(TaskTemplate(
            template_id='emergency_response',
            name='重大事件应急响应',
            description='针对突发事件的快速信息采集',
            applicable_when=TemplateCondition(
                trigger_keywords=['故障', '事故', '安全', ' outage', '中断'],
                urgency='high'
            ),
            task_structure={
                'level_1': {
                    'type': 'parallel_search',
                    'sources': 'all',
                    'timeout': 60,  # 快速响应
                }
            },
            parameters=[
                TemplateParam(name='event_keyword', type='str', required=True),
                TemplateParam(name='affected_operator', type='str', default='unknown'),
            ]
        ))
        
        return library
```

---

### 2.3 Bootstrap数据存储

```yaml
# bootstrap/knowledge_base.yaml
version: "2026.04.30"
last_updated: "2026-04-30T08:00:00+08:00"
update_frequency: "daily"

operators:
  中国移动:
    name: "中国移动"
    aliases: ["中移动", "China Mobile", "CMCC"]
    stock_code: "600941.SH / 0941.HK"
    official_sites:
      - name: "官网新闻中心"
        url: "https://www.10086.cn/aboutus/news/"
        selectors:
          title: ".news-list h3"
          date: ".news-list .date"
          link: ".news-list a"
        priority: 5
      - name: "投资者关系"
        url: "https://www.chinamobileltd.com/tc/investors/press.php"
        priority: 5
    official_wechat: ["中国移动", "中国移动研究院"]
    business_tags: ["5G", "算力网络", "移动云", "物联网"]
    recent_focus: ["5G-A商用", "AI大模型", "低空经济"]
    
  中国电信:
    name: "中国电信"
    aliases: ["中电信", "China Telecom"]
    stock_code: "601728.SH / 0728.HK"
    official_sites:
      - name: "官网新闻"
        url: "https://www.chinatelecom.com.cn/news/"
        priority: 5
    official_wechat: ["中国电信", "天翼云"]
    business_tags: ["天翼云", "5G", "卫星通信", "AI"]
    recent_focus: ["天翼云出海", "手机直连卫星", "量子通信"]
    
  # ... 中国联通、中国铁塔类似

executives:
  中国移动:
    - name: "杨杰"
      position: "董事长、党组书记"
      level: "集团领导"
      responsibilities: ["战略规划", "全面管理"]
      name_aliases: ["杨董事长", "杨书记"]
      recent_topics: ["5G-A", "AI+", "算力网络"]
      
    - name: "何飚"
      position: "总经理、党组副书记"
      level: "集团领导"
      responsibilities: ["日常经营", "市场运营"]
      name_aliases: ["何总"]
      recent_topics: ["客户服务", "网络建设"]
      
  中国电信:
    - name: "柯瑞文"
      position: "董事长、党组书记"
      level: "集团领导"
      responsibilities: ["战略规划", "全面管理"]
      name_aliases: ["柯董事长", "柯书记"]
      recent_topics: ["云改数转", "卫星通信"]
      
    - name: "邵广禄"
      position: "总经理、党组副书记"
      level: "集团领导"
      responsibilities: ["日常经营", "云网运营"]
      name_aliases: ["邵总"]
      recent_topics: ["天翼云", "数字化转型"]

keyword_graph:
  core_keywords: ["中国移动", "中国电信", "中国联通", "中国铁塔"]
  
  business_keywords:
    network:
      - keyword: "5G-A"
        aliases: ["5G-Advanced", "5.5G"]
        related: ["万兆网络", "通感一体"]
      - keyword: "6G"
        aliases: ["第六代移动通信"]
        related: ["太赫兹", "智能超表面"]
      - keyword: "算力网络"
        aliases: ["CFN", "Compute First Networking"]
        related: ["东数西算", "智算中心"]
      - keyword: "卫星通信"
        aliases: ["手机直连卫星", "天通卫星"]
        related: ["低轨卫星", "NTN"]
      - keyword: "低空经济"
        aliases: ["低空网络", "无人机通信"]
        related: ["eVTOL", "空域管理"]
        
    technology:
      - keyword: "AI"
        aliases: ["人工智能", "大模型", "AI+"]
        related: ["九天大模型", "TeleAI", "元景大模型"]
      - keyword: "量子通信"
        aliases: ["量子密钥", "QKD"]
        related: ["量子计算", "国盾量子"]
        
    service:
      - keyword: "云服务"
        aliases: ["云计算", "公有云"]
        related: ["天翼云", "移动云", "联通云"]
      - keyword: "物联网"
        aliases: ["IoT", "万物互联"]
        related: ["NB-IoT", "Cat.1", "RedCap"]

  event_keywords:
    financial:
      - keyword: "财报"
        patterns: ["年报", "半年报", "季报", "业绩发布"]
        seasonality: "quarterly"
      - keyword: "投资"
        patterns: ["战略投资", "并购", "入股"]
        
    conference:
      - keyword: "合作伙伴大会"
        aliases: ["生态大会", "开发者大会"]
        typical_months: [3, 6, 9, 11]
      - keyword: "展会"
        aliases: ["MWC", "PT展", "通信展"]
        
  relations:
    - source: "5G-A"
      target: "算力网络"
      strength: 0.8
      type: "技术协同"
    - source: "AI"
      target: "云服务"
      strength: 0.9
      type: "业务融合"
    - source: "低空经济"
      target: "5G-A"
      strength: 0.7
      type: "应用场景"

task_templates:
  operator_daily_monitor:
    name: "运营商日常新闻监测"
    applicable_scenarios: ["日常监测", "定期汇报"]
    structure:
      level_1:
        type: "by_source_type"
        children:
          - source_type: "official"
            priority: 5
            max_items: 10
          - source_type: "industry"
            priority: 3
            max_items: 15
      level_2:
        type: "by_keyword_group"
        groups: ["business", "technology"]
    
  financial_report_focus:
    name: "财报季深度追踪"
    applicable_scenarios: ["财报季", "业绩分析"]
    trigger_keywords: ["财报", "年报", "业绩"]
    structure:
      level_1:
        type: "by_operator"
        all_operators: true
      level_2:
        type: "by_content_type"
        children:
          - type: "official_report"
            priority: 5
          - type: "analyst_review"
            priority: 4
          - type: "market_reaction"
            priority: 3
```

---

### 2.4 Bootstrap更新机制

```python
class BootstrapUpdater:
    """Bootstrap知识库更新器"""
    
    async def incremental_update(self, kb: BootstrapKnowledgeBase) -> BootstrapKnowledgeBase:
        """
        增量更新知识库
        """
        # 1. 更新recent_focus（从近期新闻提取）
        kb = await self._update_recent_focus(kb)
        
        # 2. 更新高管recent_topics
        kb = await self._update_executive_topics(kb)
        
        # 3. 验证来源可用性
        kb = await self._verify_source_availability(kb)
        
        # 4. 更新关键词热度
        kb = await self._update_keyword_trends(kb)
        
        kb.last_updated = datetime.now()
        return kb
    
    async def _update_recent_focus(self, kb: BootstrapKnowledgeBase) -> BootstrapKnowledgeBase:
        """更新运营商近期热点"""
        for op_name, op in kb.operators.items():
            # 搜索近7天新闻，提取高频主题词
            recent_news = await self._search_recent_news(op_name, days=7)
            
            # 提取主题
            topics = self._extract_topics(recent_news)
            
            # 更新（保留最近3个热点）
            op.recent_focus = topics[:3]
        
        return kb
    
    async def scheduled_update(self):
        """定时更新任务"""
        # 每日更新: recent_focus, executive_topics
        # 每周更新: 验证来源可用性
        # 每月更新: 高管名单、官网结构
        pass
```

---

## 三、Bootstrap在ReAct流程中的应用

### 3.1 M1任务分解时注入Bootstrap知识

```python
class BootstrapAwareTaskPlanner:
    """感知Bootstrap知识的任务规划器"""
    
    def __init__(self, bootstrap_kb: BootstrapKnowledgeBase):
        self.kb = bootstrap_kb
        
    async def plan(self, query: UserQuery) -> TaskTree:
        """
        使用Bootstrap知识进行任务规划
        """
        # Thought: 分析查询，匹配模板
        thought = self._think_with_bootstrap(query)
        
        # 尝试匹配预定义模板
        matched_template = self._match_template(query)
        
        if matched_template and matched_template.confidence > 0.8:
            # 使用模板生成任务
            task_tree = self._instantiate_template(matched_template, query)
        else:
            # 回退到动态分解
            task_tree = await self._dynamic_decompose(query)
        
        # 注入Bootstrap知识优化任务
        task_tree = self._enrich_with_bootstrap(task_tree)
        
        return task_tree
    
    def _match_template(self, query: UserQuery) -> Optional[TemplateMatch]:
        """匹配最佳模板"""
        matches = []
        
        for template in self.kb.task_templates.templates.values():
            score = self._calculate_template_match(template, query)
            if score > 0.5:
                matches.append((template, score))
        
        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            return TemplateMatch(
                template=matches[0][0],
                confidence=matches[0][1]
            )
        return None
    
    def _enrich_with_bootstrap(self, tree: TaskTree) -> TaskTree:
        """使用Bootstrap知识丰富任务树"""
        
        def enrich_node(node: TaskNode):
            # 注入运营商别名
            if node.operator and node.operator in self.kb.operators:
                op = self.kb.operators[node.operator]
                node.keywords.extend(op.aliases)
                node.keywords = list(set(node.keywords))  # 去重
            
            # 注入高管别名
            if node.task_type == 'executive_tracking':
                exec_name = node.parameters.get('executive_name')
                for op_execs in self.kb.executives.values():
                    for exec in op_execs:
                        if exec.name == exec_name:
                            node.keywords.extend(exec.name_aliases)
            
            # 注入关键词关联
            for kw in node.keywords[:]:
                if kw in self.kb.keyword_graph:
                    related = self.kb.keyword_graph.get_related(kw, top_n=3)
                    node.keywords.extend(related)
            
            # 递归处理子节点
            for child in node.children:
                enrich_node(child)
        
        enrich_node(tree.root)
        return tree
```

### 3.2 M2采集时使用Bootstrap来源配置

```python
class BootstrapAwareCollector:
    """感知Bootstrap知识的采集器"""
    
    def __init__(self, bootstrap_kb: BootstrapKnowledgeBase):
        self.kb = bootstrap_kb
        
    async def collect(self, task: TaskNode) -> CollectionResult:
        """使用Bootstrap配置执行采集"""
        
        # 获取预配置的来源
        if task.source_id and task.source_id in self.kb.sources:
            source_config = self.kb.sources[task.source_id]
            
            # 使用预配置的selectors
            result = await self._crawl_with_config(task.url, source_config)
        else:
            # 动态发现
            result = await self._discover_and_crawl(task)
        
        return result
```

---

## 四、完整系统架构（v3.0）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    运营商新闻采集系统 v3.0 - 完整架构                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Bootstrap 层                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │ 运营商知识库 │  │ 高管数据库   │  │ 关键词图谱   │  │ 任务模板库  │ │   │
│  │  │ Operators   │  │ Executives  │  │ Keywords    │  │ Templates  │ │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │   │
│  │         └─────────────────┴─────────────────┴──────────────┘        │   │
│  │                              ↓                                       │   │
│  │                    ┌─────────────────┐                              │   │
│  │                    │  bootstrap.yaml │ (持久化存储)                   │   │
│  │                    └─────────────────┘                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ↓ 注入知识                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ReAct 主流程层                                   │   │
│  │                                                                     │   │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │   │
│  │   │  M1 任务    │ →  │  M2 采集    │ →  │  M3 存储    │            │   │
│  │   │   分解      │    │   引擎      │    │   管理      │            │   │
│  │   │             │    │             │    │             │            │   │
│  │   │ • 模板匹配  │    │ • 来源选择  │    │ • 标准化    │            │   │
│  │   │ • 知识注入  │    │ • 自适应策略│    │ • 去重      │            │   │
│  │   │ • 分层分解  │    │ • 质量评估  │    │ • 索引      │            │   │
│  │   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘            │   │
│  │          │                  │                  │                    │   │
│  │          └──────────────────┴──────────────────┘                    │   │
│  │                             ↓                                      │   │
│  │                    ┌─────────────────┐                             │   │
│  │                    │  M4 报告汇编    │                             │   │
│  │                    │                 │                             │   │
│  │                    │ • 智能摘要      │                             │   │
│  │                    │ • 交叉验证      │                             │   │
│  │                    │ • 模板渲染      │                             │   │
│  │                    └─────────────────┘                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      全局约束层                                      │   │
│  │   max_depth=3, max_tasks=100, max_duration=600s, max_memory=500MB   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 五、Bootstrap带来的优势

| 方面 | 无Bootstrap | 有Bootstrap |
|-----|------------|------------|
| **任务分解** | 每次动态分析，耗时长 | 模板匹配，毫秒级响应 |
| **来源配置** | 硬编码或动态发现，不稳定 | 预验证配置，可靠性高 |
| **关键词** | 静态列表，易遗漏 | 动态图谱，关联扩展 |
| **高管追踪** | 需人工指定全名 | 自动识别别名和职务 |
| **时效性** | 不了解当前热点 | recent_focus动态更新 |
| **准确性** | 易遗漏重要来源 | 优先级预配置，全覆盖 |

---

## 六、演进路线更新

```
Phase 1: 基础重构 (1-2周)
├── Bootstrap基础框架
│   ├── 运营商基础信息硬编码
│   ├── 高管名单初始化
│   └── 关键词图谱v1
├── 模板系统基础
│   └── 3-5个核心模板
└── 主流程ReAct循环

Phase 2: 能力增强 (2-3周)
├── Bootstrap自动更新
│   ├── 官网结构自动发现
│   ├── 高管信息自动提取
│   └── 热点动态更新
├── 模板库扩展
│   └── 10+个场景模板
└── 自适应采集策略

Phase 3: 智能化 (3-4周)
├── LLM辅助Bootstrap
│   ├── 智能模板生成
│   └── 关键词关系挖掘
├── 预测性Bootstrap
│   └── 基于日历预测热点
└── 个性化模板学习

Phase 4: 平台化 (长期)
├── Bootstrap可视化编辑
├── 模板市场/共享
└── 多行业知识库扩展
```

---

*设计文档版本: v3.0 (Bootstrap + ReAct架构)*
*最后更新: 2026-04-30*
