# Multi-Agent Coordinator - 多节点协同工作技能

## 功能概述

协调多个 Claude Code 节点协同工作，实现任务分发、执行和结果收集。

## 角色说明

本技能支持两种角色：
- **主节点**：任务分配者和协调者
- **子节点**：任务执行者

### 主节点处理逻辑（含任务计划确认）

```
用户提出需求
    │
    ▼
[主节点] 分析需求 → 生成任务执行计划
    │
    ▼
展示计划给用户 → 等待确认
    │
    ▼
用户确认后
    │
    ▼
[主节点] 预建目录 → 准备资源
    │
    ▼
[主节点] 发送任务给子节点
    │
    ▼
[子节点] 执行任务
    │
    ▼
[子节点] 返回结果
    │
    ▼
[主节点] 汇总结果 → 展示给用户
```

**任务计划确认机制**：

主节点接到用户需求后，先生成执行计划，包含：
- 执行步骤列表
- 每个步骤的负责节点
- 预计耗时
- 涉及的资源/文件

用户确认后才开始执行。

**任务执行清单**：

任务执行过程中，主节点会维护一个 Markdown 格式的执行清单文件：
- 路径：`config/task-checklist-{planId}.md`
- 每个步骤有 checkbox，完成时打勾
- 失败时在步骤后记录错误原因
- 任务结束时显示完整清单

清单格式示例：
```markdown
# 任务执行清单

**任务ID**: plan-123456
**任务名称**: 账单分析报告生成
**状态**: 🔄 执行中

## 执行步骤

- [x] **步骤 1** - 复制账单文件到共享目录 (主节点 kimi)
- [x] **步骤 2** - 预建输出目录结构 (主节点 kimi)
- [ ] **步骤 3** - 发送分析任务给 Claude Code (主节点 kimi)
- [ ] **步骤 4** - 读取账单数据并分析 (子节点 claude)
...

## 执行日志

[2026-03-05 21:30:15] ✅ 步骤 1 完成
[2026-03-05 21:30:16] ✅ 步骤 2 完成
[2026-03-05 21:30:17] ❌ 步骤 3 失败: 子节点离线
```

**主节点指令**：
- `创建任务 xxx` - 创建新任务
- `查看任务列表` - 查看所有任务
- `查看节点状态` - 查看子节点在线情况
- `确认任务 task-xxx` - 确认任务完成
- `取消任务 task-xxx` - 取消任务

### 子节点处理逻辑（任务执行者）

子节点作为任务执行者，需要自动处理接收到的任务。

**触发条件**：
当子节点收到主节点消息包含以下格式时触发：
- `执行任务: xxx` - 执行具体任务
- `# [TASK] 协同工作任务单` - 标准任务单格式

**子节点自动处理流程**：

```
检测到任务指令
    │
    ▼
[子节点] 解析任务信息
    │
    ▼
更新任务状态: received
    │
    ▼
分析任务类型
    │
    ├── 账单分析 ──► 调用 billing-analyzer 技能
    ├── 代码开发 ──► 调用代码生成技能
    └── 其他任务 ──► 根据指令执行
    │
    ▼
更新任务状态: running
    │
    ▼
执行任务（使用子节点工具）
    │
    ▼
生成结果文件
    │
    ▼
更新任务状态: completed/failed
    │
    ▼
写入结果到工作区
    │
    ▼
（可选）通知主节点
```

**任务状态更新机制**：

子节点通过 SQLite 数据库更新任务状态：

```python
# 状态更新代码模板
import sys
sys.path.insert(0, 'D:/projects/workspace-main/skills/multi-agent-coordinator/src')
from task_state_controller import TaskStateController, TaskStatus

ctrl = TaskStateController('D:/projects/workspace-main/config/task_states.db')

# 接收任务时
ctrl.update_status(task_id, TaskStatus.RECEIVED, 'claude', '已接收任务')

# 开始执行时
ctrl.update_status(task_id, TaskStatus.RUNNING, 'claude', '开始执行')

# 完成时
ctrl.update_status(task_id, TaskStatus.COMPLETED, 'claude', '执行完成')

# 失败时
ctrl.update_status(task_id, TaskStatus.FAILED, 'claude', '执行失败', '错误信息')
```

**子节点执行步骤**：

