import { generateObjectWithRetry } from './ai/providers';
import { compact } from 'lodash-es';
import pLimit from 'p-limit';
import { z } from 'zod';

import { o3MiniModel, trimPrompt } from './ai/providers';
import { getSearchLimiter } from './concurrency';
import { systemPrompt, reportSystemPrompt } from './prompt';
import { ResearchPlan, ReportOutline, QueryAnalysis } from './research-plan';
import { smartSearch, SearchResult } from './search-providers';

export type Source = {
  url: string;
  title: string;
};

export type ResearchResult = {
  learnings: string[];
  visitedSources: Source[];
  learningsByDimension?: Map<string, string[]>;
};

// take en user query, return a list of SERP queries
async function generateSerpQueries({
  query,
  numQueries = 3,
  learnings,
}: {
  query: string;
  numQueries?: number;

  // optional, if provided, the research will continue from the last learning
  learnings?: string[];
}) {
  const res = await generateObjectWithRetry({
    model: o3MiniModel,
    system: systemPrompt(),
    prompt: `Given the following prompt from the user, generate a list of SERP queries to research the topic. Return a maximum of ${numQueries} queries, but feel free to return less if the original prompt is clear. Make sure each query is unique and not similar to each other: <prompt>${query}</prompt>\n\n${
      learnings
        ? `Here are some learnings from previous research, use them to generate more specific queries: ${learnings.join(
            '\n',
          )}`
        : ''
    }`,
    schema: z.object({
      queries: z
        .array(
          z.object({
            query: z.string().describe('The SERP query'),
            researchGoal: z
              .string()
              .describe(
                'First talk about the goal of the research that this query is meant to accomplish, then go deeper into how to advance the research once the results are found, mention additional research directions. Be as specific as possible, especially for additional research directions.',
              ),
          }),
        )
        .describe(`List of SERP queries, max of ${numQueries}`),
    }),
  });
  console.log(
    `Created ${res.object.queries.length} queries`,
    res.object.queries,
  );

  return res.object.queries.slice(0, numQueries);
}

async function processSerpResult({
  query,
  results,
  numLearnings = 3,
  numFollowUpQuestions = 3,
}: {
  query: string;
  results: SearchResult[];
  numLearnings?: number;
  numFollowUpQuestions?: number;
}) {
  const contents = compact(results.map(item => item.markdown)).map(
    content => trimPrompt(content, 25_000),
  );
  console.log(`Ran ${query}, found ${contents.length} contents`);

  const res = await generateObjectWithRetry({
    model: o3MiniModel,
    system: systemPrompt(),
    prompt: `Given the following contents from a SERP search for the query <query>${query}</query>, generate a list of learnings from the contents. Return a maximum of ${numLearnings} learnings, but feel free to return less if the contents are clear. Make sure each learning is unique and not similar to each other. The learnings should be concise and to the point, as detailed and infromation dense as possible. Make sure to include any entities like people, places, companies, products, things, etc in the learnings, as well as any exact metrics, numbers, or dates. The learnings will be used to research the topic further.\n\n<contents>${contents
      .map(content => `<content>\n${content}\n</content>`)
      .join('\n')}</contents>`,
    schema: z.object({
      learnings: z
        .array(z.string())
        .describe(`List of learnings, max of ${numLearnings}`),
      followUpQuestions: z
        .array(z.string())
        .describe(
          `List of follow-up questions to research the topic further, max of ${numFollowUpQuestions}`,
        ),
    }),
  });
  console.log(
    `Created ${res.object.learnings.length} learnings`,
    res.object.learnings,
  );

  return res.object;
}

