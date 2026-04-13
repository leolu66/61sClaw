---
name: smart-web-fetcher
description: "智能网页内容获取工具，自动适配不同类型网页。普通静态网页使用内置web_fetch工具快速提取内容，反爬/动态加载/需要交互的复杂网页自动使用playwright模拟浏览器操作获取完整内容。触发场景：获取网页内容、抓取网页信息、网页内容提取、爬取网页数据。"
---

# Smart Web Fetcher

## Overview
智能网页内容抓取工具，自动选择最优抓取策略：
- 普通静态网页：使用内置web_fetch工具，快速高效提取markdown格式内容
- 复杂场景（反爬限制/动态渲染/需要登录/需要交互）：自动切换到playwright模拟浏览器操作，绕过限制获取完整内容

## 核心功能
1. 自动识别网页类型，选择最优抓取方案
2. 支持自定义User-Agent、请求头等参数
3. 支持模拟点击、滚动、输入等交互操作
4. 支持提取纯文本、markdown、HTML等多种格式内容
5. 自动处理反爬验证、Cookie管理

## 快速使用

### 基础调用
```bash
python scripts/fetch_web_content.py <网页URL>
```

### 高级参数
```bash
# 强制使用playwright模式抓取
python scripts/fetch_web_content.py <网页URL> --mode playwright

# 指定输出格式（markdown/text/html）
python scripts/fetch_web_content.py <网页URL> --format markdown

# 保存结果到文件
python scripts/fetch_web_content.py <网页URL> -o output.md

# 等待页面加载完成时间（秒）
python scripts/fetch_web_content.py <网页URL> --wait 3
```

### 特殊场景处理
- 需要登录的网页：先手动登录获取Cookie，通过`--cookie`参数传入
- 需要点击按钮/接受弹窗的页面：通过`--click-selector`参数指定要点击的元素选择器
- 需要滚动加载的页面：通过`--scroll`参数自动滚动到底部加载全部内容

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Works well when there are clear step-by-step procedures
- Example: DOCX skill with "Workflow Decision Tree" -> "Reading" -> "Creating" -> "Editing"
- Structure: ## Overview -> ## Workflow Decision Tree -> ## Step 1 -> ## Step 2...

**2. Task-Based** (best for tool collections)
- Works well when the skill offers different operations/capabilities
- Example: PDF skill with "Quick Start" -> "Merge PDFs" -> "Split PDFs" -> "Extract Text"
- Structure: ## Overview -> ## Quick Start -> ## Task Category 1 -> ## Task Category 2...

**3. Reference/Guidelines** (best for standards or specifications)
- Works well for brand guidelines, coding standards, or requirements
- Example: Brand styling with "Brand Guidelines" -> "Colors" -> "Typography" -> "Features"
- Structure: ## Overview -> ## Guidelines -> ## Specifications -> ## Usage...

**4. Capabilities-Based** (best for integrated systems)
- Works well when the skill provides multiple interrelated features
- Example: Product Management with "Core Capabilities" -> numbered capability list
- Structure: ## Overview -> ## Core Capabilities -> ### 1. Feature -> ### 2. Feature...

Patterns can be mixed and matched as needed. Most skills combine patterns (e.g., start with task-based, add workflow for complex operations).

Delete this entire "Structuring This Skill" section when done - it's just guidance.]

## [TODO: Replace with the first main section based on chosen structure]

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

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