// ============================================
// 子 Agent 脚本生成（简化版）
// ============================================

function generateWorkerScript(planId, planTitle, outputDir, claudeWorkspace) {
  const simpleInstruction = `执行任务: ${planTitle}
任务ID: ${planId}
输出目录: ${outputDir}`;

  return `const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const planId = '${planId}';
const claudeWorkspace = '${claudeWorkspace}';
const claudeOutputDir = path.join(claudeWorkspace, 'task-' + planId);
const sharedOutputDir = '${outputDir}';

console.log('[子Agent] 启动...');
console.log('[子Agent] 任务:', planId);

try {
  // 确保目录存在
  if (!fs.existsSync(claudeOutputDir)) {
    fs.mkdirSync(claudeOutputDir, { recursive: true });
  }
  if (!fs.existsSync(sharedOutputDir)) {
    fs.mkdirSync(sharedOutputDir, { recursive: true });
  }
  
  // 调用 Claude Code（简化指令）
  const instruction = "${simpleInstruction.replace(/"/g, '\\"').replace(/\n/g, '\\n')}";
  const cmd = 'claude -p "' + instruction + '" --permission-mode acceptEdits --output-format json --max-turns 15';
  
  console.log('[子Agent] 调用 Claude Code...');
  const output = execSync(cmd, { encoding: 'utf-8', timeout: 300000, cwd: claudeWorkspace });
  console.log('[子Agent] Claude Code 完成');
  
  // 等待文件生成
  const start = Date.now();
  while (Date.now() - start < 15000) {}
  
  // 查找生成的文件
  const files = fs.readdirSync(claudeOutputDir);
  const mdFiles = files.filter(f => f.endsWith('.md'));
  const hasResult = fs.existsSync(path.join(claudeOutputDir, 'result.json'));
  
  if (hasResult || mdFiles.length > 0) {
    // 复制文件
    if (hasResult) {
      fs.copyFileSync(path.join(claudeOutputDir, 'result.json'), path.join(sharedOutputDir, 'result.json'));
    }
    mdFiles.forEach(f => {
      fs.copyFileSync(path.join(claudeOutputDir, f), path.join(sharedOutputDir, f));
    });
    
    // 标记完成
    fs.writeFileSync(path.join(sharedOutputDir, '.task-completed'), JSON.stringify({
      planId: planId, completedAt: new Date().toISOString(), status: 'success'
    }));
    console.log('[子Agent] 完成');
  } else {
    throw new Error('未生成文件');
  }
} catch (e) {
  console.error('[子Agent] 错误:', e.message);
  fs.writeFileSync(path.join(sharedOutputDir, '.task-failed'), JSON.stringify({
    planId: planId, failedAt: new Date().toISOString(), reason: e.message
  }));
}
`;
}

module.exports = { generateWorkerScript };
