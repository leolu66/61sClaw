/**
 * 多源素材收集模块
 * 从 URL、本地文件、Obsidian 笔记收集预加载素材
 * AI 提取 learnings 后与网络搜索结果合并
 */

import { generateObject } from 'ai';
import { execSync } from 'child_process';
import FirecrawlApp from '@mendable/firecrawl-js';
import * as fs from 'fs/promises';
import * as path from 'path';
import { z } from 'zod';

import { o3MiniModel, trimPrompt } from './ai/providers';
import { getSearchLimiter } from './concurrency';
import type { Source } from './deep-research';
import type { ResearchPlan } from './research-plan';
import {
  type ResearchWorkspace,
  saveUrlContent,
  saveFileContent,
  saveObsidianNote,
} from './research-workspace';
import { systemPrompt } from './prompt';

// ─── 类型定义 ───────────────────────────────────────

export type UserSource = {
  type: 'url' | 'file' | 'obsidian';
  path: string;
  title: string;
  content: string;   // markdown 内容
};

export type CollectionResult = {
  sources: UserSource[];
  preloadedLearnings: string[];
  preloadedSourceRefs: Source[];
};

// ─── Firecrawl 实例 ─────────────────────────────────

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY ?? process.env.FIRECRAWL_KEY ?? '',
  apiUrl: process.env.FIRECRAWL_BASE_URL,
});

// ─── markitdown 脚本路径 ────────────────────────────

const MARKITDOWN_SCRIPT = path.resolve(__dirname, '..', '..', 'markitdown', 'scripts', 'convert.py');

// ─── 1. URL 抓取 ────────────────────────────────────

export async function collectUrls(
  urls: string[],
  ws?: ResearchWorkspace,
): Promise<UserSource[]> {
  if (urls.length === 0) return [];

  const limiter = getSearchLimiter();
  const results = await Promise.all(
    urls.map(url =>
      limiter(async (): Promise<UserSource | null> => {
        try {
          console.log(`  [URL] 抓取: ${url}`);
          const res = await firecrawl.scrapeUrl(url, { formats: ['markdown'] });
          const markdown = (res as any).markdown || (res as any).content || '';
          const title = (res as any).metadata?.title || new URL(url).hostname;

          if (!markdown) {
            console.log(`  [URL] 无内容: ${url}`);
            return null;
          }

          // 保存到归档
          if (ws) {
            await saveUrlContent(ws, url, markdown);
          }

          console.log(`  [URL] ✓ ${title} (${markdown.length} chars)`);
          return { type: 'url', path: url, title, content: markdown };
        } catch (e: any) {
          // fallback: 简单 fetch
          try {
            console.log(`  [URL] Firecrawl 失败，尝试 fetch: ${url}`);
            const resp = await fetch(url, {
              headers: { 'User-Agent': 'Mozilla/5.0 deep-research/1.2' },
              signal: AbortSignal.timeout(15000),
            });
            const text = await resp.text();
            // 简单去掉 HTML 标签
            const plainText = text.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
              .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
              .replace(/<[^>]+>/g, ' ')
              .replace(/\s+/g, ' ')
              .trim();

            if (plainText.length < 50) {
              console.log(`  [URL] fetch 也无有效内容: ${url}`);
              return null;
            }

            if (ws) await saveUrlContent(ws, url, plainText);
            console.log(`  [URL] ✓ fallback ${plainText.length} chars`);
            return { type: 'url', path: url, title: url, content: plainText };
          } catch (e2) {
            console.log(`  [URL] ✗ 失败: ${url} (${e.message || e2})`);
            return null;
          }
        }
      }),
    ),
  );

  return results.filter((r): r is UserSource => r !== null);
}

// ─── 2. 文件读取 ────────────────────────────────────

