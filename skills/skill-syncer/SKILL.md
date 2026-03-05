---
name: skill-syncer
description: 从 GitHub 远程仓库获取最新技能并更新本地同名技能。支持指定单个技能获取或批量获取全部技能，智能保护本地特有技能不被覆盖。当用户说"获取 xxx 技能"、"get xxx skill"、"获取全部技能"、"get all skills"时触发。
---

# Skill Syncer - 技能同步工具

## 概述

从 GitHub 远程仓库 (`https://github.com/leolu66/61sClaw`) 获取最新技能，智能更新本地同名技能，保护本地特有技能不被覆盖。

## 核心功能

### 1. 智能同步策略

```
远程技能列表 ←── GitHub API ──→ 本地技能列表
      │                              │
      ▼                              ▼
┌─────────────┐              ┌─────────────┐
│  skill-a    │── 同名更新 ─▶│  skill-a    │
│  skill-b    │── 同名更新 ─▶│  skill-b    │
│  skill-c    │              │  skill-d    │ ← 本地特有（保留）
└─────────────┘              └─────────────┘
```

**同步规则**:

#### 获取单个技能
- ✅ 远程和本地都有的技能 → **更新**（用远程版本覆盖）
- 📦 远程有、本地没有的技能 → **安装**（自动安装新技能）
- 🛡️ 本地有、远程没有的技能 → **保护**（不删除本地特有技能）

#### 获取全部技能
- ✅ 远程和本地都有的技能 → **更新**（用远程版本覆盖）
- 📦 远程有、本地没有的技能 → **安装**（自动安装新技能）
- 🛡️ 本地有、远程没有的技能 → **保护**（不删除本地特有技能）

### 2. 支持的命令

#### 获取单个技能

| 命令格式 | 示例 |
|---------|------|
| `获取 {skill-name}` | `获取 multi-agent-coordinator` |
| `获取技能 {skill-name}` | `获取技能 claude-code-sender` |
| `get {skill-name}` | `get todo-manager` |
| `get skill {skill-name}` | `get skill api-balance-checker` |

**强制更新**（覆盖本地特有技能保护）：
```bash
python scripts/sync_cli.py get {skill-name} --force
```

#### 获取全部技能

| 命令格式 | 说明 |
|---------|------|
| `获取全部技能` | 更新所有本地技能，安装远程新技能 |
| `获取所有技能` | 同上 |
| `get all skills` | 英文命令 |
| `get all` | 简写形式 |

**强制更新全部**（覆盖本地特有技能保护）：
```bash
python scripts/sync_cli.py get-all --force
```

## 使用方式

### 方式1: 使用脚本（推荐）

```python
from skill_syncer.scripts.sync_manager import SkillSyncManager

# 初始化同步管理器
syncer = SkillSyncManager(
    github_repo="leolu66/61sClaw",
    local_skills_dir="skills"
)

# 获取单个技能
result = syncer.sync_skill("multi-agent-coordinator")
print(f"更新: {result['updated']}")
print(f"变更文件: {result['files_changed']}")

# 获取全部技能
results = syncer.sync_all_skills()
print(f"成功: {results['success_count']}")
print(f"失败: {results['failed_count']}")
print(f"详情: {results['details']}")
```

### 方式2: 命令行

```bash
# 获取单个技能
python skills/skill-syncer/scripts/sync_cli.py get multi-agent-coordinator

# 强制更新单个技能（覆盖本地特有技能保护）
python skills/skill-syncer/scripts/sync_cli.py get multi-agent-coordinator --force

# 获取全部技能
python skills/skill-syncer/scripts/sync_cli.py get-all

# 强制更新全部技能
python skills/skill-syncer/scripts/sync_cli.py get-all --force

# 预览变更（不实际执行）
python skills/skill-syncer/scripts/sync_cli.py preview multi-agent-coordinator
```

## 配置

### 配置文件

`skills/skill-syncer/scripts/config.json`:

```json
{
  "github": {
    "repo": "leolu66/61sClaw",
    "branch": "main",
    "skills_path": "skills",
    "raw_url": "https://raw.githubusercontent.com/leolu66/61sClaw/main"
  },
  "local": {
    "skills_dir": "skills",
    "backup_before_sync": true,
    "backup_dir": "backups/skills"
  },
  "sync": {
    "protect_local_only_skills": true,
    "skip_new_remote_skills": true,
    "file_patterns": [
      "SKILL.md",
      "scripts/**/*.py",
      "scripts/**/*.js",
      "references/**/*",
      "assets/**/*"
    ]
  }
}
```

