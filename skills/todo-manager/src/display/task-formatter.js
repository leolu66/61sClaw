const dayjs = require('dayjs');

class TaskFormatter {
  /**
   * 按时间范围和类型分组显示任务
   * @param {Array} tasks - 任务列表
   * @param {string} groupBy - 分组方式（time/type/priority/table）
   * @param {string} statusFilter - 状态过滤（pending/completed/cancelled）
   * @param {string} typeFilter - 类型过滤（work/personal/study/other）
   * @param {boolean} showLegend - 是否显示图例
   * @returns {string} 格式化后的任务列表
   */
  static format(tasks, groupBy = 'time', statusFilter = 'pending', typeFilter = null, showLegend = false) {
    if (tasks.length === 0) {
      return '📭 暂无任务';
    }

    let output = '';
    
    // 表格模式不需要标题
    if (groupBy !== 'table') {
      const title = this._getStatusTitle(statusFilter, tasks.length, typeFilter);
      output += title + '\n';
    }
    
    switch (groupBy) {
      case 'time':
        output += this._formatByTime(tasks);
        break;
      case 'type':
        output += this._formatByType(tasks);
        break;
      case 'priority':
        output += this._formatByPriority(tasks);
        break;
      case 'table':
        output += this._formatAsTable(tasks);
        break;
      default:
        output += this._formatByTime(tasks);
    }

    if (showLegend && groupBy !== 'table') {
      output += '\n\n' + this._getLegend();
    }

    return output;
  }

  /**
   * 根据状态获取标题
   */
  static _getStatusTitle(statusFilter, count, typeFilter = null) {
    const typeTitles = {
      work: '💼 待办工作',
      personal: '🏠 待办个人',
      study: '📚 待办学习',
      other: '📌 待办其他'
    };

    if (statusFilter === 'pending') {
      if (typeFilter && typeTitles[typeFilter]) {
        return `${typeTitles[typeFilter]}（共 ${count} 个）`;
      }
      return `📋 待办任务（共 ${count} 个）`;
    }
    
    if (statusFilter === 'completed') {
      if (typeFilter && typeTitles[typeFilter]) {
        return `${typeTitles[typeFilter]} - 已完成（共 ${count} 个）`;
      }
      return `✅ 已完成任务（共 ${count} 个）`;
    }
    
    if (statusFilter === 'cancelled') {
      if (typeFilter && typeTitles[typeFilter]) {
        return `${typeTitles[typeFilter]} - 已取消（共 ${count} 个）`;
      }
      return `❌ 已取消任务（共 ${count} 个）`;
    }
    
    return `📋 任务列表（共 ${count} 个）`;
  }

  /**
   * 获取图例说明
   */
  static _getLegend() {
    return `
📖 图例说明
${'─'.repeat(40)}
优先级: 🔴 高 | 🟡 中 | 🟢 低
类型: 💼 工作 | 🏠 个人 | 📚 学习 | 📌 其他
    `.trim();
  }

  /**
   * 按时间分组
   */
  static _formatByTime(tasks) {
    const now = dayjs();
    const groups = {
      overdue: [],
      today: [],
      tomorrow: [],
      thisWeek: [],
      thisMonth: [],
      later: []
    };

    tasks.forEach(task => {
      const deadline = dayjs(task.deadline);
      
      if (task.status === 'pending' && deadline.isBefore(now)) {
        groups.overdue.push(task);
      } else if (deadline.isSame(now, 'day')) {
        groups.today.push(task);
      } else if (deadline.isSame(now.add(1, 'day'), 'day')) {
        groups.tomorrow.push(task);
      } else if (deadline.isSame(now, 'week')) {
        groups.thisWeek.push(task);
      } else if (deadline.isSame(now, 'month')) {
        groups.thisMonth.push(task);
      } else {
        groups.later.push(task);
      }
    });

    let output = '';

    if (groups.overdue.length > 0) {
      output += '\n⚠️  逾期任务\n';
      output += this._formatTaskList(groups.overdue, true);
    }

    if (groups.today.length > 0) {
      output += '\n📅 今天\n';
      output += this._formatTaskList(groups.today);
    }

    if (groups.tomorrow.length > 0) {
      output += '\n📆 明天\n';
      output += this._formatTaskList(groups.tomorrow);
    }

    if (groups.thisWeek.length > 0) {
      output += '\n📊 本周\n';
      output += this._formatTaskList(groups.thisWeek);
    }

    if (groups.thisMonth.length > 0) {
      output += '\n📈 本月\n';
      output += this._formatTaskList(groups.thisMonth);
    }

    if (groups.later.length > 0) {
      output += '\n🔮 更晚\n';
      output += this._formatTaskList(groups.later);
    }

    return output.trim();
  }

