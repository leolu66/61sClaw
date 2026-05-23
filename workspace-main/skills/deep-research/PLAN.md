# 问题分析 + 执行计划阶段设计

## 设计理念

**当前流程**：用户查询 → generateSerpQueries() 即兴生成搜索词 → 递归搜索

**新流程**：

```
用户查询
  ↓
[Step 1] analyzeQuery()              ← AI 分析问题类型，匹配预设模板，输出推荐维度
  ↓
[Step 2] presentAndConfirm()         ← 展示维度给用户确认/增删/调整优先级
  ↓
[Step 2.5] reviewDimensions()        ← AI 审核人角色反思：覆盖完整性/重叠/盲区/追问
  ↓
[Step 3] generateResearchPlan()      ← AI 填充子主题+搜索词+资源分配
  ↓
[Step 4] generateReportOutline()     ← AI 生成报告大纲，用户确认
  ↓
[Phase 5] deepResearchByPlan()       ← 按计划执行搜索，全局并发控制+缓存
  ↓
[Phase 6] writeFinalReportWithOutline() ← 按大纲章节结构填充内容生成报告
```

## 核心数据模型

```typescript
type AnglePreset = {
  title: string;
  priority: 'critical' | 'important' | 'nice-to-have';
  desc: string;
};

type QueryAnalysis = {
  topic: string;
  questionType: string;
  keyEntities: string[];
  scope: { domains: string[]; timeRange?: string };
  estimatedComplexity: 'low' | 'medium' | 'high';
  recommendedDimensions: {
    title: string;
    priority: 'critical' | 'important' | 'nice-to-have';
    description: string;
    source: 'preset' | 'ai-generated';
  }[];
};

type ResearchDimension = {
  id: string;
  title: string;
  subTopics: {
    title: string;
    initialQueries: string[];
    suggestedBreadth: number;
    suggestedDepth: number;
  }[];
  priority: 'critical' | 'important' | 'nice-to-have';
  estimatedWeight: number;
};

type ResearchPlan = {
  analysis: QueryAnalysis;
  dimensions: ResearchDimension[];
  totalEstimatedQueries: number;
  executionOrder: string[];
};

// 反思审核结果
type DimensionReview = {
  verdict: 'approved' | 'needs-adjustment';
  issues: {
    type: 'gap' | 'overlap' | 'ambiguity' | 'missing-perspective';
    description: string;
    suggestion?: string;
  }[];
  suggestedAdditions: {
    title: string;
    reason: string;
    priority: 'critical' | 'important' | 'nice-to-have';
  }[];
  followUpQuestions: {
    question: string;
    reason: string;
    affectedDimensions: string[];
  }[];
};

// 报告大纲
type ReportOutline = {
  title: string;
  summary: string;
  chapters: {
    id: string;
    title: string;
    description: string;
    estimatedWeight: number;
    dimensionId?: string;
    subSections?: string[];
    chapterType: 'intro' | 'body' | 'conclusion' | 'appendix';
  }[];
};

// 缓存条目
type CacheEntry = {
  query: string;
  provider: string;
  results: SearchResult[];
  timestamp: number;
  ttl: number;
};
```

## 预设研究角度模板

```typescript
const RESEARCH_ANGLE_PRESETS = {
  '对比评估': [
    { title: '功能与特性对比', priority: 'critical',     desc: '核心功能、差异化特性' },
    { title: '性能与可扩展性', priority: 'critical',     desc: '基准测试、压力测试数据' },
    { title: '成本与定价',     priority: 'important',    desc: '定价模型、TCO分析' },
    { title: '生态与社区',     priority: 'important',    desc: '插件生态、社区活跃度' },
    { title: '实际案例',       priority: 'nice-to-have', desc: '生产环境使用案例' },
  ],
  '技术调研': [
    { title: '技术原理与架构', priority: 'critical' },
    { title: '工具链与生态',   priority: 'critical' },
    { title: '性能基准',       priority: 'important' },
    { title: '开发体验',       priority: 'important' },
    { title: '发展趋势',       priority: 'nice-to-have' },
  ],
  '市场分析': [
    { title: '市场规模与趋势',  priority: 'critical' },
    { title: '竞争格局',        priority: 'critical' },
    { title: '用户画像与需求',  priority: 'important' },
    { title: '商业模式',        priority: 'important' },
    { title: '政策与合规',      priority: 'nice-to-have' },
  ],
  '综述研究': [
    { title: '概念定义与背景',   priority: 'critical' },
    { title: '发展历史与里程碑', priority: 'important' },
    { title: '核心方法/技术',    priority: 'critical' },
    { title: '当前挑战与争议',   priority: 'important' },
    { title: '未来展望',         priority: 'nice-to-have' },
  ],
};
```

