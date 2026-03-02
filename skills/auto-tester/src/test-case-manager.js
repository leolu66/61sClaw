const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '../data/test-cases.json');

/**
 * 测试用例管理器
 */
class TestCaseManager {
  constructor() {
    this.data = this._loadData();
  }

  _loadData() {
    try {
      if (fs.existsSync(DATA_FILE)) {
        return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
      }
    } catch (e) {
      console.error('加载测试用例失败:', e);
    }
    return { testCases: [] };
  }

  _saveData() {
    const dir = path.dirname(DATA_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(DATA_FILE, JSON.stringify(this.data, null, 2), 'utf8');
  }

  /**
   * 生成新编号 YYMMDD-XXX
   */
  _generateId() {
    const now = new Date();
    const dateStr = now.toISOString().slice(2, 10).replace(/-/g, '');
    
    // 找当天最大序号
    let maxSeq = 0;
    this.data.testCases.forEach(tc => {
      if (tc.id.startsWith(dateStr)) {
        const match = tc.id.match(/-(\d+)$/);
        if (match) {
          maxSeq = Math.max(maxSeq, parseInt(match[1]));
        }
      }
    });
    
    const seq = (maxSeq + 1).toString().padStart(3, '0');
    return `${dateStr}-${seq}`;
  }

  /**
   * 添加测试用例
   */
  addTestCase(options) {
    // 生成执行序号（默认最大序号+1）
    const maxOrder = this.data.testCases.reduce((max, tc) => 
      Math.max(max, tc.executionOrder || 0), 0);
    
    const testCase = {
      id: this._generateId(),
      createdAt: new Date().toISOString().slice(0, 10),
      level: options.level || 1,
      description: options.description,
      skill: options.skill || null,
      validation: options.validation || null,
      executionOrder: options.executionOrder || (maxOrder + 1),
      status: 'enabled'
    };
    
    this.data.testCases.push(testCase);
    this._saveData();
    return testCase;
  }

  /**
   * 修改测试用例
   */
  updateTestCase(id, updates) {
    const index = this.data.testCases.findIndex(tc => tc.id === id);
    if (index === -1) return null;
    
    Object.assign(this.data.testCases[index], updates);
    this._saveData();
    return this.data.testCases[index];
  }

  /**
   * 停用/启用测试用例
   */
  toggleTestCase(id) {
    const tc = this.data.testCases.find(tc => tc.id === id);
    if (!tc) return null;
    
    tc.status = tc.status === 'enabled' ? 'disabled' : 'enabled';
    this._saveData();
    return tc;
  }

  /**
   * 删除测试用例
   */
  deleteTestCase(id) {
    const index = this.data.testCases.findIndex(tc => tc.id === id);
    if (index === -1) return false;
    
    this.data.testCases.splice(index, 1);
    this._saveData();
    return true;
  }

  /**
   * 获取测试用例
   */
  getTestCase(id) {
    return this.data.testCases.find(tc => tc.id === id) || null;
  }

  /**
   * 获取所有测试用例
   */
  getAllTestCases() {
    return this.data.testCases;
  }

  /**
   * 根据级别获取测试用例（包含低级别）
   */
  getTestCasesByLevel(level) {
    return this.data.testCases.filter(tc => 
      tc.status === 'enabled' && tc.level <= level
    );
  }

  /**
   * 通过执行序号获取用例
   */
  getTestCaseByOrder(order) {
    const sorted = [...this.data.testCases].sort((a, b) => 
      (a.executionOrder || 0) - (b.executionOrder || 0)
    );
    return sorted[order - 1] || null;
  }

  /**
   * 格式化测试用例列表
   */
  formatTestCases(testCases, filterLevel = null) {
    if (testCases.length === 0) {
      return '暂无测试用例';
    }

    // 按执行序号排序
    const sorted = [...testCases].sort((a, b) => 
      (a.executionOrder || 0) - (b.executionOrder || 0)
    );

    const levelNames = { 1: '快速', 2: '基本', 3: '中等', 4: '全面' };
    const statusNames = { enabled: '启用', disabled: '停用' };

    // 统计各级别数量
    const stats = {};
    sorted.forEach(tc => {
      if (tc.level <= (filterLevel || 4)) {
        stats[tc.level] = (stats[tc.level] || 0) + 1;
      }
    });

    let title = filterLevel 
      ? `${levelNames[filterLevel]}级测试用例` 
      : '测试用例列表';
    let output = `📋 ${title}（可用序号指定用例）\n\n`;
    
    sorted.forEach((tc, index) => {
      // 如果过滤了级别，只显示该级别及以下的用例
      if (filterLevel && tc.level > filterLevel) return;
      
      const level = levelNames[tc.level] || tc.level;
      const status = tc.status === 'enabled' ? '✅' : '❌';
      const order = tc.executionOrder || (index + 1);
      output += `${order}. ${status} [${tc.id}] ${level}级 - ${tc.description}`;
      if (tc.skill) output += ` (${tc.skill})`;
      output += '\n';
      if (tc.validation) output += `   验证: ${tc.validation}\n`;
    });
    
    return output;
  }
}

module.exports = TestCaseManager;