1. **接收任务**
   - 解析任务指令
   - 提取 task_id、任务类型、输出目录
   - 更新数据库状态为 `received`

2. **准备执行**
   - 检查工作区权限
   - 预建输出目录
   - 更新数据库状态为 `running`

3. **执行任务**
   - 根据任务类型调用相应技能
   - 读取输入文件
   - 执行分析/生成

4. **生成结果**
   - 写入报告文件
   - 写入 result.json
   - 更新数据库状态为 `completed` 或 `failed`

5. **完成通知**
   - 生成 `.task-completed` 标记文件
   - （可选）通过飞书通知主节点

**子节点输出要求**：

每个任务必须生成：
- `result.json` - 执行结果元数据
- `{task_type}_report.md` - 详细报告
- `.task-state` - 状态变更记录（可选）

**result.json 格式**：
```json
{
  "taskId": "plan-xxx",
  "status": "success/failed",
  "output": "执行结果摘要",
  "outputFiles": ["billing_report.md"],
  "executedAt": "2026-03-05T22:00:00Z",
  "cost": {
    "duration_ms": 120000,
    "tokens": 50000
  }
}
```
    │
    ▼
写入结果到 results/claude/
    │
    ▼
更新 tasks.json 状态
    │
    ▼
等待主节点确认
```

**触发方式**：
| 触发条件 | 说明 |
|----------|------|
| 手动触发 | 说"检查任务"，立即扫描执行 |
| 自动检测 | 说"任务处理完成"后自动检查下一个 |

## 触发条件

当用户说以下内容时触发此技能：
- "创建任务 xxx"
- "查看任务列表" / "查看任务"
- "查看节点状态"
- "确认任务 xxx"
- "重处理任务 xxx"
- "取消任务 xxx"
- "手动分配任务 xxx 到 xxx"
- **"启动任务扫描"** / **"停止任务扫描"** / **"查看扫描状态"** - 控制定时扫描器

---

## 定时扫描器（新版）

### 配置文件

统一配置文件位于：`workspace-main/config/coordinator.json`

```json
{
  "_comment": "多智能体协调器配置 - 修改后重启扫描生效",
  "nodeType": "master",
  "nodeId": "main",
  
  "shared": {
    "outputDir": "D:\\projects\\hiagents\\output",
    "tasksDir": "D:\\projects\\hiagents\\tasks",
    "inputDir": "D:\\projects\\hiagents\\input"
  },
  
  "master": {
    "resultScanInterval": 30000,
    "heartbeatCheckInterval": 300000,
    "nodeTimeout": 360,
    "notificationEnabled": true,
    "maxRetries": 2,
    "commandsDir": "D:\\projects\\commands",
    "resultsDir": "D:\\projects\\results",
    "configDir": "D:\\projects\\config"
  },
  
  "worker": {
    "taskScanInterval": 30000,
    "heartbeatInterval": 300000,
    "maxConcurrentTasks": 2,
    "capabilities": ["code", "analysis", "doc", "writing"],
    "commandsDir": "D:\\projects\\commands",
    "resultsDir": "D:\\projects\\results",
    "configDir": "D:\\projects\\config",
    "workspaceDir": "D:\\projects\\workspace"
  }
}
```

### 配置说明

| 配置项 | 说明 | 主节点 | 子节点 |
|--------|------|--------|--------|
| `shared.outputDir` | 共享输出目录 | ✅ | ✅ |
|--------|------|--------|--------|
| `nodeType` | 节点类型 | master | worker |
| `nodeId` | 节点标识 | main | claude/kimi/... |
| `resultScanInterval` | 结果扫描间隔(ms) | 30000 | - |
| `heartbeatCheckInterval` | 心跳检查间隔(ms) | 300000 | - |
| `taskScanInterval` | 任务扫描间隔(ms) | - | 30000 |
| `heartbeatInterval` | 心跳发送间隔(ms) | - | 300000 |
| `nodeTimeout` | 节点离线阈值(秒) | 360 | - |
| `maxConcurrentTasks` | 最大并发任务数 | - | 2 |

### 命令行工具

```bash
# 进入技能目录
cd skills/multi-agent-coordinator

# 启动扫描
node coordinator-cli.js start

# 停止扫描
node coordinator-cli.js stop

