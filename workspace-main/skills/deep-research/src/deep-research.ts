import { generateObject } from 'ai';
import { compact } from 'lodash-es';
import pLimit from 'p-limit';
import { z } from 'zod';

import { o3MiniModel, trimPrompt } from './ai/providers';
import { getSearchLimiter } from './concurrency';
import { systemPrompt, reportSystemPrompt } from './prompt';
import { ResearchPlan, ReportOutline } from './research-plan';
import { smartSearch, SearchResult } from './search-providers';

export type Source = {
  url: string;
  title: string;
};

export type ResearchResult = {
  learnings: string[];
  visitedSources: Source[];
};

// increase this if you have higher API rate limits
const ConcurrencyLimit = 2;

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
  const res = await generateObject({
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

  const res = await generateObject({
    model: o3MiniModel,
    abortSignal: AbortSignal.timeout(60_000),
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

  const res = await generateObject({
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
): Promise<ResearchResult> {
  const allLearnings: string[] = [];
  const allSources: Source[] = [];
  const limiter = getSearchLimiter();

  // 按 executionOrder 遍历维度，维度间并行（受全局 limiter 控制）
  const dimensionResults = await Promise.all(
    plan.executionOrder.map(dimId => {
      const dimension = plan.dimensions.find(d => d.id === dimId);
      if (!dimension) return Promise.resolve({ learnings: [], visitedSources: [] });

      return processDimension(dimension, limiter);
    }),
  );

  // 合并所有维度结果
  for (const result of dimensionResults) {
    allLearnings.push(...result.learnings);
    allSources.push(...result.visitedSources);
  }

  // 去重
  const uniqueLearnings = [...new Set(allLearnings)];
  const uniqueSources = Array.from(
    new Map(allSources.map(source => [source.url, source])).values(),
  );

  return {
    learnings: uniqueLearnings,
    visitedSources: uniqueSources,
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
          return processSubTopic(subTopic);
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

async function processSubTopic(subTopic: {
  title: string;
  initialQueries: string[];
  suggestedBreadth: number;
  suggestedDepth: number;
}): Promise<ResearchResult> {
  let subLearnings: string[] = [];
  let subSources: Source[] = [];

  // 用预设搜索词执行搜索
  for (const query of subTopic.initialQueries) {
    try {
      const { results, provider } = await smartSearch(query, 5);
      if (results.length === 0) {
        console.log(`  No results for: ${query}`);
        continue;
      }

      console.log(`  [${provider}] "${query}" → ${results.length} results`);

      const newSources = compact(
        results.map(item =>
          item.url && item.title ? { url: item.url, title: item.title.trim() } : null,
        ),
      );
      subSources.push(...newSources);

      // AI 提取 learnings
      const extracted = await processSerpResult({
        query,
        results,
        numFollowUpQuestions: subTopic.suggestedBreadth,
      });
      subLearnings.push(...extracted.learnings);

      // 递归深入
      if (subTopic.suggestedDepth > 1) {
        const nextQuery = `
          Sub-topic: ${subTopic.title}
          Follow-up directions: ${extracted.followUpQuestions.map(q => `\n${q}`).join('')}
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
    } catch (e) {
      console.error(`  Error searching "${query}":`, e);
    }
  }

  return { learnings: subLearnings, visitedSources: subSources };
}

// ─── 按大纲生成报告 ─────────────────────────────

export async function writeFinalReportWithOutline({
  outline,
  learnings,
  visitedSources,
}: {
  outline: ReportOutline;
  learnings: string[];
  visitedSources: Source[];
}): Promise<string> {
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

  const res = await generateObject({
    model: o3MiniModel,
    system: reportSystemPrompt(),
    prompt: `Write a comprehensive research report following the exact chapter structure below.

Report title: ${outline.title}
Research overview: ${outline.summary}

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
8. Be as detailed and information-dense as possible`,
    schema: z.object({
      reportMarkdown: z
        .string()
        .describe('Complete research report in Markdown following the chapter structure'),
    }),
  });

  // 追加参考来源
  const sourcesSection = `\n\n## Sources\n\n${visitedSources
    .map(source => {
      const safeTitle = source.title.replace(/[\[\]()]/g, '').trim();
      return `- [${safeTitle}](${source.url})`;
    })
    .join('\n')}`;

  return res.object.reportMarkdown + sourcesSection;
}
