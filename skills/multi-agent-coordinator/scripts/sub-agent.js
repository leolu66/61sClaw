/**
 * 子节点 Agent - Claude Code 专用
 * 直接作为 Claude Code 执行任务，不需要再调用 claude -p
 * 
 * 使用方式:
 *   node sub-agent.js claude    # 启动 claude 节点
 *   node sub-agent.js kimi     # 启动 kimi 节点
 */

const fs = require('fs');
const path = require('path');
const dayjs = require('dayjs');

const CONFIG_DIR = 'D:\\projects\\config';
const TASKS_FILE = path.join(CONFIG_DIR, 'tasks.json');
const HEARTBEATS_FILE = path.join(CONFIG_DIR, 'heartbeats.json');
const COMMANDS_DIR = 'D:\\projects\\commands';
const RESULTS_DIR = 'D:\\projects\\results';
const LOGS_DIR = 'D:\\projects\\logs';

const DEFAULT_SCAN_INTERVAL = 60000; // 60 秒扫描一次
const DEFAULT_HEARTBEAT_INTERVAL = 3600000; // 3600 秒 = 1 小时

class SubAgent {
  constructor(nodeId) {
    this.nodeId = nodeId;
    this.scanInterval = null;
    this.heartbeatInterval = null;
    this.currentTask = null;
    this.logger = this._initLogger();
  }

