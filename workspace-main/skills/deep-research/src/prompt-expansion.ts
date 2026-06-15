/**
 * 提示词扩写模块
 * 将简短的用户 query 扩写为结构化研究任务书
 * 支持两种方向：市场雷达 (A) 和 技术拆解 (B)
 */

import { generateObjectWithRetry } from './ai/providers';
import { z } from 'zod';

import { o3MiniModel } from './ai/providers';
import { systemPrompt } from './prompt';

// ─── 类型定义 ───────────────────────────────────────

export type ResearchDirection = 'market-radar' | 'technical-deepdive' | 'general';

/** 方向 A：市场雷达变量 */
export type MarketRadarVariables = {
  coreSubject: string;
  researchIntent: string;
  temporalFocus: string;
  focusSources: string[];
  domainSpecificSources: string[];
  signalCriteria: string[];
  topicClusters: string[];
};

/** 方向 B：技术拆解变量（4层：热点归因/技术拆解/产品拆解/竞争趋势） */
export type TechnicalDeepDiveVariables = {
  coreSubject: string;
  researchIntent: string;
  focusSources: string[];          // 6 类信息来源
  technicalLayers: string[];       // 4 层分析结构
  comparisonTargets: string[];     // 竞品/替代方案
  moatDimensions: string[];        // 壁垒与可持续性维度
};

export type ExpansionVariables = MarketRadarVariables | TechnicalDeepDiveVariables;

export type ExpansionResult = {
  direction: ResearchDirection;
  variables: ExpansionVariables | null;   // null for 'general'
  expandedQuery: string;                  // original query for 'general'
};

export type DirectionDetection = {
  direction: ResearchDirection;
  confidence: number;
  reasoning: string;
};

// ─── 方向检测 ───────────────────────────────────────

export async function detectDirection(query: string): Promise<DirectionDetection> {
  const res = await generateObjectWithRetry({
    model: o3MiniModel,
    system: systemPrompt(),
    prompt: `Analyze the following research query and determine which research direction best fits it.

Three directions:
1. **market-radar**: Best for queries about discovering trends, identifying hot signals, scanning market dynamics, tracking industry movements. Triggered by queries mentioning: trends, hot topics, market landscape, industry dynamics, "what's worth watching", "recent developments", scanning, signals, emerging products, ecosystem overview.

2. **technical-deepdive**: Best for queries about deeply analyzing a specific product/technology - explaining WHY it became hot, dissecting its tech and product characteristics, competitive landscape and sustainability. Triggered by queries mentioning: why popular, deep analysis, technical breakdown, architecture dissection, competitive moat, how it works internally, design philosophy, product teardown, what makes it special.

3. **general**: For queries that don't clearly fit the above two categories. This includes: academic research, historical analysis, methodology comparison, broad knowledge surveys, how-to guides, policy analysis, or any query where the specialized templates would add more noise than value.

Query: "${query}"

Return your best judgment. If confidence is below 0.7, the system will ask the user to confirm.`,
    schema: z.object({
      direction: z.enum(['market-radar', 'technical-deepdive', 'general']),
      confidence: z.number().min(0).max(1).describe('Confidence level 0-1'),
      reasoning: z.string().describe('Brief explanation of why this direction was chosen'),
    }),
  });

  return res.object as DirectionDetection;
}

// ─── 方向 A：市场雷达扩写 ────────────────────────────

