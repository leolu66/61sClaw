const dayjs = require('dayjs');

class StrategyEngine {
  /**
   * 根据策略生成提醒时间点
   * @param {Object} task - 任务对象
   * @returns {Array} 提醒时间点数组
   */
  static generateReminders(task) {
    const { deadline, reminderStrategy } = task;
    const deadlineTime = dayjs(deadline);
    const reminders = [];

    if (!reminderStrategy || reminderStrategy.frequency === 'none') {
      return reminders;
    }

    const { type, frequency, exceptions, customTime } = reminderStrategy;
    const baseTime = customTime || '09:00';

    switch (type) {
      case 'daily':
        this._generateDailyReminders(reminders, deadlineTime, frequency, baseTime, exceptions);
        break;
      case 'weekly':
        this._generateWeeklyReminders(reminders, deadlineTime, frequency, baseTime, exceptions);
        break;
      case 'monthly':
        this._generateMonthlyReminders(reminders, deadlineTime, frequency, baseTime, exceptions);
        break;
    }

    // 过滤掉已经过期的提醒时间
    const now = dayjs();
    return reminders
      .filter(r => dayjs(r.scheduledTime).isAfter(now))
      .map(r => ({ ...r, sent: false, sentAt: null }));
  }

  static _generateDailyReminders(reminders, deadlineTime, frequency, baseTime, exceptions) {
    const taskDay = deadlineTime.startOf('day');
    const [hour, minute] = baseTime.split(':').map(Number);

    switch (frequency) {
      case 'once':
        reminders.push({
          scheduledTime: taskDay.hour(hour).minute(minute).toISOString()
        });
        break;

      case 'twice':
        reminders.push(
          { scheduledTime: taskDay.hour(9).minute(0).toISOString() },
          { scheduledTime: taskDay.hour(18).minute(0).toISOString() }
        );
        break;

      case 'every2h':
        for (let h = 9; h <= 17; h += 2) {
          reminders.push({
            scheduledTime: taskDay.hour(h).minute(0).toISOString()
          });
        }
        break;
    }
  }

  static _generateWeeklyReminders(reminders, deadlineTime, frequency, baseTime, exceptions) {
    const now = dayjs();
    const [hour, minute] = baseTime.split(':').map(Number);

    switch (frequency) {
      case 'someday': {
        // 默认周一提醒
        const weekStart = now.startOf('week');
        const monday = weekStart.add(1, 'day'); // dayjs 的 week 从周日开始，+1 天是周一
        if (monday.isBefore(deadlineTime)) {
          reminders.push({
            scheduledTime: monday.hour(hour).minute(minute).toISOString()
          });
        }
        break;
      }

      case 'everyday': {
        // 从今天到截止日期，每天提醒
        let current = now.startOf('day');
        while (current.isBefore(deadlineTime)) {
          if (this._checkExceptions(current, exceptions)) {
            reminders.push({
              scheduledTime: current.hour(hour).minute(minute).toISOString()
            });
          }
          current = current.add(1, 'day');
        }
        break;
      }
    }
  }

  static _generateMonthlyReminders(reminders, deadlineTime, frequency, baseTime, exceptions) {
    const now = dayjs();
    const [hour, minute] = baseTime.split(':').map(Number);

    switch (frequency) {
      case 'someday': {
        // 默认每月1号提醒
        const firstDay = now.startOf('month').date(1);
        if (firstDay.isBefore(deadlineTime)) {
          reminders.push({
            scheduledTime: firstDay.hour(hour).minute(minute).toISOString()
          });
        }
        break;
      }

      case 'everyMonday': {
        // 从今天到截止日期，每周一提醒
        let current = now.startOf('day');
        while (current.isBefore(deadlineTime)) {
          if (current.day() === 1 && this._checkExceptions(current, exceptions)) {
            reminders.push({
              scheduledTime: current.hour(hour).minute(minute).toISOString()
            });
          }
          current = current.add(1, 'day');
        }
        break;
      }

      case 'everyday': {
        // 从今天到截止日期，每天提醒
        let current = now.startOf('day');
        while (current.isBefore(deadlineTime)) {
          if (this._checkExceptions(current, exceptions)) {
            reminders.push({
              scheduledTime: current.hour(hour).minute(minute).toISOString()
            });
          }
          current = current.add(1, 'day');
        }
        break;
      }
    }
  }

  /**
   * 检查是否满足例外条件
   * @param {dayjs.Dayjs} time - 时间对象
   * @param {Object} exceptions - 例外条件
   * @returns {boolean} 是否满足条件
   */
  static _checkExceptions(time, exceptions) {
    if (!exceptions) return true;

    // 仅工作日
    if (exceptions.workdaysOnly) {
      const day = time.day();
      if (day === 0 || day === 6) return false; // 周日=0, 周六=6
    }

    // 仅工作时间（这个在发送时检查，生成时不过滤）
    return true;
  }

  /**
   * 检查当前时间是否在工作时间内
   * @param {Object} config - 配置对象
   * @returns {boolean}
   */
  static isWorkHours(config) {
    const now = dayjs();
    const [startHour, startMinute] = config.workHours.start.split(':').map(Number);
    const [endHour, endMinute] = config.workHours.end.split(':').map(Number);

    const start = now.hour(startHour).minute(startMinute);
    const end = now.hour(endHour).minute(endMinute);

    return now.isAfter(start) && now.isBefore(end);
  }
}

module.exports = StrategyEngine;
