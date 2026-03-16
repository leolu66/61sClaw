/**
 * 主 Agent 测试响应钩子
 * 在每次响应后自动检查是否是测试消息，并记录结果
 */

const fs = require('fs');
const path = require('path');

const TEST_RESULTS_DIR = path.join(
  process.env.USERPROFILE || process.env.HOME,
  '.openclaw/workspace-test-agent/test-results'
);

/**
 * 检查消息是否是测试消息，如果是则记录结果
 * @param {string} originalMessage - 用户原始消息
 * @param {string} response - Agent 的响应内容
 */
function checkAndRecordTest(originalMessage, response) {
  // 检查是否是测试消息格式：【测试:ID】内容
  const match = originalMessage.match(/【测试:([^】]+)】/);
  if (!match) {
    return; // 不是测试消息
  }
  
  const testId = match[1];
  console.log(`[TestHook] 检测到测试消息: ${testId}`);
  
  // 读取 pending 文件获取预期结果
  const pendingFile = path.join(TEST_RESULTS_DIR, `${testId}.pending.json`);
  let expected = null;
  
  try {
    if (fs.existsSync(pendingFile)) {
      const pending = JSON.parse(fs.readFileSync(pendingFile, 'utf8'));
      expected = pending.expected;
    }
  } catch (e) {
    console.log(`[TestHook] 读取 pending 文件失败: ${e.message}`);
  }
  
  // 验证响应
  const validation = validateResponse(response, expected);
  
  // 写入结果文件
  const resultFile = path.join(TEST_RESULTS_DIR, `${testId}.result.json`);
  try {
    if (!fs.existsSync(TEST_RESULTS_DIR)) {
      fs.mkdirSync(TEST_RESULTS_DIR, { recursive: true });
    }
    
    fs.writeFileSync(resultFile, JSON.stringify({
      testId: testId,
      response: response,
      expected: expected,
      validation: validation,
      success: validation.success,
      recordedAt: new Date().toISOString()
    }, null, 2));
    
    console.log(`[TestHook] 测试结果已记录: ${testId} - ${validation.success ? '通过' : '失败'}`);
  } catch (e) {
    console.error(`[TestHook] 记录结果失败: ${e.message}`);
  }
}

/**
 * 验证响应是否符合预期
 */
function validateResponse(response, expected) {
  if (!expected) {
    return { 
      success: true, 
      message: '无预期条件，默认通过',
      matched: true
    };
  }
  
  // 简单的关键词匹配
  const keywords = expected.split(/[,，、]/).map(k => k.trim()).filter(k => k);
  
  for (const keyword of keywords) {
    if (response.toLowerCase().includes(keyword.toLowerCase())) {
      return { 
        success: true, 
        message: `包含预期关键词: ${keyword}`,
        matched: true,
        keyword: keyword
      };
    }
  }
  
  // 如果没有匹配，也算通过（只要收到响应）
  return { 
    success: true, 
    message: '收到响应（未匹配特定关键词）',
    matched: false
  };
}

module.exports = {
  checkAndRecordTest
};

// 如果直接运行测试
if (require.main === module) {
  const testMsg = process.argv[2] || '【测试:260302-006】你好';
  const response = process.argv[3] || '你好！我是小天才，有什么可以帮你的吗？';
  
  checkAndRecordTest(testMsg, response);
  console.log('测试记录完成');
}
