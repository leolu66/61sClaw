/**
 * Node Agent - 节点任务拉取脚本
 * 部署到各执行节点，定时拉取任务并执行
 * 
 * 用法: node node-agent.js <node-id> <workspace-path>
 * 示例: node node-agent.js claude D:\projects\workspace\node-claude
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const dayjs = require('dayjs');

const CONFIG_DIR = 'D:\\projects\\config';
const TASKS_FILE = path.join(CONFIG_DIR, 'tasks.json');
const HEARTBEATS_FILE = path.join(CONFIG_DIR, 'heartbeats.json');
const SETTINGS_FILE = path.join(CONFIG_DIR, 'settings.json');
const COMMANDS_DIR = 'D:\\projects\\commands';
const RESULTS_DIR = 'D:\\projects\\results';
const LOGS_DIR = 'D:\\projects\\logs';

// 默认配置
const DEFAULT_SCAN_INTERVAL = 120000; // 120 秒
const DEFAULT_HEARTBEAT_INTERVAL = 300000; // 300 秒 = 5 分钟
const MAX_CONCURRENT_TASKS = 2;

class NodeAgent {
  constructor(nodeId, workspace) {
    this.nodeId = nodeId;
    this.workspace = workspace;
    this.scanInterval = null;
    this.heartbeatInterval = null;
    this.currentTask = null;
    this.logger = this._initLogger();
  }

  _initLogger() {
    if (!fs.existsSync(LOGS_DIR)) {
      fs.mkdirSync(LOGS_DIR, { recursive: true });
    }
    
    const logFile = path.join(LOGS_DIR, `node-${this.nodeId}.log`);
    
    return {
      info: (msg) => {
        const log = `[${dayjs().format('YYYY-MM-DD HH:mm:ss')}] [INFO] ${msg}`;
        console.log(log);
        fs.appendFileSync(logFile, log + '\n');
      },
      error: (msg) => {
        const log = `[${dayjs().format('YYYY-MM-DD HH:mm:ss')}] [ERROR] ${msg}`;
        console.error(log);
        fs.appendFileSync(logFile, log + '\n');
      },
      warn: (msg) => {
        const log = `[${dayjs().format('YYYY-MM-DD HH:mm:ss')}] [WARN] ${msg}`;
        console.warn(log);
        fs.appendFileSync(logFile, log + '\n');
      }
    };
  }

  /**
   * 加载设置
   */
  _loadSettings() {
    if (fs.existsSync(SETTINGS_FILE)) {
      return JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf-8'));
    }
    return {
      scanInterval: DEFAULT_SCAN_INTERVAL,
      heartbeatInterval: DEFAULT_HEARTBEAT_INTERVAL,
      maxTaskPerNode: MAX_CONCURRENT_TASKS,
      defaultTaskTimeout: 180
    };
  }

  /**
   * 注册节点
   */
  register() {
    const data = JSON.parse(fs.readFileSync(HEARTBEATS_FILE, 'utf-8'));
    
    if (!data.nodes[this.nodeId]) {
      data.nodes[this.nodeId] = {
        status: 'online',
        currentTaskCount: 0,
        maxTaskCount: MAX_CONCURRENT_TASKS,
        capabilities: ['code', 'analysis', 'doc'],
        lastHeartbeat: dayjs().toISOString(),
        registeredAt: dayjs().toISOString(),
        workspace: this.workspace
      };
      this.logger.info(`节点 ${this.nodeId} 已注册`);
    } else {
      data.nodes[this.nodeId].lastHeartbeat = dayjs().toISOString();
      data.nodes[this.nodeId].status = 'online';
      data.nodes[this.nodeId].workspace = this.workspace;
    }
    
    fs.writeFileSync(HEARTBEATS_FILE, JSON.stringify(data, null, 2));
  }

  /**
   * 发送心跳
   */
  sendHeartbeat() {
    try {
      const data = JSON.parse(fs.readFileSync(HEARTBEATS_FILE, 'utf-8'));
      
      if (!data.nodes[this.nodeId]) {
        this.logger.warn('节点未注册，先注册');
        this.register();
        return;
      }

      data.nodes[this.nodeId].lastHeartbeat = dayjs().toISOString();
      data.nodes[this.nodeId].status = this.currentTask ? 'busy' : 'online';
      
      fs.writeFileSync(HEARTBEATS_FILE, JSON.stringify(data, null, 2));
      this.logger.info(`心跳已发送，状态: ${data.nodes[this.nodeId].status}`);
    } catch (error) {
      this.logger.error(`发送心跳失败: ${error.message}`);
    }
  }

  /**
   * 扫描 commands 目录并拉取任务（新设计）
   */
  scanAndPullTask() {
    try {
      const settings = this._loadSettings();
      const heartbeatsData = JSON.parse(fs.readFileSync(HEARTBEATS_FILE, 'utf-8'));

      // 检查节点任务数
      const node = heartbeatsData.nodes[this.nodeId];
      if (!node) {
        this.logger.warn('节点未注册');
        return;
      }

      if (node.currentTaskCount >= (node.maxTaskCount || MAX_CONCURRENT_TASKS)) {
        this.logger.info(`任务已满（${node.currentTaskCount}/${node.maxTaskCount}），跳过`);
        return;
      }

      // 扫描 commands/{node}/ 目录
      const nodeCommandDir = path.join(COMMANDS_DIR, this.nodeId);
      if (!fs.existsSync(nodeCommandDir)) {
        this.logger.info(`命令目录不存在: ${nodeCommandDir}`);
        return;
      }

      // 获取所有命令文件
      const commandFiles = fs.readdirSync(nodeCommandDir)
        .filter(f => f.endsWith('.json'))
        .map(f => ({
          name: f,
          path: path.join(nodeCommandDir, f),
          time: fs.statSync(path.join(nodeCommandDir, f)).mtime
        }))
        .sort((a, b) => a.time - b.time); // 按时间顺序，最早的优先

      if (commandFiles.length === 0) {
        this.logger.info('暂无待执行任务');
        return;
      }

      // 处理第一个命令文件
      const commandFile = commandFiles[0];
      const command = JSON.parse(fs.readFileSync(commandFile.path, 'utf-8'));
      const taskId = command.taskId;

      this.logger.info(`收到任务: ${taskId}`);

      // 更新节点任务数
      node.currentTaskCount = (node.currentTaskCount || 0) + 1;
      node.status = 'busy';
      fs.writeFileSync(HEARTBEATS_FILE, JSON.stringify(heartbeatsData, null, 2));

      // 移动命令文件到临时位置（避免重复执行）
      const processingDir = path.join(COMMANDS_DIR, '.processing', this.nodeId);
      if (!fs.existsSync(processingDir)) {
        fs.mkdirSync(processingDir, { recursive: true });
      }
      const processingPath = path.join(processingDir, commandFile.name);
      fs.renameSync(commandFile.path, processingPath);

      // 更新任务状态
      this._updateTaskStatus(taskId, 'assigned', { assignee: this.nodeId });

      // 执行任务
      this.executeTask(command, processingPath);

    } catch (error) {
      this.logger.error(`扫描任务失败: ${error.message}`);
    }
  }

  /**
   * 使用 Claude Code 执行任务
   */
  _executeWithClaude(instruction, outputDir) {
    return new Promise((resolve) => {
      // 使用 claude -p (pipe mode) 来执行单次指令
      const cmd = `claude -p "${instruction}"`;
      
      this.logger.info(`执行命令: ${cmd}`);

      exec(cmd, { 
        cwd: outputDir,
        timeout: 300000, // 5 分钟超时
        maxBuffer: 10 * 1024 * 1024
      }, (error, stdout, stderr) => {
        if (error) {
          this.logger.error(`Claude Code 执行失败: ${error.message}`);
          resolve({ 
            success: false, 
            error: error.message + '\n' + stderr 
          });
          return;
        }

        this.logger.info(`Claude Code 执行成功`);
        
        // 收集生成的文件
        const files = [];
        try {
          const outputFiles = fs.readdirSync(outputDir);
          for (const f of outputFiles) {
            if (f !== 'prompt.txt' && f !== 'result.json') {
              files.push(f);
            }
          }
        } catch (e) {}

        resolve({ 
          success: true, 
          output: stdout,
          files: files
        });
      });
    });
  }

  /**
   * 执行任务
   */
  async executeTask(command, commandFilePath) {
    const taskId = command.taskId;
    this.currentTask = taskId;
    this.logger.info(`开始执行任务: ${taskId}`);

    try {
      // 更新任务状态为 running
      this._updateTaskStatus(taskId, 'running');

      // 读取任务指令
      const instruction = command.command;
      const outputDir = command.outputDir || path.join('D:\\projects\\workspace\\shared\\output', taskId);

      // 确保输出目录存在
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      // 创建任务指令文件
      const promptFile = path.join(outputDir, 'prompt.txt');
      fs.writeFileSync(promptFile, instruction);

      this.logger.info(`调用 Claude Code 执行任务...`);

      // 调用 Claude Code
      const claudeResult = await this._executeWithClaude(instruction, outputDir);

      // 写入结果到 results 目录
      const resultsDir = path.join(RESULTS_DIR, this.nodeId);
      if (!fs.existsSync(resultsDir)) {
        fs.mkdirSync(resultsDir, { recursive: true });
      }

      const result = {
        taskId: taskId,
        status: claudeResult.success ? 'success' : 'failed',
        output: claudeResult.output || claudeResult.error,
        outputFiles: claudeResult.files || [],
        executedAt: dayjs().toISOString()
      };

      // 写入 results 目录
      const resultFile = path.join(resultsDir, `${taskId}.json`);
      fs.writeFileSync(resultFile, JSON.stringify(result, null, 2));
      this.logger.info(`结果已写入: ${resultFile}`);

      // 同时写入输出目录
      const outputFile = path.join(outputDir, 'result.json');
      fs.writeFileSync(outputFile, JSON.stringify(result, null, 2));

      // 更新任务状态为 submitted
      this._updateTaskStatus(task.id, 'submitted', { result });

      // 减少节点任务数
      this._decrementTaskCount();

      this.logger.info(`任务执行完成: ${task.id}`);

    } catch (error) {
      this.logger.error(`任务执行失败: ${error.message}`);
      
      // 更新任务状态为 failed
      this._updateTaskStatus(task.id, 'failed', { error: error.message });
      
      // 减少节点任务数
      this._decrementTaskCount();

      // 触发重试逻辑
      this._handleTaskFailure(task);
    } finally {
      this.currentTask = null;
    }
  }

  /**
   * 更新任务状态
   */
  _updateTaskStatus(taskId, status, extra = {}) {
    const tasksData = JSON.parse(fs.readFileSync(TASKS_FILE, 'utf-8'));
    const taskIndex = tasksData.tasks.findIndex(t => t.id === taskId);
    
    if (taskIndex !== -1) {
      tasksData.tasks[taskIndex].status = status;
      if (status === 'running' && !tasksData.tasks[taskIndex].startedAt) {
        tasksData.tasks[taskIndex].startedAt = dayjs().toISOString();
      }
      if (status === 'submitted' && !tasksData.tasks[taskIndex].submittedAt) {
        tasksData.tasks[taskIndex].submittedAt = dayjs().toISOString();
      }
      Object.assign(tasksData.tasks[taskIndex], extra);
      fs.writeFileSync(TASKS_FILE, JSON.stringify(tasksData, null, 2));
    }
  }

  /**
   * 减少节点任务数
   */
  _decrementTaskCount() {
    const heartbeatsData = JSON.parse(fs.readFileSync(HEARTBEATS_FILE, 'utf-8'));
    if (heartbeatsData.nodes[this.nodeId]) {
      heartbeatsData.nodes[this.nodeId].currentTaskCount = Math.max(0, 
        (heartbeatsData.nodes[this.nodeId].currentTaskCount || 1) - 1);
      if (heartbeatsData.nodes[this.nodeId].currentTaskCount === 0) {
        heartbeatsData.nodes[this.nodeId].status = 'online';
      }
      fs.writeFileSync(HEARTBEATS_FILE, JSON.stringify(heartbeatsData, null, 2));
    }
  }

  /**
   * 处理任务失败
   */
  _handleTaskFailure(task) {
    const tasksData = JSON.parse(fs.readFileSync(TASKS_FILE, 'utf-8'));
    const taskIndex = tasksData.tasks.findIndex(t => t.id === task.id);
    
    if (taskIndex !== -1) {
      tasksData.tasks[taskIndex].retryCount = (tasksData.tasks[taskIndex].retryCount || 0) + 1;
      
      // 如果可重试，放回 pending
      if (tasksData.tasks[taskIndex].retryCount < 2) {
        tasksData.tasks[taskIndex].status = 'pending';
        tasksData.tasks[taskIndex].assignee = null;
        tasksData.tasks[taskIndex].assignedAt = null;
        this.logger.info(`任务 ${task.id} 将重试（${tasksData.tasks[taskIndex].retryCount}/2）`);
      } else {
        tasksData.tasks[taskIndex].status = 'failed';
        this.logger.error(`任务 ${task.id} 已失败（超过最大重试次数）`);
      }
      
      fs.writeFileSync(TASKS_FILE, JSON.stringify(tasksData, null, 2));
    }
  }

  /**
   * 启动
   */
  start() {
    const settings = this._loadSettings();
    
    this.logger.info(`========================================`);
    this.logger.info(`节点 ${this.nodeId} 启动`);
    this.logger.info(`工作区: ${this.workspace}`);
    this.logger.info(`扫描间隔: ${settings.scanInterval / 1000}s`);
    this.logger.info(`心跳间隔: ${settings.heartbeatInterval / 1000}s`);
    this.logger.info(`========================================`);

    // 注册节点
    this.register();

    // 启动心跳
    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat();
    }, settings.heartbeatInterval || DEFAULT_HEARTBEAT_INTERVAL);

    // 启动任务扫描
    this.scanInterval = setInterval(() => {
      this.scanAndPullTask();
    }, settings.scanInterval || DEFAULT_SCAN_INTERVAL);

    // 立即执行一次
    this.sendHeartbeat();
    this.scanAndPullTask();
  }

  /**
   * 停止
   */
  stop() {
    if (this.scanInterval) {
      clearInterval(this.scanInterval);
      this.scanInterval = null;
    }
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    this.logger.info(`节点 ${this.nodeId} 已停止`);
  }
}

// 主入口
if (require.main === module) {
  const nodeId = process.argv[2] || 'claude';
  const workspace = process.argv[3] || 'D:\\projects\\workspace\\node-claude';

  const agent = new NodeAgent(nodeId, workspace);

  // 优雅退出
  process.on('SIGINT', () => {
    console.log('\n收到退出信号，正在停止...');
    agent.stop();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    console.log('\n收到终止信号，正在停止...');
    agent.stop();
    process.exit(0);
  });

  agent.start();
}

module.exports = { NodeAgent };
