---
name: token-counter
description: |
  计算文本的 Token 数量，支持多种编码器（cl100k_base, p50k_base 等）。
  当用户说"计算 token"、"统计 token"、"token 数量"、"文本有多少 token"时使用此技能。
---

# Token 计算器

使用 tiktoken 库计算文本的 token 数量，支持 OpenAI 模型的各种编码器。

## 需求说明（SRS）

### 触发条件
用户说什么话会触发此技能：
- "计算 token"
- "统计 token"
- "token 数量"
- "这段文字有多少 token"
- "计算一下 token"

### 功能描述
- 计算文本的 token 数量
- 支持多种编码器（cl100k_base, p50k_base, r50k_base 等）
- 支持从文件读取文本
- 支持显示详细的 token 分解

### 输入/输出
- **输入**: 文本字符串或文件路径
- **输出**: Token 数量，可选详细分解

### 依赖条件
- Python 环境
- tiktoken 库 (`pip install tiktoken`)

### 边界情况
- 空文本返回 0
- 文件不存在时返回错误
- 不支持的编码器返回错误

---

## 使用方法

### 基本用法

```bash
# 计算文本 token
python scripts/count_tokens.py -t "Hello World"

# 从文件计算
python scripts/count_tokens.py -f document.txt

# 使用特定编码器
python scripts/count_tokens.py -f document.txt -e cl100k_base

# 显示详细分解
python scripts/count_tokens.py -t "Hello World" --detail

# 从管道输入
echo "Hello World" | python scripts/count_tokens.py --stdin

# 列出所有编码器
python scripts/count_tokens.py --list
```

### 编码器说明

| 编码器 | 适用模型 |
|--------|---------|
| cl100k_base | GPT-4, GPT-3.5-turbo, text-embedding-ada-002 |
| p50k_base | GPT-3 (text-davinci-003/002) |
| p50k_edit | GPT-3 编辑模型 |
| r50k_base | GPT-3 (text-davinci-001) |
| gpt2 | GPT-2 |

---

## 相关文件

- `scripts/count_tokens.py` - 主脚本

---

## 注意事项

- 默认使用 cl100k_base 编码器（GPT-4/3.5 使用）
- 中文字符通常占用 1-2 个 token
- 英文单词通常占用 1 个 token
- 标点符号和空格也占用 token

---

## DoD 检查表

**开发日期**: 2026-04-11
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

### 4. GitHub 同步
- [x] 已提交并推送

**状态**: ✅ 完成
