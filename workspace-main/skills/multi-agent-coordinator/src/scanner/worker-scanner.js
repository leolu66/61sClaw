/**
 * WorkerScanner - 子节点扫描器
 * 独立定时扫描任务指令和发送心跳
 */

const fs = require('fs');
const path = require('path');
const dayjs = require('dayjs');
const { ConfigLoader } = require('../config/config-loader');

class WorkerScanner {
  constructor() {
    this.config = null;
    this.taskScanInterval = null;
    this.heartbeatInterval = null;
    this.isRunning = false;
    this.logger = this._initLogger();
    this.currentTask = null;
    this.onTaskFound = null;
  }

  _initLogger() {
    const LOGS_DIR = 'D:\\projects\\logs';
    if (!fs.existsSync(LOGS_DIR)) {
      fs.mkdirSync(LOGS_DIR, { recursive: true });
    }
    const logFile = path.join(LOGS_DIR, `worker-scanner-${process.pid}.log`);
    
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

    if (this.config.nodeType !== 'worker') {
      throw new Error(`当前配置为 ${this.config.nodeType}，无法启动子节点扫描器`);
    }

    this.logger.info('========================================');
    this.logger.info(`子节点扫描器启动: ${this.config.nodeId}`);
    this.logger.info(`任务扫描间隔: ${this.config.taskScanInterval}ms`);
    this.logger.info(`心跳间隔: ${this.config.heartbeatInterval}ms`);
    this.logger.info('========================================');

    this.isRunning = true;

    // 注册节点
    this._registerNode();

    // 启动任务扫描
    this.taskScanInterval = setInterval(() => {
      this._scanTasks();
    }, this.config.taskScanInterval);

    // 启动心跳
    this.heartbeatInterval = setInterval(() => {
      this._sendHeartbeat();
    }, this.config.heartbeatInterval);

    // 立即执行一次
    this._sendHeartbeat();
    this._scanTasks();
  }

  /**
   * 停止扫描器
   */
  stop() {
    if (!this.isRunning) {
      return;
    }

    if (this.taskScanInterval) {
      clearInterval(this.taskScanInterval);
      this.taskScanInterval = null;
    }

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    // 标记节点离线
    this._markOffline();

    this.isRunning = false;
    this.logger.info('子节点扫描器已停止');
  }

  /**
   * 注册节点
   */
  _registerNode() {
    try {
      const heartbeatsFile = path.join(this.config.configDir, 'heartbeats.json');
      let data = { nodes: {} };
      
      if (fs.existsSync(heartbeatsFile)) {
        data = JSON.parse(fs.readFileSync(heartbeatsFile, 'utf-8'));
      }

      data.nodes[this.config.nodeId] = {
        status: 'online',
        currentTaskCount: 0,
        maxTaskCount: this.config.maxConcurrentTasks || 2,
        capabilities: this.config.capabilities || ['code', 'analysis'],
        lastHeartbeat: dayjs().toISOString(),
        registeredAt: dayjs().toISOString(),
        type: 'worker'
      };

      fs.writeFileSync(heartbeatsFile, JSON.stringify(data, null, 2));
      this.logger.info(`节点 ${this.config.nodeId} 已注册`);
    } catch (error) {
      this.logger.error(`注册节点失败: ${error.message}`);
    }
  }

  /**
   * 发送心跳
   */
  _sendHeartbeat() {
    try {
      const heartbeatsFile = path.join(this.config.configDir, 'heartbeats.json');
      if (!fs.existsSync(heartbeatsFile)) {
        this._registerNode();
        return;
      }

      const data = JSON.parse(fs.readFileSync(heartbeatsFile, 'utf-8'));
      
      if (!data.nodes[this.config.nodeId]) {
        this._registerNode();
        return;
      }

      data.nodes[this.config.nodeId].lastHeartbeat = dayjs().toISOString();
      data.nodes[this.config.nodeId].status = this.currentTask ? 'busy' : 'online';
      data.nodes[this.config.nodeId].currentTaskCount = this.currentTask ? 1 : 0;

      fs.writeFileSync(heartbeatsFile, JSON.stringify(data, null, 2));
      this.logger.info(`心跳发送: ${data.nodes[this.config.nodeId].status}`);
    } catch (error) {
      this.logger.error(`发送心跳失败: ${error.message}`);
    }
  }

  /**
   * 标记节点离线
   */
  _markOffline() {
    try {
      const heartbeatsFile = path.join(this.config.configDir, 'heartbeats.json');
      if (!fs.existsSync(heartbeatsFile)) return;

      const data = JSON.parse(fs.readFileSync(heartbeatsFile, 'utf-8'));
      
      if (data.nodes[this.config.nodeId]) {
        data.nodes[this.config.nodeId].status = 'offline';
        fs.writeFileSync(heartbeatsFile, JSON.stringify(data, null, 2));
      }
    } catch (error) {
      this.logger.error(`标记离线失败: ${error.message}`);
    }
  }

