/**
 * coordinator-cli.js - 多智能体协调器命令行工具
 * 
 * 用法:
 *   node coordinator-cli.js start     # 启动扫描
 *   node coordinator-cli.js stop      # 停止扫描
 *   node coordinator-cli.js status    # 查看状态
 *   node coordinator-cli.js restart   # 重启扫描
 *   node coordinator-cli.js reload    # 热重载配置
 * 
 * 状态文件: workspace-main/config/coordinator.status
 * PID 文件:  workspace-main/config/coordinator.pid
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { ConfigLoader } = require('./src/config/config-loader');

const CONFIG_DIR = path.resolve(__dirname, '..', '..', 'config');
const PID_FILE = path.join(CONFIG_DIR, 'coordinator.pid');
const STATUS_FILE = path.join(CONFIG_DIR, 'coordinator.status');
const LOG_FILE = path.join('D:\\projects\\logs', 'coordinator-cli.log');

/**
 * 日志输出
 */
function log(level, msg) {
  const timestamp = new Date().toISOString();
  const line = `[${timestamp}] [${level}] ${msg}`;
  console.log(line);
  
  try {
    const logsDir = path.dirname(LOG_FILE);
    if (!fs.existsSync(logsDir)) {
      fs.mkdirSync(logsDir, { recursive: true });
    }
    fs.appendFileSync(LOG_FILE, line + '\n');
  } catch (e) {}
}

/**
 * 获取配置
 */
function getConfig() {
  try {
    const loader = new ConfigLoader();
    return loader.getNodeConfig();
  } catch (error) {
    log('ERROR', `加载配置失败: ${error.message}`);
    process.exit(1);
  }
}

/**
 * 保存 PID
 */
function savePid(pid, nodeType) {
  const data = {
    pid,
    nodeType,
    startTime: Date.now(),
    updatedAt: Date.now()
  };
  fs.writeFileSync(PID_FILE, JSON.stringify(data, null, 2));
}

/**
 * 读取 PID
 */
function readPid() {
  if (!fs.existsSync(PID_FILE)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(PID_FILE, 'utf-8'));
  } catch (e) {
    return null;
  }
}

/**
 * 清除 PID
 */
function clearPid() {
  if (fs.existsSync(PID_FILE)) {
    fs.unlinkSync(PID_FILE);
  }
}

/**
 * 更新状态文件
 */
function updateStatus(status, extra = {}) {
  const data = {
    status,  // running, stopped, error, reloading
    timestamp: Date.now(),
    ...extra
  };
  fs.writeFileSync(STATUS_FILE, JSON.stringify(data, null, 2));
}

/**
 * 读取状态文件
 */
function readStatus() {
  if (!fs.existsSync(STATUS_FILE)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(STATUS_FILE, 'utf-8'));
  } catch (e) {
    return null;
  }
}

/**
 * 清除状态文件
 */
function clearStatus() {
  if (fs.existsSync(STATUS_FILE)) {
    fs.unlinkSync(STATUS_FILE);
  }
}

/**
 * 检查进程是否存在
 */
