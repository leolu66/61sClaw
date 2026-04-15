---
name: github-compliance-checker
description: 检查 GitHub 仓库上传合规性，确保隐私文件和敏感信息不会被上传到 GitHub。支持自动修复和用户确认两种模式。当用户说"检查 GitHub 合规性"、"审核 GitHub"、"检查 github"、"github 合规检查"时触发。如果用户说"检查并自动修正"则直接修复，否则需要用户确认。
---

# GitHub 合规检查器

## 概述

检查 GitHub 仓库上传合规性，防止隐私文件、敏感信息、日志文件等被意外上传到 GitHub。

**多工作空间支持**：当前 GitHub 根目录为 `~/.openclaw`，包含多个工作空间：
- `workspace-main` - 主工作空间
- `workspace-entertainment` - 娱乐工作空间
- `workspace-validator` - 验证工作空间

检查器会自动识别所有工作空间中的合规问题。

## 核心功能

### 1. 合规检查规则

#### 🔒 隐私保护规则（禁止上传）

| 类别 | 文件/目录 | 风险等级 |
|------|----------|---------|
| 个人记忆 | `MEMORY.md` | 🔴 高 |
| 用户配置 | `USER.md`, `SOUL.md`, `AGENTS.md`, `IDENTITY.md`, `HEARTBEAT.md`, `BOOTSTRAP.md` | 🔴 高 |
| 工作日志 | `logs/` | 🔴 高 |
| 本地工具 | `TOOLS.md` | 🟡 中 |
| 历史记忆 | `memory/` | 🔴 高 |
| 用户数据 | `datas/`, `data/`, `agfiles/` | 🔴 高 |
| 技能数据 | `skills/*/data/` | 🟡 中 |

#### 🚨 目录结构规则（告警）

| 类别 | 规则 | 风险等级 |
|------|------|---------|
| 非允许目录/文件新增 | 不在白名单内的目录或文件 | 🔴 高 |

**说明**：
- **仅允许以下内容同步到GitHub**（在每个工作空间内）：
  1. `skills/` 目录（所有技能文件）
  2. `scripts/` 目录（公共脚本）
  3. `.gitignore` 文件（忽略规则配置）
- 工作空间外的内容或不在白名单内的内容都将触发告警
- 如需新增其他内容，需用户确认后加入白名单

**支持的工作空间**：
- `workspace-main`
- `workspace-entertainment`
- `workspace-validator`
- `workspace-feishu-agent`
- `workspace-test-agent`

**确认机制**：
- 告警后用户可选择：
  1. ✅ 允许同步：将该项目加入白名单，后续不再告警
  2. ❌ 禁止同步：自动添加到.gitignore，并从GitHub远程仓库删除
- 已确认项目记录在技能数据目录下的 `.compliance_approvals.json`
- 下次检查将自动忽略已确认项目

**确认命令**：
```bash
# 确认允许某个项目同步到GitHub（加入白名单）
python scripts/compliance_checker.py allow <path> [原因]

# 确认禁止某个项目同步（添加到.gitignore并从GitHub删除）
python scripts/compliance_checker.py deny <path>

# 示例
python scripts/compliance_checker.py allow "workspace-main/.github/" "GitHub工作流配置，需要同步"
python scripts/compliance_checker.py deny "workspace-main/test/" "测试目录，不需要同步"

# 列出已确认的项目
python scripts/compliance_checker.py list-approvals

# 撤销确认
python scripts/compliance_checker.py revoke "workspace-main/test/"
```

#### ⚙️ 技术规范规则（禁止上传）

| 类别 | 文件/目录 | 风险等级 |
|------|----------|---------|
| Python 缓存 | `__pycache__/`, `*.pyc`, `*.pyo` | 🟢 低 |
| IDE 配置 | `.vscode/`, `.idea/`, `*.swp` | 🟢 低 |
| 临时文件 | `tmp/`, `temp/`, `*.tmp` | 🟢 低 |
| 系统文件 | `.DS_Store`, `Thumbs.db` | 🟢 低 |
| 调试文件 | `debug*.py`, `test*.py` | 🟡 中 |

### 2. 使用方式

#### 检查并自动修正（无需确认）

```
检查 GitHub 并自动修正
检查 github 并自动修复
审核 GitHub 并自动修复
```

#### 检查并报告（需要用户确认）

```
检查 GitHub 合规性
审核 GitHub
检查 github
github 合规检查
```

## 工作流程

### 自动修正模式

```
用户: 检查 GitHub 并自动修正
  │
  ▼
扫描 Git 暂存区文件
  │
  ▼
发现不合规文件 ──▶ 从暂存区移除
  │
  ▼
更新 .gitignore（如有遗漏）
  │
  ▼
报告修复结果
```