export async function collectFiles(
  filePaths: string[],
  ws?: ResearchWorkspace,
): Promise<UserSource[]> {
  if (filePaths.length === 0) return [];

  const results: UserSource[] = [];

  for (const filePath of filePaths) {
    try {
      const absPath = path.resolve(filePath);
      const ext = path.extname(absPath).toLowerCase();
      const basename = path.basename(absPath);
      let markdown: string;

      if (ext === '.md' || ext === '.txt') {
        // 直接读取
        markdown = await fs.readFile(absPath, 'utf-8');
      } else if (['.pdf', '.docx', '.pptx', '.html', '.xlsx'].includes(ext)) {
        // 调用 markitdown 转换
        console.log(`  [文件] 转换 ${basename}...`);
        try {
          markdown = execSync(
            `python "${MARKITDOWN_SCRIPT}" "${absPath}"`,
            { encoding: 'utf-8', timeout: 60000, maxBuffer: 10 * 1024 * 1024 },
          );
        } catch (e: any) {
          console.log(`  [文件] ✗ markitdown 转换失败: ${basename} (${e.message})`);
          continue;
        }
      } else {
        console.log(`  [文件] ⚠ 不支持的格式: ${ext}`);
        continue;
      }

      if (!markdown || markdown.trim().length < 10) {
        console.log(`  [文件] ⚠ 内容为空: ${basename}`);
        continue;
      }

      // 保存到归档
      if (ws) {
        await saveFileContent(ws, absPath, markdown);
      }

      console.log(`  [文件] ✓ ${basename} (${markdown.length} chars)`);
      results.push({ type: 'file', path: absPath, title: basename, content: markdown });
    } catch (e: any) {
      console.log(`  [文件] ✗ 读取失败: ${filePath} (${e.message})`);
    }
  }

  return results;
}

// ─── 3. Obsidian 搜索 ──────────────────────────────

/**
 * 检测 Obsidian vault 路径
 * 优先使用用户指定路径，否则从 obsidian.json 读取 open=true 的 vault
 */
function detectObsidianVault(): string | null {
  try {
    const appdata = process.env.APPDATA || '';
    if (!appdata) return null;

    const configPath = path.join(appdata, 'obsidian', 'obsidian.json');
    const raw = require('fs').readFileSync(configPath, 'utf-8');
    const config = JSON.parse(raw);
    const vaults = config?.vaults || {};

    // 找 "open": true 的 vault
    for (const id of Object.keys(vaults)) {
      if (vaults[id].open === true) {
        return vaults[id].path;
      }
    }

    // 没有 open 的，取最近的
    let latest: { path: string; ts: number } | null = null;
    for (const id of Object.keys(vaults)) {
      const v = vaults[id];
      if (!latest || (v.ts || 0) > latest.ts) {
        latest = { path: v.path, ts: v.ts || 0 };
      }
    }
    return latest?.path || null;
  } catch {
    return null;
  }
}

/**
 * 从研究计划中提取搜索关键词
 * 从所有 subTopic.initialQueries 中提取，去重，取前 5 个
 */
function extractKeywordsFromPlan(plan: ResearchPlan): string[] {
  const querySet = new Set<string>();

  for (const dim of plan.dimensions) {
    for (const sub of dim.subTopics) {
      for (const q of sub.initialQueries) {
        // 提取查询中的关键词（去掉常见的搜索修饰词）
        const words = q
          .split(/\s+/)
          .filter(w => w.length > 1)
          .filter(w => !['vs', 'and', 'or', 'the', 'a', 'of', 'in', 'to', 'for', 'with', 'how', 'what', 'is', 'are'].includes(w.toLowerCase()));

        // 取前 3 个有意义的词
        for (const w of words.slice(0, 3)) {
          querySet.add(w);
        }
      }
    }
  }

  return [...querySet].slice(0, 5);
}

export async function collectFromObsidian(
  keywords: string[],
  vaultPath?: string,
  ws?: ResearchWorkspace,
): Promise<UserSource[]> {
  // 检测 vault
  const vault = vaultPath || detectObsidianVault();
  if (!vault) {
    console.log('  [Obsidian] ⚠ 未检测到 Obsidian vault，跳过');
    return [];
  }

  console.log(`  [Obsidian] vault: ${vault}`);
  console.log(`  [Obsidian] 关键词: ${keywords.join(', ')}`);

  const noteFiles = new Set<string>();
  const results: UserSource[] = [];

  for (const keyword of keywords) {
    try {
      const output = execSync(
        `obsidian-cli search-content "${keyword.replace(/"/g, '\\"')}"`,
        {
          encoding: 'utf-8',
          timeout: 15000,
          cwd: vault,
          maxBuffer: 5 * 1024 * 1024,
        },
      );

      if (!output || output.trim().length === 0) continue;

      // 解析 obsidian-cli 输出：通常格式是 "path/to/note.md: 匹配行"
      const lines = output.split('\n').filter(l => l.trim());
      for (const line of lines) {
        // 提取文件路径（冒号前的部分）
        const match = line.match(/^(.+\.md):/);
        if (match) {
          noteFiles.add(match[1]);
        }
      }
    } catch (e: any) {
      console.log(`  [Obsidian] 搜索 "${keyword}" 失败: ${e.message}`);
    }
  }

  // 读取匹配的笔记（最多 10 篇）
  const noteList = [...noteFiles].slice(0, 10);
  for (const noteRelPath of noteList) {
    try {
      const fullPath = path.join(vault, noteRelPath);
      const content = await fs.readFile(fullPath, 'utf-8');
      const title = path.basename(noteRelPath, '.md');

      // 保存到归档
      if (ws) {
        await saveObsidianNote(ws, noteRelPath, content);
      }

      console.log(`  [Obsidian] ✓ ${title} (${content.length} chars)`);
      results.push({ type: 'obsidian', path: noteRelPath, title, content });
    } catch {
      // 忽略读取失败
    }
  }

  if (results.length === 0) {
    console.log('  [Obsidian] 未找到匹配笔记');
  } else {
    console.log(`  [Obsidian] 共收集 ${results.length} 篇笔记`);
  }

  return results;
}

