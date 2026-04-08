---
name: docx-to-markdown
description: |
  将 Word 文档（DOCX）转换为 Markdown 格式。
  
  触发命令：
  - Word 转 Markdown
  - DOCX 转 MD
  - 转换 Word 文件
  - 批量转换 Word
  
  支持单文件转换和批量转换整个目录。
metadata:
  openclaw:
    emoji: "📝"
    requires:
      python: ["python-docx"]
---

# DOCX to Markdown 转换器

将 Microsoft Word 文档（.docx）转换为 Markdown 格式，支持单文件和批量转换。

## 需求说明（SRS）

### 触发条件
- "Word 转 Markdown"
- "DOCX 转 MD"
- "转换 Word 文件"
- "批量转换 Word"
- "把 Word 转成 Markdown"

### 功能描述
将 Word 文档转换为 Markdown 格式，保留文档结构（标题、列表、表格等），支持单文件转换和批量转换整个目录。

### 输入/输出
- **输入**: 
  - 单文件：DOCX 文件路径
  - 批量：目录路径（可选递归）
- **输出**: 
  - 单文件：同名的 .md 文件
  - 批量：目录下所有 .docx 文件对应的 .md 文件

### 依赖条件
- Python 3.6+
- python-docx 库：`pip install python-docx`

### 边界情况
- 文件不存在时提示错误
- 非 .docx 文件跳过
- 输出文件已存在时覆盖（带提示）
- 空文档生成空 Markdown 文件

---

## 使用方法

### 单文件转换

```bash
# 基本用法
python scripts/convert.py "document.docx"

# 指定输出路径
python scripts/convert.py "document.docx" -o "output.md"
```

### 批量转换

```bash
# 转换目录下所有 docx 文件
python scripts/convert.py "C:\Documents" --batch

# 递归转换子目录
python scripts/convert.py "C:\Documents" --batch --recursive

# 指定输出目录
python scripts/convert.py "C:\Documents" --batch -O "C:\Output"
```

### Python 调用

```python
from scripts.convert import convert_file, convert_directory

# 单文件
convert_file("document.docx", "output.md")

# 批量转换
convert_directory("C:\\Documents", recursive=True)
```

---

## 转换规则

| Word 元素 | Markdown 输出 |
|-----------|--------------|
| 标题 1 | `# 标题` |
| 标题 2 | `## 标题` |
| 标题 3 | `### 标题` |
| 标题 4+ | `#### 标题` |
| 无序列表 | `- 项目` |
| 有序列表 | `1. 项目` |
| 表格 | Markdown 表格格式 |
| 粗体 | `**文本**` |
| 斜体 | `*文本*` |
| 普通段落 | 直接输出 |

---

## 相关文件

- `scripts/convert.py` - 主转换脚本

---

## 注意事项

- 暂不支持图片提取（后续版本计划）
- 复杂格式（如文本框、形状）可能丢失
- 建议转换后人工检查表格格式

---

## DoD 检查表

**开发日期**: 2026-04-08
**开发者**: 小天才

### 1. SRS 文档
- [x] 触发条件明确
- [x] 功能描述完整
- [x] 输入输出说明
- [x] 依赖条件列出
- [x] 边界情况处理

### 2. 技能文件和代码
- [x] 目录结构规范
- [x] 使用相对路径
- [x] 无 .skill 文件

### 3. 测试通过
- [x] 功能测试通过
- [x] 触发测试通过
- [x] 批量转换测试

### 4. GitHub 同步
- [x] 已提交并推送
- [x] 无隐私文件泄露

**状态**: ✅ 完成