### 用户确认模式

```
用户: 检查 GitHub 合规性
  │
  ▼
扫描 Git 暂存区文件
  │
  ▼
发现不合规文件
  │
  ▼
报告问题清单 ──▶ 用户确认
  │
  ▼
用户确认后 ──▶ 执行修复
  │
  ▼
报告修复结果
```

## 脚本资源

### scripts/compliance_checker.py

核心检查器，提供：
- `ComplianceChecker` - 合规检查类
- `check_staged_files()` - 检查暂存区文件
- `check_all_files()` - 检查所有文件
- `auto_fix()` - 自动修复
- `generate_report()` - 生成报告

### scripts/fix_gitignore.py

.gitignore 管理工具：
- 检查 .gitignore 完整性
- 补充缺失的规则
- 备份原文件

## 输出格式

### 检查结果报告

```markdown
## GitHub 合规检查报告

**检查时间**: 2026-04-15 17:30:00
**检查模式**: 自动修正 / 仅检查

### 发现的问题 (5 个)

#### 🔴 高风险 (3 个)
| 文件路径 | 问题类型 | 风险 | 状态 |
|---------|---------|------|------|
| workspace-main/memory/2026-04-15.md | 历史记忆文件 | 🔴 高 | 已移除 |
| workspace-main/logs/daily/2026-04-15.md | 工作日志 | 🔴 高 | 已移除 |
| workspace-validator/SOUL.md | 用户配置文件 | 🔴 高 | 已移除 |

#### 🟡 中风险 (1 个)
| 文件路径 | 问题类型 | 风险 | 状态 |
|---------|---------|------|------|
| workspace-main/skills/test-skill/data/config.json | 技能数据 | 🟡 中 | 已移除 |

#### 🟢 低风险 (2 个)
| 文件路径 | 问题类型 | 风险 | 状态 |
|---------|---------|------|------|
| workspace-main/__pycache__/utils.cpython-311.pyc | Python 缓存 | 🟢 低 | 已移除 |
| workspace-main/.vscode/settings.json | IDE 配置 | 🟢 低 | 已移除 |

### 修复操作

- 从 Git 暂存区移除: 5 个文件
- 更新 .gitignore: 补充 1 条规则
- 备份原文件: 是

### 建议

✅ 所有不合规文件已处理，可以安全提交。
```

### 需要确认的报告

```markdown
## GitHub 合规检查报告

**检查时间**: 2026-04-15 17:30:00

### ⚠️ 发现不合规文件 (5 个)

#### 🔴 高风险 - 需要立即处理
- `workspace-main/memory/2026-04-15.md` - 历史记忆文件
- `workspace-main/logs/daily/2026-04-15.md` - 工作日志文件
- `workspace-validator/SOUL.md` - 用户配置文件

#### 🟡 中风险 - 建议处理
- `workspace-main/skills/test-skill/data/config.json` - 技能运行时数据

#### 🟢 低风险 - 可选处理
- `workspace-main/__pycache__/utils.cpython-311.pyc` - Python 缓存文件
- `workspace-main/.vscode/settings.json` - IDE 配置文件

### 建议操作

1. **从 Git 暂存区移除这些文件**
2. **更新 .gitignore** 防止再次提交

### 确认执行

对于发现的非白名单内容，请选择操作：
- 回复 "允许 [路径]" ：允许该内容同步到GitHub，加入白名单不再告警
- 回复 "禁止 [路径]" ：禁止该内容同步，自动添加到.gitignore并从GitHub删除
- 回复 "全部禁止" ：禁止所有发现的不合规内容
- 回复 "取消" ：不做任何处理
```

## 前置条件

1. Git 仓库已初始化（根目录为 `~/.openclaw`）
2. 有执行 `git rm --cached` 的权限
3. .gitignore 文件存在（如果不存在会自动创建）
4. 支持多工作空间结构（workspace-main, workspace-entertainment 等）

## 最佳实践

1. **提交前检查** - 每次 `git add` 后执行检查
2. **定期审查** - 每周检查一次 .gitignore 完整性
3. **及时修复** - 发现问题立即修复，不要拖延
4. **备份重要** - 修复前自动备份，防止误删

## 故障排除

### 无法移除文件

```bash
# 如果文件已提交到历史记录
git rm --cached <file>
git commit -m "移除敏感文件"
```

### .gitignore 不生效

```bash
# 清除缓存后重新添加
git rm -r --cached .
git add .
git commit -m "更新 .gitignore"
```
