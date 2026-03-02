#!/usr/bin/env node
/**
 * 代码统计脚本
 * 统计 skills 目录下所有技能的工作成果 + GitHub 提交统计
 */

const fs = require('fs');
const path = require('path');

const SKILLS_DIR = path.join(__dirname, '..');

// 统计文件类型
const EXT_STATS = {
  '.py': { count: 0, lines: 0 },
  '.js': { count: 0, lines: 0 },
  '.md': { count: 0, lines: 0 },
  other: { count: 0, lines: 0 }
};

// 统计每个技能
const skills = [];

// 获取目录下的文件（递归）
function getAllFiles(dir, excludeDirs = ['node_modules', 'data', '__pycache__', '.git']) {
  const files = [];
  
  if (!fs.existsSync(dir)) return files;
  
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    
    if (entry.isDirectory()) {
      if (!excludeDirs.includes(entry.name)) {
        files.push(...getAllFiles(fullPath, excludeDirs));
      }
    } else {
      files.push(fullPath);
    }
  }
  
  return files;
}

// 统计代码行数（排除空行和纯注释行）
function countCodeLines(content, ext) {
  const lines = content.split('\n');
  let codeLines = 0;
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    if (ext === '.py' && (trimmed.startsWith('#') || trimmed.startsWith('"""') || trimmed.startsWith("'''"))) continue;
    if (ext === '.js' && (trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('*'))) continue;
    codeLines++;
  }
  
  return codeLines;
}

// GitHub 统计
async function getGitHubStats() {
  const repo = 'leolu66/61sClaw';
  const token = process.env.GITHUB_TOKEN || '';
  
  const since = new Date();
  since.setDate(since.getDate() - 7);
  const sinceStr = since.toISOString().split('T')[0];
  
  let commits = [];
  let pullRequests = 0;
  let totalAdditions = 0;
  let totalDeletions = 0;
  let totalFilesChanged = 0;
  
  try {
    const commitUrl = `https://api.github.com/repos/${repo}/commits?since=${sinceStr}&per_page=100`;
    const commitRes = await fetch(commitUrl, {
      headers: token ? { 'Authorization': `token ${token}` } : {}
    });
    
    if (commitRes.ok) {
      commits = await commitRes.json();
    }
    
    const prUrl = `https://api.github.com/repos/${repo}/pulls?state=all&sort=created&direction=desc&per_page=100`;
    const prRes = await fetch(prUrl, {
      headers: token ? { 'Authorization': `token ${token}` } : {}
    });
    
    if (prRes.ok) {
      const prs = await prRes.json();
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      
      for (const pr of prs) {
        const createdAt = new Date(pr.created_at);
        if (createdAt >= weekAgo) {
          pullRequests++;
          if (pr.additions !== undefined) {
            totalAdditions += pr.additions;
            totalDeletions += pr.deletions;
            totalFilesChanged += pr.changed_files;
          }
        } else {
          break;
        }
      }
    }
    
    let totalCommitAdditions = 0;
    let totalCommitDeletions = 0;
    
    for (const commit of commits.slice(0, 20)) {
      try {
        const detailUrl = `https://api.github.com/repos/${repo}/commits/${commit.sha}`;
        const detailRes = await fetch(detailUrl, {
          headers: token ? { 'Authorization': `token ${token}` } : {}
        });
        
        if (detailRes.ok) {
          const detail = await detailRes.json();
          if (detail.stats) {
            totalCommitAdditions += detail.stats.additions;
            totalCommitDeletions += detail.stats.deletions;
          }
        }
      } catch (e) {
        // 忽略
      }
    }
    
    totalAdditions += totalCommitAdditions;
    totalDeletions += totalCommitDeletions;
    
  } catch (e) {
    console.log('[GitHub API 请求失败，跳过统计]', e.message);
    return null;
  }
  
  return {
    commitCount: commits.length,
    prCount: pullRequests,
    additions: totalAdditions,
    deletions: totalDeletions,
    netChanges: totalAdditions - totalDeletions,
    daysWithCommits: commits.length > 0 ? new Set(commits.map(c => (c.commit?.date || c.commit?.author?.date || '').split('T')[0])).size : 0
  };
}