export async function writeFinalReport({
  prompt,
  learnings,
  visitedSources,
}: {
  prompt: string;
  learnings: string[];
  visitedSources: Source[];
}) {
  const learningsString = trimPrompt(
    learnings
      .map(learning => `<learning>\n${learning}\n</learning>`)
      .join('\n'),
    150_000,
  );

  const res = await generateObjectWithRetry({
    model: o3MiniModel,
    system: systemPrompt(),
    prompt: `Given the following prompt from the user, write a final report on the topic using the learnings from research. Make it as as detailed as possible, aim for 3 or more pages, include ALL the learnings from research:\n\n<prompt>${prompt}</prompt>\n\nHere are all the learnings from previous research:\n\n<learnings>\n${learningsString}\n</learnings>`,
    schema: z.object({
      reportMarkdown: z
        .string()
        .describe('Final report on the topic in Markdown'),
    }),
  });

  // Append the visited sources section to the report (title + url format)
  const sourcesSection = `\n\n## Sources\n\n${visitedSources.map(source => {
    // 处理标题中的特殊字符，避免破坏markdown链接格式
    const safeTitle = source.title.replace(/[\[\]()]/g, '').trim();
    return `- [${safeTitle}](${source.url})`;
  }).join('\n')}`;
  return res.object.reportMarkdown + sourcesSection;
}

export async function deepResearch({
  query,
  breadth,
  depth,
  learnings = [],
  visitedSources = [],
}: {
  query: string;
  breadth: number;
  depth: number;
  learnings?: string[];
  visitedSources?: Source[];
}): Promise<ResearchResult> {
  const serpQueries = await generateSerpQueries({
    query,
    learnings,
    numQueries: breadth,
  });
  const limit = getSearchLimiter();

  const results = await Promise.all(
    serpQueries.map(serpQuery =>
      limit(async () => {
        try {
          // 使用智能搜索（支持多搜索源）
          const { results: searchResults, provider } = await smartSearch(serpQuery.query, 5);

          if (searchResults.length === 0) {
            console.log(`No results found for: ${serpQuery.query}`);
            return {
              learnings: [],
              visitedSources: [],
            };
          }

          console.log(`Using ${provider} for: ${serpQuery.query}`);

          // Collect sources (title + url) from this search
          const newSources = compact(searchResults.map(item => 
            item.url && item.title ? { url: item.url, title: item.title.trim() } : null
          ));
          const newBreadth = Math.ceil(breadth / 2);
          const newDepth = depth - 1;

          const newLearnings = await processSerpResult({
            query: serpQuery.query,
            results: searchResults,
            numFollowUpQuestions: newBreadth,
          });
          const allLearnings = [...learnings, ...newLearnings.learnings];
          const allSources = [...visitedSources, ...newSources];

          if (newDepth > 0) {
            console.log(
              `Researching deeper, breadth: ${newBreadth}, depth: ${newDepth}`,
            );

            const nextQuery = `
            Previous research goal: ${serpQuery.researchGoal}
            Follow-up research directions: ${newLearnings.followUpQuestions.map(q => `\n${q}`).join('')}
          `.trim();

            return deepResearch({
              query: nextQuery,
              breadth: newBreadth,
              depth: newDepth,
              learnings: allLearnings,
              visitedSources: allSources,
            });
          } else {
            return {
              learnings: allLearnings,
              visitedSources: allSources,
            };
          }
        } catch (e) {
          console.error(`Error running query: ${serpQuery.query}: `, e);
          return {
            learnings: [],
            visitedSources: [],
          };
        }
      }),
    ),
  );

  // 合并结果，按URL去重
  const allLearnings = [...new Set(results.flatMap(r => r.learnings))];
  const allSources = results.flatMap(r => r.visitedSources);
  // 按URL去重，保留第一个出现的标题
  const uniqueSources = Array.from(
    new Map(allSources.map(source => [source.url, source])).values()
  );

  return {
    learnings: allLearnings,
    visitedSources: uniqueSources,
  };
}

// ─── 按计划执行研究 ─────────────────────────────