async function expandMarketRadar(query: string): Promise<{ variables: MarketRadarVariables; expandedQuery: string }> {
  const res = await generateObjectWithRetry({
    model: o3MiniModel,
    system: systemPrompt(),
    prompt: `You are helping to expand a brief research query into a detailed "Market Radar" research brief.

Original query: "${query}"

Generate the following variables to populate the research brief template. The brief should be written in the SAME LANGUAGE as the original query.

Requirements:
- coreSubject: What exactly is being studied (be specific, not generic)
- researchIntent: The specific research goal (focus on signal identification, not just listing news)
- temporalFocus: Time range appropriate for the query (e.g., "最近3-6个月", "2025年至今")
- focusSources: Exactly 5 source categories to monitor. Always include: major company releases, open-source community trends, research lab outputs, new product launches in the domain, developer/user adoption signals. Tailor each to the specific query.
- domainSpecificSources: 3-5 specific technology/product domains relevant to the query (e.g., "AI Agent、AI Coding、多模态、企业AI工具")
- signalCriteria: Exactly 5 criteria for filtering high-value signals. Each criterion should be a yes/no question format. Always include: strategic direction changes, technology reaching product stage, capability boundary improvements, ecosystem/demand shifts, sustained influence vs short-term noise. Adapt wording to the query.
- topicClusters: 4-7 topic categories for grouping the findings (e.g., "AI Agent、AI Coding、多模态、开源生态、企业AI")

Make each variable specific to this query, not generic boilerplate.`,
    schema: z.object({
      coreSubject: z.string().describe('Core research subject, specific to this query'),
      researchIntent: z.string().describe('Research goal focused on signal identification'),
      temporalFocus: z.string().describe('Time range for the research'),
      focusSources: z.array(z.string()).min(5).max(5).describe('Exactly 5 source categories to monitor'),
      domainSpecificSources: z.array(z.string()).min(3).max(6).describe('Specific technology/product domains'),
      signalCriteria: z.array(z.string()).min(5).max(5).describe('Exactly 5 filtering criteria, yes/no question format'),
      topicClusters: z.array(z.string()).min(4).max(8).describe('Topic categories for grouping findings'),
    }),
  });

  const variables = res.object as MarketRadarVariables;
  const expandedQuery = buildMarketRadarQuery(variables, query);
  return { variables, expandedQuery };
}

function buildMarketRadarQuery(v: MarketRadarVariables, originalQuery: string): string {
  const focusSourcesList = v.focusSources.map(s => `- ${s}`).join('\n');
  const signalCriteriaList = v.signalCriteria.map(c => `- ${c}`).join('\n');
  const topicClustersStr = v.topicClusters.join('、');
  const domainSourcesStr = v.domainSpecificSources.join('、');

  return `请作为 AI 行业研究分析师，对${v.temporalFocus}内的${v.coreSubject}进行系统性扫描，目标是${v.researchIntent}，而不是简单罗列新闻。

原始查询：${originalQuery}

重点关注以下来源和对象：
${focusSourcesList}
- ${domainSourcesStr}方向的新产品发布和重要进展
- 开发者社区、用户采用、投资关注度明显提升的产品方向

请按以下标准筛选"高价值信号"：
${signalCriteriaList}

请完成以下任务：
1. 提取最近最值得关注的 5-10 个市场热点信号
2. 按主题簇归类，例如：${topicClustersStr}
3. 对每个热点说明：
   - 事件/产品/发布内容是什么
   - 为什么重要
   - 它反映了什么更深层趋势
   - 对未来产品方向、创业机会或竞争格局意味着什么
4. 对这些热点进行优先级排序，并说明排序理由
5. 指出其中最值得进一步做技术/产品拆解研究的 3-5 个主题

研究要求：
- 优先引用公开、可靠、可验证的信息
- 尽量给出时间点、产品名称、机构/公司名称和具体事件
- 避免泛泛而谈，重点提炼趋势信号
- 区分"事实""推断""判断"
- 对不确定性较高的结论请明确说明

请按以下结构输出：
1. 执行摘要
2. 热点信号总览
3. 分主题热点分析
4. 热点优先级排序与理由
5. 值得深挖的主题建议
6. 未来 1-3 个月值得持续跟踪的信号清单`;
}

// ─── 方向 B：技术拆解扩写 ────────────────────────────

