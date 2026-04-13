---
name: foreign-skill-cleaner
description: 批量移除不适合国内使用的国外技能。当用户说"清理国外技能"、"移除不需要的技能"、"清理技能列表"时触发。支持配置自定义清理列表，未来可扩充。
---

# Foreign Skill Cleaner 国外技能清理工具

## Overview

批量清理OpenClaw技能目录中不适合国内使用的国外相关技能，支持自定义清理列表，模拟运行，动态添加新技能到清理清单等功能。

## 触发场景

当用户输入以下指令时触发本技能：
- "清理国外技能"
- "移除不需要的技能"
- "清理技能列表"
- "删除国外相关技能"

## 核心功能

### 1. 批量清理技能
```bash
# 执行清理
python scripts/clean_skills.py

# 模拟运行（不实际删除）
python scripts/clean_skills.py --dry-run
```

### 2. 查看待清理列表
```bash
python scripts/clean_skills.py --list
```

### 3. 添加新技能到清理列表
```bash
python scripts/clean_skills.py --add "skill-name"
```

### 4. 指定自定义配置文件
```bash
python scripts/clean_skills.py --config /path/to/custom/config.json
```

## 配置说明

配置文件 `config.json` 字段说明：
```json
{
  "skills_to_remove": [
    // 需要清理的技能名称列表
    "summarize",
    "1password",
    "apple-notes",
    // ... 更多技能
  ],
  "skills_root": "C:/Users/luzhe/.openclaw/workspace-main/skills", // 技能根目录
  "dry_run": false // 是否为模拟模式
}
```

## 使用流程

1. **默认清理**：直接运行脚本，将自动清理配置文件中列出的所有技能
2. **模拟验证**：首次使用建议先加 `--dry-run` 参数确认要删除的技能是否正确
3. **自定义列表**：编辑 `config.json` 添加或移除需要清理的技能
4. **重启网关**：清理完成后重启OpenClaw网关，技能列表会自动更新

## 安全特性

- ✅ 模拟运行模式，避免误删
- ✅ 自动跳过不存在的技能，不会报错
- ✅ 操作结果清晰统计，成功/失败数量一目了然
- ✅ 配置文件外置，方便扩充清理列表

## 资源说明

### scripts/
- `clean_skills.py`：主执行脚本，实现所有清理功能

### references/
- 暂无参考文档

## 开发规范参考

文件路径规范（重要）：**

#### 原则 1：技能自包含

**所有技能默认只能在自己的工作空间内读写文件**。

```python
# ✅ 正确：使用相对路径，保存在技能目录内
output_dir = Path(__file__).parent / "output"

# ❌ 错误：使用绝对路径或硬编码路径
output_dir = "D:\\projects\\workspace\\output"
output_dir = "C:\\Users\\xxx\\Documents"
```

**要求**：
- 使用相对路径（相对于技能目录）
- 默认输出到技能自己的工作空间
- 确保技能分享后仍可用

#### 原则 2：外部协作需配置

**如果技能需要在工作空间外读写文件（如多智能体共享目录），必须通过配置文件设置路径**。

```python
# ✅ 正确：从配置文件读取路径
import json
config = json.load(open("config.json"))
shared_dir = config.get("shared_output_dir")

# ❌ 错误：硬编码共享路径
shared_dir = "D:\\projects\\workspace\\shared\\output"
```

**要求**：
- 不硬编码外部路径
- 通过配置文件或环境变量传入
- 配置项名称清晰（如 `shared_dir`, `output_path`）

#### 示例配置

```json
{
  "output_dir": "./output",
  "shared_dir": "D:\\projects\\workspace\\shared\\output"
}
```

**为什么需要这个规范**：
1. **可移植性** - 技能分享后，其他用户可以直接使用
2. **安全性** - 避免意外写入系统目录
3. **协作性** - 明确哪些路径是配置的，哪些是固定的
