#!/usr/bin/env node
/**
 * 一键提交脚本
 * 功能：写工作日志 → 写入记忆 → 同步GitHub
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const WORKSPACE = path.join(__dirname, '..', '..');
const LOGS_DIR = path.join(WORKSPACE, 'logs', 'daily');
const MEMORY_FILE = path.join(WORKSPACE, 'MEMORY.md');
const MEMORY_DIR = path.join(WORKSPACE, 'memory');

function log(message) {
  console.log(`[一键提交] ${message}`);
}

function getTodayLogs() {
  // 获取今天的日志文件
  const today = new Date().toISOString().slice(0, 10);
  const files = fs.readdirSync(LOGS_DIR).filter(f => f.startsWith(today) && f.endsWith('.md'));
  return files.map(f => {
    const content = fs.readFileSync(path.join(LOGS_DIR, f), 'utf-8');
    return { filename: f, content };
  });
}

function summarizeLogs(logs) {
  // 简单总结：从日志中提取任务、问题、经验
  const tasks = [];
  const problems = [];
  const experiences = [];

  logs.forEach(log => {
    // 提取任务（## 完成的任务 下的内容）
    const taskMatch = log.content.match(/### 任务\d+：[^\n]+/g);
    if (taskMatch) {
      tasks.push(...taskMatch.map(t => t.replace(/### 任务\d+：/, '')));
    }
    
    // 提取问题
    const probMatch = log.content.match(/\| 问题\d+ \|[^|]+ \|/g);
    if (probMatch) {
      problems.push(...probMatch.map(p => p.split('|')[1]?.trim()).filter(Boolean));
    }
  });

  return { tasks, problems, experiences };
}

function updateMemory(summary) {
  const today = new Date().toISOString().slice(0, 10);
  const memoryFile = path.join(MEMORY_DIR, `${today}.md`);
  
  // 确保 memory 目录存在
  if (!fs.existsSync(MEMORY_DIR)) {
    fs.mkdirSync(MEMORY_DIR, { recursive: true });
  }

  let content = '';
  if (fs.existsSync(memoryFile)) {
    content = fs.readFileSync(memoryFile, 'utf-8');
  }

  // 添加今日总结
  const summaryText = `
## 今日总结 (${today})

### 完成的任务
${summary.tasks.map(t => `- ${t}`).join('\n') || '- 无'}

### 遇到的问题
${summary.problems.map(p => `- ${p}`).join('\n') || '- 无'}

### 经验教训
${summary.experiences.map(e => `- ${e}`).join('\n') || '- 无'}
`;

  // 如果文件已存在，追加；否则创建
  if (content) {
    content += '\n' + summaryText;
  } else {
    content = `# 工作日志 - ${today}\n` + summaryText;
  }

  fs.writeFileSync(memoryFile, content, 'utf-8');
  log(`记忆已更新: ${memoryFile}`);
}

function gitCommitAndPush() {
  try {
    // 添加所有更改
    execSync('git add -A', { cwd: WORKSPACE, stdio: 'pipe' });
    
    // 获取今天日期作为 commit 消息
    const today = new Date().toISOString().slice(0, 10);
    const commitMsg = `docs: 工作日志 ${today}`;
    
    // 提交
    execSync(`git commit -m "${commitMsg}"`, { cwd: WORKSPACE, stdio: 'pipe' });
    
    // 推送
    execSync('git push origin main', { cwd: WORKSPACE, stdio: 'pipe' });
    
    log('GitHub 已同步');
    return true;
  } catch (e) {
    log(`Git 操作失败: ${e.message}`);
    return false;
  }
}

async function main() {
  console.log('================================');
  console.log('[ 一键提交 ]');
  console.log('================================\n');

  // 第1步：检查是否有新日志
  log('检查工作日志...');
  const logs = getTodayLogs();
  
  if (logs.length === 0) {
    log('警告: 没有找到今日日志文件');
    log('请先通过 "记录工作日志" 创建日志\n');
  } else {
    log(`找到 ${logs.length} 个日志文件`);
    
    // 第2步：总结并写入记忆
    log('总结并写入记忆...');
    const summary = summarizeLogs(logs);
    updateMemory(summary);
  }

  // 第3步：Git 同步
  log('同步 GitHub...');
  const gitOk = gitCommitAndPush();

  console.log('\n================================');
  console.log('[ 一键提交完成 ]');
  console.log('================================');
  console.log(`1. 工作日志: ${logs.length} 个文件`);
  console.log(`2. 记忆已更新`);
  console.log(`3. GitHub: ${gitOk ? '已同步' : '失败'}`);
}

main().catch(console.error);