## Task 1: 新增 `src/search-cache.ts` — 搜索结果缓存

```typescript
// cache/ 目录，文件名 hash(query).json，TTL 默认 24h
async function getCached(query: string): Promise<SearchResult[] | null>
async function setCached(query: string, provider: string, results: SearchResult[]): void
```

集成到 `smartSearch()`：先查缓存 → 未命中则搜索 → 写入缓存。

## Task 2: 新增 `src/concurrency.ts` — 全局并发控制

```typescript
export function initConcurrency(maxConcurrent: number): void
export function getSearchLimiter(): pLimit.Limit
```

所有搜索统一 `await getSearchLimiter()(() => smartSearch(...))`。

## Task 3: 新增 `src/research-plan.ts` — 分析+确认+审核+计划+大纲

### 3.1 预设模板 + 类型定义

### 3.2 `analyzeQuery(query)` — 问题分析

1 次 AI 调用。判断问题类型，从预设模板中挑选/裁剪/补充维度。输出 `QueryAnalysis`。

### 3.3 `presentAndConfirm(analysis, askQuestion)` — 用户确认维度

交互模式展示推荐维度，支持指令：
- `y` / 空行 — 确认
- `d 1,3` — 删除维度
- `a 标题` — 新增维度
- `p 2,4` — 交换优先级
- `e 1 新标题` — 编辑维度
- 多轮编辑直到满意

非交互模式跳过。

### 3.4 `reviewDimensions(query, dimensions, userFeedback?)` — 反思审核

1 次 AI 调用（审核人角色）。从四个角度审核：
- **gap**：是否有重要角度被遗漏（利益相关者/时间/地域/风险）
- **overlap**：是否有维度高度重叠
- **ambiguity**：用户需求中是否有模糊点需要确认
- **missing-perspective**：是否只从单一视角出发

输出 `DimensionReview`：
- `verdict: 'approved'` → 通过，继续
- `verdict: 'needs-adjustment'` → 展示问题+建议新增+追问

### 3.5 `presentReviewAndHandle(review, dimensions, askQuestion)` — 处理审核结果

审核通过时：直接继续。

发现问题时展示：
```
⚠️ 维度审核发现以下问题：

问题:
  [gap] 缺少安全风险维度 — ...
  [ambiguity] 未明确对比的使用场景 — ...

建议新增:
  🟡 安全性对比 — ...

需要您确认的问题:
  Q1: 您的使用场景是新建集群还是迁移现有集群？
       (原因：迁移场景需额外考虑兼容性)

操作: y接受建议并继续 / a逐个回答追问 / i忽略审核建议
```

- `y` — 采纳建议新增维度，跳过追问
- `a` — 逐个回答追问问题，答案追加到用户反馈
- `i` — 忽略审核，按原方案继续

返回最终确认的维度列表。

### 3.6 `generateResearchPlan(query, confirmedDims, userBreadth, userDepth)` — 计划细化

1 次 AI 调用。为每个维度生成子主题 + initialQueries + breadth/depth。
资源分配：critical 50%、important 35%、nice-to-have 15%。

### 3.7 `generateReportOutline(plan)` — 报告大纲生成

1 次 AI 调用。将研究维度转化为报告章节结构：
- 自动补充 intro / conclusion / appendix
- body 章节关联 dimension.id
- subSections 可选子章节

