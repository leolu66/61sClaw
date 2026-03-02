---
name: code-stats
description: |
  统计 skills 目录下所有技能的工作成果，包括技能数量、文件数量、代码行数等，
  同时统计 GitHub 最近7天的提交活跃度。
  当用户说"代码统计"、"工作统计"、"技能统计"时触发。
triggers:
  - "代码统计"
  - "工作统计"
  - "技能统计"
  - "统计技能"
version: 1.0
---

# 代码统计技能

统计 skills 目录下所有技能的工作成果。

## 触发方式

用户说以下指令时触发：
- "代码统计"
- "工作统计"
- "技能统计"
- "统计技能"

## 输出格式

```markdown
# 📊 Skills 工作统计报告

## 总体概况
- 技能数量: XX 个
- 总文件数: XX 个
- 总代码行数: XXX 行
- 总大小: XX MB

## GitHub 提交统计（最近7天）
- 提交次数: XX 次
- 代码增行: +X,XXX
- 代码删行: -X,XXX
- 净变化: +X,XXX
- 活跃天数: X 天

## 文件类型分布
| 类型 | 文件数 | 代码行数 |
|------|--------|---------|
| Python (.py) | XX | X,XXX |
| JavaScript (.js) | XX | X,XXX |
| Markdown (.md) | XX | - |
| 其他 | XX | - |

## Top 5 技能（按代码行数）
| 排名 | 技能名称 | 代码行数 |
|------|---------|---------|
| 1 | xxx | X,XXX |
| 2 | xxx | X,XXX |
| 3 | xxx | X,XXX |
| 4 | xxx | X,XXX |
| 5 | xxx | X,XXX |
```

## 统计规则

1. **技能数量**: 包含 SKILL.md 的目录数量
2. **文件数量**: 所有文件（不含 node_modules、data、__pycache__）
3. **代码行数**: 仅统计 .py, .js 文件的有效代码行数（排除空行和注释）
4. **大小统计**: 所有文件的总大小
5. **GitHub 统计**: 自动从 vault 读取 GitHub Token，获取最近7天的提交数据

## 依赖

- GitHub Token: 自动从 `vault` 技能读取（credentials.json）
