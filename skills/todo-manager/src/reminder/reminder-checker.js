const dayjs = require('dayjs');
const isBetween = require('dayjs/plugin/isBetween');
dayjs.extend(isBetween);

const Storage = require('../core/storage');
const Notifier = require('./notifier');
const StrategyEngine = require('./strategy-engine');

class ReminderChecker {
  constructor(dataPath, feishuSender) {
    this.storage = new Storage(dataPath);
    this.feishuSender = feishuSender;
  }

  /**
   * 检查并发送提醒
   */
  async check() {
    const tasks = this.storage.getTasks();
    const config = this.storage.getConfig();
    const now = dayjs();

    let sentCount = 0;

    for (const task of tasks) {
      if (task.status !== 'pending') continue;

      // 检查每个提醒时间点
      for (const reminder of task.reminders) {
        if (reminder.sent) continue;

        const scheduledTime = dayjs(reminder.scheduledTime);

        // 检查是否到了提醒时间（允许 5 分钟误差）
        if (now.isBetween(scheduledTime.subtract(5, 'minute'), scheduledTime.add(5, 'minute'))) {
          // 检查例外条件
          if (this._shouldSendReminder(task, config)) {
            await Notifier.send(task, this.feishuSender);
            reminder.sent = true;
            reminder.sentAt = now.toISOString();
            sentCount++;
          }
        }
      }
    }

    // 保存更新后的任务
    if (sentCount > 0) {
      this.storage.saveTasks(tasks);
    }

    return sentCount;
  }

  /**
   * 检查是否应该发送提醒（根据例外条件）
   * @param {Object} task - 任务对象
   * @param {Object} config - 配置对象
   * @returns {boolean}
   */
  _shouldSendReminder(task, config) {
    const { reminderStrategy } = task;
    if (!reminderStrategy || !reminderStrategy.exceptions) return true;

    const { workHoursOnly, workdaysOnly } = reminderStrategy.exceptions;

    // 检查工作日
    if (workdaysOnly) {
      const day = dayjs().day();
      if (!config.workdays.includes(day)) {
        return false;
      }
    }

    // 检查工作时间
    if (workHoursOnly) {
      if (!StrategyEngine.isWorkHours(config)) {
        return false;
      }
    }

    return true;
  }
}

module.exports = ReminderChecker;