### 3.8 `presentOutlineAndConfirm(outline, askQuestion)` — 用户确认大纲

交互模式展示报告骨架，支持编辑/新增/删除/移动顺序。
非交互模式跳过。

## Task 4: 改造 `src/deep-research.ts`

### 4.1 新增 `deepResearchByPlan(query, plan)`

- 维度间并行（受全局 searchLimiter 控制）
- 子主题用预设 initialQueries 启动搜索
- 独立 breadth/depth
- 搜索结果走缓存
- URL 去重

### 4.2 保留原有 `deepResearch()` 作为 fallback

- `--no-plan` 可跳过计划阶段
- 原有函数也走全局 limiter + 缓存

## Task 5: 改造 `src/search-providers.ts`

- `smartSearch()` 集成缓存层
- 新增 `'cache'` provider 类型

## Task 6: 改造 `src/run.ts`

### 6.1 新增 CLI 参数

```typescript
'concurrency': { type: 'string', default: '3' },    // 搜索并发数
'no-plan': { type: 'boolean', default: false },       // 跳过计划阶段
'no-cache': { type: 'boolean', default: false },      // 跳过缓存
'cache-ttl': { type: 'string', default: '86400' },   // 缓存TTL(秒)
```

### 6.2 完整流程编排

```
需求澄清(现有)
  → initConcurrency(concurrency)
  → Step 1: analyzeQuery()               // AI 分析+模板匹配
  → Step 2: presentAndConfirm()           // 用户确认维度
  → Step 2.5: reviewDimensions()          // AI 审核人反思
  → Step 2.6: presentReviewAndHandle()    // 处理审核结果
  → Step 3: generateResearchPlan()        // AI 细化计划
  → Step 4: generateReportOutline()       // AI 生成大纲
  → Step 4.5: presentOutlineAndConfirm()  // 用户确认大纲
  → Phase 5: deepResearchByPlan()         // 搜索(并发+缓存)
  → Phase 6: writeFinalReportWithOutline() // 按大纲生成报告
```

## Task 7: 改造报告生成

新增 `writeFinalReportWithOutline(outline, learnings, sources)`：
- 大纲章节结构作为 AI 的结构约束
- body 章节填充对应 dimension 的 learnings
- 按 estimatedWeight 控制篇幅
- intro: 研究背景和方法
- conclusion: 综合建议
- appendix: 参考来源链接

## Task 8: 更新 `SKILL.md` 和 `_meta.json`

- 功能描述增加所有新特性
- 参数表增加新参数

## 改造前后对比

| 方面 | 改造前 | 改造后 |
|------|--------|--------|
| 搜索策略 | AI 即兴生成搜索词 | 预规划搜索词 + 维度拆解 |
| 维度来源 | 无 | 预设模板 + AI 适配 + 用户确认 |
| 质量保障 | 无 | 审核人角色反思(覆盖/重叠/盲区/追问) |
| 报告结构 | AI 自由发挥 | 大纲先行 + 按章节填充 |
| 资源分配 | 固定 breadth/depth 统一减半 | 按维度优先级动态分配 |
| 并发控制 | 硬编码 pLimit(2) | 可配置 `--concurrency N` |
| 搜索缓存 | 无 | cache/ 目录，24h TTL |
| 用户参与 | 无预览 | 维度确认 + 审核追问 + 大纲确认 |
| 降级兼容 | - | --no-plan 保留原有逻辑 |

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/search-cache.ts` | **新增** | 搜索结果缓存读写 |
| `src/concurrency.ts` | **新增** | 全局并发控制 |
| `src/research-plan.ts` | **新增** | 模板+分析+确认+审核+计划+大纲 |
| `src/search-providers.ts` | 修改 | smartSearch 集成缓存 |
| `src/deep-research.ts` | 修改 | deepResearchByPlan + limiter |
| `src/run.ts` | 修改 | 完整流程 + 新 CLI 参数 |
| `src/prompt.ts` | 修改 | 各阶段专用 prompt |
| `SKILL.md` | 修改 | 功能描述+参数表 |
| `_meta.json` | 修改 | 命令参数 |
