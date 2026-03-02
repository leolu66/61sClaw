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
  
  // 获取会话时间
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0];
  const timeStr = now.toTimeString().slice(0, 5);
  
  // 扫描当天已有日志
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
  const logFile = path.join(LOGS_DIR, `${dateStr}-${seq}-TODO任务优化.md`);
  
  // 读取最近的任务数据作为日志内容
  const tasksFile = path.join(WORKSPACE, 'skills/todo-manager/data/tasks.json');
  let tasksInfo = '';
  try {
    const tasksData = JSON.parse(fs.readFileSync(tasksFile, 'utf8'));
    const pending = tasksData.tasks.filter(t => t.status === 'pending');
    const completed = tasksData.tasks.filter(t => t.status === 'completed');
    tasksInfo = `
## 任务变更

- 新增待办: ${pending.length} 个
- 完成任务: ${completed.length} 个
`;
  } catch (e) {
    tasksInfo = '';
  }
  
  const logContent = `# 工作日志 #${seq}

## 基本信息

| 项目 | 内容 |
|------|------|
| 日志编号 | #${seq} |
| 日期 | ${dateStr} |
| 时间 | ${timeStr} |

## 工作内容

- 优化待办任务技能：
  - 增加年度任务类型（无提醒）
  - 增加评论功能
  - 优化快速编号（1-100，完成/取消回收）
- 创建快速提交技能

${tasksInfo}

## 备注

- 待办任务支持通过编号快速操作

---
*日志生成时间：${now.toISOString()}*
`;
  
  fs.writeFileSync(logFile, logContent, 'utf8');
  console.log(`     已写入: ${logFile}`);
  
  return logFile;
}

/**
 * 2. 提取重要内容到记忆
 */
function extractToMemory(logFile) {
  console.log('[2/3] 提取重要内容到记忆...');
  
  const logContent = fs.readFileSync(logFile, 'utf8');
  
  // 提取关键内容
  const points = [];
  
  // 从日志中提取要点
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
  
  // 读取现有 MEMORY.md
  let memoryContent = '';
  try {
    memoryContent = fs.readFileSync(MEMORY_FILE, 'utf8');
  } catch (e) {
    memoryContent = '# MEMORY.md - 长期记忆\n\n';
  }
  
  // 添加新内容到事件记录
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0].replace('2026-', '');
  const newSection = `
### ${dateStr} | 待办任务技能优化

${points.join('\n')}
`;
  
  // 插入到"事件记录"部分之后
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
  
  try {
    // 检查 skills 目录修改状态
    execSync('git status --porcelain', { cwd: workspace, stdio: 'pipe' });
  } catch (e) {
    // 没有修改
    console.log('     skills 目录无修改，跳过同步');
    return;
  }
  
  // 获取修改的文件列表
  const status = execSync('git status --porcelain skills/', { cwd: workspace, encoding: 'utf8' });
  
  if (!status.trim()) {
    console.log('     skills 目录无修改，跳过同步');
    return;
  }
  
  console.log('     检测到 skills 修改:', status.trim());
  
  // 创建临时分支
  const branchName = `quick-submit-${Date.now()}`;
  execSync(`git checkout -b ${branchName}`, { cwd: workspace });
  
  // 添加修改
  execSync('git add skills/', { cwd: workspace });
  
  // 提交
  const commitMsg = `优化待办任务技能：增加年度任务、评论功能、快速编号`;
  execSync(`git commit -m "${commitMsg}"`, { cwd: workspace });
  
  // 推送到远程
  execSync(`git push -u origin ${branchName}`, { cwd: workspace });
  
  // 创建 PR
  try {
    execSync(`gh pr create --title "${commitMsg}" --body "自动通过快速提交技能创建" --base main`, { 
      cwd: workspace,
      stdio: 'pipe'
    });
    console.log('     PR 已创建');
  } catch (e) {
    // 尝试用 git push 方式
    console.log('     已推送到远程分支:', branchName);
    console.log('     请手动创建 PR');
  }
  
  // 切回 main
  execSync('git checkout main', { cwd: workspace });
}

/**
 * 主函数
 */
function main() {
  console.log('='.repeat(50));
  console.log('Quick Submit 开始执行');
  console.log('='.repeat(50));
  
  try {
    // 1. 写工作日志
    const logFile = writeWorkLog();
    
    // 2. 提取到记忆
    extractToMemory(logFile);
    
    // 3. Git 同步
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
