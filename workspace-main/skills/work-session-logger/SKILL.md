---
name: work-session-logger
description: |
  记忆管理系统 - 总结当前会话内容并写入日志文件。
  
  **核心思路**：模型直接生成日志内容，不依赖外部脚本。
  
  触发"记录工作日志"时 → 生成详细工作日志到 logs/daily/
  触发"记录记忆"时 → 生成每日记忆到 memory/
triggers:
  - "记录工作日志"
  - "总结本次会话"
  - "保存工作内容"
  - "写入日志"
  - "记录记忆"
  - "保存记忆"
  - "记录今日记忆"
version: 2.0
---

# 工作会话日志记录器

**记忆管理系统** - 模型直接生成日志内容，不依赖外部脚本。

## 记忆管理系统说明

根据 MEMORY.md 中的持续总结原则，记忆系统分为两种记录类型：

### 1. 工作日志（logs/daily/）

| 项目 | 说明 |
|------|------|
| 路径 | `logs/daily/` |
| 用途 | 详细记录每次会话的工作内容 |
| 触发词 | "记录工作日志"、"总结本次会话"、"保存工作内容"、"写入日志" |
| 文件名 | `YYYY-MM-DD-NNN-概述.md` |
| 内容 | 完整的任务详情、问题诊断、解决方案、关键决策 |

### 2. 每日记忆（memory/）

| 项目 | 说明 |
|------|------|
| 路径 | `memory/` |
| 用途 | 当天重要工作、新知识、错误反思、开发经验 |
| 触发词 | "记录记忆"、"保存记忆"、"记录今日记忆" |
| 文件名 | `YYYY-MM-DD.md` |
| 内容 | 提炼总结，非流水账 |

## 工作流程

### 核心思路：模型直接生成

当用户触发"记录工作日志"或"记录记忆"时：

1. **理解会话**：模型根据当前上下文，理解本次会话的内容
2. **生成内容**：模型直接生成结构化日志
3. **写入文件**：使用 write 工具保存到对应目录

**重要**：不再依赖外部 Python 脚本从 session 文件提取内容，因为 session 文件已被污染。

### 当用户说"记录工作日志"

1. 模型回顾本次会话要点
2. 生成结构化工作日志（包含任务详情、问题诊断、解决方案）
3. 保存到 `logs/daily/YYYY-MM-DD-NNN-概述.md`

### 当用户说"记录记忆"

1. 模型提炼当天会话关键信息
2. 按结构生成：重要工作、新知识、错误反思、开发经验
3. 保存到 `memory/YYYY-MM-DD.md`（追加而非覆盖）

## 敏感信息过滤（重要！）

在写入日志或记忆前，必须对以下内容进行脱敏处理：

**过滤规则：**
| 类型 | 匹配模式 | 替换为 |
|------|---------|--------|
| 密码 | `password[=:]\S+`、`pwd[=:]\S+`、`密码 [=:]\S+`、` 口令 [=:]\S+` | `******` |
| API Key/Token | `api_key[=:]\S+`、`apikey[=:]\S+`、`token[=:]\S+`、`secret[=:]\S+`、`密钥 [=:]\S+` | `******` |
| 手机号 | `1[3-9]\d{9}` | 保留前 3 后 4，中间 `****`（如 `186****0622`） |
| 邮箱 | `\w+@\w+\.\w+` | 保留前后，中间 `***`（如 `abc***@gmail.com`） |
| 身份证号 | `\d{17}[\dXx]` | `******` |
| 银行卡号 | `\d{16,19}` | 保留前 4 后 4，中间 `****` |

**处理原则：**
- 保留字段名，只隐藏敏感值（便于理解上下文）
- 用户明确标记为敏感的其它内容也要过滤
- 如果不确定是否敏感，宁可过滤也不要泄露

## 配置说明

### 工作区路径配置

路径计算优先级：
1. **配置文件**：`skills/work-session-logger/config.json` 中的 `workspace_base_path` 字段
2. **相对路径兜底**：向上回退4层目录到工作区根目录

