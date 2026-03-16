# Auto Tester - 自动化测试技能

## 触发条件

当用户说以下内容时触发：
- "自动测试"
- "回归测试"
- "快速测试" / "基本测试" / "中等测试" / "全面测试"
- "测试基本" / "测试全部" / "测试所有"
- "添加测试用例"
- "修改测试用例"
- "停用测试用例"
- "删除测试用例"
- "查看测试用例"

## 功能说明

### 1. 执行测试

根据级别执行对应的测试用例：
- 快速测试（1级）
- 基本测试（2级，包含1级）
- 中等测试（3级，包含1+2级）
- 全面测试（4级，包含1+2+3级）

### 2. 管理测试用例

- 添加：编号自动生成（YYMMDD-XXX）
- 修改：更新用例信息
- 停用/启用：切换状态
- 删除：移除用例

### 3. Test-Agent 端到端测试

支持通过 test-agent 架构对 main Agent 进行端到端测试：
- test-agent 扮演测试用户向 main Agent 发送消息
- main Agent 正常处理并响应
- 自动验证响应是否符合预期

## 指令示例

```
快速测试         # 执行1级用例
基本测试         # 执行1+2级用例
中等测试         # 执行1+2+3级用例
全面测试         # 执行全部用例

添加测试用例 验证播放音乐功能
修改测试用例 260302-001
停用测试用例 260302-001
删除测试用例 260302-001
查看测试用例
```

## Test-Agent 测试用例格式

对于需要测试 main Agent 响应能力的用例，使用以下格式：

```json
{
  "id": "260302-006",
  "createdAt": "2026-03-16",
  "level": 1,
  "description": "发出你好指令测试",
  "type": "agent",          // 标记为 test-agent 测试
  "input": "你好",           // 发送给 main Agent 的消息
  "expected": "问候",        // 期望响应包含的关键词（逗号分隔）
  "status": "enabled",
  "executionOrder": 1
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `type` | `"agent"` 表示使用 test-agent 架构 |
| `input` | 实际发送给 main Agent 的消息内容 |
| `expected` | 期望响应中包含的关键词，支持多个（逗号分隔） |

## 测试流程

### 普通测试用例（skill/check 类型）
1. 检查技能文件是否存在
2. 或直接调用技能功能
3. 返回测试结果

### Test-Agent 测试用例（agent 类型）
1. 调用 `test-executor.js` 发送测试消息
2. 消息格式：`【测试:ID】input`
3. main Agent 收到消息，正常响应
4. `test-hook.js` 自动记录测试结果
5. 读取 result 文件，返回测试结果

## 相关文件

- `data/test-cases.json` - 测试用例配置
- `src/real-runner.js` - 测试执行器
- `src/test-case-manager.js` - 测试用例管理
- `../../workspace-test-agent/test-executor.js` - test-agent 执行器
- `../../test-hook.js` - 测试结果记录
- `../../docs/test-agent-architecture.md` - 架构文档

## 注意事项

1. **超时处理**：test-agent 测试默认等待 30 秒获取结果
2. **并发限制**：当前为串行执行，避免消息混乱
3. **结果清理**：测试结果读取后自动删除文件
4. **关键词匹配**：expected 字段支持多关键词，只要包含任一即通过

## 故障排查

**测试消息发送失败**：
- 检查 Gateway 是否运行：`openclaw gateway status`

**结果文件未生成**：
- 检查 `test-hook.js` 是否被调用
- 检查 `workspace-test-agent/test-results/` 目录权限

**验证失败**：
- 检查 expected 关键词是否正确
- 查看 result 文件中的实际响应内容
