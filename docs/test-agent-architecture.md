# Test-Agent 自动化测试架构

**创建日期**: 2026-03-16  
**用途**: 让 auto-tester 技能能够进行端到端测试，验证 main Agent 的响应能力

---

## 架构概述

Test-Agent 架构实现了**真正的端到端测试**：
- test-agent 扮演"测试用户"向 main Agent 发送消息
- main Agent 正常处理并响应
- 自动记录响应并验证是否符合预期

```
┌─────────────────┐
│  auto-tester    │  用户触发测试指令
│  (主测试框架)    │  如："快速测试"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ test-executor.js│  1. 发送【测试:ID】消息
│                 │  2. 记录 pending 文件
└────────┬────────┘
         │ CLI: openclaw agent --message
         ▼
┌─────────────────┐
│   main Agent    │  3. 处理消息并生成响应
│  (当前会话)      │
└────────┬────────┘
         │ 调用 test-hook.js
         ▼
┌─────────────────┐
│   test-hook.js  │  4. 检测测试标记
│                 │  5. 验证响应内容
│                 │  6. 记录 result 文件
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  auto-tester    │  7. 读取 result 文件
│  (轮询等待)      │  8. 返回测试结果
└─────────────────┘
```

---

## 文件结构

```
workspace-main/
├── test-hook.js                    # 主 Agent 钩子（自动记录测试结果）
├── skills/
│   └── auto-tester/
│       ├── src/
│       │   └── real-runner.js      # 已更新，支持 test-agent 测试
│       └── data/
│           └── test-cases.json     # 测试用例（支持 type: "agent"）

workspace-test-agent/               # 测试 Agent 工作区
├── IDENTITY.md                     # 测试 Agent 身份
├── test-executor.js                # 发送测试消息
├── test-recorder.js                # 记录测试结果（备用）
└── test-results/                   # 测试结果目录
    ├── {testId}.pending.json       # 测试等待中
    └── {testId}.result.json        # 测试结果
```

---

## 组件说明

### 1. test-executor.js

**位置**: `workspace-test-agent/test-executor.js`

**功能**:
- 接收测试用例（ID、input、expected）
- 使用 CLI 向 main Agent 发送测试消息
- 格式：`【测试:ID】input`
- 记录 pending 文件

**使用**:
```bash
node test-executor.js 260302-006 "你好" "问候"
```

### 2. test-hook.js

**位置**: `workspace-main/test-hook.js`

**功能**:
- 检测消息是否包含 `【测试:ID】` 标记
- 验证响应是否符合预期（关键词匹配）
- 自动记录结果到 result 文件

**集成方式**:
在 main Agent 每次响应后调用：
```javascript
const { checkAndRecordTest } = require('./test-hook.js');

// 响应用户后
checkAndRecordTest(originalMessage, response);
```

### 3. real-runner.js（已更新）

**位置**: `workspace-main/skills/auto-tester/src/real-runner.js`

**新增功能**:
- 检测测试用例 `type: "agent"`
- 调用 test-executor.js 发送消息
- 轮询等待 result 文件
- 返回测试结果

### 4. 测试用例格式

**位置**: `workspace-main/skills/auto-tester/data/test-cases.json`

**新增字段**:
```json
{
  "id": "260302-006",
  "type": "agent",        // 新增：标记为 test-agent 测试
  "input": "你好",         // 新增：发送给 main Agent 的消息
  "expected": "问候",      // 新增：期望响应包含的关键词
  "level": 1,              // 测试级别（1-4）
  "status": "enabled"      // 启用状态
}
```

---

## 使用流程

### 1. 添加新的 test-agent 测试用例

编辑 `skills/auto-tester/data/test-cases.json`:

```json
{
  "id": "260302-007",
  "createdAt": "2026-03-16",
  "level": 1,
  "description": "测试查询天气功能",
  "type": "agent",
  "input": "查询北京天气",
  "expected": "天气,温度,北京",
  "status": "enabled",
  "executionOrder": 7
}
```

### 2. 执行测试

用户指令：
```
快速测试    # 执行 1级用例
基本测试    # 执行 1+2级用例
中等测试    # 执行 1+2+3级用例
全面测试    # 执行全部用例
```

### 3. 自动流程

1. auto-tester 读取测试用例
2. 检测到 `type: "agent"`，调用 test-executor.js
3. test-executor 发送 `【测试:ID】input` 消息
4. main Agent 收到消息，正常响应
5. main Agent 调用 test-hook.js 记录结果
6. auto-tester 读取 result 文件，返回测试结果

---

## 测试消息格式

### 发送格式
```
【测试:260302-006】你好
```

### 标记解析
- `【测试:` - 测试消息前缀
- `260302-006` - 测试用例 ID
- `】` - 结束标记
- `你好` - 实际测试输入

### 预期验证
- 关键词匹配（支持多个，用逗号分隔）
- 不区分大小写
- 只要包含任一关键词即通过
- 无预期条件时默认通过

---

## 注意事项

### 1. 超时处理
- 默认等待 30 秒获取测试结果
- 超时则标记为失败

### 2. 并发限制
- 当前实现为串行执行
- 避免多个测试同时发送消息造成混乱

### 3. 结果清理
- 测试结果读取后自动删除文件
- pending 文件在结果读取后清理

### 4. 故障排查

**测试消息发送失败**:
- 检查 Gateway 是否运行：`openclaw gateway status`
- 检查 session ID 是否正确

**结果文件未生成**:
- 检查 test-hook.js 是否被调用
- 检查 `workspace-test-agent/test-results/` 目录权限

**验证失败**:
- 检查 expected 关键词是否正确
- 查看 result 文件中的实际响应内容

---

## 扩展计划

### 可能的改进

1. **支持正则匹配**: 不仅关键词，还支持正则表达式验证
2. **多轮对话测试**: 支持测试连续对话场景
3. **性能测试**: 记录响应时间，检测性能退化
4. **截图验证**: 对于 UI 相关测试，支持截图对比
5. **测试覆盖率**: 统计哪些技能/功能被测试覆盖

---

## 维护记录

| 日期 | 操作 | 说明 |
|------|------|------|
| 2026-03-16 | 创建 | 初始版本，实现基本 test-agent 架构 |

---

## 相关文件

- `workspace-main/test-hook.js` - 主 Agent 钩子
- `workspace-test-agent/test-executor.js` - 测试执行器
- `workspace-test-agent/IDENTITY.md` - 测试 Agent 身份
- `skills/auto-tester/src/real-runner.js` - 测试运行器
- `skills/auto-tester/data/test-cases.json` - 测试用例
