# 2026-03-05 | 多智能体协调器心跳机制优化

## 任务概述
优化 multi-agent-coordinator 技能的定时扫描机制，将任务扫描从心跳中分离，实现独立的定时扫描系统。

## 完成内容

### 1. 统一配置文件结构
- 创建 `config/coordinator.json` 统一入口配置
- 支持主节点(master)和子节点(worker)配置
- 支持本地覆盖配置 `coordinator.local.json`
- 配置项：扫描间隔(30s)、心跳间隔(5min)、节点类型等

### 2. 配置加载类
- 实现 `src/config/config-loader.js`
- 支持热加载(forceReload)
- 缓存机制(5秒)避免频繁读取
- 深度合并配置对象

### 3. CLI 工具
- 实现 `coordinator-cli.js`
- 命令：start/stop/status/restart/reload
- PID 文件管理 `coordinator.pid`
- 状态文件管理 `coordinator.status`
- 支持热重载配置

### 4. 独立扫描器
- **MasterScanner** - 主节点扫描器
  - 30秒扫描子节点结果
  - 5分钟检查节点心跳
  - 任务状态自动更新
  
- **WorkerScanner** - 子节点扫描器
  - 30秒扫描任务指令
  - 5分钟发送心跳
  - 任务执行和结果写入

### 5. 技能主入口
- 实现 `index.js` 技能主入口
- 处理用户指令：启动/停止/查看状态/重载配置
- 调用 CLI 工具并读取状态文件确认结果
- 提供 `handleCommand()` 等导出函数

## 关键设计决策

### 状态文件通信机制
```
用户指令 → 技能处理 → CLI工具 → 守护进程 → 状态文件 → 技能确认 → 返回结果
```

### 配置分层
- 统一入口：`coordinator.json`
- 本地覆盖：`coordinator.local.json` (gitignore)
- 运行时状态：`coordinator.status` / `coordinator.pid`

## 技术要点

- 扫描间隔 30 秒（比原来 2 分钟更实时）
- 心跳保持 5 分钟低频运行
- 状态文件每 30 秒自动更新
- 支持配置热重载（无需重启）

## 新增文件

```
config/
├── coordinator.json
└── .gitignore

skills/multi-agent-coordinator/
├── index.js (新增)
├── coordinator-cli.js (新增)
├── coordinator-daemon.js (新增)
└── src/
    ├── config/config-loader.js (新增)
    └── scanner/
        ├── master-scanner.js (新增)
        └── worker-scanner.js (新增)

scripts/
└── start-scanner.bat (新增)
```

## 更新文件

- `skills/multi-agent-coordinator/SKILL.md` - 新增定时扫描器文档

## 验证结果

- ✅ 启动任务扫描 - 守护进程正常启动
- ✅ 停止任务扫描 - 进程正常停止
- ✅ 查看扫描状态 - 状态文件正确读取
- ✅ PID 和状态文件管理正常

## 后续优化方向

1. 集成飞书通知（任务完成/节点离线）
2. 任务执行逻辑接入 Claude Code
3. 支持多子节点并行任务分配
4. Web 界面可视化节点状态

## 关联技能

- multi-agent-coordinator
- claude-code-sender
