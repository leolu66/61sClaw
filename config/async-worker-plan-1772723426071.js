
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const planId = 'plan-1772723426071';
const claudeWorkspace = 'D:\projects\workspace\node-claude';
const claudeOutputDir = 'D:\projects\workspace\node-claude\task-plan-1772723426071';
const sharedOutputDir = 'D:\projects\workspace\shared\output\task-billing-1772723446713';
const taskInstruction = `# [TASK] 协同工作任务单

## 任务信息
- 任务ID: plan-1772723426071
- 发送者: kimi
- 发送时间: 2026/3/5 23:10:46
- 优先级: high

## 任务指令
创建任务 查北京明天天气

请查询北京明天的天气信息，包括：
- 天气状况（晴/阴/雨等）
- 温度范围（最高/最低）
- 风力风向
- 空气质量

生成一份简洁的天气报告。

## 输出要求
- 输出目录: D:\projects\workspace\node-claude\task-plan-1772723426071
- 报告文件: D:\projects\workspace\node-claude\task-plan-1772723426071\weather_report.md
- 结果文件: D:\projects\workspace\node-claude\task-plan-1772723426071\result.json

## result.json 格式
{
  "taskId": "plan-1772723426071",
  "status": "success/failed",
  "output": "执行结果摘要",
  "outputFiles": ["weather_report.md"],
  "executedAt": "ISO时间戳"
}`;

console.log('[子Agent] 启动异步任务处理...');
console.log('[子Agent] 任务ID:', planId);

// 发送任务给 Claude Code
console.log('[子Agent] 📤 正在调用 Claude Code...');
console.log('[子Agent] ⏱️ 这可能需要 1-2 分钟，请耐心等待...');

try {
  const claudeCmd = `claude -p "${taskInstruction.replace(/"/g, '\\"').replace(/
/g, '\\n')}" --permission-mode acceptEdits --output-format json --max-turns 15`;
  
  const claudeOutput = execSync(claudeCmd, {
    encoding: 'utf-8',
    timeout: 300000,
    cwd: claudeWorkspace
  });
  
  console.log('[子Agent] ✅ Claude Code 调用完成');
  
  // 解析结果
  let sendResult;
  try {
    const jsonOutput = JSON.parse(claudeOutput.trim());
    sendResult = {
      success: jsonOutput.subtype === 'success' && !jsonOutput.is_error,
      session_id: jsonOutput.session_id,
      cost_usd: jsonOutput.total_cost_usd,
      duration_ms: jsonOutput.duration_ms
    };
  } catch (e) {
    sendResult = { success: true };
  }
  
  // 等待文件生成
  console.log('[子Agent] ⏱️ 等待 15 秒让 Claude Code 生成文件...');
  const startWait = Date.now();
  while (Date.now() - startWait < 15000) {
    // 忙等待
  }
  
  // 检查并复制文件
  const claudeResultJsonPath = path.join(claudeOutputDir, 'result.json');
  const claudeReportPath = path.join(claudeOutputDir, 'billing_report.md');
  
  if (fs.existsSync(claudeResultJsonPath) && fs.existsSync(claudeReportPath)) {
    // 复制到共享目录
    fs.copyFileSync(claudeResultJsonPath, path.join(sharedOutputDir, 'result.json'));
    fs.copyFileSync(claudeReportPath, path.join(sharedOutputDir, 'billing_report.md'));
    console.log('[子Agent] ✅ 文件已复制到共享目录');
    
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
  const failureMarker = path.join(sharedOutputDir, '.task-failed');
  fs.writeFileSync(failureMarker, JSON.stringify({
    planId: planId,
    failedAt: new Date().toISOString(),
    reason: e.message
  }, null, 2));
}

console.log('[子Agent] 🏁 子 Agent 执行结束');
