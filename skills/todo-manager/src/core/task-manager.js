const { v4: uuidv4 } = require('uuid');
const dayjs = require('dayjs');
const Storage = require('./storage');
const TimeParser = require('./time-parser');
const StrategyEngine = require('../reminder/strategy-engine');

class TaskManager {
  constructor(dataPath) {
    this.storage = new Storage(dataPath);
  }

  /**
   * 创建任务
   * @param {Object} taskData - 任务数据
   * @returns {Object} 创建的任务
   */
  createTask(taskData) {
    const { title, description, type, deadline, priority, reminderStrategy } = taskData;

    // 解析截止时间
    const parsedDeadline = TimeParser.parse(deadline);
    const taskType = TimeParser.inferTaskType(parsedDeadline);

    // 推断任务类型（如果未指定）
    const inferredType = type || this._inferTaskType(title, description);

    // 设置默认提醒策略（非年度任务才有提醒）
    const isAnnual = TimeParser.isAnnualTask(parsedDeadline);
    const defaultStrategy = isAnnual 
      ? null 
      : this._getDefaultStrategy(taskType, reminderStrategy);

    // 生成唯一编号（日期+序号）
    const uniqueId = this._generateUniqueId();

    // 分配待办编号
    const todoNumber = this._allocateTodoNumber();

    const task = {
      id: uuidv4(),
      uniqueId,
      todoNumber,
      title,
      description: description || '',
      type: inferredType,
      deadline: parsedDeadline,
      priority: priority || 'medium',
      status: 'pending',
      createdAt: dayjs().toISOString(),
      completedAt: null,
      reminderStrategy: defaultStrategy,
      reminders: [],
      comments: []
    };

    // 生成提醒时间点（非年度任务）
    if (!isAnnual) {
      task.reminders = StrategyEngine.generateReminders(task);
    }

    // 保存任务
    const tasks = this.storage.getTasks();
    tasks.push(task);
    this.storage.saveTasks(tasks);

    return task;
  }

  /**
   * 更新任务
   * @param {string} taskId - 任务 ID
   * @param {Object} updates - 更新的字段
   * @returns {Object|null} 更新后的任务
   */
  updateTask(taskId, updates) {
    const tasks = this.storage.getTasks();
    const index = tasks.findIndex(t => t.id === taskId);

    if (index === -1) return null;

    const task = tasks[index];

    // 更新字段
    Object.assign(task, updates);

    // 如果更新了截止时间或提醒策略，重新生成提醒
    if (updates.deadline || updates.reminderStrategy) {
      if (updates.deadline) {
        task.deadline = TimeParser.parse(updates.deadline);
      }
      task.reminders = StrategyEngine.generateReminders(task);
    }

    tasks[index] = task;
    this.storage.saveTasks(tasks);

    return task;
  }

  /**
   * 完成任务
   * @param {string} taskId - 任务 ID（支持 uuid/uniqueId/todoNumber）
   * @param {string} comment - 完成时的评论（可选）
   * @returns {Object|null} 完成的任务
   */
  completeTask(taskId, comment = null) {
    const task = this._findTask(taskId);
    if (!task) return null;

    // 释放待办编号
    const releasedNumber = task.todoNumber;
    if (releasedNumber) {
      this._releaseTodoNumber(releasedNumber);
    }

    // 添加评论
    const updates = {
      status: 'completed',
      completedAt: dayjs().toISOString(),
      todoNumber: 0
    };

    if (comment) {
      task.comments = task.comments || [];
      task.comments.push({
        content: comment,
        createdAt: dayjs().toISOString(),
        action: 'completed'
      });
      updates.comments = task.comments;
    }

    return this.updateTask(task.id, updates);
  }

  /**
   * 取消任务
   * @param {string} taskId - 任务 ID（支持 uuid/uniqueId/todoNumber）
   * @param {string} comment - 取消时的评论（可选）
   * @returns {Object|null} 取消的任务
   */
  cancelTask(taskId, comment = null) {
    const task = this._findTask(taskId);
    if (!task) return null;

    // 释放待办编号
    const releasedNumber = task.todoNumber;
    if (releasedNumber) {
      this._releaseTodoNumber(releasedNumber);
    }

    // 添加评论
    const updates = {
      status: 'cancelled',
      completedAt: dayjs().toISOString(),
      todoNumber: 0
    };

    if (comment) {
      task.comments = task.comments || [];
      task.comments.push({
        content: comment,
        createdAt: dayjs().toISOString(),
        action: 'cancelled'
      });
      updates.comments = task.comments;
    }

    return this.updateTask(task.id, updates);
  }