默认配置：
```json
{
  "workspace_base_path": "C:\\Users\\luzhe\\.openclaw\\workspace-main"
}
```

如果工作区路径发生变化，直接修改 `config.json` 中的路径即可，无需修改脚本代码。

## 目录结构

### 工作日志目录

```
logs/
├── daily/         # 每日会话总结
├── tasks/         # 任务执行日志
├── errors/        # 错误反思记录
└── summary/       # 阶段性总结
```

### 每日记忆目录

```
memory/
├── 2026-03-01.md  # 每日记忆文件
├── 2026-03-02.md
├── 2026-03-03.md
└── ...
```

**路径说明**：
- 所有路径均为相对于工作区根目录的相对路径
- 实际路径根据脚本位置动态计算
- 支持任意工作区名称

## 工作日志格式

```markdown
# 工作日志 #NNN

## 基本信息

| 项目 | 内容 |
|------|------|
| 日志编号 | #NNN |
| 日期 | YYYY-MM-DD |
| 开始时间 | HH:MM |
| 结束时间 | HH:MM |
| 会话时长 | X小时XX分钟 |

## 工作内容概述

简要描述本次会话的主要工作内容。

## 完成的任务

### 任务1：任务名称

**描述**：详细描述任务内容

**执行过程**：
1. 步骤一
2. 步骤二
3. 步骤三

**使用工具/技能**：
- `工具名`：用途说明
- `技能名`：用途说明

## 关键决策与成果

- **决策1**：描述决策内容及原因
- **成果1**：描述取得的具体成果

## 遇到的问题与解决方案

| 问题描述 | 原因分析 | 解决方案 | 结果 |
|---------|---------|---------|------|
| 问题1 | 原因 | 如何解决 | 已解决/待跟进 |

## 备注

- 需要后续跟进的事项
- 重要的参考链接
- 其他补充信息

---

**安全说明：** 本日志已自动过滤敏感信息（密码、API Key、手机号等），如需记录完整信息请手动补充。

*日志生成时间：YYYY-MM-DD HH:MM:SS*
```

## 每日记忆格式

```markdown
# YYYY-MM-DD 记忆

## 重要工作

- 整理了技能开发规范，创建 skill-creator-local 和 timer-alarm
- 从 AGENTS.md 移除技能开发原则，从 MEMORY.md 移除技能开发经验
- 完善 SKILL_DO.md 的文件路径规范

## 学到的新知识

- 技能创建时可以通过定制 init_skill.py 自动注入规范
- 文件路径规范：内部用相对路径，外部用配置

## 错误记录和反思

- 无

## 开发经验总结

- 规范应该集中管理，避免分散在多个文件中
- 创建技能时优先使用本地定制版 skill-creator-local
```

## 文件名生成逻辑

### 工作日志

```python
import os
import re
from datetime import datetime
from pathlib import Path

def get_next_log_filename(summary="", log_dir="logs/daily"):
    """
    生成下一个工作日志文件名
    
    Args:
        summary: 简短概述（2-4个关键词，用+连接）
        log_dir: 日志存放目录（相对路径）
    
    Returns:
        (filepath, filename): 完整路径和文件名
    """
    # 获取工作区根目录
    workspace_dir = Path(__file__).parent.parent.parent
    full_log_dir = workspace_dir / log_dir
    
    # 确保目录存在
    full_log_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 扫描现有文件，找到当天的最大序号
    max_seq = 0
    for filename in os.listdir(full_log_dir):
        if filename.startswith(today) and filename.endswith('.md'):
            try:
                parts = filename.replace('.md', '').split('-')
                if len(parts) >= 4:
                    seq = int(parts[3])
                    max_seq = max(max_seq, seq)
            except (ValueError, IndexError):
                continue
    
    # 生成新序号（3位数字，补零）
    next_seq = max_seq + 1
    
    # 清理概述字符串，确保文件名安全
    if summary:
        # 移除非法字符
        safe_summary = re.sub(r'[\\/*?:"<>|]', '', summary)
        # 空格替换为+
        safe_summary = safe_summary.replace(' ', '+')
        filename = f"{today}-{next_seq:03d}-{safe_summary}.md"
    else:
        filename = f"{today}-{next_seq:03d}.md"
    
    filepath = full_log_dir / filename
    return str(filepath), filename
```

