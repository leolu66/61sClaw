const path = require('path');
const TaskManager = require('../src/core/task-manager');
const TaskFormatter = require('../src/display/task-formatter');
const dayjs = require('dayjs');

const dataPath = path.join(__dirname, '../data/tasks.json');
const manager = new TaskManager(dataPath);

/**
 * 处理用户的任务管理请求
 * @param {string} action - 操作类型（create/list/complete/delete/update/overdue）
 * @param {Object} params - 参数
 */
async function handleTaskRequest(action, params = {}) {
  try {
    switch (action) {
      case 'create': {
        const task = manager.createTask(params);
        return {
          success: true,
          message: `✅ 任务创建成功`,
          data: TaskFormatter.formatDetail(task)
        };
      }

      case 'list': {
        const { groupBy = 'table', status = 'pending', type = null, ...filters } = params;
        const tasks = manager.getTasks({ status, type, ...filters });
        let output = TaskFormatter.format(tasks, groupBy, status, type, groupBy !== 'table');
        
        // 表格模式不显示重要提醒
        if (groupBy !== 'table' && status === 'pending') {
          const reminders = _generateReminders(tasks);
          if (reminders) {
            output += '\n\n' + '─'.repeat(40) + '\n' + reminders;
          }
        }
        
        return {
          success: true,
          message: `📋 任务列表（共 ${tasks.length} 个）`,
          data: output
        };
      }

      case 'detail': {
        const task = manager.getTask(params.taskId);
        if (!task) {
          return { success: false, message: '❌ 任务不存在' };
        }
        return {
          success: true,
          data: TaskFormatter.formatDetail(task)
        };
      }

      case 'complete': {
        const task = manager.completeTask(params.taskId);
        if (!task) {
          return { success: false, message: '❌ 任务不存在' };
        }
        return {
          success: true,
          message: `✅ 任务已完成：${task.title}`
        };
      }

      case 'cancel': {
        const task = manager.cancelTask(params.taskId);
        if (!task) {
          return { success: false, message: '❌ 任务不存在' };
        }
        return {
          success: true,
          message: `❌ 任务已取消：${task.title}`
        };
      }

      case 'delete': {
        const success = manager.deleteTaskById(params.taskId);
        if (!success) {
          return { success: false, message: '❌ 任务不存在' };
        }
        return {
          success: true,
          message: '🗑️  任务已删除'
        };
      }

      case 'update': {
        const task = manager.updateTaskById(params.taskId, params.updates);
        if (!task) {
          return { success: false, message: '❌ 任务不存在' };
        }
        return {
          success: true,
          message: `✅ 任务已更新：${task.title}`,
          data: TaskFormatter.formatDetail(task)
        };
      }

      case 'overdue': {
        const tasks = manager.getOverdueTasks();
        return {
          success: true,
          message: `⚠️  逾期任务（共 ${tasks.length} 个）`,
          data: TaskFormatter.format(tasks, 'time')
        };
      }

      default:
        return {
          success: false,
          message: '❌ 未知操作'
        };
    }
  } catch (error) {
    return {
      success: false,
      message: `❌ 操作失败：${error.message}`
    };
  }
}

/**
 * 生成重要提醒
 * @param {Array} tasks - 任务列表
 * @returns {string|null} 提醒文本
 */
function _generateReminders(tasks) {
  const now = dayjs();
  const urgentTasks = [];
  const highPriorityTasks = [];

  tasks.forEach(task => {
    const deadline = dayjs(task.deadline);
    const daysLeft = deadline.diff(now, 'day');

    // 3 天内截止的任务
    if (daysLeft <= 3 && daysLeft >= 0) {
      urgentTasks.push({ ...task, daysLeft });
    }

    // 高优先级任务
    if (task.priority === 'high' && task.status === 'pending') {
      highPriorityTasks.push(task);
    }
  });

  if (urgentTasks.length === 0 && highPriorityTasks.length === 0) {
    return null;
  }

  let output = '⚠️  重要提醒\n';

  if (urgentTasks.length > 0) {
    urgentTasks.sort((a, b) => a.daysLeft - b.daysLeft);
    urgentTasks.forEach(task => {
      const deadlineStr = dayjs(task.deadline).format('M 月 D 日');
      if (task.daysLeft === 0) {
        output += `- ${task.title} **今天截止**！\n`;
      } else if (task.daysLeft === 1) {
        output += `- ${task.title} **明天截止**！\n`;
      } else {
        output += `- ${task.title}（${deadlineStr}）\n`;
      }
    });
  }

  if (highPriorityTasks.length > 0 && urgentTasks.length === 0) {
    highPriorityTasks.forEach(task => {
      const deadlineStr = dayjs(task.deadline).format('M 月 D 日');
      output += `- ${task.title}（${deadlineStr}）\n`;
    });
  }

  return output.trim();
}

module.exports = { handleTaskRequest };
