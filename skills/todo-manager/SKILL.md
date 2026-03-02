# Todo Manager - 任务管理技能

## 功能概述

支持策略化提醒的任务管理工具，可以创建、查询、更新、完成任务，并通过 heartbeat 定时检查提醒。

## 触发条件

当用户说以下内容时触发此技能：
- "创建任务" / "新建任务" / "添加任务"
- "查看任务" / "显示任务" / "任务列表"
- "完成任务" / "标记完成"
- "删除任务" / "取消任务"
- "查看逾期任务"
- "调整任务时间"

## 使用方法

### 1. 创建任务

```javascript
const { manager } = require('./index');

const task = manager.createTask({
  title: '完成项目文档',
  description: '编写技术文档和用户手册',
  type: 'work',  // work/personal/study/other，可选，会自动推断
  deadline: '明天',  // 支持：今天/明天/周三/3月2日/2026-03-02
  priority: 'high',  // high/medium/low，可选，默认 medium
  reminderStrategy: {
    type: 'daily',  // daily/weekly/monthly，可选，会自动推断
    frequency: 'once',  // 见下方策略说明
    exceptions: {
      workHoursOnly: false,  // 仅工作时间提醒
      workdaysOnly: false    // 仅工作日提醒
    },
    customTime: '09:00'  // 自定义提醒时间
  }
});

console.log('任务已创建:', task.id);
```

### 2. 查询任务

```javascript
// 查询所有待办任务
const tasks = manager.getTasks({ status: 'pending' });

// 查询今天的任务
const todayTasks = manager.getTasks({ 
  status: 'pending', 
  timeRange: 'today' 
});

// 查询逾期任务
const overdueTasks = manager.getOverdueTasks();

// 按时间分组显示
const { TaskFormatter } = require('./index');
console.log(TaskFormatter.format(tasks, 'time'));

// 按类型分组显示
console.log(TaskFormatter.format(tasks, 'type'));

// 按优先级分组显示
console.log(TaskFormatter.format(tasks, 'priority'));
```

### 3. 更新任务

```javascript
// 更新任务信息
manager.updateTask(taskId, {
  title: '新标题',
  deadline: '后天',
  priority: 'high'
});

// 完成任务
manager.completeTask(taskId);

// 取消任务
manager.cancelTask(taskId);
```

### 4. 删除任务

```javascript
manager.deleteTask(taskId);
```

## 提醒策略说明

### 每日任务策略 (type: 'daily')

- `none` - 不提醒
- `once` - 当天早上 9:00 提醒一次
- `twice` - 早上 9:00 + 晚上 18:00 各提醒一次
- `every2h` - 从早上 9:00 开始，每 2 小时提醒一次（9:00, 11:00, 13:00, 15:00, 17:00）

### 每周任务策略 (type: 'weekly')

- `none` - 不提醒
- `someday` - 一周内某天提醒（默认周一 10:00）
- `everyday` - 每天早上 9:00 提醒

### 每月任务策略 (type: 'monthly')

- `none` - 不提醒
- `someday` - 一个月内某天提醒（默认每月 1 号 10:00）
- `everyMonday` - 每周一早上 10:00 提醒
- `everyday` - 每天早上 9:00 提醒

### 例外控制

- `workHoursOnly: true` - 只在 9:00-18:00 之间提醒
- `workdaysOnly: true` - 只在周一到周五提醒

## 时间解析支持

- **相对时间**: 今天、明天、后天、本周、下周、本月、下月
- **星期**: 周一、周二、周三、周四、周五、周六、周日
- **日期**: 3月2日、3-2、03-02
- **ISO 格式**: 2026-03-02
- **相对天数**: 3天后、5天内

## Heartbeat 集成

在 `HEARTBEAT.md` 中添加：

```markdown
## 任务提醒检查

每次 heartbeat 检查待办任务的提醒时间，如果到期则发送通知。

执行命令：
node ~/.openclaw/workspace-main/skills/todo-manager/scripts/heartbeat-check.js
```

## 通知方式

- **控制台通知**: 直接打印到控制台
- **飞书通知**: 通过 feishu-notifier 技能发送消息

## 数据存储

任务数据存储在 `data/tasks.json`，格式如下：