// ─── 4. AI 提取 learnings ──────────────────────────

export async function extractLearningsFromSources(
  sources: UserSource[],
  query: string,
): Promise<{ learnings: string[]; sourceRefs: Source[] }> {
  if (sources.length === 0) {
    return { learnings: [], sourceRefs: [] };
  }

  // 构建内容字符串（截断到 120k tokens）
  const contentsStr = trimPrompt(
    sources
      .map(s => `<source type="${s.type}" title="${s.title}">\n${trimPrompt(s.content, 25_000)}\n</source>`)
      .join('\n\n'),
    120_000,
  );

  const sourceSummary = sources
    .map(s => `${s.type}: ${s.title}`)
    .join(', ');

  console.log(`  [AI] 从 ${sources.length} 个素材中提取 learnings...`);

  try {
    const res = await generateObject({
      model: o3MiniModel,
      system: systemPrompt(),
      prompt: `Given the following reference materials collected from various sources, extract key learnings relevant to the research query.

Research query: <query>${query}</query>

Source summary: ${sourceSummary}

Reference materials:
${contentsStr}

Extract up to 20 concise, information-dense learnings from these materials. Focus on:
- Specific facts, metrics, dates, entity names
- Key insights and comparisons
- Information directly relevant to the research query

Return learnings as a list.`,
      schema: z.object({
        learnings: z
          .array(z.string())
          .describe('List of key learnings extracted from reference materials, max 20'),
      }),
    });

    const learnings = res.object.learnings || [];
    console.log(`  [AI] ✓ 提取 ${learnings.length} 条 learnings`);

    // 构建 source refs
    const sourceRefs: Source[] = sources
      .filter(s => s.type === 'url')
      .map(s => ({ url: s.path, title: s.title }));

    return { learnings, sourceRefs };
  } catch (e: any) {
    console.log(`  [AI] ✗ 提取失败: ${e.message}`);
    return { learnings: [], sourceRefs: [] };
  }
}

// ─── 5. 统一入口 ───────────────────────────────────

export async function collectAllSources(options: {
  query: string;
  urls?: string[];
  files?: string[];
  plan?: ResearchPlan;
  workspace?: ResearchWorkspace;
  obsidianVault?: string;
  obsidianEnabled?: boolean;
}): Promise<CollectionResult> {
  const {
    query,
    urls = [],
    files = [],
    plan,
    workspace,
    obsidianVault,
    obsidianEnabled = true,
  } = options;

  console.log('\n━━━ Step 4.5: 素材收集 ━━━');
  console.log(`  URL: ${urls.length} 个`);
  console.log(`  文件: ${files.length} 个`);
  console.log(`  Obsidian: ${obsidianEnabled ? '启用' : '禁用'}`);

  // 并行收集三种来源
  const tasks: Promise<UserSource[]>[] = [];

  // URL 收集
  if (urls.length > 0) {
    tasks.push(collectUrls(urls, workspace));
  }

  // 文件收集
  if (files.length > 0) {
    tasks.push(collectFiles(files, workspace));
  }

  // Obsidian 收集（默认启用）
  if (obsidianEnabled && plan) {
    const keywords = extractKeywordsFromPlan(plan);
    if (keywords.length > 0) {
      tasks.push(collectFromObsidian(keywords, obsidianVault, workspace));
    }
  }

  const taskResults = await Promise.all(tasks);
  const allSources = taskResults.flat();

  if (allSources.length === 0) {
    console.log('  无素材收集到，跳过 AI 提取');
    return { sources: [], preloadedLearnings: [], preloadedSourceRefs: [] };
  }

  console.log(`\n  素材汇总: ${allSources.length} 个来源`);
  allSources.forEach(s => {
    console.log(`    [${s.type}] ${s.title}`);
  });

  // AI 提取 learnings
  const { learnings, sourceRefs } = await extractLearningsFromSources(allSources, query);

  return {
    sources: allSources,
    preloadedLearnings: learnings,
    preloadedSourceRefs: sourceRefs,
  };
}
