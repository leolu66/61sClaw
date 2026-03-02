const TestCaseManager = require('./test-case-manager');
const RealTestRunner = require('./real-runner');

/**
 * 测试执行器
 */
class TestRunner {
  constructor() {
    this.manager = new TestCaseManager();
    this.realRunner = new RealTestRunner();
  }

  /**
   * 执行测试
   */
  async runTest(level) {
    const testCases = this.manager.getTestCasesByLevel(level);
    
    if (testCases.length === 0) {
      return { success: true, message: '没有可执行的测试用例' };
    }

    const levelNames = { 1: '快速测试', 2: '基本测试', 3: '中等测试', 4: '全面测试' };
    
    // 快速测试和基本测试显示执行过程
    const showProcess = level <= 2;
    
    let output = `🧪 ${levelNames[level]} - 共 ${testCases.length} 个用例\n`;
    output += '─'.repeat(40) + '\n\n';

    // 按执行序号排序
    testCases.sort((a, b) => (a.executionOrder || 0) - (b.executionOrder || 0));

    let passed = 0;
    let failed = 0;
    const results = [];

    for (const tc of testCases) {
      const order = tc.executionOrder || '?';
      output += `[${order}] [${tc.id}] ${tc.description}\n`;
      
      try {
        // 真正执行测试
        const result = await this.realRunner.executeTest(tc);
        
        if (result.success) {
          passed++;
          output += `   ✅ 通过: ${result.message}\n`;
        } else {
          failed++;
          output += `   ❌ 失败: ${result.message}\n`;
        }
      } catch (e) {
        failed++;
        output += `   ❌ 错误: ${e.message}\n`;
      }
      
      results.push({ id: tc.id, success: failed === 0 });
    }

    output += '\n' + '─'.repeat(40) + '\n';
    output += `📊 结果: ${passed} 通过, ${failed} 失败\n`;
    output += `   通过率: ${((passed / testCases.length) * 100).toFixed(1)}%`;

    return {
      success: failed === 0,
      message: output,
      passed,
      failed,
      total: testCases.length
    };
  }

  /**
   * 执行单个测试用例
   */
  async _executeTest(tc) {
    // 如果有验证方法，按验证方法执行
    if (tc.validation) {
      return this._executeByValidation(tc);
    }
    
    // 否则只检查技能是否可调用
    if (tc.skill) {
      return this._executeSkillCheck(tc);
    }
    
    // 默认为通过
    return { success: true };
  }

  /**
   * 根据验证方法执行
   */
  async _executeByValidation(tc) {
    const validation = tc.validation.toLowerCase();
    
    // 简单的关键词匹配验证
    if (validation.includes('余额') && validation.includes('查询')) {
      // 模拟执行查询
      return { success: true };
    }
    
    if (validation.includes('音乐') || validation.includes('播放')) {
      return { success: true };
    }
    
    if (validation.includes('待办') || validation.includes('任务')) {
      return { success: true };
    }
    
    // 默认通过
    return { success: true };
  }

  /**
   * 检查技能是否可调用
   */
  async _executeSkillCheck(tc) {
    // 这里可以扩展为实际调用技能
    // 目前只是简单检查通过
    return { success: true };
  }

  /**
   * 格式化测试结果
   */
  formatResults(results) {
    const levelNames = { 1: '快速', 2: '基本', 3: '中等', 4: '全面' };
    
    let output = '📋 测试结果\n\n';
    
    results.forEach(r => {
      const status = r.success ? '✅' : '❌';
      output += `${status} ${r.levelName} (${r.count}个)\n`;
    });
    
    return output;
  }
}

module.exports = TestRunner;
