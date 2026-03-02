const path = require('path');
const ReminderChecker = require('../src/reminder/reminder-checker');

// 飞书发送函数（通过 feishu-notifier 技能）
async function sendFeishuMessage(message) {
  // 这里需要调用 feishu-notifier 技能
  // 暂时先打印到控制台
  console.log('[飞书通知]', message);
}

async function main() {
  const dataPath = path.join(__dirname, '../data/tasks.json');
  const checker = new ReminderChecker(dataPath, sendFeishuMessage);

  try {
    const sentCount = await checker.check();
    if (sentCount > 0) {
      console.log(`✅ 发送了 ${sentCount} 条提醒`);
    }
  } catch (error) {
    console.error('❌ 检查提醒失败:', error);
  }
}

main();
