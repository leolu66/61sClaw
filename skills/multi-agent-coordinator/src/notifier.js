/**
 * Notifier - 通知模块
 * 负责发送任务状态变化通知
 */

const { sendNotification } = require('../feishu-notifier/index');

class Notifier {
  constructor() {
    this.enabled = true;
  }

  /**
   * 发送任务创建通知
   */
  async notifyTaskCreated(task) {
    if (!this.enabled) return;

    const message = `📝 新任务已创建

**${task.title}**
- 编号: ${task.id}
- 类型: ${task.type}
- 优先级: ${task.priority === 'high' ? '高' : task.priority === 'medium' ? '中' : '低'}
- 截止: ${new Date(task.deadline).toLocaleTimeString()}

等待节点拉取执行...`;

    try {
      await sendNotification(message);
    } catch (error) {
      console.error(`[Notifier] 发送通知失败: ${error.message}`);
    }
  }

  /**
   * 发送任务开始执行通知
   */
  async notifyTaskStarted(task) {
    if (!this.enabled) return;

    const message = `▶️ 任务开始执行

**${task.title}** (${task.id})
执行节点: ${task.assignee}

开始时间: ${new Date(task.startedAt).toLocaleTimeString()}`;

    try {
      await sendNotification(message);
    } catch (error) {
      console.error(`[Notifier] 发送通知失败: ${error.message}`);
    }
  }

  /**
   * 发送任务完成通知
   */
  async notifyTaskSubmitted(task) {
    if (!this.enabled) return;

    const message = `✅ 任务已完成

**${task.title}** (${task.id})
执行节点: ${task.assignee}
完成时间: ${new Date(task.submittedAt).toLocaleTimeString()}

请确认任务结果或回复"确认任务 ${task.id}"`;

    try {
      await sendNotification(message);
    } catch (error) {
      console.error(`[Notifier] 发送通知失败: ${error.message}`);
    }
  }

  /**
   * 发送任务确认完成通知
   */
  async notifyTaskConfirmed(task) {
    if (!this.enabled) return;

    const message = `🎉 任务已确认完成

**${task.title}** (${task.id})
确认时间: ${new Date().toLocaleTimeString()}`;

    try {
      await sendNotification(message);
    } catch (error) {
      console.error(`[Notifier] 发送通知失败: ${error.message}`);
    }
  }

  /**
   * 发送任务失败通知
   */
  async notifyTaskFailed(task) {
    if (!this.enabled) return;

    const message = `❌ 任务执行失败

**${task.title}** (${task.id})
执行节点: ${task.assignee}
重试次数: ${task.retryCount}/2
错误信息: ${task.error?.message || '未知错误'}

请回复"重处理任务 ${task.id}"重试或"取消任务 ${task.id}"放弃`;

    try {
      await sendNotification(message);
    } catch (error) {
      console.error(`[Notifier] 发送通知失败: ${error.message}`);
    }
  }

  /**
   * 发送节点离线通知
   */
  async notifyNodeOffline(nodeId) {
    if (!this.enabled) return;

    const message = `⚠️ 节点已离线

节点: ${nodeId}
状态: 离线
时间: ${new Date().toLocaleTimeString()}`;

    try {
      await sendNotification(message);
    } catch (error) {
      console.error(`[Notifier] 发送通知失败: ${error.message}`);
    }
  }

  /**
   * 发送节点恢复在线通知
   */
  async notifyNodeOnline(nodeId) {
    if (!this.enabled) return;

    const message = `✅ 节点恢复在线

节点: ${nodeId}
时间: ${new Date().toLocaleTimeString()}`;

    try {
      await sendNotification(message);
    } catch (error) {
      console.error(`[Notifier] 发送通知失败: ${error.message}`);
    }
  }

  /**
   * 发送节点状态摘要
   */
  async notifyStatusSummary(summary) {
    if (!this.enabled) return;

    const message = `📊 节点状态摘要

总计: ${summary.total} | 在线: ${summary.online} | 忙碌: ${summary.busy} | 离线: ${summary.offline}
当前任务数: ${summary.totalTasks}`;

    try {
      await sendNotification(message);
    } catch (error) {
      console.error(`[Notifier] 发送通知失败: ${error.message}`);
    }
  }

  /**
   * 启用/禁用通知
   */
  setEnabled(enabled) {
    this.enabled = enabled;
  }
}

module.exports = { Notifier };
