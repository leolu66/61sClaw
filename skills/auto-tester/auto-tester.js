const path = require('path');
const TestCaseManager = require('./src/test-case-manager');
const TestRunner = require('./src/test-runner');

const manager = new TestCaseManager();
const runner = new TestRunner();

/**
 * 处理测试相关请求
 */
async function handleRequest(action, params = {}) {
  try {
    switch (action) {
      // 执行测试
      case 'run': {
        const level = params.level || 1;
        const result = await runner.runTest(level);
        return {
          success: result.success,
          message: result.message
        };
      }

      // 添加测试用例
      case 'add': {
        const testCase = manager.addTestCase({
          description: params.description,
          level: params.level || 1,
          skill: params.skill,
          validation: params.validation
        });
        return {
          success: true,
          message: `✅ 测试用例已添加: [${testCase.id}] ${testCase.description}`
        };
      }

      // 修改测试用例
      case 'update': {
        // 先尝试通过ID查找，再尝试通过执行序号查找
        let testCase = manager.getTestCase(params.id);
        if (!testCase && /^\d+$/.test(params.id)) {
          testCase = manager.getTestCaseByOrder(parseInt(params.id));
        }
        if (!testCase) {
          return { success: false, message: '❌ 测试用例不存在' };
        }
        const updated = manager.updateTestCase(testCase.id, params.updates);
        return {
          success: true,
          message: `✅ 测试用例已更新: [${updated.id}] ${updated.description}`
        };
      }

      // 停用/启用测试用例
      case 'toggle': {
        let testCase = manager.getTestCase(params.id);
        if (!testCase && /^\d+$/.test(params.id)) {
          testCase = manager.getTestCaseByOrder(parseInt(params.id));
        }
        if (!testCase) {
          return { success: false, message: '❌ 测试用例不存在' };
        }
        const toggled = manager.toggleTestCase(testCase.id);
        const status = toggled.status === 'enabled' ? '启用' : '停用';
        return {
          success: true,
          message: `✅ 测试用例已${status}: [${toggled.id}]`
        };
      }

      // 删除测试用例
      case 'delete': {
        let testCase = manager.getTestCase(params.id);
        if (!testCase && /^\d+$/.test(params.id)) {
          testCase = manager.getTestCaseByOrder(parseInt(params.id));
        }
        if (!testCase) {
          return { success: false, message: '❌ 测试用例不存在' };
        }
        const success = manager.deleteTestCase(testCase.id);
        return {
          success: true,
          message: `🗑️ 测试用例已删除: [${testCase.id}]`
        };
      }

      // 查看测试用例
      case 'list': {
        let testCases = manager.getAllTestCases();
        // 如果指定了级别，只显示该级别及以下的用例
        if (params.level) {
          testCases = testCases.filter(tc => tc.level <= params.level);
        }
        return {
          success: true,
          message: manager.formatTestCases(testCases, params.level)
        };
      }

      default:
        return { success: false, message: '❌ 未知操作' };
    }
  } catch (error) {
    return { success: false, message: `❌ 操作失败: ${error.message}` };
  }
}

/**
 * 解析用户指令
 */
function parseCommand(input) {
  const cmd = input.toLowerCase().trim();
  
  // 添加测试用例（优先判断）
  if (cmd.startsWith('添加测试用例')) {
    const description = input.replace(/^添加测试用例/, '').trim();
    return { action: 'add', description };
  }
  
  // 修改测试用例
  if (cmd.startsWith('修改测试用例')) {
    const id = input.replace(/^修改测试用例/, '').trim();
    return { action: 'update', id };
  }
  
  // 停用测试用例
  if (cmd.startsWith('停用测试用例')) {
    const id = input.replace(/^停用测试用例/, '').trim();
    return { action: 'toggle', id };
  }
  
  // 删除测试用例
  if (cmd.startsWith('删除测试用例')) {
    const id = input.replace(/^删除测试用例/, '').trim();
    return { action: 'delete', id };
  }
  
  // 查看测试用例（优先判断）
  if (cmd.startsWith('查看') && cmd.includes('用例')) {
    // 判断查看哪个级别
    let level = null;
    if (cmd.includes('快速') || cmd.includes('1级')) {
      level = 1;
    } else if (cmd.includes('基本') || cmd.includes('2级')) {
      level = 2;
    } else if (cmd.includes('中等') || cmd.includes('一般') || cmd.includes('3级')) {
      level = 3;
    } else if (cmd.includes('全面') || cmd.includes('全部') || cmd.includes('4级')) {
      level = 4;
    }
    return { action: 'list', level };
  }
  
  // 执行测试（后判断）
  if (cmd.includes('测试') || cmd === '自动测试' || cmd === '回归测试') {
    let level = 1;
    
    if (cmd.includes('基本') || cmd === '测试基本' || cmd === '基本') {
      level = 2;
    } else if (cmd.includes('中等') || cmd === '一般' || cmd === '测试中等') {
      level = 3;
    } else if (cmd.includes('全面') || cmd.includes('全部') || cmd.includes('所有')) {
      level = 4;
    }
    
    return { action: 'run', level };
  }
  
  // 添加测试用例
  if (cmd.startsWith('添加测试用例')) {
    const description = input.replace(/^添加测试用例/, '').trim();
    return { action: 'add', description };
  }
  
  // 修改测试用例
  if (cmd.startsWith('修改测试用例')) {
    const id = input.replace(/^修改测试用例/, '').trim();
    return { action: 'update', id };
  }
  
  // 停用测试用例
  if (cmd.startsWith('停用测试用例')) {
    const id = input.replace(/^停用测试用例/, '').trim();
    return { action: 'toggle', id };
  }
  
  // 删除测试用例
  if (cmd.startsWith('删除测试用例')) {
    const id = input.replace(/^删除测试用例/, '').trim();
    return { action: 'delete', id };
  }
  
  // 查看测试用例
  if (cmd.startsWith('查看') && cmd.includes('用例')) {
    return { action: 'list' };
  }
  
  // 如果只是"测试用例"不算执行测试
  
  return null;
}

/**
 * 主函数 - CLI 入口
 */
function main() {
  const args = process.argv.slice(2);
  const input = args.join(' ');
  
  if (!input) {
    console.log('用法:');
    console.log('  node auto-tester.js 快速测试');
    console.log('  node auto-tester.js 基本测试');
    console.log('  node auto-tester.js 添加测试用例 描述');
    console.log('  node auto-tester.js 查看测试用例');
    process.exit(1);
  }
  
  const parsed = parseCommand(input);
  if (!parsed) {
    console.log('❌ 无法解析指令');
    process.exit(1);
  }
  
  handleRequest(parsed.action, parsed).then(result => {
    console.log(result.message);
    process.exit(result.success ? 0 : 1);
  });
}

module.exports = { handleRequest, parseCommand };

// 如果直接运行
if (require.main === module) {
  main();
}