  _initLogger() {
    if (!fs.existsSync(LOGS_DIR)) {
      fs.mkdirSync(LOGS_DIR, { recursive: true });
    }
    const logFile = path.join(LOGS_DIR, `sub-agent-${this.nodeId}.log`);
    
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
   * 注册节点
   */
  register() {
    let data = { nodes: {} };
    if (fs.existsSync(HEARTBEATS_FILE)) {
      data = JSON.parse(fs.readFileSync(HEARTBEATS_FILE, 'utf-8'));
    }
    
    if (!data.nodes[this.nodeId]) {
      data.nodes[this.nodeId] = {
        status: 'online',
        currentTaskCount: 0,
        maxTaskCount: 2,
        capabilities: ['code', 'analysis', 'doc', 'writing'],
        lastHeartbeat: dayjs().toISOString(),
        registeredAt: dayjs().toISOString(),
        type: 'claude-code' // 标记为 Claude Code 节点
      };
      this.logger.info(`节点 ${this.nodeId} 已注册`);
    } else {
      data.nodes[this.nodeId].lastHeartbeat = dayjs().toISOString();
      data.nodes[this.nodeId].status = 'online';
      data.nodes[this.nodeId].type = 'claude-code';
    }
    
    fs.writeFileSync(HEARTBEATS_FILE, JSON.stringify(data, null, 2));
  }

  /**
   * 发送心跳
   */
  sendHeartbeat() {
    try {
      let data = { nodes: {} };
      if (fs.existsSync(HEARTBEATS_FILE)) {
        data = JSON.parse(fs.readFileSync(HEARTBEATS_FILE, 'utf-8'));
      }
      
      if (!data.nodes[this.nodeId]) {
        this.register();
        return;
      }

      data.nodes[this.nodeId].lastHeartbeat = dayjs().toISOString();
      data.nodes[this.nodeId].status = this.currentTask ? 'busy' : 'online';
      
      fs.writeFileSync(HEARTBEATS_FILE, JSON.stringify(data, null, 2));
      this.logger.info(`心跳: ${data.nodes[this.nodeId].status}`);
    } catch (error) {
      this.logger.error(`心跳失败: ${error.message}`);
    }
  }

  /**
   * 扫描并执行任务
   */
  async scanAndExecuteTask() {
    try {
      // 检查节点是否忙碌
      const heartbeatsData = JSON.parse(fs.readFileSync(HEARTBEATS_FILE, 'utf-8'));
      const node = heartbeatsData.nodes[this.nodeId];
      
      if (!node) {
        this.logger.warn('节点未注册');
        return;
      }

      if (node.currentTaskCount >= (node.maxTaskCount || 2)) {
        this.logger.info(`节点忙碌，跳过扫描`);
        return;
      }

      // 扫描 commands/{node}/ 目录
      const nodeCommandDir = path.join(COMMANDS_DIR, this.nodeId);
      if (!fs.existsSync(nodeCommandDir)) {
        this.logger.info(`命令目录不存在: ${nodeCommandDir}`);
        return;
      }

      // 获取所有任务文件
      const commandFiles = fs.readdirSync(nodeCommandDir)
        .filter(f => f.endsWith('.json'))
        .map(f => ({
          name: f,
          path: path.join(nodeCommandDir, f),
          time: fs.statSync(path.join(nodeCommandDir, f)).mtime
        }))
        .sort((a, b) => a.time - b.time);

      if (commandFiles.length === 0) {
        this.logger.info('暂无待执行任务');
        return;
      }

      // 执行第一个任务
      const commandFile = commandFiles[0];
      await this.executeTask(commandFile);

    } catch (error) {
      this.logger.error(`扫描任务失败: ${error.message}`);
    }
  }

  /**
   * 执行任务
   * 子节点作为 Claude Code 自己理解并执行任务
   */
  async executeTask(commandFile) {
    const command = JSON.parse(fs.readFileSync(commandFile.path, 'utf-8'));
    const taskId = command.taskId;
    
    if (this.currentTask) {
      this.logger.warn(`正在执行任务 ${this.currentTask}，跳过 ${taskId}`);
      return;
    }

    this.currentTask = taskId;
    this.logger.info(`========================================`);
    this.logger.info(`开始执行任务: ${taskId}`);
    this.logger.info(`指令: ${command.instruction.substring(0, 100)}...`);
    this.logger.info(`========================================`);

    try {
      // 1. 更新任务状态为 running
      this._updateTaskStatus(taskId, 'running', { assignee: this.nodeId });
      
      // 2. 更新节点状态为忙碌
      this._updateNodeStatus('busy');

      // 3. 创建输出目录
      const outputDir = command.outputDir || path.join('D:\\projects\\workspace\\shared\\output', taskId);
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      // 4. 写入指令文件（方便后续追溯）
      const promptFile = path.join(outputDir, 'prompt.txt');
      fs.writeFileSync(promptFile, command.instruction);

      // 5. 执行任务（这里应该调用实际的执行逻辑）
      const result = await this._doExecuteTask(command, outputDir);

      // 6. 写入结果
      const resultsDir = path.join(RESULTS_DIR, this.nodeId);
      if (!fs.existsSync(resultsDir)) {
        fs.mkdirSync(resultsDir, { recursive: true });
      }

      const resultFile = path.join(resultsDir, `${taskId}.json`);
      const resultData = {
        taskId: taskId,
        status: result.success ? 'success' : 'failed',
        output: result.output,
        outputFiles: result.files || [],
        executedAt: dayjs().toISOString(),
        executedBy: this.nodeId,
        type: 'claude-code'
      };
      
      fs.writeFileSync(resultFile, JSON.stringify(resultData, null, 2));
      this.logger.info(`结果已写入: ${resultFile}`);

      // 7. 更新任务状态为 submitted
      this._updateTaskStatus(taskId, 'submitted', { 
        result: resultData 
      });

      // 8. 删除命令文件
      try {
        fs.unlinkSync(commandFile.path);
        this.logger.info(`已清除命令文件`);
      } catch (e) {}

      this.logger.info(`任务完成: ${taskId}, 状态: ${resultData.status}`);

    } catch (error) {
      this.logger.error(`任务执行失败: ${error.message}`);
      
      // 写入失败结果
      const resultsDir = path.join(RESULTS_DIR, this.nodeId);
      const resultFile = path.join(resultsDir, `${taskId}.json`);
      const resultData = {
        taskId: taskId,
        status: 'failed',
        output: error.message,
        executedAt: dayjs().toISOString(),
        executedBy: this.nodeId
      };
      fs.writeFileSync(resultFile, JSON.stringify(resultData, null, 2));
      
      this._updateTaskStatus(taskId, 'failed', { error: error.message });
      
      // 失败时也删除命令文件，避免重复执行
      try {
        fs.unlinkSync(commandFile.path);
        this.logger.info(`已清除失败任务命令文件`);
      } catch (e) {}
    } finally {
      this.currentTask = null;
      this._updateNodeStatus('online');
    }
  }

  /**
   * 实际执行任务
   * 支持两种执行方式：
   * 1. executeBy: 'claude' - 调用 Claude Code 执行
   * 2. executeBy: 'command' - 直接调用外部程序
   */
  async _doExecuteTask(command, outputDir) {
    const { executeBy, instruction, command: cmd, args } = command;
    
    if (executeBy === 'claude') {
      // 调用 Claude Code 执行
      return await this._executeByClaude(instruction, outputDir);
    } else if (executeBy === 'command') {
      // 直接调用外部程序
      return await this._executeCommand(cmd, args, outputDir);
    } else {
      // 默认行为：模拟执行（向后兼容）
      return await this._executeByClaude(command.instruction, outputDir);
    }
  }

  /**
   * 通过 Claude Code 执行任务
   */
  async _executeByClaude(instruction, outputDir) {
    this.logger.info(`[Claude执行] ${instruction.substring(0, 100)}...`);
    
    const { spawn } = require('child_process');
    const path = require('path');
    
    return new Promise((resolve, reject) => {
      const claudeProcess = spawn('claude', [
        '-p',
        instruction,
        '--max-turns', '20',
        '--permission-mode', 'bypassPermissions'
      ], {
        cwd: outputDir,
        shell: true
      });
      
      let output = '';
      let errorOutput = '';
      
      claudeProcess.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      claudeProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });
      
      claudeProcess.on('close', (code) => {
        if (code === 0) {
          resolve({
            success: true,
            output: output,
            files: []
          });
        } else {
          resolve({
            success: false,
            output: errorOutput || output,
            files: []
          });
        }
      });
      
      claudeProcess.on('error', (error) => {
        resolve({
          success: false,
          output: `执行错误: ${error.message}`,
          files: []
        });
      });
    });
  }

  /**
   * 直接执行外部命令
   */
  async _executeCommand(cmd, args, outputDir) {
    this.logger.info(`[命令执行] ${cmd} ${args ? args.join(' ') : ''}`);
    
    const { spawn } = require('child_process');
    
    return new Promise((resolve, reject) => {
      const childProcess = spawn(cmd, args || [], {
        cwd: outputDir,
        shell: true
      });
      
      let output = '';
      let errorOutput = '';
      
      childProcess.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      childProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });
      
      childProcess.on('close', (code) => {
        resolve({
          success: code === 0,
          output: output || errorOutput,
          files: []
        });
      });
      
      childProcess.on('error', (error) => {
        resolve({
          success: false,
          output: `命令执行错误: ${error.message}`,
          files: []
        });
      });
    });
  }

  /**
   * 更新任务状态
   */
  _updateTaskStatus(taskId, status, extra = {}) {
    try {
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
    } catch (error) {
      this.logger.error(`更新任务状态失败: ${error.message}`);
    }
  }

  /**
   * 更新节点状态
   */
  _updateNodeStatus(status) {
    try {
      const data = JSON.parse(fs.readFileSync(HEARTBEATS_FILE, 'utf-8'));
      if (data.nodes[this.nodeId]) {
        data.nodes[this.nodeId].status = status;
        data.nodes[this.nodeId].currentTaskCount = status === 'busy' ? 1 : 0;
        fs.writeFileSync(HEARTBEATS_FILE, JSON.stringify(data, null, 2));
      }
    } catch (error) {
      this.logger.error(`更新节点状态失败: ${error.message}`);
    }
  }

  /**
   * 启动
   */
  start() {
    this.logger.info(`========================================`);
    this.logger.info(`子节点 ${this.nodeId} 启动 (Claude Code 模式)`);
    this.logger.info(`扫描间隔: ${DEFAULT_SCAN_INTERVAL / 1000}s`);
    this.logger.info(`心跳间隔: ${DEFAULT_HEARTBEAT_INTERVAL / 1000}s`);
    this.logger.info(`========================================`);

    // 注册节点
    this.register();

    // 启动心跳
    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat();
    }, DEFAULT_HEARTBEAT_INTERVAL);

    // 启动任务扫描
    this.scanInterval = setInterval(() => {
      this.scanAndExecuteTask();
    }, DEFAULT_SCAN_INTERVAL);

    // 立即执行一次
    this.sendHeartbeat();
    this.scanAndExecuteTask();
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
    this.logger.info(`子节点 ${this.nodeId} 已停止`);
  }
}

// 主入口
if (require.main === module) {
  const nodeId = process.argv[2] || 'claude';
  
  const agent = new SubAgent(nodeId);

  process.on('SIGINT', () => {
    console.log('\n正在停止...');
    agent.stop();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    console.log('\n正在停止...');
    agent.stop();
    process.exit(0);
  });

  agent.start();
}

module.exports = { SubAgent };
