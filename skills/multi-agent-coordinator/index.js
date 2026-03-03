/**
 * Multi-Agent Coordinator - 技能入口
 * 负责协调多个 Claude Code 节点协同工作
 */

const { TaskManager } = require('./src/task/task-manager');
const { NodeManager } = require('./src/node/node-manager');
const { HeartbeatChecker } = require('./src/heartbeat/heartbeat-checker');
const path = require('path');
const fs = require('fs');
const dayjs = require('dayjs');

const PROJECTS_DIR = 'D:\\projects';

// 任务管理器
const taskManager = new TaskManager();

// 节点管理器
const nodeManager = new NodeManager();

// 心跳检查器（延迟启动，不在模块加载时自动启动）
let heartbeatChecker = null;

// 启动心跳检查（需要时调用）
function startHeartbeatChecker(intervalMs = 60000) {
  if (!heartbeatChecker) {
    heartbeatChecker = new HeartbeatChecker();
  }
  heartbeatChecker.start(intervalMs);
}

// 心跳检查回调：节点离线时处理
function onNodeOffline(nodeId, node) {
  console.log(`[Coordinator] 节点 ${nodeId} 已离线`);
}

// 心跳检查回调：节点恢复在线
function onNodeOnline(nodeId, node) {
  console.log(`[Coordinator] 节点 ${nodeId} 恢复在线`);
}

/**
 * 创建任务
 */
function createTask(options) {
  const { title, type, priority, instruction, deadline, inputFiles, outputFiles, assignTo } = options;
  
  const task = taskManager.createTask({
    title,
    type: type || 'code',
    priority: priority || 'medium',
    instruction,
    deadline,
    inputFiles: inputFiles || [],
    outputFiles: outputFiles || []
  });

  // 创建任务 README
  createTaskReadme(task);

  // 写入 commands 目录（指定节点或自动分配）
  const targetNode = assignTo || nodeManager.selectBestNode() || 'claude';
  writeCommandFile(task, targetNode);

  return task;
}

/**
 * 写入指令文件到 commands 目录
 */
function writeCommandFile(task, nodeId) {
  const commandDir = path.join(PROJECTS_DIR, 'commands', nodeId);
  if (!fs.existsSync(commandDir)) {
    fs.mkdirSync(commandDir, { recursive: true });
  }

  const commandFile = path.join(commandDir, `${task.id}.json`);
  const command = {
    taskId: task.id,
    command: task.instruction || task.title,
    workspace: path.join(PROJECTS_DIR, 'workspace', 'shared'),
    outputDir: path.join(PROJECTS_DIR, 'workspace', 'shared', 'output', task.id),
    timeout: 300000,
    createdAt: dayjs().toISOString(),
    deadline: task.deadline
  };

  fs.writeFileSync(commandFile, JSON.stringify(command, null, 2));
  console.log(`[Coordinator] 任务 ${task.id} 已下发到节点 ${nodeId}`);
}

/**
 * 创建任务说明书
 */
function createTaskReadme(task) {
  const taskDir = path.join(PROJECTS_DIR, 'workspace', 'shared', 'tasks', task.id);
  
  if (!fs.existsSync(taskDir)) {
    fs.mkdirSync(taskDir, { recursive: true });
  }

  const readme = `# 任务说明书：${task.title}

## 任务概述
- 任务编号：${task.id}
- 创建时间：${dayjs(task.createdAt).format('YYYY-MM-DD HH:mm:ss')}
- 截止时间：${dayjs(task.deadline).format('YYYY-MM-DD HH:mm:ss')}
- 优先级：${task.priority === 'high' ? '高' : task.priority === 'medium' ? '中' : '低'}
- 类型：${task.type === 'code' ? '代码开发' : task.type === 'analysis' ? '数据分析' : '文档处理'}

## 执行指令
${task.instruction || task.title}

## 输入资源
${task.input?.resources?.length > 0 
  ? task.input.resources.map(r => `- ${r}`).join('\n') 
  : '无'}

## 输出要求
${task.output?.resources?.length > 0 
  ? task.output.resources.map(r => `- ${r}`).join('\n') 
  : '无'}

## 状态
- 当前状态：${task.status}
- 分配节点：${task.assignee || '待分配'}
`;

  fs.writeFileSync(path.join(taskDir, 'README.md'), readme);
  return task;
}

/**
 * 获取任务列表
 */
function getTaskList(filter = {}) {
  return taskManager.getTasks(filter);
}

/**
 * 获取任务详情
 */
function getTaskDetail(taskId) {
  return taskManager.getTask(taskId);
}

/**
 * 确认完成任务
 */
function confirmTask(taskId) {
  return taskManager.completeTask(taskId);
}

/**
 * 重处理任务
 */
