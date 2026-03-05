/**
 * index.js - Multi-Agent Coordinator 技能主入口
 * 处理用户指令，调用 CLI 工具控制扫描器
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SKILL_DIR = __dirname;
const CONFIG_DIR = path.join(SKILL_DIR, '..', '..', 'config');
const PID_FILE = path.join(CONFIG_DIR, 'coordinator.pid');
const STATUS_FILE = path.join(CONFIG_DIR, 'coordinator.status');

/**
 * 执行 CLI 命令
 */
function runCli(command) {
  const cliPath = path.join(SKILL_DIR, 'coordinator-cli.js');
  try {
    const output = execSync(`node "${cliPath}" ${command}`, {
      encoding: 'utf-8',
      timeout: 10000
    });
    return { success: true, output: output.trim() };
  } catch (error) {
    return { 
      success: false, 
      output: error.stdout?.trim() || '',
      error: error.stderr?.trim() || error.message 
    };
  }
}

/**
 * 读取状态文件
 */
function readStatus() {
  try {
    if (!fs.existsSync(STATUS_FILE)) {
      return null;
    }
    return JSON.parse(fs.readFileSync(STATUS_FILE, 'utf-8'));
  } catch (e) {
    return null;
  }
}

/**
 * 读取 PID 文件
 */
function readPid() {
  try {
    if (!fs.existsSync(PID_FILE)) {
      return null;
    }
    return JSON.parse(fs.readFileSync(PID_FILE, 'utf-8'));
  } catch (e) {
    return null;
  }
}

/**
 * 启动任务扫描
 */
function startScan() {
  console.log('[技能] 正在启动任务扫描...');
  
  const result = runCli('start');
  
  if (!result.success) {
    return {
      success: false,
      message: `启动失败: ${result.error}`
    };
  }
  
  // 等待并检查状态
  setTimeout(() => {
    const status = readStatus();
    const pidInfo = readPid();
    
    if (status && status.status === 'running') {
      console.log(`[技能] 扫描器已启动`);
      console.log(`  - 节点类型: ${status.nodeType || pidInfo?.nodeType}`);
      console.log(`  - 进程ID: ${status.pid}`);
      console.log(`  - 已处理任务: ${status.tasksProcessed || 0}`);
    } else {
      console.log(`[技能] 扫描器启动中，请稍后查看状态`);
    }
  }, 1500);
  
  return {
    success: true,
    message: '扫描器启动指令已发送',
    output: result.output
  };
}

/**
 * 停止任务扫描
 */
function stopScan() {
  console.log('[技能] 正在停止任务扫描...');
  
  const pidInfo = readPid();
  if (!pidInfo) {
    return {
      success: false,
      message: '扫描器未运行'
    };
  }
  
  const result = runCli('stop');
  
  // 检查是否已停止
  setTimeout(() => {
    const newPidInfo = readPid();
    if (!newPidInfo) {
      console.log('[技能] 扫描器已停止');
    }
  }, 1000);
  
  return {
    success: result.success,
    message: result.success ? '扫描器停止指令已发送' : `停止失败: ${result.error}`,
    output: result.output
  };
}

/**
 * 查看扫描状态
 */
function getStatus() {
  const result = runCli('status');
  
  // 同时读取详细状态
  const status = readStatus();
  const pidInfo = readPid();
  
  let detail = '';
  if (status) {
    const uptime = status.startTime ? Math.floor((Date.now() - status.startTime) / 1000) : 0;
    const mins = Math.floor(uptime / 60);
    const secs = uptime % 60;
    
    detail = `
详细状态:
  - 运行状态: ${status.status}
  - 进程ID: ${status.pid || pidInfo?.pid || '未知'}
  - 运行时间: ${mins}分${secs}秒
  - 已处理任务: ${status.tasksProcessed || 0}
  - 错误次数: ${status.errors || 0}
  - 最后扫描: ${status.lastScan ? new Date(status.lastScan).toLocaleString() : '无'}
  - 最后更新: ${new Date(status.timestamp).toLocaleString()}`;
  }
  
  return {
    success: true,
    message: result.output + detail,
    status: status,
    pidInfo: pidInfo
  };
}

/**
 * 重载配置
 */
function reloadConfig() {
  console.log('[技能] 正在重载配置...');
  
  const pidInfo = readPid();
  if (!pidInfo) {
    return {
      success: false,
      message: '扫描器未运行，无需重载'
    };
  }
  
  const result = runCli('reload');
  
  // 检查重载状态
  setTimeout(() => {
    const status = readStatus();
    if (status && status.status === 'running' && status.reloadedAt) {
      console.log(`[技能] 配置已重载于 ${new Date(status.reloadedAt).toLocaleString()}`);
    }
  }, 2000);
  
  return {
    success: result.success,
    message: result.success ? '配置重载指令已发送' : `重载失败: ${result.error}`,
    output: result.output
  };
}

/**
 * 主处理函数
 * @param {string} command - 用户指令
 * @returns {Object} 处理结果
 */
function handleCommand(command) {
  const cmd = command.toLowerCase().trim();
  
  // 启动扫描
  if (cmd.includes('启动') && cmd.includes('扫描')) {
    return startScan();
  }
  
  // 停止扫描
  if (cmd.includes('停止') && cmd.includes('扫描')) {
    return stopScan();
  }
  
  // 查看状态
  if (cmd.includes('查看') && cmd.includes('状态')) {
    return getStatus();
  }
  
  // 重载配置
  if (cmd.includes('重载') || (cmd.includes(' reload'))) {
    return reloadConfig();
  }
  
  return {
    success: false,
    message: '未知指令，支持的指令: 启动任务扫描、停止任务扫描、查看扫描状态、重载扫描配置'
  };
}

// 如果直接运行，处理命令行参数
if (require.main === module) {
  const command = process.argv[2] || 'status';
  const result = handleCommand(command);
  
  console.log('\n========================================');
  console.log('执行结果:', result.success ? '成功' : '失败');
  console.log('消息:', result.message);
  console.log('========================================\n');
  
  process.exit(result.success ? 0 : 1);
}

module.exports = { handleCommand, startScan, stopScan, getStatus, reloadConfig };
