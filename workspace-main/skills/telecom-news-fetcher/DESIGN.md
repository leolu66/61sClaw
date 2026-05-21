# 运营商新闻采集系统 - 重新设计方案

## 一、设计目标

构建一个模块化、可扩展、高质量的运营商新闻采集系统，实现从任务规划到报告生成的全流程自动化。

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         运营商新闻采集系统 v2.0                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  M1: 任务   │  │  M2: 采集   │  │  M3: 存储   │  │  M4: 汇编   │        │
│  │   分解模块   │→│   引擎模块   │→│   管理模块   │→│   报告模块   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│         ↓                ↓                ↓                ↓               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ • 任务规划   │  │ • 爬虫调度   │  │ • 原始数据   │  │ • 去重合并   │        │
│  │ • 关键词生成 │  │ • 反爬策略   │  │ • 清洗归档   │  │ • 智能摘要   │        │
│  │ • 来源分配   │  │ • 并发控制   │  │ • 索引检索   │  │ • 模板渲染   │        │
│  │ • 时间切片   │  │ • 失败重试   │  │ • 版本管理   │  │ • 多格式输出 │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                           ┌─────────────────┐
                           │   配置中心      │
                           │  (YAML/JSON)    │
                           └─────────────────┘
```

---

## 三、模块详细设计

### M1: 任务分解模块 (Task Planner)

#### 3.1.1 功能职责
- 接收用户查询请求，生成结构化任务计划
- 智能生成搜索关键词组合
- 分配采集来源和优先级
- 生成可执行的采集任务清单

#### 3.1.2 核心组件

```python
class TaskPlanner:
    """任务规划器"""
    
    def generate_task_plan(self, request: QueryRequest) -> TaskPlan:
        """
        输入: 用户查询请求
        输出: 结构化任务计划
        """
        pass
    
    def generate_keywords(self, operator: str, context: dict) -> KeywordSet:
        """
        生成多层级关键词:
        - L1 核心词: 运营商名称 (中国移动/China Mobile)
        - L2 业务词: 5G-A/算力网络/云服务等
        - L3 事件词: 财报/战略合作/技术创新等
        - L4 高管词: 董事长/总经理等关键人名
        """
        pass
    
    def assign_sources(self, task_type: str, priority: int) -> List[Source]:
        """
        根据任务类型分配采集来源:
        - 突发新闻: 官方渠道 + 央媒 (高优先级)
        - 深度分析: 行业媒体 + 财经平台
        - 技术动态: 专业论坛 + 专利数据库
        """
        pass
```

#### 3.1.3 任务清单结构

```yaml
task_id: "tel_20250430_001"
created_at: "2026-04-30T08:20:00+08:00"
query:
  operators: ["中国移动", "中国电信"]
  date_range: { start: "2026-04-23", end: "2026-04-30" }
  focus_areas: ["5G-A", "算力网络", "财报"]

tasks:
  # 任务1: 官网新闻
  - id: "t1"
    source: "china_mobile_official"
    source_type: "official"
    keywords: ["中国移动", "5G-A", "算力网络"]
    priority: 5
    estimated_items: 20
    
  # 任务2: C114行业新闻
  - id: "t2"  
    source: "c114"
    source_type: "industry"
    keywords: ["中国移动", "中国电信", "5G-A部署"]
    priority: 3
    estimated_items: 30
    
  # 任务3: 搜索引擎补充
  - id: "t3"
    source: "brave_search"
    source_type: "search_engine"
    keywords: ["中国移动 董事长 2026", "中国电信 战略合作 4月"]
    priority: 2
    estimated_items: 15
    
  # 任务4: 高管动态
  - id: "t4"
    source: "baidu_news"
    source_type: "search_engine"
    keywords: ["杨杰 中国移动", "柯瑞文 中国电信"]
    priority: 4
    estimated_items: 10