# 查看状态
node coordinator-cli.js status

# 重启扫描
node coordinator-cli.js restart
```

### 技能指令

| 指令 | 说明 | 执行逻辑 |
|------|------|----------|
| `启动任务扫描` | 根据 coordinator.json 中的 nodeType 启动对应扫描器 | 调用 `coordinator-cli.js start`，读取 PID 和状态文件确认 |
| `停止任务扫描` | 停止当前运行的扫描器 | 调用 `coordinator-cli.js stop`，读取状态文件确认停止 |
| `查看扫描状态` | 显示扫描器运行状态和配置信息 | 调用 `coordinator-cli.js status`，解析状态文件 |
| `重载扫描配置` | 重新加载配置文件（无需重启） | 调用 `coordinator-cli.js reload`，发送重载信号 |

### 技能指令通信机制

```
用户指令 ──► 技能处理 ──► 调用 CLI 工具 ──► 守护进程
                              │
                              ▼
                    ┌─────────────────────┐
                    │ coordinator.pid     │
                    │ coordinator.status  │
                    └─────────────────────┘
                              │
                              ▼
                    技能读取状态文件 ──► 返回执行结果给用户
```

**状态文件格式** (`config/coordinator.status`):
```json
{
  "status": "running",      // running, stopped, error, reloading
  "timestamp": 1709630400000,
  "pid": 12345,
  "startTime": 1709630000000,
  "tasksProcessed": 10,
  "lastScan": 1709630400000,
  "nodeType": "master"
}
```

**PID 文件格式** (`config/coordinator.pid`):
```json
{
  "pid": 12345,
  "nodeType": "master",
  "startTime": 1709630000000,
  "updatedAt": 1709630400000
}
```

---

## 技能主入口

技能主入口文件: `index.js`

### 使用方式

```javascript
const coordinator = require('./skills/multi-agent-coordinator');

// 启动扫描
const result = coordinator.handleCommand('启动任务扫描');
console.log(result.message);

// 查看状态
const status = coordinator.getStatus();
console.log(status.message);
```

### 导出函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `handleCommand(command)` | 用户指令字符串 | `{success, message, ...}` | 主处理函数 |
| `startScan()` | 无 | `{success, message}` | 启动扫描 |
| `stopScan()` | 无 | `{success, message}` | 停止扫描 |
| `getStatus()` | 无 | `{success, message, status, pidInfo}` | 获取状态 |
| `reloadConfig()` | 无 | `{success, message}` | 重载配置 |

### 命令行测试

```bash
cd skills/multi-agent-coordinator

# 启动扫描
node index.js "启动任务扫描"

# 查看状态
node index.js "查看扫描状态"

# 停止扫描
node index.js "停止任务扫描"

# 重载配置
node index.js "重载扫描配置"
```

### 扫描器架构

```
┌─────────────────────────────────────────────────────────────┐
│                     coordinator.json                        │
│  ┌──────────────┐              ┌──────────────┐            │
│  │  nodeType    │─────────────►│  master      │            │
│  │  = master    │              │  config      │            │
│  └──────────────┘              └──────────────┘            │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐              ┌──────────────┐            │
│  │  nodeType    │─────────────►│  worker      │            │
│  │  = worker    │              │  config      │            │
│  └──────────────┘              └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    coordinator-cli.js                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  start → 读取配置 → 判断 nodeType → 启动对应扫描器   │   │
│  │  stop  → 读取 PID → 终止进程                        │   │
│  │  status → 读取配置 + PID → 显示状态                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│     MasterScanner       │    │     WorkerScanner       │
│  ┌───────────────────┐  │    │  ┌───────────────────┐  │
│  │ 结果扫描 (30s)    │  │    │  │ 任务扫描 (30s)    │  │
│  │ 检查 results/     │  │    │  │ 检查 commands/    │  │
│  └───────────────────┘  │    │  └───────────────────┘  │
│  ┌───────────────────┐  │    │  ┌───────────────────┐  │
│  │ 心跳检查 (5min)   │  │    │  │ 心跳发送 (5min)   │  │
│  │ 检查 heartbeats   │  │    │  │ 更新 heartbeats   │  │
│  └───────────────────┘  │    │  └───────────────────┘  │
└─────────────────────────┘    └─────────────────────────┘
```

---

## 目录结构

```
D:\projects\
├── config/
│   ├── tasks.json           # 任务状态表
│   ├── heartbeats.json      # 节点心跳表
│   └── settings.json        # 全局设置
├── workspace/
│   ├── shared/
│   │   ├── tasks/           # 任务素材
│   │   ├── input/           # 输入文件
│   │   └── output/          # 输出文件
│   ├── node-claude/         # Claude Code 工作区
│   ├── node-kimi/           # Kimi Code 工作区
│   └── node-xiaobai/        # 小白工作区
└── logs/                    # 运行日志
```

## 核心模块

### TaskManager（任务管理）

```javascript
const { TaskManager } = require('./src/task/task-manager');
const taskManager = new TaskManager();

