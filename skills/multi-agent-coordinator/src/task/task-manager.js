/**
 * TaskManager - 任务管理模块
 * 负责任务的创建、查询、更新等操作
 */

const fs = require('fs');
const path = require('path');
const dayjs = require('dayjs');

const CONFIG_DIR = 'D:\\projects\\config';
const TASKS_FILE = path.join(CONFIG_DIR, 'tasks.json');
const WORKSPACE_DIR = 'D:\\projects\\workspace';

class TaskManager {
  constructor() {
    this._ensureConfigFile();
  }

  /**
   * 确保配置文件存在
   */
  _ensureConfigFile() {
    if (!fs.existsSync(TASKS_FILE)) {
      fs.mkdirSync(CONFIG_DIR, { recursive: true });
      fs.writeFileSync(TASKS_FILE, JSON.stringify({ tasks: [], lastTaskId: 0 }, null, 2));
    }
  }

  /**
   * 读取任务表
   */
  _readTasks() {
    const data = fs.readFileSync(TASKS_FILE, 'utf-8');
    return JSON.parse(data);
  }

  /**
   * 写入任务表（原子操作）
   */
  _writeTasks(data) {
    fs.writeFileSync(TASKS_FILE, JSON.stringify(data, null, 2), 'utf-8');
  }

  /**
   * 生成任务 ID
   */
  _generateTaskId(data) {
    const today = dayjs().format('YYYYMMDD');
    const lastId = data.lastTaskId || 0;
    const newId = lastId + 1;
    data.lastTaskId = newId;
    return `task-${today}-${String(newId).padStart(3, '0')}`;
  }

  /**
   * 创建任务
   */
  createTask(options) {
    const { title, type = 'code', priority = 'medium', instruction, deadline, inputFiles = [], outputFiles = [] } = options;

    const data = this._readTasks();
    const taskId = this._generateTaskId(data);

    const task = {
      id: taskId,
      title,
      type,
      priority,
      status: 'pending',
      instruction: instruction || title,
      assignee: null,
      assignedAt: null,
      startedAt: null,
      submittedAt: null,
      completedAt: null,
      retryCount: 0,
      createdAt: dayjs().toISOString(),
      deadline: deadline || dayjs().add(3, 'minute').toISOString(),
      input: { resources: inputFiles },
      output: { resources: outputFiles },
      result: null,
      error: null
    };

    data.tasks.push(task);
    this._writeTasks(data);

    // 创建任务素材目录
    const taskDir = path.join(WORKSPACE_DIR, 'shared', 'tasks', taskId);
    if (!fs.existsSync(taskDir)) {
      fs.mkdirSync(taskDir, { recursive: true });
    }

    return task;
  }

  /**
   * 获取所有任务
   */
  getTasks(filter = {}) {
    const data = this._readTasks();
    let tasks = data.tasks;

    if (filter.status) {
      tasks = tasks.filter(t => t.status === filter.status);
    }
    if (filter.type) {
      tasks = tasks.filter(t => t.type === filter.type);
    }
    if (filter.priority) {
      tasks = tasks.filter(t => t.priority === filter.priority);
    }
    if (filter.assignee) {
      tasks = tasks.filter(t => t.assignee === filter.assignee);
    }

    return tasks.sort((a, b) => dayjs(b.createdAt).valueOf() - dayjs(a.createdAt).valueOf());
  }

  /**
   * 获取单个任务
   */
  getTask(taskId) {
    const data = this._readTasks();
    return data.tasks.find(t => t.id === taskId);
  }

  /**
   * 更新任务状态
   */
  updateTaskStatus(taskId, status, extra = {}) {
    const data = this._readTasks();
    const task = data.tasks.find(t => t.id === taskId);
    
    if (!task) {
      throw new Error(`任务不存在: ${taskId}`);
    }

    task.status = status;

    // 更新相关时间戳
    const now = dayjs().toISOString();
    if (status === 'assigned' && !task.assignedAt) {
      task.assignedAt = now;
    }
    if (status === 'running' && !task.startedAt) {
      task.startedAt = now;
    }
    if (status === 'submitted' && !task.submittedAt) {
      task.submittedAt = now;
    }
    if (status === 'done' && !task.completedAt) {
      task.completedAt = now;
    }

    // 合并额外字段
    Object.assign(task, extra);

    this._writeTasks(data);
    return task;
  }

  /**
   * 锁定任务（分配给节点）
   */
  assignTask(taskId, nodeId) {
    return this.updateTaskStatus(taskId, 'assigned', { assignee: nodeId });
  }

  /**
   * 开始执行任务
   */
  startTask(taskId) {
    return this.updateTaskStatus(taskId, 'running');
  }

  /**
   * 提交任务结果
   */
  submitTask(taskId, result) {
    return this.updateTaskStatus(taskId, 'submitted', { result });
  }

  /**
   * 完成任务
   */
  completeTask(taskId) {
    return this.updateTaskStatus(taskId, 'done');
  }

  /**
   * 标记任务失败
   */
  failTask(taskId, error) {
    const data = this._readTasks();
    const task = data.tasks.find(t => t.id === taskId);
    
    if (!task) {
      throw new Error(`任务不存在: ${taskId}`);
    }

    task.error = error;
    task.retryCount = (task.retryCount || 0) + 1;

    // 检查是否可重试
    if (task.retryCount < 2) {
      task.status = 'pending';
      task.assignee = null;
      task.assignedAt = null;
    } else {
      task.status = 'failed';
    }

    this._writeTasks(data);
    return task;
  }

  /**
   * 删除任务
   */
  deleteTask(taskId) {
    const data = this._readTasks();
    const index = data.tasks.findIndex(t => t.id === taskId);
    
    if (index === -1) {
      throw new Error(`任务不存在: ${taskId}`);
    }

    data.tasks.splice(index, 1);
    this._writeTasks(data);

    // 删除任务素材目录
    const taskDir = path.join(WORKSPACE_DIR, 'shared', 'tasks', taskId);
    if (fs.existsSync(taskDir)) {
      fs.rmSync(taskDir, { recursive: true });
    }

    return true;
  }

  /**
   * 获取待执行任务（按优先级和时间排序）
   */
  getPendingTasks() {
    const data = this._readTasks();
    return data.tasks
      .filter(t => t.status === 'pending')
      .sort((a, b) => {
        // 优先级排序：高 > 中 > 低
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        if (priorityOrder[b.priority] !== priorityOrder[a.priority]) {
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        }
        // 同优先级按创建时间
        return dayjs(a.createdAt).valueOf() - dayjs(b.createdAt).valueOf();
      });
  }
}

module.exports = { TaskManager };