total_estimated: 75
expected_duration: "3-5分钟"
```

---

### M2: 信息采集引擎 (Collection Engine)

#### 3.2.1 功能职责
- 统一调度多种采集方式（爬虫/API/搜索）
- 实施反爬策略和请求管理
- 处理并发控制和速率限制
- 实现失败重试和降级机制

#### 3.2.2 采集方式矩阵

| 来源类型 | 具体来源 | 采集方式 | 反爬策略 | 优先级 |
|---------|---------|---------|---------|--------|
| **官方渠道** | 运营商官网 | 爬虫 | 动态UA+随机延迟 | P0 |
| **央媒** | 新华社/人民日报 | API/爬虫 | 官方API优先 | P1 |
| **行业媒体** | C114/通信世界 | 爬虫 | 代理池+请求指纹 | P2 |
| **搜索引擎** | Brave/Bing | API | API Key轮询 | P2 |
| **财经平台** | 新浪财经/东方财富 | 爬虫 | 无头浏览器 | P3 |
| **公众号** | 微信搜狗 | 爬虫 | Cookie池 | P3 |

#### 3.2.3 核心组件

```python
class CollectionEngine:
    """采集引擎"""
    
    def __init__(self):
        self.crawlers = {
            'c114': C114Spider(),
            'official': OfficialSiteSpider(),
            'cnii': CNIISpider(),
            # ...
        }
        self.search_apis = {
            'brave': BraveSearchAPI(),
            'bing': BingSearchAPI(),
        }
        self.request_manager = RequestManager()
    
    async def execute_task(self, task: Task) -> CollectionResult:
        """执行单个采集任务"""
        
        # 1. 选择采集器
        collector = self._get_collector(task.source)
        
        # 2. 配置反爬策略
        config = self._get_antispider_config(task.source)
        
        # 3. 执行采集（带重试）
        for attempt in range(config.max_retries):
            try:
                result = await collector.fetch(
                    keywords=task.keywords,
                    date_range=task.date_range,
                    limit=task.limit,
                    config=config
                )
                return CollectionResult(success=True, data=result)
            except AntiSpiderDetected:
                await self._handle_antispider(config, attempt)
            except Exception as e:
                logger.error(f"采集失败: {e}")
                
        # 4. 降级处理
        return await self._fallback_collect(task)


