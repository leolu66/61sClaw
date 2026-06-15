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
  loadWorkspaceFromDir,
  findLatestWorkspace,
  loadExpansion,
  loadAnalysis,
  loadDimensions,
  loadPlan,
  loadOutline,
  loadLearnings,
  loadSources,
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
import { getSearchMonitorStats } from './search-providers';

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
      // v1.4.0: 断点续传
      resume: { type: 'boolean', default: false },
      'from-workspace': { type: 'string', default: '' },
      // 模型配置（覆盖 DEEP_RESEARCH_MODEL 环境变量）
      model: { type: 'string', default: '' },
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
  const customModel = values.model as string;
  if (customModel) {
    process.env.DEEP_RESEARCH_MODEL = customModel;
  }

  // v1.4.0: 断点续传参数
  const isResume = values.resume as boolean;
  const fromWorkspacePath = values['from-workspace'] as string;

  // 初始化并发控制和缓存
  initConcurrency(concurrency);
  initCache({ enabled: cacheEnabled, ttlSeconds: cacheTtl });
  await cleanExpiredCache();

  // 如果没有提供查询参数，提示用户输入（resume/from-workspace 时不强制）
  if (!initialQuery && !isResume && !fromWorkspacePath) {
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

  let report: string = '';
  let planFailed = false;

  if (usePlan) {
    // ─── 计划驱动流程（v1.4.0: 逐步骤错误处理 + 断点续传）───
    const timings: Record<string, number> = {};
    let ws!: import('./research-workspace').ResearchWorkspace;
    let isExpanded = false;
    let analysis: Awaited<ReturnType<typeof analyzeQuery>> | null = null;
    let confirmedDims: Awaited<ReturnType<typeof presentAndConfirm>> | null = null;
    let plan: Awaited<ReturnType<typeof generateResearchPlan>> | null = null;
    let outline: Awaited<ReturnType<typeof generateReportOutline>> | null = null;
    let researchLearnings: string[] | null = null;
    let researchSources: import('./deep-research').Source[] | null = null;
    let learningsByDimension: Map<string, string[]> | undefined;
    let isResuming = false;
    let t0: number;

    // ─── 解析工作目录（resume / from-workspace / 新建）───
    if (isResume || fromWorkspacePath) {
      let wsDir = fromWorkspacePath;
      if (!wsDir) {
        const latest = await findLatestWorkspace();
        if (!latest) {
          console.warn('⚠️  未找到已有工作目录，将创建新的');
        } else {
          wsDir = latest;
        }
      }
      if (wsDir) {
        ws = await loadWorkspaceFromDir(wsDir);
        isResuming = true;
        console.log(`\n📂 恢复研究: research/${ws.topicName}/`);

        // 加载已有产物
        const [exp, ana, dims, pln, out, lrn, src] = await Promise.all([
          loadExpansion(ws), loadAnalysis(ws), loadDimensions(ws),
          loadPlan(ws), loadOutline(ws), loadLearnings(ws), loadSources(ws),
        ]);
        if (exp && exp.direction !== 'general') {
          combinedQuery = exp.expandedQuery;
          isExpanded = true;
          console.log('  ✓ 已加载: 提示词扩写');
        }
        if (ana) { analysis = ana; console.log('  ✓ 已加载: 问题分析'); }
        if (dims) { confirmedDims = dims; console.log('  ✓ 已加载: 研究维度'); }
        if (pln) { plan = pln; console.log('  ✓ 已加载: 执行计划'); }
        if (out) { outline = out; console.log('  ✓ 已加载: 报告大纲'); }
        if (lrn) {
          researchLearnings = lrn.all;
          if (lrn.byDimension) {
            learningsByDimension = new Map(Object.entries(lrn.byDimension));
          }
          console.log(`  ✓ 已加载: ${lrn.all.length} 条 learnings`);
        }
        if (src) { researchSources = src; console.log(`  ✓ 已加载: ${src.length} 个来源`); }
      }
    }

    if (!isResuming) {
      try {
        ws = await createWorkspace(initialQuery || 'research');
      } catch (err: any) {
        console.warn(`⚠️  创建工作目录失败: ${err.message}. Falling back to legacy mode.`);
        planFailed = true;
      }
    }

    // ─── Step 1: 提示词扩写 ───
    if (!planFailed && useExpand && !isExpanded) {
      t0 = Date.now();
      console.log('\n━━━ Step 1: 提示词扩写 ━━━');
      try {
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
      } catch (err: any) {
        console.warn(`⚠️  提示词扩写失败: ${err.message}. 使用原始 query 继续.`);
        timings['提示词扩写'] = Date.now() - t0;
      }
    }

    // ─── Step 2: 问题分析 ───
    if (!planFailed && !analysis) {
      t0 = Date.now();
      console.log('\n━━━ Step 2: 问题分析 ━━━');
      try {
        analysis = await analyzeQuery(combinedQuery, isExpanded);
        await saveAnalysis(ws, analysis);
        timings['问题分析'] = Date.now() - t0;
        console.log(`主题: ${analysis.topic}`);
        console.log(`类型: ${analysis.questionType} | 复杂度: ${analysis.estimatedComplexity}`);
        console.log(`推荐维度: ${analysis.recommendedDimensions.length} 个`);
      } catch (err: any) {
        console.error(`❌ 问题分析失败: ${err.message}`);
        planFailed = true;
      }
    }

    // ─── Step 3: 维度确认 ───
    if (!planFailed && analysis && !confirmedDims) {
      t0 = Date.now();
      console.log('\n━━━ Step 3: 维度确认 ━━━');
      try {
        confirmedDims = await presentAndConfirm(analysis, askQuestion, interactive);
        await saveDimensions(ws, confirmedDims);
        timings['维度确认'] = Date.now() - t0;
      } catch (err: any) {
        console.error(`❌ 维度确认失败: ${err.message}`);
        planFailed = true;
      }
    }

    // ─── Step 4: 反思审核（非关键，失败则跳过）───
    if (!planFailed && confirmedDims) {
      t0 = Date.now();
      console.log('\n━━━ Step 4: 反思审核 ━━━');
      try {
        const review = await reviewDimensions(combinedQuery, confirmedDims, combinedQuery);
        const reviewResult = await presentReviewAndHandle(review, confirmedDims, askQuestion, interactive);
        timings['反思审核'] = Date.now() - t0;
        confirmedDims = reviewResult.dimensions;
        if (reviewResult.additionalFeedback) {
          additionalFeedback = reviewResult.additionalFeedback;
          combinedQuery += `\n\nAdditional clarifications:\n${additionalFeedback}`;
        }
      } catch (err: any) {
        console.warn(`⚠️  反思审核失败: ${err.message}. 跳过审核继续.`);
        timings['反思审核'] = Date.now() - t0;
      }
    }

    // ─── Step 5: 执行计划细化 ───
    if (!planFailed && analysis && confirmedDims && !plan) {
      t0 = Date.now();
      console.log('\n━━━ Step 5: 执行计划细化 ━━━');
      try {
        plan = await generateResearchPlan(combinedQuery, analysis, confirmedDims, breadth, depth);
        await savePlan(ws, plan);
        timings['计划细化'] = Date.now() - t0;
        console.log(`维度数: ${plan.dimensions.length}`);
        plan.dimensions.forEach(d => {
          console.log(`  [${d.priority}] ${d.title} (${d.subTopics.length} sub-topics, weight: ${d.estimatedWeight})`);
        });
        console.log(`预估搜索量: ${plan.totalEstimatedQueries}`);
      } catch (err: any) {
        console.error(`❌ 计划细化失败: ${err.message}`);
        planFailed = true;
      }
    }

    // ─── Step 6: 报告大纲生成 ───
    if (!planFailed && plan && !outline) {
      t0 = Date.now();
      console.log('\n━━━ Step 6: 报告大纲生成 ━━━');
      try {
        outline = await generateReportOutline(plan);
        outline = await presentOutlineAndConfirm(outline, askQuestion, interactive);
        await saveOutline(ws, outline);
        timings['大纲生成'] = Date.now() - t0;
      } catch (err: any) {
        console.error(`❌ 大纲生成失败: ${err.message}`);
        planFailed = true;
      }
    }

    // ─── Step 7: 素材收集（非关键，失败则跳过）───
    let preloadedLearnings: string[] = [];
    let preloadedSourceRefs: { url: string; title: string }[] = [];

    if (!planFailed && plan && !researchLearnings) {
      t0 = Date.now();
      console.log('\n━━━ Step 7: 素材收集 ━━━');
      try {
        let collectedUrls = [...presetUrls];
        let collectedFiles = [...presetFiles];

        // 交互模式且非 resume：询问用户是否补充素材
        if (interactive && !isResuming) {
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

        const hasMaterials = collectedUrls.length > 0 || collectedFiles.length > 0 || obsidianEnabled;
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
          console.log('  跳过素材收集');
        }
        timings['素材收集'] = Date.now() - t0;
      } catch (err: any) {
        console.warn(`⚠️  素材收集失败: ${err.message}. 跳过素材收集继续.`);
        timings['素材收集'] = Date.now() - t0;
      }
    } else if (isResuming && researchLearnings) {
      console.log('\n━━━ Step 7: 素材收集 [已跳过 - resume 已有研究结果] ━━━');
    }

    // ─── Step 8: 执行研究 ───
    if (!planFailed && plan && outline && !researchLearnings) {
      t0 = Date.now();
      console.log('\n━━━ Step 8: 执行研究 ━━━');
      try {
        const researchResult = await deepResearchByPlan(
          combinedQuery,
          plan,
          preloadedLearnings.length > 0 ? preloadedLearnings : undefined,
          preloadedSourceRefs.length > 0 ? preloadedSourceRefs : undefined,
        );
        timings['研究执行'] = Date.now() - t0;

        researchLearnings = researchResult.learnings;
        researchSources = researchResult.visitedSources;
        learningsByDimension = researchResult.learningsByDimension;
        await saveLearnings(ws, researchLearnings, learningsByDimension);
        await saveSources(ws, researchSources);

        console.log(`\nLearnings: ${researchLearnings.length}`);
        console.log(`Sources: ${researchSources.length}`);
      } catch (err: any) {
        console.error(`❌ 研究执行失败: ${err.message}`);
        planFailed = true;
      }
    }

    // ─── Step 9: 生成报告 ───
    if (!planFailed && outline && researchLearnings && researchSources && !report) {
      t0 = Date.now();
      console.log('\n━━━ Step 9: 生成报告 ━━━');
      try {
        report = await writeFinalReportWithOutline({
          outline, learnings: researchLearnings, visitedSources: researchSources,
          analysis: analysis ?? undefined, plan: plan ?? undefined, learningsByDimension,
        });
        timings['报告生成'] = Date.now() - t0;

        const wsReportPath = await saveReport(ws, report);
        console.log(`[归档] 报告已保存: ${wsReportPath}`);
      } catch (err: any) {
        console.error(`❌ 报告生成失败: ${err.message}`);
        planFailed = true;
      }
    }

    // 打印计时和缓存统计
    if (!planFailed && Object.keys(timings).length > 0) {
      const timingStr = Object.entries(timings)
        .map(([k, v]) => `${k}: ${(v / 1000).toFixed(1)}s`)
        .join(' | ');
      console.log(`\n[计时] ${timingStr}`);
      const { hits, misses, writes } = getCacheStats();
      const total = hits + misses;
      const hitRate = total > 0 ? Math.round((hits / total) * 100) : 0;
      console.log(`[缓存] 命中: ${hits} | 未命中: ${misses} | 写入: ${writes} | 命中率: ${hitRate}%`);
      const searchStats = getSearchMonitorStats();
      console.log(`[搜索] 总计: ${searchStats.total} | 成功: ${searchStats.success} | 成功率: ${searchStats.rate}%`);
      if (searchStats.total > 0) {
        const providerDetails = Object.entries(searchStats.byProvider)
          .map(([p, s]) => `${p}: ${s.success}/${s.success + s.fail}`)
          .join(' | ');
        if (providerDetails) console.log(`[搜索] 各源: ${providerDetails}`);
      }
      console.log(`[归档] 研究目录: research/${ws?.topicName ?? '(unknown)'}/`);
    }

    if (planFailed) {
      console.warn('\n⚠️  Plan mode failed. Falling back to legacy mode.');
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
  if (!report) {
    console.error('\n❌ 未生成报告，请检查以上步骤的错误信息');
    rl.close();
    process.exit(1);
  }

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

  // 只打印摘要，不输出完整报告到终端
  const reportLines = report.split('\n');
  const summaryLines = reportLines.slice(0, Math.min(20, reportLines.length));
  const summary = summaryLines.join('\n');
  console.log(`\n📝 报告摘要 (${report.length} chars, ${reportLines.length} lines):\n`);
  console.log(summary);
  if (reportLines.length > 20) {
    console.log('\n  ... (完整报告已保存到文件)');
  }
  console.log(`\n📄 Report saved to ${finalOutputPath}`);
  rl.close();
}

run().catch(console.error);
