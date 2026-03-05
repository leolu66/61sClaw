
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const planId = 'plan-1772719054700';
const claudeWorkspace = 'D:\projects\workspace\node-claude';
const claudeOutputDir = 'D:\projects\workspace\node-claude\task-plan-1772719054700';
const sharedOutputDir = 'D:\projects\workspace\shared\output\task-billing-1772719058850';
const taskInstruction = `# [TASK] 协同工作任务单

## 任务信息
- 任务ID: plan-1772719054700
- 发送者: kimi
- 发送时间: 2026/3/5 21:57:38
- 优先级: high

## 任务指令
请分析账单文件并生成专业报告：

1. 读取文件: billing_2026-02-09_2026-03-04.csv（当前目录）
2. 分析账单数据，计算：
   - 总消费金额
   - 日均消费
   - 总请求次数
   - 总Token数
   - 使用的模型数量
   - 按模型统计消费排行
   - 按日期统计消费趋势
   - 按提供商统计消费分布
3. 生成 Markdown 格式的完整报告

## 输出要求
- 输出目录: D:\projects\workspace\node-claude\task-plan-1772719054700
- 报告文件: D:\projects\workspace\node-claude\task-plan-1772719054700\billing_report.md
- 结果文件: D:\projects\workspace\node-claude\task-plan-1772719054700\result.json

## result.json 格式
{
  "taskId": "plan-1772719054700",
  "status": "success/failed",
  "output": "执行结果摘要",
  "outputFiles": ["billing_report.md"],
  "executedAt": "ISO时间戳"
}

请使用 Read 工具读取 CSV 文件，然后用 Write 工具写入报告文件。`;

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