function isProcessRunning(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * 启动扫描
 */
function start() {
  const pidInfo = readPid();
  
  if (pidInfo && isProcessRunning(pidInfo.pid)) {
    log('WARN', `扫描器已在运行 (PID: ${pidInfo.pid}, 类型: ${pidInfo.nodeType})`);
    updateStatus('running', { pid: pidInfo.pid, nodeType: pidInfo.nodeType });
    return;
  }

  const config = getConfig();
  log('INFO', `启动 ${config.nodeType} 节点扫描器...`);

  // 更新状态为 starting
  updateStatus('starting', { nodeType: config.nodeType });

  // 后台启动守护进程
  const script = path.join(__dirname, 'coordinator-daemon.js');
  const child = spawn('node', [script], {
    detached: true,
    stdio: 'ignore',
    windowsHide: true
  });

  child.unref();
  
  savePid(child.pid, config.nodeType);
  
  // 等待守护进程启动完成
  setTimeout(() => {
    const status = readStatus();
    if (status && status.status === 'running') {
      log('INFO', `扫描器已启动 (PID: ${child.pid}, 状态: ${status.status})`);
    } else {
      log('WARN', `扫描器进程已启动 (PID: ${child.pid})，但状态未知`);
    }
  }, 1000);
}

/**
 * 停止扫描
 */
function stop() {
  const pidInfo = readPid();
  
  if (!pidInfo) {
    log('WARN', '未找到运行中的扫描器');
    updateStatus('stopped', { reason: 'no_pid_file' });
    return;
  }

  if (!isProcessRunning(pidInfo.pid)) {
    log('WARN', `进程 ${pidInfo.pid} 已不存在`);
    clearPid();
    updateStatus('stopped', { reason: 'process_not_found' });
    return;
  }

  log('INFO', `停止扫描器 (PID: ${pidInfo.pid})...`);
  updateStatus('stopping', { pid: pidInfo.pid });
  
  try {
    process.kill(pidInfo.pid, 'SIGTERM');
    
    // 等待进程退出
    let attempts = 0;
    const checkInterval = setInterval(() => {
      attempts++;
      if (!isProcessRunning(pidInfo.pid) || attempts > 10) {
        clearInterval(checkInterval);
        
        if (isProcessRunning(pidInfo.pid)) {
          log('WARN', '进程未能正常退出，强制终止');
          try {
            process.kill(pidInfo.pid, 'SIGKILL');
          } catch (e) {}
        }
        
        clearPid();
        updateStatus('stopped', { pid: pidInfo.pid, stoppedAt: Date.now() });
        log('INFO', '扫描器已停止');
      }
    }, 500);
  } catch (error) {
    log('ERROR', `停止失败: ${error.message}`);
    updateStatus('error', { error: error.message });
  }
}

/**
 * 查看状态
 */
function status() {
  const config = getConfig();
  const pidInfo = readPid();
  const scannerStatus = readStatus();
  
  console.log('\n========================================');
  console.log('多智能体协调器状态');
  console.log('========================================');
  console.log(`节点类型: ${config.nodeType}`);
  console.log(`节点ID: ${config.nodeId}`);
  
  if (config.nodeType === 'master') {
    console.log(`结果扫描间隔: ${config.resultScanInterval}ms`);
    console.log(`心跳检查间隔: ${config.heartbeatCheckInterval}ms`);
  } else {
    console.log(`任务扫描间隔: ${config.taskScanInterval}ms`);
    console.log(`心跳间隔: ${config.heartbeatInterval}ms`);
    console.log(`最大并发任务: ${config.maxConcurrentTasks}`);
  }
  
  console.log('\n--- 运行状态 ---');
  
  if (pidInfo && isProcessRunning(pidInfo.pid)) {
    const uptime = Math.floor((Date.now() - pidInfo.startTime) / 1000);
    const mins = Math.floor(uptime / 60);
    const secs = uptime % 60;
    
    console.log(`运行状态: [运行中]`);
    console.log(`进程ID: ${pidInfo.pid}`);
    console.log(`运行时间: ${mins}分${secs}秒`);
    
    if (scannerStatus) {
      console.log(`扫描器状态: ${scannerStatus.status}`);
      if (scannerStatus.lastScan) {
        console.log(`最后扫描: ${new Date(scannerStatus.lastScan).toLocaleString()}`);
      }
      if (scannerStatus.tasksProcessed !== undefined) {
        console.log(`已处理任务: ${scannerStatus.tasksProcessed}`);
      }
    }
  } else {
    console.log(`运行状态: [已停止]`);
    if (scannerStatus && scannerStatus.stoppedAt) {
      console.log(`停止时间: ${new Date(scannerStatus.stoppedAt).toLocaleString()}`);
    }
    if (pidInfo) {
      clearPid();
    }
  }
  
  console.log('========================================\n');
}

/**
 * 热重载配置
 */
function reload() {
  const pidInfo = readPid();
  
  if (!pidInfo || !isProcessRunning(pidInfo.pid)) {
    log('WARN', '扫描器未运行，无需重载');
    return;
  }

  log('INFO', '发送配置重载信号...');
  updateStatus('reloading', { pid: pidInfo.pid });
  
  try {
    // 发送 SIGUSR1 信号触发重载（Windows 不支持，使用文件标记）
    const reloadFlag = path.join(CONFIG_DIR, '.reload');
    fs.writeFileSync(reloadFlag, Date.now().toString());
    
    log('INFO', '配置重载信号已发送');
    
    // 清理标记文件
    setTimeout(() => {
      if (fs.existsSync(reloadFlag)) {
        fs.unlinkSync(reloadFlag);
      }
    }, 5000);
  } catch (error) {
    log('ERROR', `重载失败: ${error.message}`);
    updateStatus('error', { error: error.message });
  }
}

/**
 * 重启扫描
 */
function restart() {
  log('INFO', '重启扫描器...');
  stop();
  setTimeout(start, 1000);
}

/**
 * 主入口
 */
function main() {
  const command = process.argv[2] || 'status';
  
  switch (command) {
    case 'start':
      start();
      break;
    case 'stop':
      stop();
      break;
    case 'status':
      status();
      break;
    case 'restart':
      restart();
      break;
    case 'reload':
      reload();
      break;
    default:
      console.log('用法: node coordinator-cli.js [start|stop|status|restart|reload]');
      process.exit(1);
  }
}

main();
