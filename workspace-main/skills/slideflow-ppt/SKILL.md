---
name: slideflow-ppt
description: |
  AI PPT 自动化生成引擎。基于 SlideFlow 项目，通过 LangGraph 编排 + MCP 协议 + RAG 知识增强，
  从模糊创意或复杂文档生成专业可编辑的 PPTX 演示文稿。
  
  触发场景：
  - 用户请求生成 PPT / 演示文稿 / 幻灯片
  - 用户需要将文档、想法或研究报告转化为 PPT
  - 用户要求 AI 自动制作演讲幻灯片
  - 涉及"帮我做个 PPT"、"生成演示文稿"、"做幻灯片"等需求
  - HTML 演示文稿转 PPTX 格式
---

# SlideFlow PPT 生成引擎

基于 [SlideFlow](https://github.com/xiaoyesoso/SlideFlow)（MIT 协议）的 AI PPT 生成技能。

## 需求说明（SRS）

### 触发条件
- "帮我做个 PPT / 演示文稿 / 幻灯片"
- "基于这个主题生成 PPT"
- "把这份文档变成 PPT"
- "生成关于 XX 的演示文稿"
- "SlideFlow 生成 PPT"
- "转化 html 为 ppt 格式"

### 功能描述

**功能 A：AI 自动生成 PPT（start_ppt.py）**

通过 SlideFlow 的 LangGraph 状态机编排，从主题自动生成完整演示文稿：
1. 联网搜索 — 自动搜索主题的互联网实时信息
2. 大纲生成 — AI 生成结构化 JSON 大纲（封面/目录/章节/内容/结束）
3. 内容扩写 — 每章自动扩写 2-3 页详细内容（并行处理）
4. HTML 渲染 — Jinja2 模板 + Tailwind CSS 生成美观幻灯片
5. PDF 合成 — Playwright 渲染为高保真 PDF
6. PPTX 转换 — 像素级 DOM 捕获 + python-pptx 矢量重建

可选：RAG 知识增强（上传 PDF）、自动搜索高清背景图。

**功能 B：HTML 多页演示文稿转 PPTX（html_deck_to_pptx.py）**

将已有 HTML 演示文稿转换为可编辑 PPTX，支持 3 种多页格式自动检测：

| 格式 | 检测特征 | 翻页机制 | 来源技能 |
|------|----------|----------|----------|
| **huashu-design** | `#deck > .slide-page` | `display:block/none` 切换 | huashu-design |
| **html-ppt-skill** | `.deck > section.slide` | `.is-active` 类 (opacity) | html-ppt-skill |
| **guizang-ppt** | `#deck > .slide` | `translateX` 偏移 | guizang-ppt |

转换原理：Playwright 渲染 → 逐页截图背景 → DOM 提取文本坐标/样式 → python-pptx 矢量重建（文字可编辑）。外部 CSS 路径无法解析时自动注入关键布局规则。

### 输入/输出
- **输入 AI 生成**: `topic`（必填）, `language`（zh/en）, `template`（company_report 等）, `pdf_paths`（可选）
- **输入 HTML 转换**: HTML 文件所在目录路径
- **输出**: `*.pptx`（可编辑 PowerPoint）, `*.pdf`（高保真 PDF）

### 依赖条件
- Python 3.10+
- Playwright Chromium 浏览器引擎
- OpenAI 兼容 LLM API（AI 生成模式需要）
- DuckDuckGo 搜索（内置，无需 API Key）
- **项目路径**: `repos/SlideFlow/`（已克隆）

### 边界情况
- AI 生成支持 stop_event 随时停止
- 每章节最多重试 2 次大纲生成
- 网络搜索失败时降级为纯 LLM 生成
- HTML 转换自动检测格式，未匹配则单页处理
- 外部 CSS 路径自动注入 fallback 规则
- 字体映射：Google Fonts → 系统字体（微软雅黑/SimSun/Georgia）

---

## 架构概览

```
四层架构：
┌──────────────────────────────────────┐
│  交互层                              │
│  Web Dashboard / MCP Agent / CLI     │
├──────────────────────────────────────┤
│  接口层                              │
│  FastMCP Server / Flask REST API     │
├──────────────────────────────────────┤
│  编排层 - LangGraph StateGraph       │
│  搜索大纲 → 内容扩写(并行) → HTML生  │
│  成(并行) → PDF合成 → PPTX转换       │
├──────────────────────────────────────┤
│  基础设施层                          │
│  DuckDuckGo/Serper/Milvus/Playwright │
│  python-pptx / Pillow / pymupdf      │
└──────────────────────────────────────┘
```

## 使用方法

### 方法 1：Web 交互模式（推荐）

启动 Dashboard，浏览器中可视化操作：

```bash
python scripts/start_web.py           # 默认端口 5001
python scripts/start_web.py -p 8080   # 自定义端口
```

访问 `http://localhost:5001`，输入主题即可。

### 方法 2：命令行一键生成 PPT

```bash
# 基础用法
python scripts/start_ppt.py --topic "人工智能在医疗领域的应用"
python scripts/start_ppt.py --topic "AI in Healthcare" --language en

# 指定模型
python scripts/start_ppt.py --topic "量子计算" --model "deepseek-chat" ^
    --base-url "https://api.deepseek.com/v1" --api-key "sk-xxx"

# RAG 增强 + 特定模板
python scripts/start_ppt.py --topic "..." --pdf "doc1.pdf" "doc2.pdf" ^
    --template company_report --no-search
```

### 方法 3：HTML 多页演示文稿转 PPTX

```bash
# 自动检测格式，一键转换
python scripts/html_deck_to_pptx.py <html文件所在目录> [output.pptx]

# 示例：三种格式都能自动处理
python scripts/html_deck_to_pptx.py "E:\ppt\huashu-design"
python scripts/html_deck_to_pptx.py "E:\ppt\html-ppt" "result.pptx"
python scripts/html_deck_to_pptx.py "E:\ppt\guizang-ppt"
```

### 方法 4：MCP Agent 模式

```json
{
  "mcpServers": {
    "slideflow": {
      "command": "python",
      "args": ["<workspace>/repos/SlideFlow/mcp_server.py"]
    }
  }
}
```

---

## 脚本说明

| 脚本 | 功能 | 用法 |
|------|------|------|
| `scripts/start_web.py` | 启动 Web Dashboard | `python scripts/start_web.py [-p PORT]` |
| `scripts/start_ppt.py` | 命令行 AI 生成 PPT | `python scripts/start_ppt.py --topic "主题" [--model M]` |
| `scripts/html_deck_to_pptx.py` | HTML 多页转 PPTX | `python scripts/html_deck_to_pptx.py <目录> [输出]` |
| `scripts/start_mcp.py` | 启动 MCP Server | `python scripts/start_mcp.py` |
| `scripts/setup_whalecloud.py` | 从 OpenClaw 配置提取 WhaleCloud Key | `python scripts/setup_whalecloud.py` |
| `scripts/config.json` | 技能配置文件 | 模型/端口/模板默认值 |

---

## HTML 转换格式适配详情

### huashu-design
- 结构: `<section class="slide-page">` 内嵌 `<div class="slide">`
- CSS: 全部内联 `<style>`，无需外部文件
- 导航: JS 用 `style.display` 切换
- 提取: 遍历 `#deck > .slide-page`，找 `display !== 'none'` 的当前页

### html-ppt-skill
- 结构: `<section class="slide">` 在 `.deck` 内
- CSS: 外部 `assets/base.css` 等（需复制到同目录）
- 导航: `.is-active` 类 + `opacity/pointer-events`
- 注入: 自动注入关键 `.deck/.slide` CSS 规则

### guizang-ppt
- 结构: `<div class="slide">` 在 `#deck` 内
- CSS: 内联 + Google Fonts
- 导航: `deck.style.transform = translateX(-N*100vw)`
- 特性: WebGL 双背景、Hero 页、ESC 索引视图

---

## 模型配置

SlideFlow 支持任何 **OpenAI 兼容 API** 的模型。

**方式 1：命令行参数**

```bash
python scripts/start_ppt.py --topic "主题" ^
  --model "deepseek-chat" ^
  --base-url "https://api.deepseek.com/v1" ^
  --api-key "sk-your-key"
```

**方式 2：编辑 repos/SlideFlow/config/config.json**

```json
{
  "api_key": "sk-xxxx",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o",
  "emb_api_key": "sk-xxxx",
  "emb_base_url": "https://api.openai.com/v1",
  "embedding_model": "text-embedding-3-small"
}
```

### 支持的模型提供商

| 提供商 | base_url | model 示例 |
|--------|----------|-----------|
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o`, `gpt-4-turbo` |
| **DeepSeek** | `https://api.deepseek.com/v1` | `deepseek-chat` |
| **智谱 GLM** | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-plus` |
| **Moonshot** | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| **通义千问** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| **WhaleCloud** | `https://lab.iwhalecloud.com/gpt-proxy/v1` | `deepseek-v4-pro` |

### 优先级

```
命令行参数 > skills/.../config.json > 环境变量 > SlideFlow config.json
```

### 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `OPENAI_API_KEY` | LLM API Key | 推荐 |
| `OPENAI_BASE_URL` | LLM API 地址 | 否 |
| `SERPER_API_KEY` | Serper 图片搜索 API Key | 否 |

---

## 注意事项

- **首次使用**: `pip install -r repos/SlideFlow/requirements.txt && playwright install chromium`
- 建议使用 **Claude 3.5 Sonnet** 或 **GPT-4o** 作为底层模型
- AI 生成输出在 `repos/SlideFlow/output/<task_id>/`
- HTML 转换输出默认在源目录 `output.pptx`
- WhaleCloud DeepSeek V4 Pro 已预配置（通过 `setup_whalecloud.py`）
- **html-ppt-skill 格式需确保 CSS 文件在 HTML 同目录的 `assets/` 下**

---

## DoD 检查表

**开发日期**: 2026-05-14
**开发者**: 小天才

### 开发前检查
- [x] 已查看现有技能列表，确认无重复功能
- [x] 已阅读相关技能 SKILL.md，了解可复用组件
- [x] 已决定是扩展还是新建（新建独立技能）

### 开发检查
- [x] SRS 文档完整（触发条件、功能、输入输出、依赖、边界）
- [x] 技能文件结构规范
- [x] 代码使用相对路径
- [x] 配置外置，敏感信息通过环境变量
- [x] 功能测试通过：
  - AI 生成 PPT: 已验证导入和配置文件
  - HTML 转 PPTX (huashu-design): 10 页 ✅
  - HTML 转 PPTX (html-ppt-skill): 12 页 ✅
  - HTML 转 PPTX (guizang-ppt): 12 页 ✅
- [x] 触发测试通过
- [x] 无 .skill 文件
- [x] 无隐私文件
- [x] 已提交并推送到 GitHub
- [x] SKILL.md 包含使用示例

**状态**: ✅ 完成