  /**
   * 格式化为表格（无表头）
   * 字段：编号，优先级，类别，内容，截止时间
   */
  static _formatAsTable(tasks) {
    const now = dayjs();
    
    // 先按时间段分组，再按截止时间排序
    const groups = {
      today: [],
      tomorrow: [],
      thisWeek: [],
      thisMonth: [],
      later: []
    };

    tasks.forEach(task => {
      const deadline = dayjs(task.deadline);
      
      if (deadline.isSame(now, 'day')) {
        groups.today.push(task);
      } else if (deadline.isSame(now.add(1, 'day'), 'day')) {
        groups.tomorrow.push(task);
      } else if (deadline.isSame(now, 'week')) {
        groups.thisWeek.push(task);
      } else if (deadline.isSame(now, 'month')) {
        groups.thisMonth.push(task);
      } else {
        groups.later.push(task);
      }
    });

    const priorityMap = {
      high: '高',
      medium: '中',
      low: '低'
    };

    const typeMap = {
      work: '工作',
      personal: '个人',
      study: '学习',
      other: '其他'
    };

    let output = '';

    // 今天
    if (groups.today.length > 0) {
      groups.today.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
      groups.today.forEach(task => {
        output += `${task.todoNumber || ''} | ${priorityMap[task.priority] || ''} | ${typeMap[task.type] || ''} | ${task.title || ''} | 今天\n`;
      });
    }

    // 明天
    if (groups.tomorrow.length > 0) {
      groups.tomorrow.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
      groups.tomorrow.forEach(task => {
        output += `${task.todoNumber || ''} | ${priorityMap[task.priority] || ''} | ${typeMap[task.type] || ''} | ${task.title || ''} | 明天\n`;
      });
    }

    // 本周
    if (groups.thisWeek.length > 0) {
      groups.thisWeek.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
      groups.thisWeek.forEach(task => {
        const dd = dayjs(task.deadline).format('MM-DD');
        output += `${task.todoNumber || ''} | ${priorityMap[task.priority] || ''} | ${typeMap[task.type] || ''} | ${task.title || ''} | 本周(${dd})\n`;
      });
    }

    // 本月
    if (groups.thisMonth.length > 0) {
      groups.thisMonth.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
      groups.thisMonth.forEach(task => {
        const dd = dayjs(task.deadline).format('MM-DD');
        output += `${task.todoNumber || ''} | ${priorityMap[task.priority] || ''} | ${typeMap[task.type] || ''} | ${task.title || ''} | 本月(${dd})\n`;
      });
    }

    // 长期
    if (groups.later.length > 0) {
      groups.later.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
      groups.later.forEach(task => {
        const dd = dayjs(task.deadline).format('MM-DD');
        output += `${task.todoNumber || ''} | ${priorityMap[task.priority] || ''} | ${typeMap[task.type] || ''} | ${task.title || ''} | ${dd}\n`;
      });
    }

    return output.trim();
  }

  /**
   * 按类型分组
   */
  static _formatByType(tasks) {
    const groups = {
      work: [],
      personal: [],
      study: [],
      other: []
    };

    tasks.forEach(task => {
      groups[task.type].push(task);
    });

    let output = '';

    if (groups.work.length > 0) {
      output += '\n💼 工作\n';
      output += this._formatTaskList(groups.work);
    }

    if (groups.personal.length > 0) {
      output += '\n🏠 个人\n';
      output += this._formatTaskList(groups.personal);
    }

    if (groups.study.length > 0) {
      output += '\n📚 学习\n';
      output += this._formatTaskList(groups.study);
    }

    if (groups.other.length > 0) {
      output += '\n📌 其他\n';
      output += this._formatTaskList(groups.other);
    }

    return output.trim();
  }

  /**
   * 按优先级分组
   */
  static _formatByPriority(tasks) {
    const groups = {
      high: [],
      medium: [],
      low: []
    };

    tasks.forEach(task => {
      groups[task.priority].push(task);
    });

    let output = '';

    if (groups.high.length > 0) {
      output += '\n🔴 高优先级\n';
      output += this._formatTaskList(groups.high);
    }

    if (groups.medium.length > 0) {
      output += '\n🟡 中优先级\n';
      output += this._formatTaskList(groups.medium);
    }

    if (groups.low.length > 0) {
      output += '\n🟢 低优先级\n';
      output += this._formatTaskList(groups.low);
    }

    return output.trim();
  }

  /**
   * 格式化任务列表
   */
  static _formatTaskList(tasks, showOverdue = false) {
    return tasks.map(task => {
      const typeEmoji = {
        work: '💼',
        personal: '🏠',
        study: '📚',
        other: '📌'
      };

      const priorityEmoji = {
        high: '🔴',
        medium: '🟡',
        low: '🟢'
      };

      const deadline = dayjs(task.deadline).format('MM-DD HH:mm');
      const overdueFlag = showOverdue ? '⚠️ ' : '';
      const todoNum = task.todoNumber ? `[${task.todoNumber}]` : '';

      return `  ${overdueFlag}${todoNum} ${priorityEmoji[task.priority]} ${typeEmoji[task.type]} ${task.title} (${deadline})`;
    }).join('\n');
  }

  /**
   * 格式化单个任务详情
   */
  static formatDetail(task) {
    const typeEmoji = {
      work: '💼 工作',
      personal: '🏠 个人',
      study: '📚 学习',
      other: '📌 其他'
    };

    const priorityEmoji = {
      high: '🔴 高',
      medium: '🟡 中',
      low: '🟢 低'
    };

    const statusEmoji = {
      pending: '⏳ 进行中',
      completed: '✅ 已完成',
      cancelled: '❌ 已取消'
    };

    const deadline = dayjs(task.deadline).format('YYYY-MM-DD HH:mm');
    const now = dayjs();
    const isOverdue = task.status === 'pending' && dayjs(task.deadline).isBefore(now);

    let output = `
📋 任务详情
${'='.repeat(50)}
唯一编号: ${task.uniqueId || 'N/A'}
${task.todoNumber ? `待办编号: ${task.todoNumber}` : ''}
标题: ${task.title}
${task.description ? `描述: ${task.description}` : ''}
类型: ${typeEmoji[task.type]}
优先级: ${priorityEmoji[task.priority]}
状态: ${statusEmoji[task.status]}
截止时间: ${deadline} ${isOverdue ? '⚠️ 已逾期' : ''}
创建时间: ${dayjs(task.createdAt).format('YYYY-MM-DD HH:mm')}
${task.completedAt ? `完成时间: ${dayjs(task.completedAt).format('YYYY-MM-DD HH:mm')}` : ''}
${'='.repeat(50)}
    `.trim();

    return output;
  }
}

module.exports = TaskFormatter;