```json
{
  "tasks": [
    {
      "id": "uuid",
      "title": "任务标题",
      "description": "详细描述",
      "type": "work",
      "deadline": "2026-03-02T23:59:59+08:00",
      "priority": "medium",
      "status": "pending",
      "createdAt": "2026-03-01T03:31:00+08:00",
      "completedAt": null,
      "reminderStrategy": {
        "type": "daily",
        "frequency": "once",
        "exceptions": {},
        "customTime": "09:00"
      },
      "reminders": [
        {
          "scheduledTime": "2026-03-02T09:00:00+08:00",
          "sent": false,
          "sentAt": null
        }
      ]
    }
  ],
  "config": {
    "workHours": {
      "start": "09:00",
      "end": "18:00"
    },
    "workdays": [1, 2, 3, 4, 5]
  }
}
```

## 示例场景

### 场景 1: 创建每日任务

```javascript
manager.createTask({
  title: '完成代码审查',
  deadline: '今天',
  reminderStrategy: {
    frequency: 'twice'  // 早晚各提醒一次
  }
});
```

### 场景 2: 创建每周任务

```javascript
manager.createTask({
  title: '周报总结',
  deadline: '本周',
  reminderStrategy: {
    type: 'weekly',
    frequency: 'someday',  // 周一提醒
    exceptions: {
      workdaysOnly: true
    }
  }
});
```

### 场景 3: 创建每月任务

```javascript
manager.createTask({
  title: '月度复盘',
  deadline: '本月',
  reminderStrategy: {
    type: 'monthly',
    frequency: 'everyMonday',  // 每周一提醒
    exceptions: {
      workHoursOnly: true
    }
  }
});
```

### 场景 4: 查询并调整逾期任务

```javascript
const overdueTasks = manager.getOverdueTasks();
console.log(TaskFormatter.format(overdueTasks, 'time'));

// 调整逾期任务到明天
overdueTasks.forEach(task => {
  manager.updateTask(task.id, { deadline: '明天' });
});
```

## 注意事项

1. **逾期任务不会继续提醒**，需要手动调整时间
2. **任务类型会自动推断**，也可以手动指定
3. **提醒策略默认值**：
   - 每日任务默认 `once`
   - 每周任务默认 `someday`（周一）
   - 每月任务默认 `someday`（1号）
4. **Heartbeat 检查频率**：约 60 分钟一次，允许 5 分钟误差
5. **工作时间默认**：9:00-18:00
6. **工作日默认**：周一到周五

## 依赖

- `dayjs` - 时间处理
- `uuid` - 生成唯一 ID

## 文件结构

```
todo-manager/
├── data/
│   └── tasks.json              # 任务数据存储
├── src/
│   ├── core/
│   │   ├── task-manager.js     # 任务 CRUD
│   │   ├── time-parser.js      # 时间解析
│   │   └── storage.js          # JSON 存储
│   ├── reminder/
│   │   ├── strategy-engine.js  # 策略引擎
│   │   ├── reminder-checker.js # 提醒检查器
│   │   └── notifier.js         # 通知发送器
│   └── display/
│       └── task-formatter.js   # 任务格式化
├── scripts/
│   └── heartbeat-check.js      # Heartbeat 入口
├── index.js                    # 主入口
├── package.json
└── SKILL.md                    # 本文档
```

## 输出格式模板
### 待办任务列表
```markdown
#### 📋 待办任务（共 X 个）
**今天任务**
- [数字编号] 优先级 类别 任务名
**本周任务**
- [数字编号] 优先级 类别 任务名 (MM-DD)
**本月任务**
- [数字编号] 优先级 类别 任务名 (MM-DD) **-->【有评论】**
**长期任务**
- [数字编号] 优先级 类别 任务名
#### 图例 
- 优先级: 🔴 高 | 🟡 中 | 🟢 低
- 类别: 💼 工作 | 🏠 个人 | 📚 学习 | 📌 其他
#### 提醒：总结今日和近期高优先级的事情
```

### 任务详情

```markdown
📋 任务标题 [编号]
- 唯一编号: YYYYMMDD-XXX
- 类型: 💼 工作 | 优先级: 🔴 高
- 截止: YYYY-MM-DD HH:mm
- 描述: 任务描述内容

💬 最新评论:
1. 评论内容 (MM-DD HH:mm)
```

### 完成任务

```markdown
✅ 任务已完成：任务标题
💬 备注：评论内容（可选）
```
```