// 创建任务
const task = taskManager.createTask({
  title: '分析销售数据',
  type: 'analysis',
  priority: 'high',
  instruction: '请分析 Q1 销售数据...',
  deadline: dayjs().add(3, 'minute').toISOString()
});

// 查询任务
const tasks = taskManager.getTasks({ status: 'pending' });
const task = taskManager.getTask('task-001');

// 更新状态
taskManager.assignTask('task-001', 'claude');
taskManager.startTask('task-001');
taskManager.submitTask('task-001', { output: '结果' });
taskManager.completeTask('task-001');
taskManager.failTask('task-001', { error: '错误信息' });
```

### NodeManager（节点管理）

```javascript
const { NodeManager } = require('./src/node/node-manager');
const nodeManager = new NodeManager();

// 注册节点
nodeManager.registerNode('claude', 'D:\\projects\\workspace\\node-claude');

// 发送心跳
nodeManager.heartbeat('claude', 'online');

// 查询节点
const nodes = nodeManager.getNodes();
const onlineNodes = nodeManager.getOnlineNodes();
const availableNodes = nodeManager.getAvailableNodes();

// 选择最优节点（负载最低）
const bestNode = nodeManager.selectBestNode();

// 获取状态摘要
const summary = nodeManager.getStatusSummary();
```

### HeartbeatChecker（心跳检查）

```javascript
const { HeartbeatChecker } = require('./src/heartbeat/heartbeat-checker');
const checker = new HeartbeatChecker();

// 设置回调
checker.setOnNodeOffline((nodeId, node) => {
  console.log(`节点 ${nodeId} 已离线`);
});

checker.setOnNodeOnline((nodeId, node) => {
  console.log(`节点 ${nodeId} 恢复在线`);
});

// 启动检查
checker.start(60000); // 每 60 秒检查一次
```

## 节点侧脚本

部署到各执行节点的脚本，负责拉取任务并执行：

```bash
# 启动节点
node scripts/node-agent.js claude D:\projects\workspace\node-claude
node scripts/node-agent.js kimi D:\projects\workspace\node-kimi
node scripts/node-agent.js xiaobai D:\projects\workspace\node-xiaobai
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| node-id | 节点 ID | claude |
| workspace | 节点工作区路径 | D:\projects\workspace\node-claude |

## 技能指令

### 创建任务

```
创建任务 [任务名称]
创建任务 [任务名称]，类型 [code/analysis/doc]
创建任务 [任务名称]，优先级 [high/medium/low]
创建任务 [任务名称]，截止时间 [3分钟/5分钟/自定义时间]
```

示例：
- 创建任务 分析 Q1 销售数据
- 创建任务 编写用户认证模块，类型 code，优先级 high
- 创建任务 生成月度报告，类型 doc，截止时间 10 分钟

### 查询任务

```
查看任务列表
查看任务 [任务ID]
查看待处理任务
查看已完成任务
查看失败任务
```

### 节点管理

```
查看节点状态
查看节点列表
```

### 任务操作

```
确认任务 [任务ID]
重处理任务 [任务ID]
取消任务 [任务ID]
手动分配任务 [任务ID] 到 [节点ID]
```

## 输出格式模板

### 任务列表

```markdown
## 任务列表（共 X 个）

**待执行（X）**
- [task-001] 任务名称 (高)
- [task-002] 任务名称 (中)

**执行中（X）**
- [task-003] 任务名称 -> claude

**已提交（X）**
- [task-004] 任务名称 -> claude [待确认]

**已完成（X）**
- [task-005] 任务名称

**失败（X）**
- [task-006] 任务名称 [重试1次]
```