export async function deepResearchByPlan(
  query: string,
  plan: ResearchPlan,
  preloadedLearnings?: string[],
  preloadedSourceRefs?: Source[],
): Promise<ResearchResult> {
  const allLearnings: string[] = [];
  const allSources: Source[] = [];
  const limiter = getSearchLimiter();
  const totalDims = plan.executionOrder.length;
  let completedDims = 0;

  // 按 executionOrder 遍历维度，维度间并行（受全局 limiter 控制）
  const dimensionResults = await Promise.all(
    plan.executionOrder.map(dimId => {
      const dimension = plan.dimensions.find(d => d.id === dimId);
      if (!dimension) return Promise.resolve({ learnings: [], visitedSources: [] });

      console.log(`\n[进度] 维度 ${completedDims + 1}/${totalDims} 开始: ${dimension.title}`);

      return processDimension(dimension, limiter).then(result => {
        completedDims++;
        console.log(`[进度] 维度 ${completedDims}/${totalDims} 完成: ${dimension.title} (${result.learnings.length} learnings, ${result.visitedSources.length} sources)`);
        return result;
      });
    }),
  );

  // 合并所有维度结果，按维度记录 learnings
  const learningsByDimension = new Map<string, string[]>();
  for (let i = 0; i < dimensionResults.length; i++) {
    const dimId = plan.executionOrder[i];
    const result = dimensionResults[i];
    allLearnings.push(...result.learnings);
    allSources.push(...result.visitedSources);
    learningsByDimension.set(dimId, result.learnings);
  }

  // 合并预加载素材的 learnings 和 sources
  if (preloadedLearnings && preloadedLearnings.length > 0) {
    allLearnings.push(...preloadedLearnings);
    console.log(`[预加载] 合并 ${preloadedLearnings.length} 条预加载 learnings`);
  }
  if (preloadedSourceRefs && preloadedSourceRefs.length > 0) {
    allSources.push(...preloadedSourceRefs);
    console.log(`[预加载] 合并 ${preloadedSourceRefs.length} 个预加载来源`);
  }

  // 去重
  const uniqueLearnings = [...new Set(allLearnings)];
  const uniqueSources = Array.from(
    new Map(allSources.map(source => [source.url, source])).values(),
  );

  return {
    learnings: uniqueLearnings,
    visitedSources: uniqueSources,
    learningsByDimension,
  };
}

async function processDimension(
  dimension: ResearchPlan['dimensions'][number],
  limiter: ReturnType<typeof pLimit>,
): Promise<ResearchResult> {
  console.log(`\n━━ 研究维度: ${dimension.title} (${dimension.priority}) ━━`);

  // 维度内子主题并行（受全局 limiter 控制）
  const subTopicResults = await Promise.all(
    dimension.subTopics.map(subTopic =>
      limiter(async () => {
        try {
          return processSubTopic(subTopic, limiter);
        } catch (e) {
          console.error(`Error processing sub-topic "${subTopic.title}":`, e);
          return { learnings: [], visitedSources: [] };
        }
      }),
    ),
  );

  const dimLearnings = subTopicResults.flatMap(r => r.learnings);
  const dimSources = subTopicResults.flatMap(r => r.visitedSources);
  const uniqueSources = Array.from(
    new Map(dimSources.map(s => [s.url, s])).values(),
  );

  console.log(`━━ 维度 "${dimension.title}" 完成: ${dimLearnings.length} learnings, ${uniqueSources.length} sources ━━`);

  return { learnings: dimLearnings, visitedSources: uniqueSources };
}

