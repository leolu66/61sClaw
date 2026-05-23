import * as fs from 'fs/promises';
import * as readline from 'readline';
import { parseArgs } from 'util';
import * as path from 'path';

import { initConcurrency } from './concurrency';
import { initCache, cleanExpiredCache } from './search-cache';
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

  if (usePlan) {
    // ─── 计划驱动流程 ─────────────────────
    console.log('\n━━━ Step 1: 问题分析 ━━━');
    const analysis = await analyzeQuery(combinedQuery);
    console.log(`主题: ${analysis.topic}`);
    console.log(`类型: ${analysis.questionType} | 复杂度: ${analysis.estimatedComplexity}`);
    console.log(`推荐维度: ${analysis.recommendedDimensions.length} 个`);

    console.log('\n━━━ Step 2: 维度确认 ━━━');
    let confirmedDims = await presentAndConfirm(analysis, askQuestion, interactive);

    console.log('\n━━━ Step 2.5: 反思审核 ━━━');
    const review = await reviewDimensions(combinedQuery, confirmedDims, combinedQuery);
    const reviewResult = await presentReviewAndHandle(review, confirmedDims, askQuestion, interactive);
    confirmedDims = reviewResult.dimensions;
    if (reviewResult.additionalFeedback) {
      additionalFeedback = reviewResult.additionalFeedback;
      combinedQuery += `\n\nAdditional clarifications:\n${additionalFeedback}`;
    }

    console.log('\n━━━ Step 3: 执行计划细化 ━━━');
    const plan = await generateResearchPlan(combinedQuery, confirmedDims, breadth, depth);
    console.log(`维度数: ${plan.dimensions.length}`);
    plan.dimensions.forEach(d => {
      console.log(`  [${d.priority}] ${d.title} (${d.subTopics.length} sub-topics, weight: ${d.estimatedWeight})`);
    });
    console.log(`预估搜索量: ${plan.totalEstimatedQueries}`);

    console.log('\n━━━ Step 4: 报告大纲生成 ━━━');
    let outline = await generateReportOutline(plan);
    outline = await presentOutlineAndConfirm(outline, askQuestion, interactive);

    console.log('\n━━━ Phase 5: 执行研究 ━━━');
    console.log('Researching your topic by plan...');
    const { learnings, visitedSources } = await deepResearchByPlan(combinedQuery, plan);

    console.log(`\nLearnings: ${learnings.length}`);
    console.log(`Sources: ${visitedSources.length}`);

    console.log('\n━━━ Phase 6: 生成报告 ━━━');
    console.log('Writing final report with outline...');
    report = await writeFinalReportWithOutline({ outline, learnings, visitedSources });
  } else {
    // ─── 原有流程（fallback）────────────────
    console.log('\nResearching your topic (legacy mode)...');

    const { learnings, visitedSources } = await deepResearch({
      query: combinedQuery,
      breadth,
      depth,
    });

    console.log(`\nLearnings: ${learnings.length}`);
    console.log(`Sources: ${visitedSources.length}`);
    console.log('Writing final report...');

    report = await writeFinalReport({
      prompt: combinedQuery,
      learnings,
      visitedSources,
    });
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