### 节点状态

```markdown
## 节点状态

总计: 3 | 在线: 2 | 忙碌: 1 | 离线: 1 | 任务数: 1

### claude
- 状态: 忙碌
- 任务数: 1/2
- 最后心跳: 20:45:00
- 工作区: D:\projects\workspace\node-claude

### kimi
- 状态: 在线
- 任务数: 0/2
- 最后心跳: 20:44:30
- 工作区: D:\projects\workspace\node-kimi

### xiaobai
- 状态: 离线
- 任务数: 0/2
- 最后心跳: 15:00:00
- 工作区: D:\projects\workspace\node-xiaobai
```

## 配置说明

### settings.json

```json
{
  "scanInterval": 120000,
  "heartbeatInterval": 300000,
  "heartbeatTimeout": 360,
  "maxTaskPerNode": 2,
  "defaultTaskTimeout": 180000,
  "retry": {
    "maxRetries": 2,
    "delaySeconds": 30
  }
}
```

---

## 子节点部署说明（Claude Code 模式）

### 架构说明

子节点作为 Claude Code 直接执行任务，不需要再调用 `claude -p`。

```
子节点（Claude Code）:
  1. 定时扫描 commands/{node}/ 目录
  2. 读取 task-xxx.json
  3. 自己理解并执行任务
  4. 写入 results/{node}/task-xxx.json
```

### 启动子节点

```bash
# 方式1：使用 bat 脚本（需要先复制到 D:\projects\）
D:\projects\start-sub-agent-claude.bat

# 方式2：手动启动
cd D:\projects\skills\multi-agent-coordinator
node scripts\sub-agent.js claude
```

### 部署流程

子节点启动前需要将 Skills 代码同步到运行目录：

```
1. 从 GitHub 拉取最新代码
2. 复制到 D:\projects\skills\multi-agent-coordinator\
3. 双击 start-sub-agent-claude.bat 启动
```

### 启动文件

| 文件 | 说明 |
|------|------|
| `D:\projects\start-sub-agent-claude.bat` | 启动 claude 子节点 |
| `D:\projects\start-sub-agent-kimi.bat` | 启动 kimi 子节点 |

### 子节点工作流程

```
1. 启动时
   └── 注册节点到 heartbeats.json

2. 每 5 分钟
   └── 发送心跳

3. 每 60 秒
   └── 扫描 commands/{node}/ 目录
   └── 发现任务文件
   └── 读取指令
   └── 更新任务状态为 running
   └── 执行任务（自己理解并执行）
   └── 写入 results/{node}/
   └── 更新任务状态为 submitted
```

---

## 替代方案：SDK 直接调用模式

如果你希望主节点直接通过 SDK 发送消息给 Claude Code 进程（而不是通过文件同步），可以使用 `claude-code-sender` 技能。

### 使用 SDK 方式的优势

1. **实时响应** - 不需要等待文件扫描周期
2. **会话保持** - 可以维持多轮对话上下文
3. **简化架构** - 不需要文件同步机制
4. **直接返回** - 结果直接返回，不需要轮询文件

### SDK 调用示例

```python
from claude_code_sender.scripts.claude_node_sdk import ClaudeNodeSDK, MultiNodeCoordinator

# 方式1: 单节点调用
sdk = ClaudeNodeSDK("claude", workspace="D:\\projects\\workspace\\node-claude")
result = sdk.send_task(
    instruction="创建一个简单的 Python 计算器类",
    max_turns=5
)
print(result["text"])

# 方式2: 多节点协调
coordinator = MultiNodeCoordinator()
coordinator.register_node("claude")
coordinator.register_node("kimi")

# 发送到指定节点
result = coordinator.send_task_to_node(
    node_id="claude",
    instruction="分析这个文件",
    file_path="data.txt"
)

# 广播到所有节点
results = coordinator.broadcast_task("检查代码风格")
```

### 两种模式对比

| 特性 | 文件同步模式 | SDK 直接调用模式 |
|------|-------------|-----------------|
| 通信方式 | 文件读写 | `claude -p` 命令 |
| 实时性 | 延迟（扫描周期） | 实时 |
| 会话保持 | 需手动管理 | 自动 `--continue` |
| 架构复杂度 | 需要文件目录结构 | 仅需 CLI |
| 适用场景 | 多节点异步任务 | 单节点同步任务 |