  /**
   * 为任务添加评论
   * @param {string} taskId - 任务 ID（支持 uuid/uniqueId/todoNumber）
   * @param {string} content - 评论内容
   * @returns {Object|null} 更新后的任务
   */
  addComment(taskId, content) {
    const task = this._findTask(taskId);
    if (!task) return null;

    const comments = task.comments || [];
    comments.push({
      content: content,
      createdAt: dayjs().toISOString()
    });

    return this.updateTask(task.id, { comments });
  }

  /**
   * 获取任务的最近 N 条评论
   * @param {string} taskId - 任务 ID
   * @param {number} limit - 返回数量，默认3
   * @returns {Array} 评论列表
   */
  getTaskComments(taskId, limit = 3) {
    const task = this._findTask(taskId);
    if (!task || !task.comments) return [];

    return task.comments.slice(-limit);
  }

  /**
   * 删除任务
   * @param {string} taskId - 任务 ID
   * @returns {boolean} 是否删除成功
   */
  deleteTask(taskId) {
    const tasks = this.storage.getTasks();
    const filtered = tasks.filter(t => t.id !== taskId);

    if (filtered.length === tasks.length) return false;

    this.storage.saveTasks(filtered);
    return true;
  }

  /**
   * 获取任务
   * @param {string} taskId - 任务 ID
   * @returns {Object|null} 任务对象
   */
  getTask(taskId) {
    const tasks = this.storage.getTasks();
    return tasks.find(t => t.id === taskId) || null;
  }

  /**
   * 获取所有任务
   * @param {Object} filters - 过滤条件
   * @returns {Array} 任务列表
   */
  getTasks(filters = {}) {
    let tasks = this.storage.getTasks();

    // 状态过滤
    if (filters.status) {
      tasks = tasks.filter(t => t.status === filters.status);
    }

    // 类型过滤
    if (filters.type) {
      tasks = tasks.filter(t => t.type === filters.type);
    }

    // 优先级过滤
    if (filters.priority) {
      tasks = tasks.filter(t => t.priority === filters.priority);
    }

    // 时间范围过滤
    if (filters.timeRange) {
      tasks = this._filterByTimeRange(tasks, filters.timeRange);
    }

    return tasks;
  }

  /**
   * 获取逾期任务
   * @returns {Array} 逾期任务列表
   */
  getOverdueTasks() {
    const now = dayjs();
    return this.storage.getTasks().filter(t => 
      t.status === 'pending' && dayjs(t.deadline).isBefore(now)
    );
  }

  /**
   * 根据时间范围过滤任务
   * @param {Array} tasks - 任务列表
   * @param {string} timeRange - 时间范围（today/tomorrow/week/month/overdue）
   * @returns {Array} 过滤后的任务列表
   */
  _filterByTimeRange(tasks, timeRange) {
    const now = dayjs();

    switch (timeRange) {
      case 'today':
        return tasks.filter(t => dayjs(t.deadline).isSame(now, 'day'));
      case 'tomorrow':
        return tasks.filter(t => dayjs(t.deadline).isSame(now.add(1, 'day'), 'day'));
      case 'week':
        return tasks.filter(t => dayjs(t.deadline).isSame(now, 'week'));
      case 'month':
        return tasks.filter(t => dayjs(t.deadline).isSame(now, 'month'));
      case 'overdue':
        return tasks.filter(t => t.status === 'pending' && dayjs(t.deadline).isBefore(now));
      default:
        return tasks;
    }
  }

  /**
   * 推断任务类型
   * @param {string} title - 任务标题
   * @param {string} description - 任务描述
   * @returns {string} 任务类型
   */
  _inferTaskType(title, description) {
    const text = `${title} ${description}`.toLowerCase();

    const workKeywords = ['工作', '开发', '代码', '会议', '项目', '需求', '设计', '测试', '部署', 'work', 'code', 'meeting', 'project'];
    const studyKeywords = ['学习', '阅读', '课程', '教程', '文档', 'study', 'learn', 'read', 'course'];
    const personalKeywords = ['买', '购物', '健身', '运动', '看电影', '约会', 'buy', 'shopping', 'gym', 'movie'];

    if (workKeywords.some(kw => text.includes(kw))) return 'work';
    if (studyKeywords.some(kw => text.includes(kw))) return 'study';
    if (personalKeywords.some(kw => text.includes(kw))) return 'personal';

    return 'other';
  }

