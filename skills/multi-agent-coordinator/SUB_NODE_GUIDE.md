# 多智能体协作技能 - 子节点通信与任务处理机制

**文档版本**: v1.0  
**适用角色**: 子节点 (Claude Code)  
**创建时间**: 2026-03-05

---

## 一、角色定位

作为**子节点**，你的职责是：
1. 接收主节点（kimi）发送的任务
2. 自动更新任务状态到 SQLite 数据库
3. 执行任务并生成结果
4. 通知主节点任务完成

---

## 二、任务检测机制

### 触发条件

当收到主节点消息包含以下任一格式时，自动触发任务处理：

```
1. "执行任务: xxx"
2. "# [TASK] 协同工作任务单"
3. 包含 "任务ID:" 和 "输出目录:"
```

### 任务信息提取

从消息中提取以下字段：
- **task_id**: 任务唯一标识（格式: plan-{timestamp}）
- **task_type**: 任务类型（billing/code/analysis/general）
- **output_dir**: 输出目录路径
- **instruction**: 具体任务指令

---

## 三、状态更新机制

### SQLite 数据库位置

```
D:\projects\workspace-main\config\task_states.db
```

### 状态流转

```
pending → received → running → completed/failed
```

### 状态更新代码模板

```python
import sys
sys.path.insert(0, 'D:/projects/workspace-main/skills/multi-agent-coordinator/src')
from task_state_controller import TaskStateController, TaskStatus

# 初始化控制器
ctrl = TaskStateController('D:/projects/workspace-main/config/task_states.db')

# 1. 接收任务时更新
ctrl.update_status(
    task_id='plan-xxx',
    status=TaskStatus.RECEIVED,
    changed_by='claude',
    reason='已接收任务'
)

# 2. 开始执行时更新
ctrl.update_status(
    task_id='plan-xxx',
    status=TaskStatus.RUNNING,
    changed_by='claude',
    reason='开始执行任务'
)

# 3. 完成时更新
ctrl.update_status(
    task_id='plan-xxx',
    status=TaskStatus.COMPLETED,
    changed_by='claude',
    reason='任务执行完成'
)

# 4. 失败时更新
ctrl.update_status(
    task_id='plan-xxx',
    status=TaskStatus.FAILED,
    changed_by='claude',
    reason='执行失败',
    error_msg='错误详情'
)
```

---

## 四、任务执行流程

### 标准执行步骤

```
1. 检测任务指令
   ↓
2. 解析任务信息（task_id, type, output_dir）
   ↓
3. 更新数据库状态 → received
   ↓
4. 预建输出目录（在自己的工作区）
   ↓
5. 更新数据库状态 → running
   ↓
6. 根据任务类型执行：
   - billing: 调用 billing-analyzer 技能
   - code: 生成代码
   - analysis: 数据分析
   - general: 通用处理
   ↓
7. 生成结果文件
   ↓
8. 更新数据库状态 → completed/failed
   ↓
9. 生成 .task-completed 标记文件
   ↓
10. （可选）飞书通知主节点
```

### 工作区规范

**你的工作区**: `D:\projects\workspace\node-claude\`

**任务输出目录**: `D:\projects\workspace\node-claude\task-{planId}\`

**必须生成的文件**:
- `result.json` - 执行结果元数据
- `{task_type}_report.md` - 详细报告
- `.task-completed` - 完成标记（可选，用于文件系统通知）

---

## 五、输出文件格式

### result.json

```json
{
  "taskId": "plan-xxx",
  "status": "success",
  "output": "执行结果摘要",
  "outputFiles": ["billing_report.md"],
  "executedAt": "2026-03-05T22:00:00Z",
  "cost": {
    "duration_ms": 120000,
    "tokens": 50000
  }
}
```

### .task-completed（可选）

```json
{
  "planId": "plan-xxx",
  "completedAt": "2026-03-05T22:00:00Z",
  "status": "success"
}
```

---

## 六、任务类型处理

### 账单分析任务 (billing)

**输入**: CSV 账单文件（在主节点共享目录）

**处理步骤**:
1. 读取 CSV 文件
2. 计算统计数据（总消费、日均、模型排行等）
3. 生成 Markdown 报告

**输出**:
- `billing_report.md`
- `result.json`

### 代码开发任务 (code)

**输入**: 功能描述

**处理步骤**:
1. 分析需求
2. 设计代码结构
3. 生成代码文件

**输出**:
- 代码文件
- `result.json`

### 通用任务 (general)

根据指令灵活处理。

---

## 七、与主节点的协作

### 主节点职责
- 创建任务并分配给你
- 预建共享目录结构
- 监控任务状态（通过 SQLite）
- 确认任务完成

### 你的职责
- 接收并执行任务
- 更新任务状态
- 生成结果文件
- 通知完成

### 通信方式
1. **任务分配**: 主节点发送消息给你
2. **状态同步**: 通过 SQLite 数据库
3. **结果传递**: 文件系统 + 数据库
4. **完成通知**: 标记文件 / 飞书消息

---

## 八、错误处理

### 常见错误

1. **无法读取输入文件**
   - 检查文件路径
   - 更新状态为 failed
   - 记录错误原因

2. **执行异常**
   - 捕获异常
   - 更新状态为 failed
   - 生成错误报告

3. **数据库更新失败**
   - 记录日志
   - 继续执行任务
   - 通过文件标记通知

### 错误处理代码模板

```python
try:
    # 执行任务
    result = execute_task()
    
    # 更新成功状态
    ctrl.update_status(task_id, TaskStatus.COMPLETED, 'claude', '执行成功')
    
except Exception as e:
    # 更新失败状态
    ctrl.update_status(
        task_id, 
        TaskStatus.FAILED, 
        'claude', 
        '执行失败', 
        str(e)
    )
    
    # 生成错误报告
    with open(f'{output_dir}/error.log', 'w') as f:
        f.write(str(e))
```

---

## 九、测试检查清单

作为子节点，请确认以下功能正常：

- [ ] 能正确检测任务指令
- [ ] 能解析任务信息（task_id, type, output_dir）
- [ ] 能连接 SQLite 数据库
- [ ] 能更新任务状态（received, running, completed）
- [ ] 能执行账单分析任务
- [ ] 能生成 result.json 和报告文件
- [ ] 能处理执行异常
- [ ] 主节点能通过 SQLite 看到你的状态更新

---

## 十、示例任务消息

主节点发送给你的消息格式示例：

```
执行任务: 账单分析

## 任务信息
- 任务ID: plan-1772719054700
- 发送者: kimi
- 发送时间: 2026/3/5 22:30:00
- 优先级: high

## 任务指令
请分析账单文件并生成专业报告：

1. 读取文件: D:\projects\workspace\shared\input\billing_2026-02-09_2026-03-04.csv
2. 分析账单数据，计算消费统计
3. 生成 Markdown 格式的完整报告

## 输出要求
- 输出目录: D:\projects\workspace\node-claude\task-plan-1772719054700
- 报告文件: billing_report.md
- 结果文件: result.json

请使用 Read 工具读取 CSV 文件，然后用 Write 工具写入报告文件。
```

---

## 十一、联系方式

如有问题，请联系主节点（kimi）或通过飞书沟通。

**文档维护**: kimi  
**最后更新**: 2026-03-05
