/**
 * 主 Agent 响应包装器
 * 在每次响应后自动调用 test-hook 记录测试结果
 * 
 * 使用方法：在生成响应后调用 wrapResponse(originalMessage, response)
 */

const { checkAndRecordTest } = require('./test-hook.js');

/**
 * 包装响应，自动记录测试
 * @param {string} originalMessage - 用户原始消息
 * @param {string|object} response - Agent 的响应
 * @returns {string} - 原样返回响应
 */
function wrapResponse(originalMessage, response) {
  // 转换为字符串
  const responseStr = typeof response === 'string' 
    ? response 
    : JSON.stringify(response);
  
  // 检查并记录测试
  try {
    checkAndRecordTest(originalMessage, responseStr);
  } catch (e) {
    // 记录失败不影响正常响应
    console.error('[ResponseWrapper] 测试记录失败:', e.message);
  }
  
  return response;
}

/**
 * 检查消息是否是测试消息
 * @param {string} message - 消息内容
 * @returns {boolean}
 */
function isTestMessage(message) {
  return /【测试:[^】]+】/.test(message);
}

/**
 * 提取测试 ID
 * @param {string} message - 消息内容
 * @returns {string|null}
 */
function extractTestId(message) {
  const match = message.match(/【测试:([^】]+)】/);
  return match ? match[1] : null;
}

module.exports = {
  wrapResponse,
  isTestMessage,
  extractTestId,
  checkAndRecordTest
};

// 如果直接运行测试
if (require.main === module) {
  const testMsg = process.argv[2] || '【测试:260302-006】你好';
  const response = process.argv[3] || '你好！我是小天才。';
  
  console.log('原始消息:', testMsg);
  console.log('是测试消息:', isTestMessage(testMsg));
  console.log('测试ID:', extractTestId(testMsg));
  
  const result = wrapResponse(testMsg, response);
  console.log('响应:', result);
}