async function expandTechnicalDeepDive(query: string): Promise<{ variables: TechnicalDeepDiveVariables; expandedQuery: string }> {
  const res = await generateObjectWithRetry({
    model: o3MiniModel,
    system: systemPrompt(),
    prompt: `You are helping to expand a brief research query into a detailed "Technical Deep-dive" research brief.

Original query: "${query}"

Generate the following variables to populate the research brief template. The brief should be written in the SAME LANGUAGE as the original query.

The core question is NOT "what is this product" but "WHY is it hot right now" - explain the hype, dissect the tech and product, and judge sustainability.

Requirements:
- coreSubject: The specific product/technology being analyzed (be precise, e.g., "Cursor AI 代码编辑器" not just "AI coding tools")
- researchIntent: The deep-dive goal focused on WHY it's popular, HOW it works, WHO it competes with, and WHETHER it's sustainable (e.g., "解释 Cursor 为什么成为 AI Coding 赛道热点，拆解其技术特征、产品特征、竞争格局和可持续性")
- focusSources: Exactly 6 information source categories tailored to this query. Should cover: official tech blogs/engineering articles, open-source repos or code analysis, academic papers or whitepapers, competitive reviews and benchmarks, founder/CTO interviews and talks, developer community deep-dive discussions. Adapt each to the specific product/tech.
- technicalLayers: Exactly 4 analysis layers following this structure (adapt descriptions to be specific to this query):
  1. 热点归因层 — 为什么在当前时间点成为热点？哪些因素共同推动了关注度？是短期舆论还是长期趋势信号？
  2. 技术拆解层 — 核心技术路线、模型能力依赖、系统架构、关键工程设计、与同类方案的技术差异和限制、技术壁垒深度
  3. 产品拆解层 — 目标用户和核心场景、为什么"明显更好用"、关键产品机制和交互体验、推动传播/留存/口碑的设计
  4. 竞争与趋势判断层 — 主要竞品和替代方案、差异化优势和短板、可持续性判断、未来6-12个月走势预判
- comparisonTargets: 3-5 direct competitors or comparable products/technologies (AI should identify the most relevant ones based on the query)
- moatDimensions: 4-6 dimensions for evaluating competitive moat and sustainability (e.g., data flywheel, user habit lock-in, switching costs, ecosystem lock-in, technical lead durability)

Make each variable specific to this query, not generic boilerplate.`,
    schema: z.object({
      coreSubject: z.string().describe('Specific product/technology being analyzed'),
      researchIntent: z.string().describe('Deep-dive research goal focused on WHY it is hot'),
      focusSources: z.array(z.string()).min(6).max(6).describe('Exactly 6 information source categories'),
      technicalLayers: z.array(z.string()).min(4).max(4).describe('Exactly 4 analysis layers: 热点归因/技术拆解/产品拆解/竞争趋势'),
      comparisonTargets: z.array(z.string()).min(3).max(5).describe('Direct competitors or comparable products'),
      moatDimensions: z.array(z.string()).min(4).max(6).describe('Competitive moat and sustainability dimensions'),
    }),
  });

  const variables = res.object as TechnicalDeepDiveVariables;
  const expandedQuery = buildTechnicalDeepDiveQuery(variables, query);
  return { variables, expandedQuery };
}

function buildTechnicalDeepDiveQuery(v: TechnicalDeepDiveVariables, originalQuery: string): string {
  const focusSourcesList = v.focusSources.map(s => `- ${s}`).join('\n');
  const layersList = v.technicalLayers.map(l => `- ${l}`).join('\n');
  const comparisonTargetsStr = v.comparisonTargets.join('、');
  const moatDimensionsStr = v.moatDimensions.join('、');

  return `请对${v.coreSubject}进行一项系统性的深度研究，目标不是简单介绍其功能，而是${v.researchIntent}。

原始查询：${originalQuery}

请重点从以下四个层面展开：

${v.technicalLayers[0] ? `一、热点归因\n${v.technicalLayers[0]}` : '一、热点归因\n- 它为什么在当前时间点成为热点？\n- 是哪些因素共同推动了关注度上升？\n- 这是短期舆论热点，还是长期产品趋势信号？'}

${v.technicalLayers[1] ? `二、技术拆解\n${v.technicalLayers[1]}` : '二、技术拆解\n- 产品背后的核心技术路线是什么？\n- 它依赖哪些模型能力、系统架构或关键工程设计？\n- 与同类方案相比，技术上最关键的特征和限制是什么？\n- 是否存在明显的技术壁垒，还是容易被复制？'}

${v.technicalLayers[2] ? `三、产品拆解\n${v.technicalLayers[2]}` : '三、产品拆解\n- 它面向哪些用户群体和核心场景？\n- 用户为什么会觉得它"明显更好用"或"值得尝试"？\n- 它的关键产品机制、交互体验、工作流设计和价值主张是什么？\n- 哪些设计直接推动了传播、留存或口碑扩散？'}

${v.technicalLayers[3] ? `四、竞争与趋势判断\n${v.technicalLayers[3]}` : '四、竞争与趋势判断\n- 它的主要竞品和替代方案有哪些？\n- 它与竞品相比的差异化优势和短板是什么？\n- 这种优势是否具备可持续性？\n- 从未来 6-12 个月看，这种产品方向是否会持续升温、趋于同质化，还是被平台能力吸收？'}

重点关注以下信息来源：
${focusSourcesList}

主要竞品/替代方案参考：${comparisonTargetsStr}
壁垒评估维度：${moatDimensionsStr}

研究要求：
- 同时从技术视角和产品视角分析
- 尽量引用具体产品案例、功能、发布时间、公开演示、用户反馈、定价和社区讨论
- 区分事实、推断和分析判断
- 如果关键信息缺失，请明确指出并做谨慎推断
- 避免空泛介绍，重点解释"为什么它会火"和"它是否真的有价值"

请按以下结构输出：
1. 执行摘要
2. 热点形成原因分析
3. 技术特征拆解
4. 产品特征拆解
5. 竞品与替代方案对比
6. 壁垒、风险与可持续性判断
7. 对行业、创业者或产品团队的启示`;
}

