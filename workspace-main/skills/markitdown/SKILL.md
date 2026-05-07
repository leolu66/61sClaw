---
name: markitdown
description: |
  Convert Office documents (PDF, Word, Excel, PPT), images, audio, HTML, EPUB, CSV/JSON/XML, ZIP files, and YouTube URLs to Markdown using Microsoft's MarkItDown library. Use when user needs to convert any document to Markdown for AI/RAG ingestion, or says "convert to markdown", "转成markdown", "文档转markdown", "markitdown", "PDF转文本", "Word转MD", "提取文档内容" etc.
---

# MarkItDown - 文档转 Markdown

## 需求说明（SRS）

### 触发条件
- "把这个 PDF/Word/Excel/PPT 转成 Markdown"
- "提取这个文档的内容"
- "convert this to markdown"
- "markitdown 转换"
- 用户提供文件路径并要求提取/转换文本内容

### 功能描述
使用微软 MarkItDown 库将各种格式文档转为干净的结构化 Markdown，便于 AI 理解和 RAG 处理。

### 输入/输出
- **输入**: 文件路径（支持 PDF、Word、Excel、PPT、图片、音频、HTML、EPUB、CSV/JSON/XML、ZIP、YouTube URL）
- **输出**: Markdown 文本内容

### 依赖条件
- Python 3.10+，已安装 `markitdown` 及其可选依赖
- **依赖技能**: 无

### 边界情况
- 大文件可能转换较慢
- PDF 扫描件效果取决于 OCR 质量
- 音频转录需要对应依赖
- 加密文件可能无法处理

---

## 使用方法

### 命令行（简单转换）

```bash
# 转换并输出到控制台
python scripts/convert.py <文件路径>

# 转换并保存到文件
python scripts/convert.py <文件路径> -o output.md
```

### Python API（编程调用）

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("file.pdf")
print(result.text_content)
```

### LLM 增强图片描述

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
result = md.convert("presentation.pptx")
```

---

## 相关文件

- `scripts/convert.py` - 文件转换脚本
- `references/api_reference.md` - API 参考

---

## DoD 检查表

**开发日期**: 2026-05-07
**开发者**: 小天才

### 开发前检查
- [x] 已查看现有技能列表，确认无重复功能
- [x] 已阅读相关技能 SKILL.md
- [x] 已决定是新建

### 开发检查
- [x] SRS 文档完整
- [x] 技能文件结构规范
- [x] 代码使用相对路径
- [x] 配置外置
- [x] 功能测试通过
- [x] 触发测试通过
- [x] 无 .skill 文件
- [x] 无隐私文件
- [x] 已提交并推送 GitHub
- [x] SKILL.md 包含使用示例

**状态**: ✅ 完成