function retryTask(taskId) {
  const task = taskManager.getTask(taskId);
  if (!task) {
    throw new Error(`任务不存在: ${taskId}`);
  }

  // 重置任务状态
  return taskManager.updateTaskStatus(taskId, 'pending', {
    assignee: null,
    assignedAt: null,
    startedAt: null,
    submittedAt: null,
    completedAt: null,
    retryCount: 0,
    error: null
  });
}

/**
 * 取消任务
 */
function cancelTask(taskId) {
  return taskManager.deleteTask(taskId);
}

/**
 * 获取节点列表
 */
function getNodeList() {
  return nodeManager.getNodes();
}

/**
 * 获取节点状态
 */
function getNodeStatus() {
  return nodeManager.getStatusSummary();
}

/**
 * 手动分配任务到指定节点
 */
function assignTaskToNode(taskId, nodeId) {
  const node = nodeManager.getNode(nodeId);
  if (!node) {
    throw new Error(`节点不存在: ${nodeId}`);
  }

  if (!nodeManager.isNodeOnline(nodeId)) {
    throw new Error(`节点不在线: ${nodeId}`);
  }

  // 锁定任务
  taskManager.assignTask(taskId, nodeId);
  
  // 增加节点任务数
  nodeManager.incrementTaskCount(nodeId);

  return taskManager.getTask(taskId);
}

/**
 * 格式化任务列表输出
 */
function formatTaskList(tasks) {
  if (tasks.length === 0) {
    return '暂无任务';
  }

  // 按状态分组
  const pending = tasks.filter(t => t.status === 'pending');
  const assigned = tasks.filter(t => t.status === 'assigned');
  const running = tasks.filter(t => t.status === 'running');
  const submitted = tasks.filter(t => t.status === 'submitted');
  const done = tasks.filter(t => t.status === 'done');
  const failed = tasks.filter(t => t.status === 'failed');

  let output = `## 任务列表（共 ${tasks.length} 个）\n\n`;

  if (pending.length > 0) {
    output += `**待执行（${pending.length}）**\n`;
    pending.forEach(t => {
      output += `- [${t.id}] ${t.title} (${t.priority === 'high' ? '高' : t.priority === 'medium' ? '中' : '低'})\n`;
    });
    output += '\n';
  }

  if (assigned.length > 0) {
    output += `**已分配（${assigned.length}）**\n`;
    assigned.forEach(t => {
      output += `- [${t.id}] ${t.title} -> ${t.assignee}\n`;
    });
    output += '\n';
  }

  if (running.length > 0) {
    output += `**执行中（${running.length}）**\n`;
    running.forEach(t => {
      output += `- [${t.id}] ${t.title} -> ${t.assignee}\n`;
    });
    output += '\n';
  }

  if (submitted.length > 0) {
    output += `**已提交（${submitted.length}）**\n`;
    submitted.forEach(t => {
      output += `- [${t.id}] ${t.title} -> ${t.assignee} [待确认]\n`;
    });
    output += '\n';
  }

  if (done.length > 0) {
    output += `**已完成（${done.length}）**\n`;
    done.forEach(t => {
      output += `- [${t.id}] ${t.title}\n`;
    });
    output += '\n';
  }

  if (failed.length > 0) {
    output += `**失败（${failed.length}）**\n`;
    failed.forEach(t => {
      output += `- [${t.id}] ${t.title} [重试${t.retryCount}次]\n`;
    });
    output += '\n';
  }

  return output;
}

/**
 * 格式化节点状态输出
 */
function formatNodeStatus() {
  const summary = nodeManager.getStatusSummary();
  const nodes = nodeManager.getNodes();

  let output = `## 节点状态\n\n`;
  output += `总计: ${summary.total} | 在线: ${summary.online} | 忙碌: ${summary.busy} | 离线: ${summary.offline} | 任务数: ${summary.totalTasks}\n\n`;

  for (const [nodeId, node] of Object.entries(nodes)) {
    const isOnline = nodeManager.isNodeOnline(nodeId);
    const statusIcon = isOnline ? (node.status === 'busy' ? '忙碌' : '在线') : '离线';
    const lastHeartbeat = dayjs(node.lastHeartbeat).format('HH:mm:ss');
    
    output += `### ${nodeId}\n`;
    output += `- 状态: ${statusIcon}\n`;
    output += `- 任务数: ${node.currentTaskCount || 0}/${node.maxTaskCount || 2}\n`;
    output += `- 最后心跳: ${lastHeartbeat}\n`;
    output += `- 工作区: ${node.workspace || '-'}\n\n`;
  }

  return output;
}

module.exports = {
  // 任务管理
  createTask,
  getTaskList,
  getTaskDetail,
  confirmTask,
  retryTask,
  cancelTask,
  assignTaskToNode,
  
  // 节点管理
  getNodeList,
  getNodeStatus,
  
  // 格式化
  formatTaskList,
  formatNodeStatus,
  
  // 内部模块
  taskManager,
  nodeManager,
  heartbeatChecker
};