// ─── 统一入口 ───────────────────────────────────────

export async function expandQuery(
  query: string,
  options: {
    directionHint?: 'auto' | 'radar' | 'deepdive' | 'general';
    interactive?: boolean;
    askQuestion?: (q: string) => Promise<string>;
  } = {},
): Promise<ExpansionResult> {
  const { directionHint = 'auto', interactive = true, askQuestion } = options;

  // Step 1: 确定方向
  let detection: DirectionDetection;
  if (directionHint === 'radar') {
    detection = { direction: 'market-radar', confidence: 1, reasoning: '用户指定方向 A' };
  } else if (directionHint === 'deepdive') {
    detection = { direction: 'technical-deepdive', confidence: 1, reasoning: '用户指定方向 B' };
  } else if (directionHint === 'general') {
    detection = { direction: 'general', confidence: 1, reasoning: '用户指定通用模式' };
  } else {
    detection = await detectDirection(query);
  }

  // Step 2: 路由判断
  // - general 方向或低置信度 → 让用户选择
  // - A/B 高置信度 → 直接使用专业模板
  const CONFIDENCE_THRESHOLD = 0.7;
  let needsUserConfirm = false;

  if (detection.direction === 'general') {
    // general 高置信度：直接跳过扩写
    // general 低置信度：让用户确认
    needsUserConfirm = detection.confidence < CONFIDENCE_THRESHOLD;
  } else if (detection.confidence < CONFIDENCE_THRESHOLD) {
    // A/B 但低置信度：让用户确认
    needsUserConfirm = true;
  }

  // Step 3: 如果需要用户确认且支持交互
  if (needsUserConfirm && interactive && askQuestion) {
    detection = await askUserForDirection(query, detection, askQuestion);
  }

  // Step 4: 按方向执行
  if (detection.direction === 'general') {
    console.log('  路由判定: 通用模式，跳过提示词扩写');
    return { direction: 'general', variables: null, expandedQuery: query };
  }

  let result: ExpansionResult;
  if (detection.direction === 'market-radar') {
    const { variables, expandedQuery } = await expandMarketRadar(query);
    result = { direction: 'market-radar', variables, expandedQuery };
  } else {
    const { variables, expandedQuery } = await expandTechnicalDeepDive(query);
    result = { direction: 'technical-deepdive', variables, expandedQuery };
  }

  // Step 5: 交互确认（非 general 方向）
  if (interactive && askQuestion) {
    result = await presentExpansion(result, detection, askQuestion);
  }

  return result;
}

// ─── 用户方向选择 ──────────────────────────────────

async function askUserForDirection(
  query: string,
  detection: DirectionDetection,
  askQuestion: (q: string) => Promise<string>,
): Promise<DirectionDetection> {
  const suggestionLabel = detection.direction === 'market-radar'
    ? 'A: 市场雷达型'
    : detection.direction === 'technical-deepdive'
      ? 'B: 技术拆解型'
      : 'G: 通用模式';

  console.log('\n═══════════════════════════════════════════════════');
  console.log('  任务类型确认');
  console.log('═══════════════════════════════════════════════════');
  console.log(`  AI 建议: ${suggestionLabel} (置信度 ${(detection.confidence * 100).toFixed(0)}%)`);
  console.log(`  原因: ${detection.reasoning}`);
  console.log('');
  console.log('  a  — 市场雷达型（发现热点、识别趋势、筛选信号）');
  console.log('  b  — 技术拆解型（热点归因、技术拆解、产品拆解、竞争判断）');
  console.log('  g  — 通用模式（由 AI 自行确定研究方法和路径）');
  console.log('═══════════════════════════════════════════════════');

  const action = (await askQuestion('\n  选择: ')).trim().toLowerCase();

  if (action === 'a') {
    return { direction: 'market-radar', confidence: 1, reasoning: '用户选择方向 A' };
  } else if (action === 'b') {
    return { direction: 'technical-deepdive', confidence: 1, reasoning: '用户选择方向 B' };
  } else {
    // 'g' or default
    return { direction: 'general', confidence: 1, reasoning: '用户选择通用模式' };
  }
}