async function processSubTopic(
  subTopic: {
    title: string;
    initialQueries: string[];
    suggestedBreadth: number;
    suggestedDepth: number;
  },
  limiter: ReturnType<typeof pLimit>,
): Promise<ResearchResult> {
  // 并行执行所有 initialQueries（受全局 limiter 控制）
  const queryResults = await Promise.all(
    subTopic.initialQueries.map(query =>
      limiter(async () => {
        try {
          const { results, provider } = await smartSearch(query, 5);
          if (results.length === 0) {
            console.log(`  No results for: ${query}`);
            return { learnings: [] as string[], sources: [] as Source[], followUpQuestions: [] as string[] };
          }

          console.log(`  [${provider}] "${query}" → ${results.length} results`);

          const newSources = compact(
            results.map(item =>
              item.url && item.title ? { url: item.url, title: item.title.trim() } : null,
            ),
          );

          const extracted = await processSerpResult({
            query,
            results,
            numFollowUpQuestions: subTopic.suggestedBreadth,
          });

          return {
            learnings: extracted.learnings,
            sources: newSources,
            followUpQuestions: extracted.followUpQuestions,
          };
        } catch (e) {
          console.error(`  Error searching "${query}":`, e);
          return { learnings: [] as string[], sources: [] as Source[], followUpQuestions: [] as string[] };
        }
      }),
    ),
  );

  // 合并所有查询结果
  let subLearnings = queryResults.flatMap(r => r.learnings);
  let subSources = queryResults.flatMap(r => r.sources);
  const allFollowUps = queryResults.flatMap(r => r.followUpQuestions);

  // 递归深入（串行，依赖前一轮 learnings）
  if (subTopic.suggestedDepth > 1 && allFollowUps.length > 0) {
    const nextQuery = `
      Sub-topic: ${subTopic.title}
      Follow-up directions: ${allFollowUps.map(q => `\n${q}`).join('')}
    `.trim();

    const deeper = await deepResearch({
      query: nextQuery,
      breadth: subTopic.suggestedBreadth,
      depth: subTopic.suggestedDepth - 1,
      learnings: subLearnings,
      visitedSources: subSources,
    });
    subLearnings = deeper.learnings;
    subSources = deeper.visitedSources;
  }

  return { learnings: subLearnings, visitedSources: subSources };
}

// ─── 按大纲生成报告 ─────────────────────────────

export async function writeFinalReportWithOutline({
  outline,
  learnings,
  visitedSources,
  analysis,
  plan,
  learningsByDimension,
}: {
  outline: ReportOutline;
  learnings: string[];
  visitedSources: Source[];
  analysis?: QueryAnalysis;
  plan?: ResearchPlan;
  learningsByDimension?: Map<string, string[]>;
}): Promise<string> {
  const analysisContext = analysis
    ? `\nResearch type: ${analysis.questionType} | Complexity: ${analysis.estimatedComplexity}${analysis.keyEntities.length > 0 ? `\nKey entities: ${analysis.keyEntities.join(', ')}` : ''}${analysis.scope.domains.length > 0 ? `\nDomains: ${analysis.scope.domains.join(', ')}` : ''}`
    : '';

  // 如果有 plan + learningsByDimension，按章节生成（质量更高）
  if (plan && learningsByDimension) {
    return writeReportPerChapter(outline, plan, learnings, learningsByDimension, visitedSources, analysisContext);
  }

  // fallback: 单次生成（无 plan 时）
  const learningsString = trimPrompt(
    learnings
      .map(learning => `<learning>\n${learning}\n</learning>`)
      .join('\n'),
    150_000,
  );

  const chapterStructure = outline.chapters
    .map(ch => {
      const weight = `~${Math.round(ch.estimatedWeight * 100)}%`;
      const subs = ch.subSections?.map(s => `    - ${s}`).join('\n') || '';
      return `  ${ch.chapterType === 'intro' ? '0' : ch.chapterType === 'appendix' ? '附' : ch.id}: ${ch.title} [${ch.chapterType}] (${weight})\n    内容要求: ${ch.description}${subs ? '\n    子章节:\n' + subs : ''}`;
    })
    .join('\n');

  const res = await generateObjectWithRetry({
    model: o3MiniModel,
    system: reportSystemPrompt(),
    prompt: `Write a comprehensive research report following the exact chapter structure below.

Report title: ${outline.title}
Research overview: ${outline.summary}${analysisContext}

Chapter structure (follow this EXACTLY):
${chapterStructure}

Here are all the learnings from research:
<learnings>
${learningsString}
</learnings>

Requirements:
1. Write in Markdown format with proper headings (## for chapters, ### for sub-sections)
2. Each body chapter should be proportional to its estimated weight
3. Use ALL learnings - distribute them across the appropriate chapters
4. The intro chapter should explain the research scope and methodology
5. The conclusion chapter should synthesize findings and provide actionable recommendations
6. Include specific numbers, dates, entity names from the learnings
7. Use tables where comparison data is available
8. Be as detailed and information-dense as possible
9. Write in the SAME LANGUAGE as the research query/overview above`,
    schema: z.object({
      reportMarkdown: z
        .string()
        .describe('Complete research report in Markdown following the chapter structure'),
    }),
  });

  // 追加参考来源
  const sourcesSection = buildSourcesSection(visitedSources);
  return res.object.reportMarkdown + sourcesSection;
}