class RequestManager:
    """请求管理器 - 反爬核心"""
    
    def __init__(self):
        self.ua_rotator = UserAgentRotator()
        self.proxy_pool = ProxyPool()
        self.cookie_jar = CookieJar()
        self.rate_limiter = RateLimiter()
    
    async def request(self, url, **kwargs):
        """智能请求封装"""
        headers = {
            'User-Agent': self.ua_rotator.get(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        # 速率控制
        await self.rate_limiter.wait(url)
        
        # 代理选择
        proxy = self.proxy_pool.get(url)
        
        # 执行请求
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy) as resp:
                return await resp.text()
```

#### 3.2.4 反爬策略配置

```yaml
# config/antispider.yaml
strategies:
  c114:
    delay: { min: 1.0, max: 3.0 }  # 随机延迟
    user_agents: rotate  # 轮换UA
    cookies: persist     # 保持Cookie
    retry: 3
    
  official_sites:
    delay: { min: 0.5, max: 1.5 }
    respect_robots: true
    
  search_apis:
    rate_limit:  # API限流
      brave: 20/min
      bing: 1000/day
    key_rotation: true  # Key轮询
```

---

### M3: 存储管理模块 (Storage Manager)

#### 3.3.1 功能职责
- 原始数据持久化存储
- 数据清洗和标准化
- 建立索引支持检索
- 版本管理和去重

#### 3.3.2 存储架构

```
data/
├── raw/                    # 原始采集数据
│   ├── 2026-04-30/
│   │   ├── c114_001.json
│   │   ├── official_cm_001.json
│   │   └── brave_search_001.json
│   └── ...
├── processed/              # 清洗后数据
│   ├── 2026-04-30/
│   │   ├── normalized.json
│   │   └── deduplicated.json
│   └── ...
├── index/                  # 索引文件
│   ├── by_date.json
│   ├── by_operator.json
│   ├── by_source.json
│   └── full_text.index
└── archive/                # 归档数据
    └── 2026-Q2/
```

#### 3.3.3 数据模型

```python
@dataclass
class NewsItem:
    """标准化新闻条目"""
    # 基础信息
    id: str                    # 唯一ID (hash)
    title: str                 # 标题
    url: str                   # 原文链接
    content: str               # 正文内容
    summary: str               # 智能摘要
    
    # 时间信息
    published_at: datetime     # 发布时间
    collected_at: datetime     # 采集时间
    
    # 来源信息
    source_name: str           # 来源名称
    source_type: SourceType    # 来源类型枚举
    source_url: str            # 来源站点
    
    # 分类标签
    operators: List[str]       # 涉及运营商
    categories: List[str]      # 新闻分类
    keywords: List[str]        # 关键词
    
    # 质量评分
    credibility_score: float   # 可信度 0-5
    importance_score: float    # 重要性 0-5
    freshness_score: float     # 时效性 0-5
    overall_score: float       # 综合得分
    
    # 元数据
    language: str              # 语言
    word_count: int            # 字数
    has_image: bool            # 是否含图
    
    # 去重相关
    content_hash: str          # 内容指纹
    similar_to: List[str]      # 相似文章ID


class StorageManager:
    """存储管理器"""
    
    def save_raw(self, task_id: str, data: List[dict]):
        """保存原始数据"""
        pass
    
    def normalize(self, raw_data: List[dict]) -> List[NewsItem]:
        """数据标准化"""
        pass
    
    def deduplicate(self, items: List[NewsItem]) -> List[NewsItem]:
        """去重处理 - 基于内容相似度"""
        pass
    
    def build_index(self, items: List[NewsItem]):
        """构建索引"""
        pass
    
    def query(self, filters: QueryFilter) -> List[NewsItem]:
        """检索查询"""
        pass
```

#### 3.3.4 去重算法

```python
class Deduplicator:
    """智能去重器"""
    
    def __init__(self):
        self.simhash = SimHash()
        self.minhash = MinHash()
    
    def find_duplicates(self, items: List[NewsItem]) -> List[DuplicateGroup]:
        """
        多层级去重:
        1. URL精确匹配
        2. 标题相似度 (编辑距离 < 0.2)
        3. 内容SimHash (海明距离 < 3)
        4. 语义相似度 (可选)
        """
        pass
    
    def merge_duplicates(self, group: DuplicateGroup) -> NewsItem:
        """合并重复条目，保留最佳版本"""
        # 优先保留: 官方来源 > 高可信度 > 完整内容
        pass
```

---

### M4: 信息汇编模块 (Report Assembler)

#### 3.4.1 功能职责
- 按模板汇总生成报告
- 智能摘要和关键信息提取
- 多格式输出 (Markdown/HTML/PDF)
- 交叉验证和冲突标注

#### 3.4.2 报告模板系统

```yaml
# templates/report_v2.yaml
templates:
  daily_digest:      # 日报模板
    sections:
      - title: "📰 重要头条"
        filter: "score >= 4.0"
        limit: 5
        sort: "score desc"
        
      - title: "🏢 各运营商动态"
        group_by: "operator"
        sub_sections:
          - "中国移动"
          - "中国电信"
          - "中国联通"
          - "中国铁塔"
          
      - title: "📊 分类统计"
        type: "statistics"
        charts: ["by_category", "by_source", "by_time"]
        
      - title: "🔍 热点追踪"
        type: "topic_clustering"
        cluster_count: 5

  executive_summary:  # 高管摘要
    sections:
      - title: "🎯 核心要点"
        type: "bullet_summary"
        limit: 10
        
      - title: "📈 战略动态"
        filter: "category in ['战略合作', '重大事件']"
        
      - title: "⚠️ 风险提示"
        filter: "category in ['安全事件', '业务关停']"
```

#### 3.4.3 智能摘要

```python
class SmartSummarizer:
    """智能摘要器"""
    
    def generate_summary(self, item: NewsItem) -> str:
        """
        生成新闻摘要:
        1. 提取关键句子 (TextRank)
        2. 识别关键实体 (运营商/人名/数字)
        3. 压缩到100-150字
        """
        pass
    
    def extract_key_points(self, items: List[NewsItem]) -> List[str]:
        """提取多条新闻的关键要点"""
        pass
    
    def cross_verify(self, items: List[NewsItem]) -> VerificationResult:
        """
        交叉验证:
        - 同一事件多来源报道对比
        - 标注信息冲突
        - 标注"未经官方证实"
        """
        pass
```

#### 3.4.4 输出格式

```python
class ReportRenderer:
    """报告渲染器"""
    
    def render_markdown(self, report: Report) -> str:
        """渲染Markdown格式"""
        pass
    
    def render_html(self, report: Report) -> str:
        """渲染HTML格式（带样式）"""
        pass
    
    def render_json(self, report: Report) -> dict:
        """渲染JSON格式（供API使用）"""
        pass
```

---

## 四、工作流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              完整工作流程                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. 接收查询                                                                 │
│     └── 用户输入: 运营商列表、时间范围、关注领域                               │
│         ↓                                                                   │
│  2. 任务规划 (M1)                                                            │
│     ├── 生成关键词组合 (核心词+业务词+事件词+高管词)                           │
│     ├── 分配采集来源 (按优先级)                                               │
│     └── 生成任务清单 (TaskPlan)                                              │
│         ↓                                                                   │
│  3. 并发采集 (M2)                                                            │
│     ├── 启动多个采集任务 (asyncio.gather)                                     │
│     ├── 应用反爬策略 (UA轮换/代理/延迟)                                        │
│     ├── 失败重试与降级                                                        │
│     └── 原始数据存入 raw/                                                    │
│         ↓                                                                   │
│  4. 数据处理 (M3)                                                            │
│     ├── 数据标准化 (统一字段格式)                                              │
│     ├── 去重处理 (SimHash + 标题相似度)                                        │
│     ├── 质量评分 (可信度/重要性/时效性)                                        │
│     └── 构建索引 (支持多维度检索)                                              │
│         ↓                                                                   │
│  5. 报告生成 (M4)                                                            │
│     ├── 按模板筛选和分组                                                       │
│     ├── 智能摘要生成                                                          │
│     ├── 交叉验证与冲突标注                                                     │
│     └── 多格式输出 (Markdown/HTML/JSON)                                       │
│         ↓                                                                   │
│  6. 结果交付                                                                 │
│     ├── 保存到 output/                                                       │
│     └── 返回报告路径和摘要                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 五、关键技术方案

### 5.1 反爬策略

| 策略 | 实现方式 | 适用场景 |
|-----|---------|---------|
| **UA轮换** | 维护100+真实UA池 | 所有爬虫 |
| **请求指纹** | 随机化Header顺序、TLS指纹 | 高防护站点 |
| **代理池** | 住宅代理 + 数据中心代理 | 频繁请求 |
| **Cookie持久** | 模拟登录后保持Session | 需要登录的站点 |
| **请求间隔** | 随机延迟 + 指数退避 | 所有爬虫 |
| **无头浏览器** | Playwright/Selenium | 动态渲染页面 |

### 5.2 并发控制

```python
# 使用信号量控制并发
semaphore = asyncio.Semaphore(5)  # 最多5个并发

async def fetch_with_limit(task):
    async with semaphore:
        return await fetch(task)
```

### 5.3 数据质量保障

```python
# 质量检查规则
quality_rules = [
    # 标题不能为空且长度合理
    lambda item: 10 <= len(item.title) <= 100,
    # 必须有发布时间
    lambda item: item.published_at is not None,
    # 内容不能太短
    lambda item: len(item.content) >= 50,
    # 来源必须在白名单
    lambda item: item.source_name in SOURCE_WHITELIST,
]
```

---

## 六、目录结构

```
telecom-news-fetcher/
├── SKILL.md                    # 技能文档
├── DESIGN.md                   # 本设计文档
├── README.md                   # 使用说明
├── config/
│   ├── main.yaml              # 主配置
│   ├── sources.yaml           # 来源配置
│   ├── keywords.yaml          # 关键词配置
│   └── antispider.yaml        # 反爬策略
├── src/
│   ├── __init__.py
│   ├── main.py                # 主入口
│   ├── planner/               # M1: 任务分解
│   │   ├── __init__.py
│   │   ├── task_planner.py
│   │   ├── keyword_generator.py
│   │   └── source_allocator.py
│   ├── collector/             # M2: 采集引擎
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── request_manager.py
│   │   ├── spiders/           # 爬虫集合
│   │   │   ├── base.py
│   │   │   ├── c114_spider.py
│   │   │   ├── official_spider.py
│   │   │   └── ...
│   │   └── apis/              # API集合
│   │       ├── brave_search.py
│   │       └── bing_search.py
│   ├── storage/               # M3: 存储管理
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── models.py
│   │   ├── deduplicator.py
│   │   └── indexer.py
│   └── assembler/             # M4: 报告汇编
│       ├── __init__.py
│       ├── assembler.py
│       ├── summarizer.py
│       ├── verifier.py
│       └── templates/
│           ├── daily_digest.md
│           └── executive_summary.md
├── data/                      # 数据目录
│   ├── raw/                   # 原始数据
│   ├── processed/             # 处理后数据
│   ├── index/                 # 索引文件
│   └── archive/               # 归档数据
├── output/                    # 报告输出
├── tests/                     # 测试用例
├── requirements.txt
└── pyproject.toml
```

---

## 七、演进路线

### Phase 1: 基础重构 (1-2周)
- [ ] 模块化拆分现有代码
- [ ] 实现基础的任务规划器
- [ ] 重构爬虫为统一接口
- [ ] 实现本地存储和去重

### Phase 2: 能力增强 (2-3周)
- [ ] 集成Brave/Bing搜索API
- [ ] 实现智能摘要生成
- [ ] 完善反爬策略
- [ ] 添加更多行业来源

### Phase 3: 智能化 (3-4周)
- [ ] 引入LLM进行内容理解
- [ ] 实现话题聚类
- [ ] 添加情感分析
- [ ] 智能推荐关注领域

### Phase 4: 平台化 (长期)
- [ ] Web管理界面
- [ ] 定时任务调度
- [ ] 数据可视化仪表盘
- [ ] API服务化

---

## 八、与现有系统的对比

| 维度 | 当前实现 | 新设计方案 |
|-----|---------|-----------|
| **架构** | 单体脚本 | 模块化设计 |
| **任务规划** | 简单参数传递 | 智能任务分解 |
| **采集方式** | 仅爬虫 | 爬虫+API+搜索 |
| **反爬能力** | 基础UA轮换 | 多层级反爬策略 |
| **数据存储** | 内存处理 | 持久化+索引 |
| **去重** | 无 | SimHash+语义去重 |
| **报告生成** | 固定模板 | 可配置模板系统 |
| **扩展性** | 难扩展 | 插件化设计 |
| **可维护性** | 低 | 高 |

---

## 九、下一步行动建议

1. **确认设计方向** - review本方案，确认是否符合预期
2. **确定Phase 1范围** - 明确MVP要实现的功能
3. **技术选型确认** - 确认关键技术方案（如是否引入LLM）
4. **开始重构** - 按Phase 1计划逐步实施

---

*设计文档版本: v1.0*
*最后更新: 2026-04-30*