// ─── 交互展示与确认 ──────────────────────────────────

async function presentExpansion(
  result: ExpansionResult,
  detection: DirectionDetection,
  askQuestion: (q: string) => Promise<string>,
): Promise<ExpansionResult> {
  const directionLabel = result.direction === 'market-radar'
    ? 'A: 市场雷达型（发现热点、识别趋势、筛选信号）'
    : 'B: 技术拆解型（热点归因、技术拆解、产品拆解、竞争判断）';

  console.log('\n═══════════════════════════════════════════════════');
  console.log('  提示词扩写');
  console.log('═══════════════════════════════════════════════════');
  console.log(`  检测到方向: ${directionLabel}`);
  console.log(`  置信度: ${(detection.confidence * 100).toFixed(0)}% | ${detection.reasoning}`);
  console.log('');

  // 展示核心变量
  if (result.direction === 'market-radar') {
    const v = result.variables as MarketRadarVariables;
    console.log(`  研究对象: ${v.coreSubject}`);
    console.log(`  研究目的: ${v.researchIntent}`);
    console.log(`  时间范围: ${v.temporalFocus}`);
    console.log(`  关注来源: ${v.focusSources.length} 类`);
    v.focusSources.forEach(s => console.log(`    - ${s}`));
    console.log(`  筛选标准: ${v.signalCriteria.length} 条`);
    v.signalCriteria.forEach(c => console.log(`    - ${c}`));
    console.log(`  主题簇:   ${v.topicClusters.join('、')}`);
  } else {
    const v = result.variables as TechnicalDeepDiveVariables;
    console.log(`  研究对象: ${v.coreSubject}`);
    console.log(`  研究目的: ${v.researchIntent}`);
    console.log(`  信息来源: ${v.focusSources.length} 类`);
    v.focusSources.forEach(s => console.log(`    - ${s}`));
    console.log(`  分析层次: ${v.technicalLayers.length} 层`);
    v.technicalLayers.forEach((l, i) => console.log(`    ${['一', '二', '三', '四'][i]}、${l}`));
    console.log(`  对比对象: ${v.comparisonTargets.join('、')}`);
    console.log(`  壁垒维度: ${v.moatDimensions.join('、')}`);
  }

  console.log('\n  操作: y 确认 / a 切换到市场雷达 / b 切换到技术拆解 / g 通用模式');
  console.log('═══════════════════════════════════════════════════');

  const action = (await askQuestion('\n  选择: ')).trim().toLowerCase();

  // 提取原始 coreSubject 用于方向切换
  const currentSubject = result.direction === 'market-radar'
    ? (result.variables as MarketRadarVariables).coreSubject
    : (result.variables as TechnicalDeepDiveVariables).coreSubject;

  if (action === 'a' && result.direction !== 'market-radar') {
    console.log('  切换到方向 A: 市场雷达型...');
    const { variables, expandedQuery } = await expandMarketRadar(currentSubject);
    return { direction: 'market-radar', variables, expandedQuery };
  } else if (action === 'b' && result.direction !== 'technical-deepdive') {
    console.log('  切换到方向 B: 技术拆解型...');
    const { variables, expandedQuery } = await expandTechnicalDeepDive(currentSubject);
    return { direction: 'technical-deepdive', variables, expandedQuery };
  } else if (action === 'g') {
    console.log('  切换到通用模式，跳过提示词扩写');
    return { direction: 'general', variables: null, expandedQuery: currentSubject };
  }

  // 'y' or any other key: confirm current
  console.log('  已确认扩写方案');
  return result;
}
