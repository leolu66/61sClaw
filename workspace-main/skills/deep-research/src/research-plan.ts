/**
 * 研究计划模块
 * 问题分析 → 维度确认 → 反思审核 → 计划细化 → 报告大纲
 */

import { generateObject } from 'ai';
import { z } from 'zod';

import { o3MiniModel } from './ai/providers';
import { systemPrompt } from './prompt';

// ─── 类型定义 ───────────────────────────────────────

export type AnglePreset = {
  title: string;
  priority: 'critical' | 'important' | 'nice-to-have';
  desc: string;
};

export type RecommendedDimension = {
  title: string;
  priority: 'critical' | 'important' | 'nice-to-have';
  description: string;
  source: 'preset' | 'ai-generated';
};

export type QueryAnalysis = {
  topic: string;
  questionType: string;
  keyEntities: string[];
  scope: { domains: string[]; timeRange?: string };
  estimatedComplexity: 'low' | 'medium' | 'high';
  recommendedDimensions: RecommendedDimension[];
};

export type ResearchDimension = {
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

export type ResearchPlan = {
  analysis: QueryAnalysis;
  dimensions: ResearchDimension[];
  totalEstimatedQueries: number;
  executionOrder: string[];
};

export type DimensionReview = {
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

export type ReportOutline = {
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

// ─── 预设研究角度模板 ──────────────────────────────

const RESEARCH_ANGLE_PRESETS: Record<string, AnglePreset[]> = {
  '对比评估': [
    { title: '功能与特性对比', priority: 'critical', desc: '核心功能、差异化特性' },
    { title: '性能与可扩展性', priority: 'critical', desc: '基准测试、压力测试数据' },
    { title: '成本与定价', priority: 'important', desc: '定价模型、TCO分析' },
    { title: '生态与社区', priority: 'important', desc: '插件生态、社区活跃度' },
    { title: '实际案例', priority: 'nice-to-have', desc: '生产环境使用案例' },
  ],
  '技术调研': [
    { title: '技术原理与架构', priority: 'critical', desc: '核心技术原理、系统架构设计' },
    { title: '工具链与生态', priority: 'critical', desc: '配套工具、生态系统' },
    { title: '性能基准', priority: 'important', desc: '性能测试数据、基准对比' },
    { title: '开发体验', priority: 'important', desc: '上手难度、开发效率、文档质量' },
    { title: '发展趋势', priority: 'nice-to-have', desc: '技术演进方向、未来规划' },
  ],
  '市场分析': [
    { title: '市场规模与趋势', priority: 'critical', desc: '市场容量、增长率、发展趋势' },
    { title: '竞争格局', priority: 'critical', desc: '主要玩家、市场份额、竞争策略' },
    { title: '用户画像与需求', priority: 'important', desc: '目标用户、核心需求、痛点' },
    { title: '商业模式', priority: 'important', desc: '盈利方式、定价策略、价值链' },
    { title: '政策与合规', priority: 'nice-to-have', desc: '监管政策、合规要求' },
  ],
  '综述研究': [
    { title: '概念定义与背景', priority: 'critical', desc: '核心概念、历史背景' },
    { title: '发展历史与里程碑', priority: 'important', desc: '关键事件、发展阶段' },
    { title: '核心方法/技术', priority: 'critical', desc: '主要方法论、关键技术' },
    { title: '当前挑战与争议', priority: 'important', desc: '面临的问题、学术/行业争议' },
    { title: '未来展望', priority: 'nice-to-have', desc: '发展趋势、预测' },
  ],
};

const PRIORITY_ICON: Record<string, string> = {
  critical: '🔴',
  important: '🟡',
  'nice-to-have': '🟢',
};

// ─── Step 1: 问题分析 ───────────────────────────────

export async function analyzeQuery(query: string): Promise<QueryAnalysis> {
  const presetTypes = Object.keys(RESEARCH_ANGLE_PRESETS).join('、');

  const res = await generateObject({
    model: o3MiniModel,
    system: systemPrompt(),
    prompt: `Analyze the following research query and determine the research approach.

Query: "${query}"

Tasks:
1. Identify the core research topic and key entities (people, companies, products, concepts)
2. Classify the question type into ONE of: ${presetTypes}. If none fits perfectly, choose the closest match.
3. Identify the domains/fields involved and any time range constraints
4. Estimate the complexity: low (simple factual), medium (multi-faceted), high (deep analysis needed)
5. Select and adapt research dimensions from the preset template for the identified question type. You may:
   - Remove dimensions that are not relevant to this specific query
   - Add new dimensions if the query has unique angles not covered by presets
   - Adjust priorities based on the query's focus
   - Mark each dimension's source as "preset" (from template) or "ai-generated" (new)

Available preset dimensions for each type:
${Object.entries(RESEARCH_ANGLE_PRESETS).map(([type, dims]) =>
  `  ${type}: ${dims.map(d => `${d.title}(${d.priority})`).join(', ')}`
).join('\n')}

Return the analysis as a structured object.`,
    schema: z.object({
      topic: z.string().describe('Core research topic'),
      questionType: z.string().describe(`Question type, one of: ${presetTypes}`),
      keyEntities: z.array(z.string()).describe('Key entities mentioned or implied'),
      scope: z.object({
        domains: z.array(z.string()).describe('Domains/fields involved'),
        timeRange: z.string().optional().describe('Time range if specified'),
      }),
      estimatedComplexity: z.enum(['low', 'medium', 'high']),
      recommendedDimensions: z.array(z.object({
        title: z.string(),
        priority: z.enum(['critical', 'important', 'nice-to-have']),
        description: z.string().describe('What this dimension should cover for THIS specific query'),
        source: z.enum(['preset', 'ai-generated']),
      })),
    }),
  });

  return res.object as QueryAnalysis;
}

// ─── Step 2: 用户确认维度 ──────────────────────────

export async function presentAndConfirm(
  analysis: QueryAnalysis,
  askQuestion: (q: string) => Promise<string>,
  interactive: boolean = true,
): Promise<RecommendedDimension[]> {
  const dims = analysis.recommendedDimensions;

  if (!interactive) {
    console.log(`Auto-confirmed ${dims.length} dimensions (non-interactive mode)`);
    return dims;
  }

  let confirmed = [...dims];

  while (true) {
    printDimensions(analysis, confirmed);
    const input = (await askQuestion('\n操作 (y确认/d删除/a新增/p交换/e编辑): ')).trim();

    if (!input || input === 'y') {
      console.log(`Confirmed ${confirmed.length} dimensions`);
      return confirmed;
    }

    confirmed = applyDimensionCommand(input, confirmed);
  }
}

function printDimensions(analysis: QueryAnalysis, dims: RecommendedDimension[]): void {
  console.log('\n═══════════════════════════════════════════════════');
  console.log(`📋 研究分析结果`);
  console.log('═══════════════════════════════════════════════════');
  console.log(`主题: ${analysis.topic}`);
  console.log(`类型: ${analysis.questionType} | 复杂度: ${analysis.estimatedComplexity}`);
  if (analysis.keyEntities.length > 0) {
    console.log(`关键实体: ${analysis.keyEntities.join(', ')}`);
  }
  console.log(`\n推荐研究维度 (${dims.length}个):`);
  dims.forEach((d, i) => {
    const icon = PRIORITY_ICON[d.priority] || '⚪';
    const tag = d.source === 'ai-generated' ? ' [AI]' : '';
    console.log(`  [${i + 1}] ${icon} ${d.title}${tag} — ${d.description}`);
  });
  console.log('\n操作: y确认 / d 1,3删除 / a 标题新增 / p 2,4交换优先级 / e 1 新标题编辑');
  console.log('═══════════════════════════════════════════════════');
}

function applyDimensionCommand(input: string, dims: RecommendedDimension[]): RecommendedDimension[] {
  const parts = input.split(/\s+/);
  const cmd = parts[0].toLowerCase();
  const result = [...dims];

  try {
    switch (cmd) {
      case 'd': { // 删除: d 1,3
        const indices = parseIndices(parts[1]);
        const toRemove = new Set(indices.map(i => i - 1));
        return result.filter((_, i) => !toRemove.has(i));
      }
      case 'a': { // 新增: a 安全性对比
        const title = parts.slice(1).join(' ');
        if (title) {
          result.push({ title, priority: 'important', description: `研究${title}相关内容`, source: 'ai-generated' });
          console.log(`  ✅ 新增维度: ${title}`);
        }
        return result;
      }
      case 'p': { // 交换优先级: p 2,4
        const indices = parseIndices(parts[1]);
        if (indices.length === 2) {
          const [a, b] = indices.map(i => i - 1);
          if (a >= 0 && a < result.length && b >= 0 && b < result.length) {
            const temp = result[a].priority;
            result[a] = { ...result[a], priority: result[b].priority };
            result[b] = { ...result[b], priority: temp };
            console.log(`  ✅ 交换优先级: [${a + 1}] ↔ [${b + 1}]`);
          }
        }
        return result;
      }
      case 'e': { // 编辑标题: e 1 新标题
        const idx = parseInt(parts[1], 10) - 1;
        const newTitle = parts.slice(2).join(' ');
        if (idx >= 0 && idx < result.length && newTitle) {
          result[idx] = { ...result[idx], title: newTitle };
          console.log(`  ✅ 编辑维度 [${idx + 1}]: ${newTitle}`);
        }
        return result;
      }
      default:
        console.log('  ⚠️ 未知指令，请重试');
        return result;
    }
  } catch {
    console.log('  ⚠️ 指令格式错误，请重试');
    return result;
  }
}

function parseIndices(s: string): number[] {
  if (!s) return [];
  return s.split(',').map(n => parseInt(n.trim(), 10)).filter(n => !isNaN(n));
}

// ─── Step 2.5: 反思审核 ──────────────────────────

export async function reviewDimensions(
  query: string,
  dimensions: RecommendedDimension[],
  userFeedback?: string,
): Promise<DimensionReview> {
  const res = await generateObject({
    model: o3MiniModel,
    system: `You are a senior research methodology reviewer. Your job is to critically evaluate a proposed research dimension plan and identify issues. Be thorough but not pedantic — only flag real problems, not minor nitpicks.

Review criteria:
1. gap: Are important angles missing? Consider: stakeholder perspectives, time dimensions, geographical scope, risk dimensions, ethical considerations
2. overlap: Are any dimensions highly overlapping in what they would research?
3. ambiguity: Are there unclear aspects of the user's needs that should be clarified before research?
4. missing-perspective: Is the plan only considering one viewpoint (e.g., only technical, ignoring business; only short-term, ignoring long-term)?

Rules:
- If the plan is solid, return verdict "approved" with empty arrays
- If there are issues, return verdict "needs-adjustment"
- Limit followUpQuestions to max 3, only the most critical ones
- Do NOT invent problems just to have something to say`,
    prompt: `Research topic: "${query}"
${userFeedback ? `User additional context: ${userFeedback}` : ''}

Proposed research dimensions:
${dimensions.map((d, i) => `  ${i + 1}. [${d.priority}] ${d.title} — ${d.description}`).join('\n')}

Please review this dimension plan critically.`,
    schema: z.object({
      verdict: z.enum(['approved', 'needs-adjustment']),
      issues: z.array(z.object({
        type: z.enum(['gap', 'overlap', 'ambiguity', 'missing-perspective']),
        description: z.string(),
        suggestion: z.string().optional(),
      })),
      suggestedAdditions: z.array(z.object({
        title: z.string(),
        reason: z.string(),
        priority: z.enum(['critical', 'important', 'nice-to-have']),
      })),
      followUpQuestions: z.array(z.object({
        question: z.string(),
        reason: z.string(),
        affectedDimensions: z.array(z.string()),
      })),
    }),
  });

  return res.object as DimensionReview;
}

export async function presentReviewAndHandle(
  review: DimensionReview,
  dimensions: RecommendedDimension[],
  askQuestion: (q: string) => Promise<string>,
  interactive: boolean = true,
): Promise<{ dimensions: RecommendedDimension[]; additionalFeedback: string }> {
  let result = [...dimensions];
  let additionalFeedback = '';

  if (review.verdict === 'approved') {
    console.log('\n✅ 维度审核通过 — 覆盖完整，维度独立，需求明确。');
    return { dimensions: result, additionalFeedback };
  }

  if (!interactive) {
    // 非交互模式：自动采纳建议新增
    for (const addition of review.suggestedAdditions) {
      result.push({
        title: addition.title,
        priority: addition.priority,
        description: addition.reason,
        source: 'ai-generated',
      });
    }
    console.log(`Auto-applied ${review.suggestedAdditions.length} reviewer suggestions`);
    return { dimensions: result, additionalFeedback };
  }

  // 展示审核结果
  console.log('\n═══════════════════════════════════════════════════');
  console.log('⚠️  维度审核发现以下问题：');
  console.log('═══════════════════════════════════════════════════');

  if (review.issues.length > 0) {
    console.log('\n问题:');
    review.issues.forEach(issue => {
      console.log(`  [${issue.type}] ${issue.description}`);
      if (issue.suggestion) console.log(`    建议: ${issue.suggestion}`);
    });
  }

  if (review.suggestedAdditions.length > 0) {
    console.log('\n建议新增:');
    review.suggestedAdditions.forEach(s => {
      console.log(`  ${PRIORITY_ICON[s.priority]} ${s.title} — ${s.reason}`);
    });
  }

  if (review.followUpQuestions.length > 0) {
    console.log('\n需要您确认的问题:');
    review.followUpQuestions.forEach((q, i) => {
      console.log(`  Q${i + 1}: ${q.question}`);
      console.log(`       (原因: ${q.reason})`);
    });
  }

  console.log('\n操作: y接受建议并继续 / a逐个回答追问 / i忽略审核建议');
  console.log('═══════════════════════════════════════════════════');

  const action = (await askQuestion('\n选择: ')).trim().toLowerCase();

  if (action === 'i') {
    console.log('已忽略审核建议，按原方案继续。');
    return { dimensions: result, additionalFeedback };
  }

  // 采纳建议新增
  for (const addition of review.suggestedAdditions) {
    result.push({
      title: addition.title,
      priority: addition.priority,
      description: addition.reason,
      source: 'ai-generated',
    });
  }
  if (review.suggestedAdditions.length > 0) {
    console.log(`已采纳 ${review.suggestedAdditions.length} 个新增维度`);
  }

  // 逐个回答追问
  if (action === 'a' && review.followUpQuestions.length > 0) {
    const answers: string[] = [];
    for (const q of review.followUpQuestions) {
      const answer = await askQuestion(`\n${q.question}\n(原因: ${q.reason})\n回答: `);
      answers.push(`Q: ${q.question}\nA: ${answer}`);
    }
    additionalFeedback = answers.join('\n');
  }

  return { dimensions: result, additionalFeedback };
}

// ─── Step 3: 计划细化 ──────────────────────────────

export async function generateResearchPlan(
  query: string,
  analysis: QueryAnalysis,
  confirmedDimensions: RecommendedDimension[],
  userBreadth: number,
  userDepth: number,
): Promise<ResearchPlan> {
  const totalBudget = userBreadth * userDepth;

  const res = await generateObject({
    model: o3MiniModel,
    system: systemPrompt(),
    prompt: `Given the confirmed research dimensions below, generate a detailed research execution plan.

Research query: "${query}"
User's total research budget: breadth=${userBreadth}, depth=${userDepth} (approximately ${totalBudget} search operations)

Confirmed dimensions:
${confirmedDimensions.map((d, i) => `  ${i + 1}. [${d.priority}] ${d.title} — ${d.description}`).join('\n')}

For each dimension, generate:
1. Sub-topics (2-4 per dimension)
2. Initial search queries for each sub-topic (1-2 specific queries)
3. Suggested breadth (how many queries to generate in recursive search) and depth (how many levels to recurse)

Resource allocation guidelines:
- critical dimensions: allocate ~50% of total budget
- important dimensions: allocate ~35% of total budget
- nice-to-have dimensions: allocate ~15% of total budget
- Higher depth (2-3) for complex topics, lower (1) for straightforward ones
- Breadth should be 2-4 for most sub-topics

Also determine execution order: critical dimensions first, then important, then nice-to-have.`,
    schema: z.object({
      dimensions: z.array(z.object({
        id: z.string().describe('Dimension ID like d1, d2...'),
        title: z.string(),
        priority: z.enum(['critical', 'important', 'nice-to-have']),
        estimatedWeight: z.number().min(0).max(1).describe('Weight in final report, 0-1, all should sum to ~1'),
        subTopics: z.array(z.object({
          title: z.string(),
          initialQueries: z.array(z.string()).describe('Specific search queries to start with'),
          suggestedBreadth: z.number().min(1).max(6),
          suggestedDepth: z.number().min(1).max(3),
        })),
      })),
      totalEstimatedQueries: z.number().describe('Total estimated search operations'),
      executionOrder: z.array(z.string()).describe('Dimension IDs in execution order'),
    }),
  });

  return {
    analysis,
    dimensions: res.object.dimensions as ResearchDimension[],
    totalEstimatedQueries: res.object.totalEstimatedQueries,
    executionOrder: res.object.executionOrder,
  };
}

// ─── Step 4: 报告大纲 ──────────────────────────────

export async function generateReportOutline(plan: ResearchPlan): Promise<ReportOutline> {
  const { analysis } = plan;
  const entityContext = analysis.keyEntities.length > 0
    ? `\nKey entities: ${analysis.keyEntities.join(', ')}`
    : '';
  const scopeContext = analysis.scope.domains.length > 0
    ? `\nDomains: ${analysis.scope.domains.join(', ')}${analysis.scope.timeRange ? `, time range: ${analysis.scope.timeRange}` : ''}`
    : '';

  const res = await generateObject({
    model: o3MiniModel,
    system: systemPrompt(),
    prompt: `Generate a report outline (chapter structure) based on the research plan below.

Research topic: "${analysis.topic}"
Question type: ${analysis.questionType}
Complexity: ${analysis.estimatedComplexity}${entityContext}${scopeContext}

Research dimensions:
${plan.dimensions.map(d => `  [${d.priority}] ${d.title} (weight: ${d.estimatedWeight})
    Sub-topics: ${d.subTopics.map(s => s.title).join(', ')}`).join('\n')}

Requirements:
1. Start with an "intro" chapter: research overview, background, methodology
2. Create one "body" chapter per research dimension, linking it to the dimension ID
3. Body chapter titles should be reader-friendly (may differ from dimension titles)
4. Add optional sub-sections within body chapters (2-4 per chapter)
5. End with a "conclusion" chapter: synthesis, recommendations, key takeaways
6. Add an "appendix" chapter: references, terminology, data sources
7. Each chapter needs an estimatedWeight (0-1) indicating its proportion of the total report

Return the outline as a structured object.`,
    schema: z.object({
      title: z.string().describe('Full report title'),
      summary: z.string().describe('1-2 sentence research overview'),
      chapters: z.array(z.object({
        id: z.string().describe('Chapter ID like ch0, ch1...'),
        title: z.string(),
        description: z.string().describe('What this chapter covers'),
        estimatedWeight: z.number().min(0).max(1),
        dimensionId: z.string().optional().describe('Linked dimension ID for body chapters'),
        subSections: z.array(z.string()).optional(),
        chapterType: z.enum(['intro', 'body', 'conclusion', 'appendix']),
      })),
    }),
  });

  return res.object as ReportOutline;
}

export async function presentOutlineAndConfirm(
  outline: ReportOutline,
  askQuestion: (q: string) => Promise<string>,
  interactive: boolean = true,
): Promise<ReportOutline> {
  if (!interactive) {
    console.log('Auto-confirmed report outline (non-interactive mode)');
    return outline;
  }

  let confirmed = { ...outline, chapters: [...outline.chapters] };

  while (true) {
    printOutline(confirmed);
    const input = (await askQuestion('\n操作 (y确认/e编辑/a新增/d删除/m移动顺序): ')).trim();

    if (!input || input === 'y') {
      console.log('Report outline confirmed.');
      return confirmed;
    }

    confirmed = applyOutlineCommand(input, confirmed);
  }
}

function printOutline(outline: ReportOutline): void {
  console.log('\n═══════════════════════════════════════════════════');
  console.log('📑 报告大纲预览');
  console.log('═══════════════════════════════════════════════════');
  console.log(`标题: ${outline.title}`);
  console.log(`概述: ${outline.summary}`);
  console.log('');

  outline.chapters.forEach((ch, i) => {
    const typeLabel: Record<string, string> = {
      intro: '引言', body: '', conclusion: '总结', appendix: '附录',
    };
    const tag = typeLabel[ch.chapterType] ? ` [${typeLabel[ch.chapterType]}]` : '';
    const weight = ch.chapterType === 'body' ? ` [~${Math.round(ch.estimatedWeight * 100)}%]` : '';
    console.log(`  ${i}. ${ch.title}${tag}${weight}`);
    if (ch.subSections) {
      ch.subSections.forEach((sub, j) => {
        console.log(`     ${i}.${j + 1} ${sub}`);
      });
    }
  });

  console.log('\n操作: y确认 / e 0 新标题编辑 / a 章节标题新增 / d 5删除 / m 2,4移动顺序');
  console.log('═══════════════════════════════════════════════════');
}

function applyOutlineCommand(input: string, outline: ReportOutline): ReportOutline {
  const parts = input.split(/\s+/);
  const cmd = parts[0].toLowerCase();
  const result = { ...outline, chapters: [...outline.chapters] };

  try {
    switch (cmd) {
      case 'e': { // 编辑: e 0 新标题
        const idx = parseInt(parts[1], 10);
        const newTitle = parts.slice(2).join(' ');
        if (idx >= 0 && idx < result.chapters.length && newTitle) {
          result.chapters[idx] = { ...result.chapters[idx], title: newTitle };
          console.log(`  ✅ 编辑章节 [${idx}]: ${newTitle}`);
        }
        return result;
      }
      case 'a': { // 新增: a 章节标题
        const title = parts.slice(1).join(' ');
        if (title) {
          const newCh = {
            id: `ch${result.chapters.length}`,
            title,
            description: `覆盖${title}相关内容`,
            estimatedWeight: 0.1,
            chapterType: 'body' as const,
          };
          // 在 conclusion 之前插入
          const conclusionIdx = result.chapters.findIndex(c => c.chapterType === 'conclusion');
          if (conclusionIdx >= 0) {
            result.chapters.splice(conclusionIdx, 0, newCh);
          } else {
            result.chapters.push(newCh);
          }
          console.log(`  ✅ 新增章节: ${title}`);
        }
        return result;
      }
      case 'd': { // 删除: d 5
        const idx = parseInt(parts[1], 10);
        if (idx >= 0 && idx < result.chapters.length) {
          const removed = result.chapters.splice(idx, 1);
          console.log(`  ✅ 删除章节: ${removed[0]?.title}`);
        }
        return result;
      }
      case 'm': { // 移动: m 2,4
        const indices = parseIndices(parts[1]);
        if (indices.length === 2) {
          const [a, b] = indices;
          if (a >= 0 && a < result.chapters.length && b >= 0 && b < result.chapters.length) {
            const temp = result.chapters[a];
            result.chapters[a] = result.chapters[b];
            result.chapters[b] = temp;
            console.log(`  ✅ 交换章节: [${a}] ↔ [${b}]`);
          }
        }
        return result;
      }
      default:
        console.log('  ⚠️ 未知指令，请重试');
        return result;
    }
  } catch {
    console.log('  ⚠️ 指令格式错误，请重试');
    return result;
  }
}

