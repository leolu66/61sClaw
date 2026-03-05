const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const planId = process.argv[2] || 'unknown';
const claudeWorkspace = 'D:\\projects\\workspace\\node-claude';

console.log('[子Agent] 启动异步任务处理...');
console.log('[子Agent] 任务ID:', planId);

// 读取任务指令文件
const instructionFile = path.join(claudeWorkspace, `task-${planId}-instruction.txt`);
if (!fs.existsSync(instructionFile)) {
  console.error('[子Agent] ❌ 任务指令文件不存在:', instructionFile);
  process.exit(1);
}

const taskInstruction = fs.readFileSync(instructionFile, 'utf-8');
console.log('[子Agent] ✅ 任务指令已加载');

// 发送任务给 Claude Code
console.log('[子Agent] 📤 正在调用 Claude Code...');
console.log('[子Agent] ⏱️ 这可能需要 1-2 分钟，请耐心等待...');

try {
  // 将指令写入临时文件，避免命令行转义问题
  const tempCmdFile = path.join(claudeWorkspace, `task-${planId}-cmd.txt`);
  fs.writeFileSync(tempCmdFile, taskInstruction, 'utf-8');
  
  // 调用 Claude Code 读取文件
  const claudeCmd = `claude -p "请读取文件: ${tempCmdFile}" --permission-mode acceptEdits --output-format json --max-turns 15`;
  
  const claudeOutput = execSync(claudeCmd, {
    encoding: 'utf-8',
    timeout: 300000,
    cwd: claudeWorkspace
  });
  
  console.log('[子Agent] ✅ Claude Code 调用完成');
  
  // 清理临时文件
  fs.unlinkSync(tempCmdFile);
  
  // 等待文件生成
  console.log('[子Agent] ⏱️ 等待 15 秒让 Claude Code 生成文件...');
  const startWait = Date.now();
  while (Date.now() - startWait < 15000) {
    // 忙等待
  }
  
  // 检查输出目录
  const claudeOutputDir = path.join(claudeWorkspace, `task-${planId}`);
  const sharedOutputDir = path.join('D:\\projects\\workspace\\shared\\output', `task-${planId}`);
  
  // 确保共享目录存在
  if (!fs.existsSync(sharedOutputDir)) {
    fs.mkdirSync(sharedOutputDir, { recursive: true });
  }
  
  // 检查并复制文件
  const claudeResultJsonPath = path.join(claudeOutputDir, 'result.json');
  const claudeReportPath = path.join(claudeOutputDir, 'weather_report.md') || path.join(claudeOutputDir, 'billing_report.md');
  
  let hasResult = false;
  
  if (fs.existsSync(claudeResultJsonPath)) {
    fs.copyFileSync(claudeResultJsonPath, path.join(sharedOutputDir, 'result.json'));
    console.log('[子Agent] ✅ result.json 已复制');
    hasResult = true;
  }
  
  if (fs.existsSync(claudeReportPath)) {
    fs.copyFileSync(claudeReportPath, path.join(sharedOutputDir, path.basename(claudeReportPath)));
    console.log('[子Agent] ✅ 报告文件已复制');
    hasResult = true;
  }
  
  if (hasResult) {
    // 写入完成标记文件
    const completionMarker = path.join(sharedOutputDir, '.task-completed');
    fs.writeFileSync(completionMarker, JSON.stringify({
      planId: planId,
      completedAt: new Date().toISOString(),
      status: 'success'
    }, null, 2));
    
    console.log('[子Agent] ✅ 任务完成标记已创建');
  } else {
    console.error('[子Agent] ❌ Claude Code 未生成文件');
    
    // 写入失败标记
    const failureMarker = path.join(sharedOutputDir, '.task-failed');
    fs.writeFileSync(failureMarker, JSON.stringify({
      planId: planId,
      failedAt: new Date().toISOString(),
      reason: 'Claude Code 未生成文件'
    }, null, 2));
  }
  
} catch (e) {
  console.error('[子Agent] ❌ 执行失败:', e.message);
  
  // 写入失败标记
  const sharedOutputDir = path.join('D:\\projects\\workspace\\shared\\output', `task-${planId}`);
  if (!fs.existsSync(sharedOutputDir)) {
    fs.mkdirSync(sharedOutputDir, { recursive: true });
  }
  const failureMarker = path.join(sharedOutputDir, '.task-failed');
  fs.writeFileSync(failureMarker, JSON.stringify({
    planId: planId,
    failedAt: new Date().toISOString(),
    reason: e.message
  }, null, 2));
}

console.log('[子Agent] 🏁 子 Agent 执行结束');
