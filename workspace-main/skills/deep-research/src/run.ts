import * as fs from 'fs/promises';
import * as readline from 'readline';
import { parseArgs } from 'util';
import * as path from 'path';

import { initConcurrency } from './concurrency';
import { initCache, cleanExpiredCache, getCacheStats } from './search-cache';
import {
  deepResearch,
  deepResearchByPlan,
  writeFinalReport,
  writeFinalReportWithOutline,
} from './deep-research';
import { generateFeedback } from './feedback';
import {
  analyzeQuery,
  presentAndConfirm,
  reviewDimensions,
  presentReviewAndHandle,
  generateResearchPlan,
  generateReportOutline,
  presentOutlineAndConfirm,
} from './research-plan';
import {
  createWorkspace,
  saveAnalysis,
  saveDimensions,
  savePlan,
  saveOutline,
  saveLearnings,
  saveSources,
  saveReport,
  saveExpansion,
} from './research-workspace';
import { collectAllSources } from './source-collector';
import { expandQuery } from './prompt-expansion';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function askQuestion(query: string): Promise<string> {
  return new Promise(resolve => {
    rl.question(query, answer => {
      resolve(answer);
    });
  });
}

async function run() {
  // 解析命令行参数
  const { values, positionals } = parseArgs({
    options: {
      breadth: { type: 'string', default: '12' },
      depth: { type: 'string', default: '3' },
      output: { type: 'string', default: 'report.md' },
      'no-interactive': { type: 'boolean', default: false },
      'no-plan': { type: 'boolean', default: false },
      concurrency: { type: 'string', default: '3' },
      'no-cache': { type: 'boolean', default: false },
      'cache-ttl': { type: 'string', default: '86400' },
      // v1.2.0: 多源素材
      urls: { type: 'string', default: '' },
      files: { type: 'string', default: '' },
      'no-obsidian': { type: 'boolean', default: false },
      'obsidian-vault': { type: 'string', default: '' },
      // v1.3.0: 提示词扩写
      direction: { type: 'string', default: 'auto' },
      'no-expand': { type: 'boolean', default: false },
    },
    allowPositionals: true,
  });

  let initialQuery = positionals[0];
  let breadth = parseInt(values.breadth as string, 10) || 4;
  let depth = parseInt(values.depth as string, 10) || 2;
  const outputPath = values.output as string;
  const interactive = !values['no-interactive'];
  const usePlan = !values['no-plan'];
  const concurrency = parseInt(values.concurrency as string, 10) || 3;
  const cacheEnabled = !values['no-cache'];
  const cacheTtl = parseInt(values['cache-ttl'] as string, 10) || 86400;

  // v1.2.0: 多源素材参数
  const presetUrls = (values.urls as string)
    ? (values.urls as string).split(',').map(u => u.trim()).filter(Boolean)
    : [];
  const presetFiles = (values.files as string)
    ? (values.files as string).split(',').map(f => f.trim()).filter(Boolean)
    : [];
  const obsidianEnabled = !values['no-obsidian'];
  const obsidianVault = values['obsidian-vault'] as string || undefined;

  // v1.3.0: 提示词扩写参数
  const directionParam = values.direction as 'auto' | 'radar' | 'deepdive' | 'general';
  const useExpand = !values['no-expand'];

  // 初始化并发控制和缓存
  initConcurrency(concurrency);
  initCache({ enabled: cacheEnabled, ttlSeconds: cacheTtl });
  await cleanExpiredCache();

  // 如果没有提供查询参数，提示用户输入
  if (!initialQuery) {
    initialQuery = await askQuestion('What would you like to research? ');
  }

  let combinedQuery = initialQuery;
  let additionalFeedback = '';

  // 交互模式：需求澄清
  if (interactive) {
    if (!values.breadth) {
      breadth = parseInt(
        await askQuestion('Enter research breadth (recommended 2-10, default 4): '),
        10,
      ) || 4;
    }
    if (!values.depth) {
      depth = parseInt(
        await askQuestion('Enter research depth (recommended 1-5, default 2): '),
        10,
      ) || 2;
    }

    console.log('Creating research plan...');

    const followUpQuestions = await generateFeedback({ query: initialQuery });

    console.log(
      '\nTo better understand your research needs, please answer these follow-up questions:',
    );

    const answers: string[] = [];
    for (const question of followUpQuestions) {
      const answer = await askQuestion(`\n${question}\nYour answer: `);
      answers.push(answer);
    }

    combinedQuery = `
Initial Query: ${initialQuery}
Follow-up Questions and Answers:
${followUpQuestions.map((q, i) => `Q: ${q}\nA: ${answers[i]}`).join('\n')}
`;
  } else {
    console.log(`Starting non-interactive research...`);
    console.log(`Query: ${initialQuery}`);
    console.log(`Breadth: ${breadth}, Depth: ${depth}`);
  }

  let report: string;
  let planFailed = false;

  if (usePlan) {
    try {
      // ─── 计划驱动流程 ─────────────────────
      const timings: Record<string, number> = {};

    // Step 0: 创建工作目录
    let t0 = Date.now();
    const ws = await createWorkspace(initialQuery);
    timings['工作目录'] = Date.now() - t0;

    // ─── Step 0.5: 提示词扩写 ───
    let isExpanded = false;
    if (useExpand) {
      t0 = Date.now();
      console.log('\n━━━ Step 0.5: 提示词扩写 ━━━');
      const expansion = await expandQuery(combinedQuery, {
        directionHint: directionParam,
        interactive,
        askQuestion,
      });

      if (expansion.direction !== 'general') {
        combinedQuery = expansion.expandedQuery;
        await saveExpansion(ws, expansion);
        isExpanded = true;
      }
      timings['提示词扩写'] = Date.now() - t0;
    }

    t0 = Date.now();
    console.log('\n━━━ Step 1: 问题分析 ━━━');
    const analysis = await analyzeQuery(combinedQuery, isExpanded);
    await saveAnalysis(ws, analysis);
    timings['问题分析'] = Date.now() - t0;
    console.log(`主题: ${analysis.topic}`);
    console.log(`类型: ${analysis.questionType} | 复杂度: ${analysis.estimatedComplexity}`);
    console.log(`推荐维度: ${analysis.recommendedDimensions.length} 个`);

    t0 = Date.now();
    console.log('\n━━━ Step 2: 维度确认 ━━━');
    let confirmedDims = await presentAndConfirm(analysis, askQuestion, interactive);
    await saveDimensions(ws, confirmedDims);
    timings['维度确认'] = Date.now() - t0;

    t0 = Date.now();
    console.log('\n━━━ Step 2.5: 反思审核 ━━━');
    const review = await reviewDimensions(combinedQuery, confirmedDims, combinedQuery);
    const reviewResult = await presentReviewAndHandle(review, confirmedDims, askQuestion, interactive);
    timings['反思审核'] = Date.now() - t0;
    confirmedDims = reviewResult.dimensions;
    if (reviewResult.additionalFeedback) {
      additionalFeedback = reviewResult.additionalFeedback;
      combinedQuery += `\n\nAdditional clarifications:\n${additionalFeedback}`;
    }

    t0 = Date.now();
    console.log('\n━━━ Step 3: 执行计划细化 ━━━');
    const plan = await generateResearchPlan(combinedQuery, analysis, confirmedDims, breadth, depth);
    await savePlan(ws, plan);
    timings['计划细化'] = Date.now() - t0;
    console.log(`维度数: ${plan.dimensions.length}`);
    plan.dimensions.forEach(d => {
      console.log(`  [${d.priority}] ${d.title} (${d.subTopics.length} sub-topics, weight: ${d.estimatedWeight})`);
    });
    console.log(`预估搜索量: ${plan.totalEstimatedQueries}`);

    t0 = Date.now();
    console.log('\n━━━ Step 4: 报告大纲生成 ━━━');
    let outline = await generateReportOutline(plan);
    outline = await presentOutlineAndConfirm(outline, askQuestion, interactive);
    await saveOutline(ws, outline);
    timings['大纲生成'] = Date.now() - t0;

    // ─── Step 4.5: 素材收集（交互 + Obsidian 自动搜索）───
    t0 = Date.now();
    let collectedUrls = [...presetUrls];
    let collectedFiles = [...presetFiles];

    // 交互模式：询问用户是否补充素材
    if (interactive) {
      console.log('\n═══════════════════════════════════════════════════');
      console.log('  是否提供补充素材？');
      if (obsidianEnabled) {
        console.log('  （Obsidian 笔记将自动用搜索关键词搜索）');
      }
      console.log('');
      console.log('  u URL1,URL2    — 添加参考网页');
      console.log('  f 文件路径      — 添加本地文件 (md/pdf/docx/html)');
      console.log('  y              — 确认，开始研究');
      console.log('  n              — 跳过素材收集');
      console.log('═══════════════════════════════════════════════════');

      let collecting = true;
      while (collecting) {
        const answer = (await askQuestion('\n  操作: ')).trim();
        if (!answer || answer === 'y') {
          collecting = false;
        } else if (answer === 'n') {
          collecting = false;
          // 用户选择跳过，禁用所有素材收集
          collectedUrls = [];
          collectedFiles = [];
        } else if (answer.startsWith('u ')) {
          const newUrls = answer.slice(2).split(',').map(u => u.trim()).filter(Boolean);
          collectedUrls.push(...newUrls);
          console.log(`  ✓ 已添加 ${newUrls.length} 个 URL`);
        } else if (answer.startsWith('f ')) {
          const newFiles = answer.slice(2).split(',').map(f => f.trim()).filter(Boolean);
          collectedFiles.push(...newFiles);
          console.log(`  ✓ 已添加 ${newFiles.length} 个文件`);
        } else {
          console.log('  无效指令，请输入 u/f/y/n');
        }
      }
    }

    // 执行素材收集
    const hasMaterials = collectedUrls.length > 0 || collectedFiles.length > 0 || obsidianEnabled;
    let preloadedLearnings: string[] = [];
    let preloadedSourceRefs: { url: string; title: string }[] = [];

    if (hasMaterials) {
      const collectionResult = await collectAllSources({
        query: combinedQuery,
        urls: collectedUrls,
        files: collectedFiles,
        plan,
        workspace: ws,
        obsidianVault,
        obsidianEnabled,
      });

      preloadedLearnings = collectionResult.preloadedLearnings;
      preloadedSourceRefs = collectionResult.preloadedSourceRefs;

      console.log(`\n  素材收集完成: ${collectionResult.sources.length} 个来源, ${preloadedLearnings.length} 条 learnings`);
    } else {
      console.log('\n  跳过素材收集');
    }
    timings['素材收集'] = Date.now() - t0;

    // ─── Phase 5: 执行研究 ───
    t0 = Date.now();
    console.log('\n━━━ Phase 5: 执行研究 ━━━');
    console.log('Researching your topic by plan...');
    const researchResult = await deepResearchByPlan(
      combinedQuery,
      plan,
      preloadedLearnings.length > 0 ? preloadedLearnings : undefined,
      preloadedSourceRefs.length > 0 ? preloadedSourceRefs : undefined,
    );
    timings['研究执行'] = Date.now() - t0;

    const { learnings, visitedSources, learningsByDimension } = researchResult;
    await saveLearnings(ws, learnings, learningsByDimension);
    await saveSources(ws, visitedSources);

    console.log(`\nLearnings: ${learnings.length}`);
    console.log(`Sources: ${visitedSources.length}`);

    // ─── Phase 6: 生成报告 ───
    t0 = Date.now();
    console.log('\n━━━ Phase 6: 生成报告 ━━━');
    console.log('Writing final report with outline...');
    report = await writeFinalReportWithOutline({ outline, learnings, visitedSources, analysis, plan, learningsByDimension });
    timings['报告生成'] = Date.now() - t0;

    // 保存报告到归档目录
    const wsReportPath = await saveReport(ws, report);
    console.log(`[归档] 报告已保存: ${wsReportPath}`);

    // 打印计时和缓存统计
    const timingStr = Object.entries(timings)
      .map(([k, v]) => `${k}: ${(v / 1000).toFixed(1)}s`)
      .join(' | ');
    console.log(`\n[计时] ${timingStr}`);
    const { hits, misses, writes } = getCacheStats();
    const total = hits + misses;
    const hitRate = total > 0 ? Math.round((hits / total) * 100) : 0;
    console.log(`[缓存] 命中: ${hits} | 未命中: ${misses} | 写入: ${writes} | 命中率: ${hitRate}%`);
      console.log(`[归档] 研究目录: research/${ws.topicName}/`);
    } catch (err: any) {
      planFailed = true;
      console.warn(`\n⚠️  Plan mode failed: ${err.name || 'error'}. Falling back to legacy mode.`);
    }
  }

  if (!usePlan || planFailed) {
    // ─── 原有流程（fallback）────────────────
    console.log('\nResearching your topic (legacy mode)...');

    let { learnings, visitedSources } = await deepResearch({
      query: combinedQuery,
      breadth,
      depth,
    });

    console.log(`\nLearnings: ${learnings.length}`);
    console.log(`Sources: ${visitedSources.length}`);

    if (learnings.length === 0) {
      console.warn('No learnings collected, search phase may have entirely failed');
    }

    console.log('Writing final report...');
    try {
      report = await writeFinalReport({
        prompt: combinedQuery,
        learnings,
        visitedSources,
      });
      console.log(`Report generated: ${report.length} chars`);
    } catch (reportErr: any) {
      console.error(`Report generation failed: ${reportErr.name || 'error'}`, reportErr.message || '');
      report = `# Research Report\n\n## Learnings\n\n${learnings.map((l: string, i: number) => `${i + 1}. ${l}`).join('\n\n')}\n\n*Auto-generated report failed, showing raw learnings.*`;
    }
  }

  // ─── 保存报告 ─────────────────────────
  let finalOutputPath = outputPath;
  if (outputPath === 'report.md') {
    const titleMatch = report.match(/^#\s+(.+)$/m);
    let filename = 'report.md';
    if (titleMatch) {
      const title = titleMatch[1].trim();
      filename = title.replace(/[<>:"/\\|?*]/g, '_').replace(/\s+/g, '-') + '.md';
    }
    finalOutputPath = path.join(__dirname, '..', 'output', filename);
    await fs.mkdir(path.dirname(finalOutputPath), { recursive: true });
  }

  await fs.writeFile(finalOutputPath, report, 'utf-8');
  console.log(`\n\nFinal Report:\n\n${report}`);
  console.log(`\nReport has been saved to ${finalOutputPath}`);
  rl.close();
}

run().catch(console.error);
