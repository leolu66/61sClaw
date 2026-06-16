/**
 * 研究归档模块
 * 每次深度研究建立独立目录，保存全流程产物（输入素材 / 加工过程 / 输出报告）
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import * as crypto from 'crypto';

import type { Source } from './deep-research';
import type { ExpansionResult } from './prompt-expansion';
import type { QueryAnalysis, ResearchPlan, ReportOutline } from './research-plan';

// ─── 类型定义 ───────────────────────────────────────

export type ResearchWorkspace = {
  rootDir: string;        // absolute path: <skill-root>/research/<topic>/
  srcDir: string;         // rootDir/src/
  workDir: string;        // rootDir/work/
  outputDir: string;      // rootDir/output/
  topicName: string;
};

// ─── 常量 ───────────────────────────────────────────

/** 技能根目录（deep-research/） */
const SKILL_ROOT = path.resolve(__dirname, '..');
const RESEARCH_DIR = path.join(SKILL_ROOT, 'research');

// ─── 主题名生成 ─────────────────────────────────────

/**
 * 从用户查询生成简短、文件系统安全的主题名
 * 规则：取前 30 字符，替换非法字符，加时间戳后缀避免冲突
 */
function generateTopicName(query: string): string {
  // 提取查询的核心部分（取第一行，去除多余空白）
  const firstLine = query.split('\n')[0].trim();

  // 保留中英文、数字、连字符，替换其他字符为连字符
  let safe = firstLine
    .replace(/[<>:"/\\|?*\x00-\x1f]/g, '-')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');

  // 截断到 30 字符
  if (safe.length > 30) {
    safe = safe.slice(0, 30).replace(/-$/, '');
  }

  // 加短时间戳避免冲突 (YYMMDD-HHmm)
  const now = new Date();
  const ts = [
    String(now.getFullYear()).slice(2),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
    '-',
    String(now.getHours()).padStart(2, '0'),
    String(now.getMinutes()).padStart(2, '0'),
  ].join('');

  return `${safe}-${ts}`;
}

// ─── 创建工作目录 ───────────────────────────────────

/**
 * 创建研究归档目录结构：
 * ```
 * research/<topicName>/
 *   src/urls/
 *   src/files/
 *   src/obsidian/
 *   work/
 *   output/
 * ```
 */
export async function createWorkspace(query: string): Promise<ResearchWorkspace> {
  const topicName = generateTopicName(query);
  const rootDir = path.join(RESEARCH_DIR, topicName);

  const ws: ResearchWorkspace = {
    rootDir,
    srcDir: path.join(rootDir, 'src'),
    workDir: path.join(rootDir, 'work'),
    outputDir: path.join(rootDir, 'output'),
    topicName,
  };

  // 创建目录结构
  await fs.mkdir(path.join(ws.srcDir, 'urls'), { recursive: true });
  await fs.mkdir(path.join(ws.srcDir, 'files'), { recursive: true });
  await fs.mkdir(path.join(ws.srcDir, 'obsidian'), { recursive: true });
  await fs.mkdir(ws.workDir, { recursive: true });
  await fs.mkdir(ws.outputDir, { recursive: true });

  console.log(`[归档] 创建工作目录: research/${topicName}/`);
  return ws;
}

// ─── JSON 写入辅助 ──────────────────────────────────

async function writeJson(filePath: string, data: unknown): Promise<void> {
  await fs.writeFile(filePath, JSON.stringify(data, null, 2), 'utf-8');
}

// ─── 各阶段保存方法 ─────────────────────────────────

/** 保存 QueryAnalysis 到 work/analysis.json */
export async function saveAnalysis(ws: ResearchWorkspace, analysis: QueryAnalysis): Promise<void> {
  await writeJson(path.join(ws.workDir, 'analysis.json'), analysis);
}

/** 保存确认后的维度到 work/dimensions.json */
export async function saveDimensions(
  ws: ResearchWorkspace,
  dimensions: { title: string; priority: string; description: string }[],
): Promise<void> {
  await writeJson(path.join(ws.workDir, 'dimensions.json'), dimensions);
}

/** 保存 ResearchPlan 到 work/plan.json */
export async function savePlan(ws: ResearchWorkspace, plan: ResearchPlan): Promise<void> {
  await writeJson(path.join(ws.workDir, 'plan.json'), plan);
}

/** 保存 ReportOutline 到 work/outline.json */
export async function saveOutline(ws: ResearchWorkspace, outline: ReportOutline): Promise<void> {
  await writeJson(path.join(ws.workDir, 'outline.json'), outline);
}

/** 保存提示词扩写结果到 work/expansion.json */
export async function saveExpansion(ws: ResearchWorkspace, expansion: ExpansionResult): Promise<void> {
  await writeJson(path.join(ws.workDir, 'expansion.json'), {
    direction: expansion.direction,
    variables: expansion.variables,
    expandedQuery: expansion.expandedQuery,
  });
}

/** 保存 URL 抓取的 markdown 到 src/urls/ */
export async function saveUrlContent(ws: ResearchWorkspace, url: string, markdown: string): Promise<void> {
  const hash = crypto.createHash('md5').update(url).digest('hex').slice(0, 12);
  const filename = `${hash}.md`;
  const header = `<!-- source: ${url} -->\n\n`;
  await fs.writeFile(path.join(ws.srcDir, 'urls', filename), header + markdown, 'utf-8');
}

/** 保存用户参考文件（转换后 md）到 src/files/ */
export async function saveFileContent(ws: ResearchWorkspace, originalPath: string, markdown: string): Promise<void> {
  const basename = path.basename(originalPath, path.extname(originalPath));
  const filename = `${basename}.md`;
  const header = `<!-- source: ${originalPath} -->\n\n`;
  await fs.writeFile(path.join(ws.srcDir, 'files', filename), header + markdown, 'utf-8');
}

/** 保存 Obsidian 笔记到 src/obsidian/ */
export async function saveObsidianNote(
  ws: ResearchWorkspace,
  notePath: string,
  content: string,
): Promise<void> {
  // 从笔记路径提取文件名
  const noteName = path.basename(notePath, '.md');
  const safeName = noteName.replace(/[<>:"/\\|?*]/g, '_');
  const filename = `${safeName}.md`;
  const header = `<!-- obsidian: ${notePath} -->\n\n`;
  await fs.writeFile(path.join(ws.srcDir, 'obsidian', filename), header + content, 'utf-8');
}

/** 保存 learnings 到 work/learnings.json */
export async function saveLearnings(
  ws: ResearchWorkspace,
  learnings: string[],
  learningsByDimension?: Map<string, string[]>,
): Promise<void> {
  const data: Record<string, unknown> = {
    total: learnings.length,
    all: learnings,
  };
  if (learningsByDimension) {
    data.byDimension = Object.fromEntries(learningsByDimension);
  }
  await writeJson(path.join(ws.workDir, 'learnings.json'), data);
}

/** 保存所有来源到 work/sources.json */
export async function saveSources(ws: ResearchWorkspace, sources: Source[]): Promise<void> {
  await writeJson(path.join(ws.workDir, 'sources.json'), {
    total: sources.length,
    sources,
  });
}

/** 保存最终报告到 output/report.md */
export async function saveReport(ws: ResearchWorkspace, report: string): Promise<string> {
  const reportPath = path.join(ws.outputDir, 'report.md');
  await fs.writeFile(reportPath, report, 'utf-8');
  return reportPath;
}

// ─── 断点续传：加载已有工作目录 ─────────────────────

/** 从已有目录加载 Workspace 对象（不创建新目录） */
export async function loadWorkspaceFromDir(rootDir: string): Promise<ResearchWorkspace> {
  const topicName = path.basename(rootDir);
  return {
    rootDir,
    srcDir: path.join(rootDir, 'src'),
    workDir: path.join(rootDir, 'work'),
    outputDir: path.join(rootDir, 'output'),
    topicName,
  };
}

/** 查找最新的研究工作目录（按修改时间排序） */
export async function findLatestWorkspace(): Promise<string | null> {
  try {
    const entries = await fs.readdir(RESEARCH_DIR, { withFileTypes: true });
    const dirs = entries.filter(e => e.isDirectory());
    if (dirs.length === 0) return null;

    // 按修改时间倒序
    const withStats = await Promise.all(
      dirs.map(async d => {
        const full = path.join(RESEARCH_DIR, d.name);
        const stat = await fs.stat(full);
        return { path: full, mtime: stat.mtimeMs };
      }),
    );
    withStats.sort((a, b) => b.mtime - a.mtime);
    return withStats[0].path;
  } catch {
    return null;
  }
}

/** 通用 JSON 读取 */
async function readJson<T>(filePath: string): Promise<T | null> {
  try {
    const raw = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export async function loadAnalysis(ws: ResearchWorkspace) {
  return readJson<import('./research-plan').QueryAnalysis>(path.join(ws.workDir, 'analysis.json'));
}

export async function loadDimensions(ws: ResearchWorkspace) {
  return readJson<import('./research-plan').RecommendedDimension[]>(path.join(ws.workDir, 'dimensions.json'));
}

export async function loadPlan(ws: ResearchWorkspace) {
  return readJson<import('./research-plan').ResearchPlan>(path.join(ws.workDir, 'plan.json'));
}

export async function loadOutline(ws: ResearchWorkspace) {
  return readJson<import('./research-plan').ReportOutline>(path.join(ws.workDir, 'outline.json'));
}

export async function loadExpansion(ws: ResearchWorkspace) {
  return readJson<import('./prompt-expansion').ExpansionResult>(path.join(ws.workDir, 'expansion.json'));
}

export async function loadLearnings(ws: ResearchWorkspace): Promise<{ all: string[]; byDimension?: Record<string, string[]> } | null> {
  const data = await readJson<{ total: number; all: string[]; byDimension?: Record<string, string[]> }>(path.join(ws.workDir, 'learnings.json'));
  if (!data) return null;
  return { all: data.all, byDimension: data.byDimension };
}

export async function loadSources(ws: ResearchWorkspace) {
  const data = await readJson<{ total: number; sources: import('./deep-research').Source[] }>(path.join(ws.workDir, 'sources.json'));
  return data?.sources ?? null;
}
