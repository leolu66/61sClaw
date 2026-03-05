/**
 * MasterScanner - 主节点扫描器
 * 独立定时扫描子节点结果和心跳状态
 */

const fs = require('fs');
const path = require('path');
const dayjs = require('dayjs');
const { ConfigLoader } = require('../config/config-loader');

class MasterScanner {
  constructor() {
    this.config = null;
    this.resultScanInterval = null;
    this.heartbeatCheckInterval = null;
    this.isRunning = false;
    this.logger = this._initLogger();
    this.onResultFound = null;
    this.onNodeOffline = null;
    this.processedResults = new Set(); // 避免重复处理
  }

  _initLogger() {
    const LOGS_DIR = 'D:\\projects\\logs';
    if (!fs.existsSync(LOGS_DIR)) {
      fs.mkdirSync(LOGS_DIR, { recursive: true });
    }
    const logFile = path.join(LOGS_DIR, 'master-scanner.log');
    
    return {
      info: (msg) => {
        const log = `[${dayjs().format('YYYY-MM-DD HH:mm:ss')}] [INFO] ${msg}`;
        console.log(log);
        fs.appendFileSync(logFile, log + '\n');
      },
      warn: (msg) => {
        const log = `[${dayjs().format('YYYY-MM-DD HH:mm:ss')}] [WARN] ${msg}`;
        console.warn(log);
        fs.appendFileSync(logFile, log + '\n');
      },
      error: (msg) => {
        const log = `[${dayjs().format('YYYY-MM-DD HH:mm:ss')}] [ERROR] ${msg}`;
        console.error(log);
        fs.appendFileSync(logFile, log + '\n');
      }
    };
  }

  /**
   * 启动扫描器
   */
  start() {
    if (this.isRunning) {
      this.logger.warn('扫描器已在运行');
      return;
    }

    // 加载配置
    const configLoader = new ConfigLoader();
    this.config = configLoader.getNodeConfig();

    if (this.config.nodeType !== 'master') {
      throw new Error(`当前配置为 ${this.config.nodeType}，无法启动主节点扫描器`);
    }

    this.logger.info('========================================');
    this.logger.info('主节点扫描器启动');
    this.logger.info(`结果扫描间隔: ${this.config.resultScanInterval}ms`);
    this.logger.info(`心跳检查间隔: ${this.config.heartbeatCheckInterval}ms`);
    this.logger.info('========================================');

    this.isRunning = true;

    // 启动结果扫描
    this.resultScanInterval = setInterval(() => {
      this._scanResults();
    }, this.config.resultScanInterval);

    // 启动心跳检查
    this.heartbeatCheckInterval = setInterval(() => {
      this._checkHeartbeats();
    }, this.config.heartbeatCheckInterval);

    // 立即执行一次
    this._scanResults();
    this._checkHeartbeats();
  }

  /**
   * 停止扫描器
   */
  stop() {
    if (!this.isRunning) {
      return;
    }

    if (this.resultScanInterval) {
      clearInterval(this.resultScanInterval);
      this.resultScanInterval = null;
    }

    if (this.heartbeatCheckInterval) {
      clearInterval(this.heartbeatCheckInterval);
      this.heartbeatCheckInterval = null;
    }

    this.isRunning = false;
    this.logger.info('主节点扫描器已停止');
  }

  /**
   * 扫描子节点结果
   */
  _scanResults() {
    try {
      const resultsDir = this.config.resultsDir;
      if (!fs.existsSync(resultsDir)) {
        return;
      }

      // 遍历所有子节点目录
      const nodeDirs = fs.readdirSync(resultsDir)
        .filter(dir => fs.statSync(path.join(resultsDir, dir)).isDirectory());

      let foundCount = 0;

      for (const nodeId of nodeDirs) {
        const nodeResultsDir = path.join(resultsDir, nodeId);
        const resultFiles = fs.readdirSync(nodeResultsDir)
          .filter(f => f.endsWith('.json'));

        for (const file of resultFiles) {
          const resultId = `${nodeId}/${file}`;
          
          // 避免重复处理
          if (this.processedResults.has(resultId)) {
            continue;
          }

          const filePath = path.join(nodeResultsDir, file);
          const result = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
          
          this.logger.info(`发现新结果: ${result.taskId} from ${nodeId}`);
          
          // 触发回调
          if (this.onResultFound) {
            this.onResultFound(result, nodeId);
          }

          // 更新任务状态
          this._updateTaskStatus(result.taskId, 'submitted', {
            result: result,
            processedBy: nodeId
          });

          this.processedResults.add(resultId);
          foundCount++;
        }
      }

      if (foundCount > 0) {
        this.logger.info(`本次扫描发现 ${foundCount} 个新结果`);
      }
      
      // 返回扫描统计
      return {
        scannedAt: Date.now(),
        resultsFound: foundCount,
        totalProcessed: this.processedResults.size
      };
    } catch (error) {
      this.logger.error(`扫描结果失败: ${error.message}`);
      return { error: error.message };
    }
  }

  /**
   * 检查节点心跳
   */
  _checkHeartbeats() {
    try {
      const heartbeatsFile = path.join(this.config.configDir, 'heartbeats.json');
      if (!fs.existsSync(heartbeatsFile)) {
        return;
      }

      const data = JSON.parse(fs.readFileSync(heartbeatsFile, 'utf-8'));
      const now = dayjs();
      const timeout = this.config.nodeTimeout || 360;
      let changed = false;

      for (const [nodeId, node] of Object.entries(data.nodes || {})) {
        const lastHeartbeat = dayjs(node.lastHeartbeat);
        const diff = now.diff(lastHeartbeat, 'second');

        if (diff >= timeout && node.status !== 'offline') {
          this.logger.warn(`节点 ${nodeId} 已离线（${diff}秒无心跳）`);
          node.status = 'offline';
          changed = true;

          if (this.onNodeOffline) {
            this.onNodeOffline(nodeId, node);
          }
        }
      }

      if (changed) {
        fs.writeFileSync(heartbeatsFile, JSON.stringify(data, null, 2));
      }
    } catch (error) {
      this.logger.error(`检查心跳失败: ${error.message}`);
    }
  }

  /**
   * 更新任务状态
   */
  _updateTaskStatus(taskId, status, extra = {}) {
    try {
      const tasksFile = path.join(this.config.configDir, 'tasks.json');
      if (!fs.existsSync(tasksFile)) {
        return;
      }

      const data = JSON.parse(fs.readFileSync(tasksFile, 'utf-8'));
      const taskIndex = data.tasks.findIndex(t => t.id === taskId);

      if (taskIndex !== -1) {
        data.tasks[taskIndex].status = status;
        
        if (status === 'submitted' && !data.tasks[taskIndex].submittedAt) {
          data.tasks[taskIndex].submittedAt = dayjs().toISOString();
        }

        Object.assign(data.tasks[taskIndex], extra);
        fs.writeFileSync(tasksFile, JSON.stringify(data, null, 2));
      }
    } catch (error) {
      this.logger.error(`更新任务状态失败: ${error.message}`);
    }
  }

  /**
   * 设置结果发现回调
   */
  setOnResultFound(callback) {
    this.onResultFound = callback;
  }

  /**
   * 设置节点离线回调
   */
  setOnNodeOffline(callback) {
    this.onNodeOffline = callback;
  }

  /**
   * 获取状态
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      config: this.config,
      processedResultsCount: this.processedResults.size
    };
  }
}

module.exports = { MasterScanner };
