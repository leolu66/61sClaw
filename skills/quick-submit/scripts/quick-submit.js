#!/usr/bin/env node
/**
 * Quick Submit - 快速提交技能
 * 一键完成：写日志 → 提取记忆 → Git同步
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const WORKSPACE = path.join(__dirname, '../../..');
const LOGS_DIR = path.join(WORKSPACE, 'logs/daily');
const MEMORY_FILE = path.join(WORKSPACE, 'MEMORY.md');
const SKILLS_DIR = path.join(WORKSPACE, 'skills');

/**
 * 1. 写工作日志
 */
function writeWorkLog() {
  console.log('[1/3] 写工作日志...');
  
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0];
  const timeStr = now.toTimeString().slice(0, 5);
  
  let maxSeq = 0;
  try {
    const files = fs.readdirSync(LOGS_DIR);
    files.forEach(f => {
      if (f.startsWith(dateStr) && f.endsWith('.md')) {
        const match = f.match(/-(\d+)-/);
        if (match) {
          maxSeq = Math.max(maxSeq, parseInt(match[1]));
        }
      }
    });
  } catch (e) {
    fs.mkdirSync(LOGS_DIR, { recursive: true });
  }
  
  const seq = (maxSeq + 1).toString().padStart(3, '0');
  const logFile = path.join(LOGS_DIR, `${dateStr}-${seq}-会话任务处理.md`);
  
  const logContent = `# 工作日志 #${seq}

## 基本信息

| 项目 | 内容 |
|------|------|
| 日志编号 | #${seq} |
| 日期 | ${dateStr} |
| 时间 | ${timeStr} |

## 工作内容

- 处理待办任务：
  - 查询余额、播放音乐
  - 增加年度任务类型（无提醒）
  - 增加评论功能
  - 优化快速编号
  - 创建快速提交技能

## 备注

- 本次会话完成

---
*日志生成时间：${now.toISOString()}*
`;
  
  fs.writeFileSync(logFile, logContent, 'utf8');
  console.log(`     已写入: ${path.basename(logFile)}`);
  
  return logFile;
}

/**
 * 2. 提取重要内容到记忆
 */
function extractToMemory(logFile) {
  console.log('[2/3] 提取重要内容到记忆...');
  
  const logContent = fs.readFileSync(logFile, 'utf8');
  
  const points = [];
  if (logContent.includes('年度任务')) {
    points.push('- 年度任务（超过365天）不提醒，只在列表显示');
  }
  if (logContent.includes('评论功能')) {
    points.push('- 任务评论功能：完成任务/取消任务时可添加评论');
  }
  if (logContent.includes('快速编号')) {
    points.push('- 待办任务快速编号1-100，完成/取消后回收');
  }
  if (logContent.includes('快速提交')) {
    points.push('- 新增快速提交技能：一键完成写日志、提取记忆、Git同步');
  }
  
  if (points.length === 0) {
    console.log('     无新内容需要记录');
    return;
  }
  
  let memoryContent = '';
  try {
    memoryContent = fs.readFileSync(MEMORY_FILE, 'utf8');
  } catch (e) {
    memoryContent = '# MEMORY.md - 长期记忆\n\n';
  }
  
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0].replace('2026-', '');
  const newSection = `
### ${dateStr} | 会话任务处理

${points.join('\n')}
`;
  
  const insertMarker = '## 事件记录';
  const insertIndex = memoryContent.indexOf(insertMarker);
  
  if (insertIndex !== -1) {
    const before = memoryContent.slice(0, insertIndex + insertMarker.length);
    const after = memoryContent.slice(insertIndex + insertMarker.length);
    memoryContent = before + newSection + after;
  } else {
    memoryContent += newSection;
  }
  
  fs.writeFileSync(MEMORY_FILE, memoryContent, 'utf8');
  console.log('     已更新 MEMORY.md');
}

/**
 * 3. Git PR 同步
 */
function gitSync() {
  console.log('[3/3] Git 同步...');
  
  const workspace = WORKSPACE;
  
  // 检查 skills 目录修改
  let status = '';
  try {
    status = execSync('git status --porcelain skills/', { cwd: workspace, encoding: 'utf8' });
  } catch (e) {
    console.log('     Git 状态检查失败，跳过同步');
    return;
  }
  
  if (!status.trim()) {
    console.log('     skills 目录无修改，跳过同步');
    return;
  }
  
  console.log('     检测到 skills 修改');
  
  // 创建临时分支
  const branchName = `quick-submit-${Date.now()}`;
  execSync(`git checkout -b ${branchName}`, { cwd: workspace });
  
  // 添加并提交
  execSync('git add skills/', { cwd: workspace });
  const commitMsg = `更新技能`;
  execSync(`git commit -m "${commitMsg}"`, { cwd: workspace });
  
  // 推送
  execSync(`git push -u origin ${branchName}`, { cwd: workspace });
  
  console.log(`     已推送到分支: ${branchName}`);
  console.log('     PR 链接: https://github.com/leolu66/61sClaw/pull/new/' + branchName);
  
  // 切回 main
  execSync('git checkout -f main', { cwd: workspace });
}

/**
 * 主函数
 */
function main() {
  console.log('='.repeat(50));
  console.log('Quick Submit 开始执行');
  console.log('='.repeat(50));
  
  try {
    const logFile = writeWorkLog();
    extractToMemory(logFile);
    gitSync();
    
    console.log('='.repeat(50));
    console.log('✅ 提交完成！');
    console.log('='.repeat(50));
  } catch (e) {
    console.error('❌ 提交失败:', e.message);
    process.exit(1);
  }
}

main();