### 每日记忆

```python
def get_memory_filename(date_str=None):
    """
    生成每日记忆文件名
    
    Args:
        date_str: 日期字符串（YYYY-MM-DD），默认为今天
    
    Returns:
        filepath: 记忆文件完整路径
    """
    workspace_dir = Path(__file__).parent.parent.parent
    memory_dir = workspace_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    filepath = memory_dir / f"{date_str}.md"
    return str(filepath)
```

## 使用示例

### 示例1：记录工作日志

```markdown
# 工作日志 #001

## 基本信息

| 项目 | 内容 |
|------|------|
| 日志编号 | #001 |
| 日期 | 2026-02-13 |
| 开始时间 | 09:30 |
| 结束时间 | 10:45 |
| 会话时长 | 1小时15分钟 |

## 工作内容概述

修复了MCP服务器的连接问题，验证了邮件读取功能，并创建了工作日志记录机制。

## 完成的任务

### 任务1：修复MCP连接问题

**描述**：用户反映MCP服务器无法连接，需要诊断并修复。

**执行过程**：
1. 检查了MCP配置文件，发现端口配置错误
2. 修改了配置文件中的端口号
3. 重启MCP服务，验证连接正常

**使用工具**：
- `ReadFile`：读取配置文件
- `StrReplaceFile`：修改配置
- `Shell`：重启服务

## 关键决策与成果

- **决策**：将MCP服务端口从8080改为3000，避免与其他服务冲突
- **成果**：邮件读取功能验证通过，可以正常使用

## 遇到的问题与解决方案

| 问题描述 | 原因分析 | 解决方案 | 结果 |
|---------|---------|---------|------|
| MCP连接超时 | 端口被占用 | 修改配置文件，更换端口 | 已解决 |
| 邮件附件乱码 | 编码问题 | 添加UTF-8编码处理 | 已解决 |

## 备注

- 后续需要监控MCP服务稳定性
- 考虑添加端口占用检测机制
```

### 示例2：记录每日记忆

```markdown
# 2026-03-05 记忆

## 重要工作

- 整理了技能开发规范，创建 skill-creator-local 和 timer-alarm
- 从 AGENTS.md 移除技能开发原则，从 MEMORY.md 移除技能开发经验
- 完善 SKILL_DO.md 的文件路径规范

## 学到的新知识

- 技能创建时可以通过定制 init_skill.py 自动注入规范
- 文件路径规范：内部用相对路径，外部用配置

## 错误记录和反思

- 无

## 开发经验总结

- 规范应该集中管理，避免分散在多个文件中
- 创建技能时优先使用本地定制版 skill-creator-local
```

## 注意事项

### 工作日志
1. **自动递增序号**：同一天内多次记录会自动递增序号（001, 002, 003...）
2. **摘要精炼**：概述控制在2-4个关键词，便于快速识别内容
3. **非法字符处理**：自动移除文件名中的非法字符（`\/*?:"<>|`）
4. **目录自动创建**：如果日志目录不存在，自动创建
5. **时间记录**：使用24小时制，精确到分钟

### 每日记忆
1. **每天一个文件**：同一天多次记录会追加到同一文件
2. **简洁为主**：突出重点，不要详细描述
3. **分类清晰**：按重要工作、新知识、错误反思、开发经验分类
4. **便于回顾**：方便日后快速回顾当天重点

## 相关技能

- `doc-coauthoring`：编写文档和提案
- `internal-comms`：内部沟通文档
- `kimi-cli-help`：Kimi CLI使用帮助