  /**
   * 获取默认提醒策略
   * @param {string} taskType - 任务类型（daily/weekly/monthly）
   * @param {Object} customStrategy - 用户自定义策略
   * @returns {Object} 提醒策略
   */
  _getDefaultStrategy(taskType, customStrategy) {
    const defaults = {
      daily: { type: 'daily', frequency: 'once', exceptions: {}, customTime: '09:00' },
      weekly: { type: 'weekly', frequency: 'someday', exceptions: {}, customTime: '10:00' },
      monthly: { type: 'monthly', frequency: 'someday', exceptions: {}, customTime: '10:00' }
    };

    return customStrategy || defaults[taskType] || defaults.daily;
  }

  /**
   * 生成唯一编号（YYYYMMDD-NNN）
   * @returns {string} 唯一编号
   */
  _generateUniqueId() {
    const today = dayjs().format('YYYYMMDD');
    const tasks = this.storage.getTasks();
    
    // 找出今天创建的任务中最大的序号
    const todayTasks = tasks.filter(t => t.uniqueId && t.uniqueId.startsWith(today));
    let maxSeq = 0;
    
    todayTasks.forEach(t => {
      const match = t.uniqueId.match(/-(\d+)$/);
      if (match) {
        const seq = parseInt(match[1]);
        if (seq > maxSeq) maxSeq = seq;
      }
    });

    const nextSeq = (maxSeq + 1).toString().padStart(3, '0');
    return `${today}-${nextSeq}`;
  }

  /**
   * 分配待办编号（1-100，完成/取消时回收，新任务从最大+1，超过100从1找空号）
   * @returns {number} 待办编号
   */
  _allocateTodoNumber() {
    const tasks = this.storage.getTasks();
    const usedNumbers = tasks
      .filter(t => t.status === 'pending' && t.todoNumber && t.todoNumber > 0)
      .map(t => t.todoNumber)
      .sort((a, b) => a - b);

    // 先尝试从最大编号+1开始
    let maxUsed = usedNumbers.length > 0 ? Math.max(...usedNumbers) : 0;
    
    // 如果小于100，从最大+1开始找
    if (maxUsed < 100) {
      const nextNumber = maxUsed + 1;
      if (!usedNumbers.includes(nextNumber)) {
        return nextNumber;
      }
    }

    // 否则从1开始找空号
    for (let i = 1; i <= 100; i++) {
      if (!usedNumbers.includes(i)) {
        return i;
      }
    }

    // 如果1-100都满了，返回null（理论上不太可能）
    return null;
  }

  /**
   * 释放待办编号（标记为可重用，设置为0表示已回收）
   * @param {number} todoNumber - 待办编号
   */
  _releaseTodoNumber(todoNumber) {
    // 编号会在下次分配时自动重用，这里不需要额外操作
  }

  /**
   * 查找任务（支持 uuid/uniqueId/todoNumber）
   * @param {string|number} identifier - 任务标识
   * @returns {Object|null} 任务对象
   */
  _findTask(identifier) {
    const tasks = this.storage.getTasks();

    // 尝试按 todoNumber 查找（数字）
    if (typeof identifier === 'number' || /^\d+$/.test(identifier)) {
      const todoNumber = parseInt(identifier);
      const task = tasks.find(t => t.todoNumber === todoNumber);
      if (task) return task;
    }

    // 尝试按 uniqueId 查找（YYYYMMDD-NNN）
    if (/^\d{8}-\d{3}$/.test(identifier)) {
      const task = tasks.find(t => t.uniqueId === identifier);
      if (task) return task;
    }

    // 尝试按 uuid 查找
    const task = tasks.find(t => t.id === identifier);
    return task || null;
  }

  /**
   * 更新任务（支持多种标识符）
   * @param {string|number} taskId - 任务标识
   * @param {Object} updates - 更新的字段
   * @returns {Object|null} 更新后的任务
   */
  updateTaskById(taskId, updates) {
    const task = this._findTask(taskId);
    if (!task) return null;
    return this.updateTask(task.id, updates);
  }

  /**
   * 删除任务（支持多种标识符）
   * @param {string|number} taskId - 任务标识
   * @returns {boolean} 是否删除成功
   */
  deleteTaskById(taskId) {
    const task = this._findTask(taskId);
    if (!task) return false;

    // 释放待办编号
    if (task.todoNumber) {
      this._releaseTodoNumber(task.todoNumber);
    }

    return this.deleteTask(task.id);
  }
}

module.exports = TaskManager;
