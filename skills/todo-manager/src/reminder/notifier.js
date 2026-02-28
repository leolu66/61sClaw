const dayjs = require('dayjs');

class Notifier {
  /**
   * 发送通知
   * @param {Object} task - 任务对象
   * @param {Function} feishuSender - 飞书发送函数
   */
  static async send(task, feishuSender) {
    const message = this._formatMessage(task);

    // 控制台通知
    console.log('\n' + '='.repeat(60));
    console.log('📋 任务提醒');
    console.log('='.repeat(60));
    console.log(message);
    console.log('='.repeat(60) + '\n');

    // 飞书通知
    if (feishuSender) {
      try {
        await feishuSender(message);
      } catch (error) {
        console.error('飞书通知发送失败:', error.message);
      }
    }
  }

  /**
   * 格式化通知消息
   * @param {Object} task - 任务对象
   * @returns {string} 格式化后的消息
   */
  static _formatMessage(task) {
    const { title, description, type, deadline, priority } = task;
    const deadlineStr = dayjs(deadline).format('YYYY-MM-DD HH:mm');
    const now = dayjs();
    const timeLeft = dayjs(deadline).diff(now, 'hour');

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

    let urgency = '';
    if (timeLeft <= 1) {
      urgency = '⚠️ 即将到期！';
    } else if (timeLeft <= 24) {
      urgency = `⏰ 还剩 ${timeLeft} 小时`;
    }

    return `
${typeEmoji[type] || '📌'} ${priorityEmoji[priority]} ${title}
${description ? `📝 ${description}` : ''}
⏰ 截止时间: ${deadlineStr}
${urgency}
`.trim();
  }
}

module.exports = Notifier;
