# MarkItDown API 参考

## 支持的格式

| 格式 | 说明 | 可选依赖 |
|------|------|----------|
| PDF | PDF 文档（含 OCR） | `[pdf]` |
| DOCX | Word 文档 | `[docx]` |
| PPTX | PowerPoint 演示 | `[pptx]` |
| XLSX | Excel 表格 | `[xlsx]` |
| XLS | 旧版 Excel | `[xls]` |
| HTML | 网页 | 内置 |
| 图片 (JPG/PNG等) | EXIF 元数据 + OCR | 内置 |
| 音频 (WAV/MP3) | 语音转录 | `[audio-transcription]` |
| EPUB | 电子书 | 内置 |
| CSV/JSON/XML | 文本数据格式 | 内置 |
| ZIP | 遍历压缩包内容 | 内置 |
| YouTube URL | 视频字幕提取 | `[youtube-transcription]` |
| Outlook MSG | 邮件消息 | `[outlook]` |

## Python API

### 基本转换

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

### LLM 图片描述

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
result = md.convert("presentation.pptx")
```

### Azure Document Intelligence

```python
md = MarkItDown(docintel_endpoint="<endpoint>")
result = md.convert("scan.pdf")
```

### 启用插件

```python
md = MarkItDown(enable_plugins=True)
result = md.convert("file.pdf")
```

## 命令行

```bash
# 输出到控制台
markitdown file.pdf

# 保存到文件
markitdown file.pdf -o output.md

# 管道输入
cat file.pdf | markitdown

# 查看已安装插件
markitdown --list-plugins

# 启用插件
markitdown --use-plugins file.pdf
```

## 安装可选依赖

```bash
# 全部格式
pip install 'markitdown[all]'

# 按需安装
pip install 'markitdown[pdf,docx,pptx,xlsx]'
pip install 'markitdown[audio-transcription]'
pip install 'markitdown[youtube-transcription]'
```

## 安全注意事项

MarkItDown 以当前进程权限执行 I/O。在不受信任的环境中，应使用最窄的 `convert_*` 函数（如 `convert_stream()` 或 `convert_local()`），并主动清理输入。
