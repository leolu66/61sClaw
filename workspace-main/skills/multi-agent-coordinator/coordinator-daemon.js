/**
 * coordinator-daemon.js - 协调器守护进程
 * 在后台运行扫描器，维护状态文件
 */

const fs = require('fs');
const path = require('path');
const { MasterScanner } = require('./src/scanner/master-scanner');
const { WorkerScanner } = require('./src/scanner/worker-scanner');
const { ConfigLoader } = require('./src/config/config-loader');

const CONFIG_DIR = path.resolve(__dirname, '..', '..', 'config');
const STATUS_FILE = path.join(CONFIG_DIR, 'coordinator.status');
const RELOAD_FLAG = path.join(CONFIG_DIR, '.reload');

let scanner = null;
let statusInterval = null;
let reloadCheckInterval = null;
let stats = {
  startTime: Date.now(),
  tasksProcessed: 0,
  lastScan: null,
  errors: 0
};

/**
 * 更新状态文件
 */
function updateStatus(status, extra = {}) {
  const data = {
    status,
    timestamp: Date.now(),
    pid: process.pid,
    ...stats,
    ...extra
  };
  
  try {
    fs.writeFileSync(STATUS_FILE, JSON.stringify(data, null, 2));
  } catch (e) {
    console.error('更新状态文件失败:', e.message);
  }
}

/**
 * 检查重载标记
 */
function checkReload() {
  if (fs.existsSync(RELOAD_FLAG)) {
    console.log('[Daemon] 检测到配置重载信号');
    updateStatus('reloading');
    
    try {
      // 重新加载配置
      if (scanner) {
        const configLoader = new ConfigLoader();
        const newConfig = configLoader.load(true); // 强制重新加载
        console.log('[Daemon] 配置已重载:', newConfig.nodeType);
        
        // 更新扫描器配置
        if (scanner.config) {
          Object.assign(scanner.config, configLoader.getNodeConfig());
        }
      }
      
      updateStatus('running', { reloadedAt: Date.now() });
      console.log('[Daemon] 配置重载完成');
    } catch (error) {
      console.error('[Daemon] 配置重载失败:', error.message);
      updateStatus('error', { error: error.message });
    }
    
    // 删除重载标记
    try {
      fs.unlinkSync(RELOAD_FLAG);
    } catch (e) {}
  }
}

/**
 * 启动扫描器
 */
function startScanner() {
  const configLoader = new ConfigLoader();
  const config = configLoader.getNodeConfig();
  
  console.log(`[Daemon] 启动 ${config.nodeType} 节点扫描器`);
  
  if (config.nodeType === 'master') {
    scanner = new MasterScanner();
    
    // 设置回调
    scanner.setOnResultFound((result, nodeId) => {
      console.log(`[Master] 收到结果: ${result.taskId} from ${nodeId}`);
      stats.tasksProcessed++;
      stats.lastScan = Date.now();
      
      // TODO: 飞书通知
    });
    
    scanner.setOnNodeOffline((nodeId, node) => {
      console.log(`[Master] 节点离线: ${nodeId}`);
      // TODO: 飞书通知
    });
    
  } else {
    scanner = new WorkerScanner();
    
    // 设置任务处理回调
    scanner.setOnTaskFound(async (command, nodeId) => {
      console.log(`[Worker] 执行任务: ${command.taskId}`);
      stats.lastScan = Date.now();
      
      try {
        // TODO: 实际执行任务
        // 这里可以调用 Claude Code 或其他执行逻辑
        
        // 模拟执行成功
        scanner._writeResult(command.taskId, {
          status: 'success',
          output: '任务执行完成',
          files: []
        });
        
        stats.tasksProcessed++;
      } catch (error) {
        console.error(`[Worker] 任务执行失败: ${error.message}`);
        stats.errors++;
        
        scanner._writeResult(command.taskId, {
          status: 'failed',
          output: error.message
        });
      }
    });
  }
  
  scanner.start();
  updateStatus('running', { nodeType: config.nodeType });
  
  // 启动状态更新定时器
  statusInterval = setInterval(() => {
    updateStatus('running');
  }, 30000); // 每30秒更新一次状态文件
  
  // 启动重载检查定时器
  reloadCheckInterval = setInterval(checkReload, 2000); // 每2秒检查重载标记
}

/**
 * 停止扫描器
 */
function stopScanner() {
  console.log('[Daemon] 正在停止...');
  updateStatus('stopping');
  
  if (statusInterval) {
    clearInterval(statusInterval);
    statusInterval = null;
  }
  
  if (reloadCheckInterval) {
    clearInterval(reloadCheckInterval);
    reloadCheckInterval = null;
  }
  
  if (scanner) {
    scanner.stop();
    scanner = null;
  }
  
  updateStatus('stopped', { stoppedAt: Date.now() });
  console.log('[Daemon] 已停止');
  process.exit(0);
}

// 信号处理
process.on('SIGINT', stopScanner);
process.on('SIGTERM', stopScanner);

// Windows 信号处理
if (process.platform === 'win32') {
  process.on('message', (msg) => {
    if (msg === 'shutdown') {
      stopScanner();
    }
  });
}

// 启动
startScanner();

// 保持进程运行
setInterval(() => {}, 1000);