function buildSourcesSection(sources: Source[]): string {
  return `\n\n## Sources\n\n${sources
    .map(source => {
      const safeTitle = source.title.replace(/[\[\]()]/g, '').trim();
      return `- [${safeTitle}](${source.url})`;
    })
    .join('\n')}`;
}

async function writeReportPerChapter(
  outline: ReportOutline,
  plan: ResearchPlan,
  allLearnings: string[],
  learningsByDimension: Map<string, string[]>,
  visitedSources: Source[],
  analysisContext: string,
): Promise<string> {
  const chapterContents: string[] = [];
  const totalChapters = outline.chapters.length;

  // 构建所有标题的上下文（让每章知道前后章节）
  const allChapterTitles = outline.chapters.map((ch, i) => `${i + 1}. ${ch.title}`).join('\n');

  for (let i = 0; i < totalChapters; i++) {
    const chapter = outline.chapters[i];
    console.log(`  Generating chapter ${i + 1}/${totalChapters}: ${chapter.title}`);

    // 确定该章节的 learnings
    let chapterLearnings: string[];
    if (chapter.chapterType === 'body' && chapter.dimensionId) {
      // body 章节使用对应维度的 learnings
      chapterLearnings = learningsByDimension.get(chapter.dimensionId) || [];
      // 如果该维度没有 learnings，使用全部 learnings 的一小部分
      if (chapterLearnings.length === 0) {
        chapterLearnings = allLearnings.slice(0, Math.ceil(allLearnings.length / totalChapters));
      }
    } else {
      // intro/conclusion/appendix 使用全部 learnings（截断）
      chapterLearnings = allLearnings;
    }

    const learningsStr = trimPrompt(
      chapterLearnings
        .map(l => `<learning>\n${l}\n</learning>`)
        .join('\n'),
      80_000,
    );

    // 章节类型特定的指令
    let typeInstruction = '';
    switch (chapter.chapterType) {
      case 'intro':
        typeInstruction = 'Write an introduction that sets the research context, explains the scope and methodology. Mention key entities and the research question type.';
        break;
      case 'body':
        typeInstruction = `Write a detailed body chapter. Use ALL provided learnings. Include specific numbers, dates, entity names. Use tables where comparison data is available. Aim for ~${Math.round(chapter.estimatedWeight * 100)}% of total report length.`;
        break;
      case 'conclusion':
        typeInstruction = 'Write a conclusion that synthesizes all findings, provides actionable recommendations and key takeaways. Reference specific data points from the research.';
        break;
      case 'appendix':
        typeInstruction = 'Write an appendix with terminology definitions, data sources overview, and any supplementary information.';
        break;
    }

    const subSectionsHint = chapter.subSections?.length
      ? `\nInclude these sub-sections: ${chapter.subSections.join(', ')}`
      : '';

    const res = await generateObjectWithRetry({
      model: o3MiniModel,
      system: reportSystemPrompt(),
      prompt: `Write ONE chapter of a research report.

Report title: ${outline.title}
Research overview: ${outline.summary}${analysisContext}

Full report structure (for context):
${allChapterTitles}

--- YOUR CHAPTER ---
Title: ${chapter.title}
Type: ${chapter.chapterType}
Description: ${chapter.description}${subSectionsHint}

${typeInstruction}

Learnings for this chapter:
<learnings>
${learningsStr}
</learnings>

Write ONLY this chapter in Markdown (start with ## heading). Do NOT include any other chapters.
Write in the SAME LANGUAGE as the research query/overview above.`,
      schema: z.object({
        chapterMarkdown: z.string().describe('The chapter content in Markdown'),
      }),
    });

    chapterContents.push(res.object.chapterMarkdown);
  }

  // 拼接所有章节 + sources
  const fullReport = chapterContents.join('\n\n');
  return fullReport + buildSourcesSection(visitedSources);
}
