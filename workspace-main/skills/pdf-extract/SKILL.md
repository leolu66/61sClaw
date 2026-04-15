---
name: pdf-extract
description: |
  提取 PDF 文件文本内容。
  
  触发命令：
  - 提取 PDF 内容
  - 读取 PDF
  - PDF 转文本
  
  使用 Python pdfplumber 库，纯本地处理，无需外部服务。
metadata:
  {
    "openclaw":
      {
        "emoji": "📄",
        "requires": { "python": ["pdfplumber"] },
      },
  }
---

# PDF Extract

提取 PDF 文件文本内容，支持整文档或指定页面范围。

## 特点

- ✅ 纯本地处理，无需联网
- ✅ 无大模型依赖
- ✅ 支持中文 PDF
- ✅ 保持文本排版

## 使用方法

### 命令行

```bash
# 提取整个 PDF
python scripts/extract.py "document.pdf"

# 提取指定页面
python scripts/extract.py "document.pdf" --pages 1-5
python scripts/extract.py "document.pdf" --pages 1,3,5
```

### 在技能中调用

```python
import subprocess
result = subprocess.run(
    ['python', 'scripts/extract.py', 'document.pdf'],
    capture_output=True, text=True
)
text = result.stdout
```

## 依赖安装

```bash
pip install pdfplumber
```

## 输出格式

提取的文本保持原始排版，适合直接输入 LLM 处理。
