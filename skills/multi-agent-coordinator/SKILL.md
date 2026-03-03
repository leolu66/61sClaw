# Multi-Agent Coordinator - 多节点协同工作技能

## 功能概述

协调多个 Claude Code 节点（Claude Code、Kimi Code、小白）协同工作，实现任务分发、执行和结果收集。

## 触发条件

当用户说以下内容时触发此技能：
- "创建任务 xxx"
- "查看任务列表" / "查看任务"
- "查看节点状态"
- "确认任务 xxx"
- "重处理任务 xxx"
- "取消任务 xxx"
- "手动分配任务 xxx 到 xxx"

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

## 节点 Agent 部署说明

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