  /**
   * 扫描任务
   */
  _scanTasks() {
    try {
      // 检查是否忙碌
      if (this.currentTask) {
        this.logger.info(`正在执行任务 ${this.currentTask}，跳过扫描`);
        return;
      }

      // 检查节点任务数限制
      const heartbeatsFile = path.join(this.config.configDir, 'heartbeats.json');
      if (fs.existsSync(heartbeatsFile)) {
        const data = JSON.parse(fs.readFileSync(heartbeatsFile, 'utf-8'));
        const node = data.nodes[this.config.nodeId];
        
        if (node && node.currentTaskCount >= (node.maxTaskCount || 2)) {
          this.logger.info('节点任务数已达上限，跳过扫描');
          return;
        }
      }

      // 扫描命令目录
      const commandDir = path.join(this.config.commandsDir, this.config.nodeId);
      if (!fs.existsSync(commandDir)) {
        return;
      }

      const commandFiles = fs.readdirSync(commandDir)
        .filter(f => f.endsWith('.json'))
        .map(f => ({
          name: f,
          path: path.join(commandDir, f),
          time: fs.statSync(path.join(commandDir, f)).mtime
        }))
        .sort((a, b) => a.time - b.time);

      if (commandFiles.length === 0) {
        return;
      }

      // 执行第一个任务
      const commandFile = commandFiles[0];
      this._executeTask(commandFile);

    } catch (error) {
      this.logger.error(`扫描任务失败: ${error.message}`);
    }
  }

  /**
   * 执行任务
   */
  async _executeTask(commandFile) {
    const command = JSON.parse(fs.readFileSync(commandFile.path, 'utf-8'));
    const taskId = command.taskId;
    
    this.currentTask = taskId;
    this.logger.info(`========================================`);
    this.logger.info(`开始执行任务: ${taskId}`);
    this.logger.info(`指令: ${command.instruction?.substring(0, 100)}...`);
    this.logger.info(`========================================`);

    try {
      // 更新任务状态
      this._updateTaskStatus(taskId, 'running', { assignee: this.config.nodeId });
      
      // 更新节点状态
      this._updateNodeStatus('busy');

      // 触发回调（由外部实现具体执行逻辑）
      if (this.onTaskFound) {
        await this.onTaskFound(command, this.config.nodeId);
      } else {
        this.logger.warn('未设置任务处理回调，任务未实际执行');
      }

      // 删除命令文件
      try {
        fs.unlinkSync(commandFile.path);
        this.logger.info('已清除命令文件');
      } catch (e) {}

    } catch (error) {
      this.logger.error(`任务执行失败: ${error.message}`);
      
      // 写入失败结果
      this._writeResult(taskId, {
        status: 'failed',
        output: error.message
      });
      
      this._updateTaskStatus(taskId, 'failed', { error: error.message });
      
      // 删除命令文件
      try {
        fs.unlinkSync(commandFile.path);
      } catch (e) {}
    } finally {
      this.currentTask = null;
      this._updateNodeStatus('online');
    }
  }

  /**
   * 写入结果
   */
  _writeResult(taskId, result) {
    try {
      const resultsDir = path.join(this.config.resultsDir, this.config.nodeId);
      if (!fs.existsSync(resultsDir)) {
        fs.mkdirSync(resultsDir, { recursive: true });
      }

      const resultFile = path.join(resultsDir, `${taskId}.json`);
      const resultData = {
        taskId: taskId,
        status: result.status || 'success',
        output: result.output || '',
        outputFiles: result.files || [],
        executedAt: dayjs().toISOString(),
        executedBy: this.config.nodeId
      };

      fs.writeFileSync(resultFile, JSON.stringify(resultData, null, 2));
      this.logger.info(`结果已写入: ${resultFile}`);

      // 更新任务状态
      this._updateTaskStatus(taskId, 'submitted', { result: resultData });

    } catch (error) {
      this.logger.error(`写入结果失败: ${error.message}`);
    }
  }

  /**
   * 更新任务状态
   */
  _updateTaskStatus(taskId, status, extra = {}) {
    try {
      const tasksFile = path.join(this.config.configDir, 'tasks.json');
      if (!fs.existsSync(tasksFile)) return;

      const data = JSON.parse(fs.readFileSync(tasksFile, 'utf-8'));
      const taskIndex = data.tasks.findIndex(t => t.id === taskId);

      if (taskIndex !== -1) {
        data.tasks[taskIndex].status = status;
        
        if (status === 'running' && !data.tasks[taskIndex].startedAt) {
          data.tasks[taskIndex].startedAt = dayjs().toISOString();
        }
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
   * 更新节点状态
   */
  _updateNodeStatus(status) {
    try {
      const heartbeatsFile = path.join(this.config.configDir, 'heartbeats.json');
      if (!fs.existsSync(heartbeatsFile)) return;

      const data = JSON.parse(fs.readFileSync(heartbeatsFile, 'utf-8'));
      
      if (data.nodes[this.config.nodeId]) {
        data.nodes[this.config.nodeId].status = status;
        data.nodes[this.config.nodeId].currentTaskCount = status === 'busy' ? 1 : 0;
        fs.writeFileSync(heartbeatsFile, JSON.stringify(data, null, 2));
      }
    } catch (error) {
      this.logger.error(`更新节点状态失败: ${error.message}`);
    }
  }

  /**
   * 设置任务发现回调
   */
  setOnTaskFound(callback) {
    this.onTaskFound = callback;
  }

  /**
   * 获取状态
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      config: this.config,
      currentTask: this.currentTask
    };
  }
}

module.exports = { WorkerScanner };
