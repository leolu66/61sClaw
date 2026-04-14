---
name: skill-conflict-detector
description: 技能冲突检测与分析工具。触发场景："技能冲突检测"、"分析技能相似度"、"检查技能触发冲突"、"技能分组"、"列出重复功能的技能"。功能：扫描所有技能的描述和触发词，分析功能相似度，检测触发条件冲突，对类似功能的技能进行分组展示，提供冲突解决建议。
---

# Skill Conflict Detector

## Overview
扫描本地所有技能的元数据，自动分析技能功能相似度、检测触发词冲突，对类似功能的技能进行分组，提供冲突解决建议，帮助维护技能库的整洁性和可用性。

## 核心功能

### 1. 触发词冲突检测
- 扫描所有技能SKILL.md的description字段，提取触发关键词
- 检测重复触发词、相似触发词、模糊匹配冲突
- 标记高/中/低风险冲突等级

### 2. 功能相似度分析
- 基于技能描述的语义相似度计算
- 对功能高度重叠的技能进行自动分组
- 分析技能的互补性和替代性

### 3. 冲突报告输出
- 结构化展示冲突详情：冲突技能、冲突类型、风险等级
- 提供优化建议：触发词调整、功能合并、优先级设置
- 生成技能分组清单，便于管理和使用

## 工作流程

1. **扫描技能库**：遍历skills目录下所有子目录，读取每个技能的SKILL.md文件
2. **提取元数据**：解析每个技能的name、description字段，提取功能描述和触发关键词
3. **冲突检测**：
   - 触发词精确匹配检测
   - 触发词语义相似度检测（阈值>0.7标记为高风险）
   - 功能描述相似度检测（阈值>0.6标记为相似功能）
4. **生成报告**：按冲突等级排序输出，附优化建议

## 使用方式

### 直接运行检测
```bash
python scripts/detect_conflicts.py
```

### 常用参数
- `--output report.md`：将检测结果保存到指定文件
- `--threshold 0.7`：自定义相似度阈值（默认0.7）
- `--only-conflicts`：只输出存在冲突的技能，不展示全部

## 输出格式示例

```
## 🔴 高风险冲突（触发词完全重复）

### 冲突组1：AI新闻采集
| 技能名称 | 触发词 | 功能描述 |
|----------|--------|----------|
| ai-news-fetcher | 获取AI新闻、AI动态 | 采集国内AI媒体新闻 |
| ai-news-collector | AI新闻、AI动态 | 多维度全球AI新闻采集 |

💡 优化建议：调整触发词区分功能定位，例如ai-news-fetcher使用「国内AI新闻」，ai-news-collector使用「多维度AI新闻」

## 🟡 中风险冲突（功能高度相似）

### 冲突组2：搜索工具
| 技能名称 | 功能相似度 | 说明 |
|----------|------------|------|
| baidu-search | 0.85 | 百度单引擎搜索 |
| multi-search-engine | 0.72 | 多引擎聚合搜索 |

💡 优化建议：保留两个技能，通过触发词区分使用场景
```

## Resources (optional)

Create only the resource directories this skill actually needs. Delete this section if no resources are required.

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Codex for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Codex's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Codex should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Codex produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Not every skill requires all three types of resources.**

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