### 选择建议

- **文件同步模式**：适合多节点分布式任务、异步处理、任务队列场景
- **SDK 直接调用模式**：适合单节点快速响应、需要多轮对话、简单集成场景

---

## 节点 Agent 部署说明（已废弃）

### 通信机制

```
D:\projects\
├── config/
│   ├── tasks.json           # 任务状态表（主节点管理）
│   ├── heartbeats.json      # 节点心跳表
│   └── settings.json        # 全局设置
├── commands/                # 指令箱（主节点 → 节点）
│   ├── claude/
│   │   └── task-xxx.json   # 任务指令文件
│   ├── kimi/
│   └── xiaobai/
├── results/                # 结果箱（节点 → 主节点）
│   ├── claude/
│   │   └── task-xxx.json   # 任务结果文件
│   ├── kimi/
│   └── xiaobai/
└── workspace/
    └── shared/
        └── output/         # 任务输出目录
            └── task-xxx/
                ├── prompt.txt    # 任务指令
                └── result.json   # 执行结果
```

### 节点部署步骤

#### 1. 创建工作区目录

```bash
mkdir -p D:\projects\workspace\node-{node-id}
mkdir -p D:\projects\commands\{node-id}
mkdir -p D:\projects\results\{node-id}
```

#### 2. 复制必要文件

需要复制以下文件到节点工作区：
- `scripts/node-agent.js` - 节点 Agent 脚本
- `node_modules/dayjs/` - 依赖库

#### 3. 安装依赖（如果需要）

```bash
cd D:\projects\workspace\node-{node-id}
npm install dayjs
```

#### 4. 启动节点 Agent

```bash
cd D:\projects\workspace\node-{node-id}
node node-agent.js {node-id} "D:\projects\workspace\node-{node-id}"
```

示例：
```bash
# 启动 Claude Code 节点
node node-agent.js claude "D:\projects\workspace\node-claude"

# 启动 Kimi Code 节点
node node-agent.js kimi "D:\projects\workspace\node-kimi"

# 启动小白节点
node node-agent.js xiaobai "D:\projects\workspace\node-xiaobai"
```

### 节点 Agent 工作流程

```
1. 启动时
   └── 注册节点到 heartbeats.json
   
2. 每 5 分钟（心跳间隔）
   └── 更新心跳状态
   
3. 每 2 分钟（扫描间隔）
   └── 扫描 commands/{node-id}/ 目录
   └── 发现任务指令文件
   └── 读取指令
   └── 更新任务状态为 assigned
   └── 调用 Claude Code 执行任务
   └── 写入结果到 results/{node-id}/
   └── 更新任务状态为 submitted
   
4. 任务完成
   └── 减少节点任务计数
```

### 指令文件格式

```json
// commands/claude/task-001.json
{
  "taskId": "task-001",
  "command": "创建一个测试文件 test.txt，内容为 Hello",
  "workspace": "D:\\projects\\workspace\\shared",
  "outputDir": "D:\\projects\\workspace\\shared\\output\\task-001",
  "timeout": 300000,
  "createdAt": "2026-03-03T22:00:00.000Z",
  "deadline": "2026-03-03T22:05:00.000Z"
}
```

### 结果文件格式

```json
// results/claude/task-001.json
{
  "taskId": "task-001",
  "status": "success",
  "output": "文件已创建: test.txt\n内容: Hello",
  "outputFiles": ["test.txt"],
  "executedAt": "2026-03-03T22:00:05.000Z"
}
```

### 常用命令

```bash
# 查看节点日志
Get-Content D:\projects\logs\node-{node-id}.log -Tail 20

# 手动触发任务扫描
# 节点会在下次扫描周期自动执行

# 停止节点
# Ctrl+C 或关闭进程
```

---

## 注意事项

1. 节点需要先启动 node-agent.js 才能接收任务
2. 任务创建后需要等待节点拉取（约 2 分钟内）
3. 节点离线超过 6 分钟会被标记为 offline
4. 任务失败后会自动重试 2 次
5. 建议通过飞书通知任务状态变化
