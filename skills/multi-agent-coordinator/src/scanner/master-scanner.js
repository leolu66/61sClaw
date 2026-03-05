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
      // 1. 扫描传统结果目录
      const resultsDir = this.config.resultsDir;
      if (fs.existsSync(resultsDir)) {
        this._scanTraditionalResults(resultsDir);
      }

      // 2. 扫描异步任务标记文件
      this._scanAsyncTaskMarkers();

    } catch (error) {
      this.logger.error(`扫描结果失败: ${error.message}`);
      return { error: error.message };
    }
  }

  /**
   * 扫描传统结果目录
   */
  _scanTraditionalResults(resultsDir) {
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
      this.logger.info(`传统结果扫描: 发现 ${foundCount} 个新结果`);
    }
  }

  /**
   * 扫描异步任务标记文件
   * 检查子 Agent 生成的 .task-completed 和 .task-failed 文件
   */
  _scanAsyncTaskMarkers() {
    try {
      const sharedOutputDir = this.config.shared?.outputDir || 'D:\\projects\\workspace\\shared\\output';
      if (!fs.existsSync(sharedOutputDir)) {
        return;
      }

      // 遍历所有任务输出目录
      const taskDirs = fs.readdirSync(sharedOutputDir)
        .filter(dir => dir.startsWith('task-'))
        .map(dir => path.join(sharedOutputDir, dir))
        .filter(dir => fs.statSync(dir).isDirectory());

      let completedCount = 0;
      let failedCount = 0;

      for (const taskDir of taskDirs) {
        // 检查完成标记
        const completedMarker = path.join(taskDir, '.task-completed');
        const failedMarker = path.join(taskDir, '.task-failed');

        if (fs.existsSync(completedMarker)) {
          const markerData = JSON.parse(fs.readFileSync(completedMarker, 'utf-8'));
          const planId = markerData.planId;
          
          if (!this.processedResults.has(`async/${planId}`)) {
            this.logger.info(`发现异步任务完成: ${planId}`);
            
            // 更新任务清单
            this._updateAsyncTaskChecklist(planId, 'completed', markerData);
            
            this.processedResults.add(`async/${planId}`);
            completedCount++;
          }
        }

        if (fs.existsSync(failedMarker)) {
          const markerData = JSON.parse(fs.readFileSync(failedMarker, 'utf-8'));
          const planId = markerData.planId;
          
          if (!this.processedResults.has(`async/${planId}`)) {
            this.logger.warn(`发现异步任务失败: ${planId}`);
            
            // 更新任务清单
            this._updateAsyncTaskChecklist(planId, 'failed', markerData);
            
            this.processedResults.add(`async/${planId}`);
            failedCount++;
          }
        }
      }

      if (completedCount > 0 || failedCount > 0) {
        this.logger.info(`异步任务扫描: ${completedCount} 完成, ${failedCount} 失败`);
      }
    } catch (error) {
      this.logger.error(`扫描异步任务标记失败: ${error.message}`);
    }
  }

  /**
   * 更新异步任务清单
   */
  _updateAsyncTaskChecklist(planId, status, markerData) {
    try {
      const configDir = this.config.configDir;
      const checklistPath = path.join(configDir, `task-checklist-${planId}.md`);
      
      if (!fs.existsSync(checklistPath)) {
        this.logger.warn(`任务清单不存在: ${checklistPath}`);
        return;
      }

      let content = fs.readFileSync(checklistPath, 'utf-8');
      const timestamp = dayjs().format('YYYY-MM-DD HH:mm:ss');

      // 更新状态
      content = content.replace(
        /\*\*状态\*\*: .*$/m,
        `**状态**: ${status === 'completed' ? '✅ 已完成' : '❌ 失败'}`
      );

      // 添加扫描器检测记录
      content += `\n## 扫描器检测\n\n`;
      content += `- **检测时间**: ${timestamp}\n`;
      content += `- **检测结果**: ${status === 'completed' ? '任务成功完成' : '任务执行失败'}\n`;
      if (markerData.completedAt) {
        content += `- **完成时间**: ${markerData.completedAt}\n`;
      }
      if (markerData.failedAt) {
        content += `- **失败时间**: ${markerData.failedAt}\n`;
      }
      if (markerData.reason) {
        content += `- **原因**: ${markerData.reason}\n`;
      }

      fs.writeFileSync(checklistPath, content, 'utf-8');
      this.logger.info(`已更新任务清单: ${planId}`);

      // 触发通知（如果配置了）
      if (this.config.notificationEnabled && status === 'completed') {
        this._sendNotification(planId, markerData);
      }
    } catch (error) {
      this.logger.error(`更新任务清单失败: ${error.message}`);
    }
  }

  /**
   * 发送通知（飞书等）
   */
  _sendNotification(planId, markerData) {
    // TODO: 集成飞书通知
    this.logger.info(`[通知] 任务 ${planId} 已完成`);
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