// 格式化大小
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function main() {
  // 遍历 skills 目录
  const skillsDirs = fs.readdirSync(SKILLS_DIR).filter(name => {
    const stat = fs.statSync(path.join(SKILLS_DIR, name));
    return stat.isDirectory() && !name.startsWith('.') && name !== 'README.md';
  });

  let totalFiles = 0;
  let totalCodeLines = 0;
  let totalSize = 0;

  for (const skillName of skillsDirs) {
    const skillPath = path.join(SKILLS_DIR, skillName);
    const files = getAllFiles(skillPath);
    
    let skillFiles = 0;
    let skillLines = 0;
    let skillSize = 0;
    
    for (const file of files) {
      const ext = path.extname(file).toLowerCase();
      const content = fs.readFileSync(file, 'utf-8');
      const size = fs.statSync(file).size;
      
      skillFiles++;
      skillSize += size;
      totalFiles++;
      totalSize += size;
      
      if (ext === '.py' || ext === '.js') {
        const codeLines = countCodeLines(content, ext);
        skillLines += codeLines;
        totalCodeLines += codeLines;
        
        if (EXT_STATS[ext]) {
          EXT_STATS[ext].count++;
          EXT_STATS[ext].lines += codeLines;
        }
      } else if (ext === '.md') {
        EXT_STATS['.md'].count++;
      } else {
        EXT_STATS.other.count++;
      }
    }
    
    if (skillFiles > 0) {
      skills.push({
        name: skillName,
        files: skillFiles,
        lines: skillLines,
        size: skillSize
      });
    }
  }

  skills.sort((a, b) => b.lines - a.lines);

  // 获取 GitHub 统计
  console.log('[正在获取 GitHub 统计...]');
  const ghStats = await getGitHubStats();
  
  // 输出报告
  console.log(`
# 📊 Skills 工作统计报告

## 总体概况
- **技能数量**: ${skills.length} 个
- **总文件数**: ${totalFiles} 个
- **总代码行数**: ${totalCodeLines.toLocaleString()} 行
- **总大小**: ${formatSize(totalSize)}
${ghStats ? `
## GitHub 提交统计（最近7天）
- **提交次数**: ${ghStats.commitCount} 次
- **PR 数量**: ${ghStats.prCount} 个
- **代码增行**: +${ghStats.additions.toLocaleString()}
- **代码删行**: -${ghStats.deletions.toLocaleString()}
- **净变化**: ${ghStats.netChanges >= 0 ? '+' : ''}${ghStats.netChanges.toLocaleString()}
- **活跃天数**: ${ghStats.daysWithCommits} 天` : ''}
## 文件类型分布
| 类型 | 文件数 | 代码行数 |
|------|--------|---------|
| Python (.py) | ${EXT_STATS['.py'].count} | ${EXT_STATS['.py'].lines.toLocaleString()} |
| JavaScript (.js) | ${EXT_STATS['.js'].count} | ${EXT_STATS['.js'].lines.toLocaleString()} |
| Markdown (.md) | ${EXT_STATS['.md'].count} | - |
| 其他 | ${EXT_STATS.other.count} | - |

## 技能列表（按代码行数排序）
| 排名 | 技能名称 | 文件数 | 代码行数 | 大小 |
|------|---------|--------|---------|------|
${skills.map((s, i) => `| ${i + 1} | ${s.name} | ${s.files} | ${s.lines.toLocaleString()} | ${formatSize(s.size)} |`).join('\n')}
`);

  // 写入日志
  const today = new Date().toISOString().slice(0, 10);
  const logPath = path.join(__dirname, '..', '..', 'logs', 'stats', `stats-${today}.md`);
  const logDir = path.dirname(logPath);
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  let ghStatsStr = '';
  if (ghStats) {
    ghStatsStr = `
## GitHub 提交统计（最近7天）
- 提交次数: ${ghStats.commitCount} 次
- PR 数量: ${ghStats.prCount} 个
- 代码增行: +${ghStats.additions}
- 代码删行: -${ghStats.deletions}
- 净变化: ${ghStats.netChanges}
- 活跃天数: ${ghStats.daysWithCommits} 天`;
  }

  fs.writeFileSync(logPath, `# 代码统计 - ${today}

- 技能数量: ${skills.length}
- 总文件数: ${totalFiles}
- 总代码行数: ${totalCodeLines}
- 总大小: ${formatSize(totalSize)}
${ghStatsStr}
`);

  console.log(`\n[统计已保存到: ${logPath}]`);
}

main().catch(console.error);
