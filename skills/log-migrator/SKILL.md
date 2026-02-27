---
name: log-migrator
description: 定时迁移工作日志到外部归档目录，解决 Git 仓库空间不足问题。每天自动扫描工作区日志目录，将超过 7 天的文件迁移到 D:\openclaw\logs\archive\ 目录。
triggers:
  - 迁移日志
  - 归档日志
  - 清理日志
version: 1.0
---

# 日志迁移技能

自动将工作区内的旧日志迁移到外部归档目录，避免占用 Git 仓库空间。

## 触发条件

用户说以下任一指令时触发：
- "迁移日志"
- "归档日志"
- "清理日志"

## 功能描述

1. **扫描旧日志** - 检测工作区日志目录中超过 7 天的文件
2. **自动迁移** - 将旧文件迁移到外部归档目录
3. **清理源目录** - 删除已迁移的旧文件
4. **记录迁移日志** - 生成迁移报告和错误日志
5. **保留 7 天** - 只迁移 7 天前的文件，保留近期日志方便查阅

## 目录结构

```
workspace-main/logs/daily/           # 工作区日志（源）
├── 2026-02-21-001-...
├── 2026-02-27-003-...           # 7 天内的保留
└── 2026-02-20-002-...           # 超过 7 天的迁移

D:\openclaw\logs\daily\              # 外部归档（目标）
└── archive/
    ├── 2026/                       # 按年份归档
    │   ├── 02/                     # 按月份归档
    │   │   ├── 2026-02-15-...
    │   │   └── ...
    │   └── ...
    └── ...

workspace-main/logs/errors/           # 迁移日志
└── log-migration-YYYY-MM-DD.md
```

## 输入/输出

- **输入**: 无（自动运行）
- **输出**:
  - 迁移文件列表
  - 迁移统计信息
  - 错误报告（如有）

## 依赖条件

- 源目录存在：`workspace-main/logs/daily/`
- 目标目录可写：`D:\openclaw\logs\`
- Python 标准库（无额外依赖）

## 使用方法

### 手动执行

```bash
python scripts/migrate_logs.py
```

### 设置定时任务

#### Windows 任务计划程序

```powershell
# 创建每天凌晨 2 点运行的定时任务
$taskName = "日志自动归档"
$taskDescription = "每天晚上 11:20 自动迁移超过 7 天的工作日志"
$scriptPath = "C:\Users\luzhe\.openclaw\workspace-main\skills\log-migrator\scripts\migrate_logs.bat"

$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory "C:\Users\luzhe\.openclaw\workspace-main\skills\log-migrator\scripts"
$trigger = New-ScheduledTaskTrigger -Daily -At "23:20"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Description $taskDescription

Register-ScheduledTask -TaskName $taskName -InputObject $task -Force
```

### 快速启动

```bash
# 创建定时任务
python scripts/setup_task.ps1
```

## 配置项

在 `scripts/config.json` 中可调整以下参数：

```json
{
  "retention_days": 7,
  "source_dir": "logs/daily",
  "archive_base": "D:\\\\openclaw\\\\logs\\\\daily\\\\archive",
  "log_dir": "logs/errors"
  "dry_run": false
}
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| retention_days | 保留天数，超过此天数的文件将被迁移 | 7 |
| source_dir | 工作区日志源目录（相对路径） | logs/daily |
| archive_base | 外部归档根目录（绝对路径） | D:\openclaw\logs\daily\archive |
| log_dir | 迁移日志目录（相对路径） | logs/errors |
| dry_run | 试运行模式，只显示将要迁移的文件，不实际迁移 | false |

## 输出示例

```bash
============================================================
日志自动归档
============================================================
扫描目录: logs/daily/
保留天数: 7 天
目标目录: D:\openclaw\logs\daily\archive
------------------------------------------------------------
📋 发现 3 个文件需要迁移:

  2026-02-15-001-...
  2026-02-16-002-...
  2026-02-18-003-...

------------------------------------------------------------
📦 开始迁移...

  ✅ 2026-02-15-001-... → D:\openclaw\logs\daily\archive\2026\02\
  ✅ 2026-02-16-002-... → D:\openclaw\logs\daily\archive\2026\02\
  ✅ 2026-02-18-003-... → D:\openclaw\logs\daily\archive\2026\02\

------------------------------------------------------------
✅ 迁移完成！
  迁移文件: 3
  节省空间: 15 KB
  归档目录: D:\openclaw\logs\daily\archive\2026\02\

============================================================
迁移日志已保存: logs/errors/log-migration-2026-02-28.md
============================================================
```

## 边界情况

- **源目录不存在**：提示创建目录，不执行迁移
- **目标目录不可写**：报错并记录到日志
- **文件被占用**：跳过该文件，记录到错误日志
- **文件已存在**：跳过迁移，记录到日志
- **干运行模式**：只显示将要迁移的文件，不实际移动

## 注意事项

1. **定时任务权限**：确保任务计划程序有足够的权限访问目录
2. **磁盘空间**：确保目标目录有足够的磁盘空间
3. **备份策略**：建议定期备份归档目录
4. **日志清理**：定期查看归档目录，手动清理不再需要的日志
5. **保留策略**：默认保留 7 天，可根据需要调整

---

## DoD 检查表

**开发日期**: 2026-02-28
**开发者**: 小天才

- [x] SRS 文档完整（触发条件、功能、输入输出、依赖、边界）
- [x] 技能文件结构规范
- [x] 代码使用相对路径
- [x] 配置外置（config.json）
- [ ] 功能测试通过
- [ ] 触发测试通过
- [ ] 定时任务测试通过
- [ ] 无 .skill 文件
- [ ] 无隐私文件
- [ ] 已提交并推送到 GitHub（master 和 main）

**状态**: 🚧 开发中