## 脚本资源

### scripts/sync_manager.py

核心同步管理器，提供：
- `SkillSyncManager` - 同步管理类
- `sync_skill(skill_name)` - 同步单个技能
- `sync_all_skills()` - 同步所有技能
- `compare_versions(skill_name)` - 比较版本差异
- `backup_skill(skill_name)` - 备份技能

### scripts/github_client.py

GitHub API 客户端：
- `GitHubClient` - GitHub 客户端类
- `get_repo_tree()` - 获取仓库文件树
- `get_file_content(path)` - 获取文件内容
- `get_skills_list()` - 获取技能列表

### scripts/sync_cli.py

命令行工具：
- `get <skill-name>` - 获取单个技能
- `get-all` - 获取全部技能
- `preview <skill-name>` - 预览变更
- `list` - 列出可同步的技能

## 输出格式

### 单个技能同步结果

```markdown
## 技能同步结果: multi-agent-coordinator

✅ 同步成功

**变更详情**:
- 更新文件: 3 个
  - SKILL.md (修改: +45/-12)
  - scripts/sub-agent.js (修改: +23/-5)
  - references/api.md (新增)
- 删除文件: 0 个

**备份位置**: backups/skills/multi-agent-coordinator/20260304-221530/

**本地特有文件保护** (未受影响):
- config/local-settings.json
```

### 批量同步结果

```markdown
## 批量技能同步结果

**统计**:
- 总计: 8 个
- 更新: 5 个（本地技能已更新）
- 安装: 1 个（新技能已安装）
- 失败: 0 个
- 跳过: 2 个（本地特有技能已保护）

**详情**:

| 技能名称 | 状态 | 变更文件 | 说明 |
|---------|------|---------|------|
| claude-code-sender | ✅ 已更新 | 3 | 文件已更新 |
| multi-agent-coordinator | ✅ 已更新 | 1 | 文件已更新 |
| skill-syncer | 📦 新安装 | 4 | 新技能已安装 |
| local-custom-skill | 🛡️ 已保护 | - | 本地特有，已保护 |
```

## 安全机制

### 1. 备份机制

**更新技能前自动备份**（仅针对已存在的技能）：
```
backups/skills/
├── multi-agent-coordinator/
│   └── 20260304-221530/     # 时间戳备份
│       ├── SKILL.md
│       └── scripts/
├── claude-code-sender/
│   └── 20260304-221545/
```

**说明**:
- 只有更新已存在的技能时才会备份
- 新技能安装时不需要备份（本地没有旧版本）
- 备份保留原技能完整内容，可随时恢复

### 2. 本地技能保护

本地特有技能（远程不存在的）会被标记并保护：
- 不删除
- 不修改
- 在报告中列出

### 3. 新技能处理

无论获取单个技能还是全部技能，只要远程有新技能而本地没有，都会**自动安装**：
- 📦 远程有、本地没有的技能 → **安装**（自动安装新技能）

这样设计确保用户可以方便地获取任何想要的技能。

## 前置条件

1. 网络连接（访问 GitHub）
2. Python 3.8+
3. 可选: GitHub Token（提高 API 限制）

## 最佳实践

1. **定期获取更新** - 建议每天或每次使用前获取一次
2. **查看变更摘要** - 获取后查看哪些文件被修改
3. **保留本地配置** - 本地特有配置文件不会被覆盖
4. **测试后再使用** - 重要技能更新后先测试再投入使用
5. **备份重要修改** - 如果对官方技能有本地修改，先备份

## 故障排除

### 网络问题

```bash
# 测试 GitHub 连接
curl -I https://raw.githubusercontent.com/leolu66/61sClaw/main/README.md
```

### API 限制

如果频繁遇到 API 限制：
1. 设置 GitHub Token: `export GITHUB_TOKEN=your_token`
2. 或使用本地 Git 克隆方式

### 权限问题

确保对 `skills/` 目录有写权限：
```bash
ls -la skills/
```
