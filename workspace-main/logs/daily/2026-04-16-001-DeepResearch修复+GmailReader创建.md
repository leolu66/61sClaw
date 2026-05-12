# 工作日志 #001

## 基本信息

| 项目 | 内容 |
|------|------|
| 日志编号 | #001 |
| 日期 | 2026-04-16 |
| 开始时间 | 22:00 |
| 结束时间 | 00:00 |
| 会话时长 | 2小时 |

## 工作内容概述

本次会话主要完成了 Deep Research 技能的修复工作（百度搜索和 Brave Search 代理问题），并创建了一个全新的 Gmail Reader 技能用于读取邮件。

## 完成的任务

### 任务1：修复 Deep Research 技能 - 百度搜索问题

**描述**：百度搜索功能在 Windows 环境下存在多个问题，导致搜索结果无法正常获取。

**问题诊断与修复**：

1. **JSON 参数传递问题**
   - **现象**：通过 shell 传递 JSON 参数时因引号转义失败
   - **原因**：Windows PowerShell 对引号和特殊字符的转义规则复杂，JSON 中的引号容易被错误解析
   - **解决方案**：改用临时文件传递 JSON 参数，避免 shell 转义问题
   - **实现**：Python 脚本读取临时文件中的 JSON 参数，而不是从命令行参数获取

2. **JSON 解析问题**
   - **现象**：原代码只取第一行解析，但 JSON 格式化结果跨多行
   - **原因**：百度搜索返回的 JSON 结果经过格式化后包含换行，单行截取导致解析失败
   - **解决方案**：使用正则匹配提取完整 JSON 数组/对象
   - **实现**：`re.search(r'\[.*\]', text, re.DOTALL)` 匹配完整的 JSON 数组

3. **编码问题**
   - **现象**：Windows 控制台默认 GBK 编码，无法输出 Unicode 字符
   - **原因**：Windows 中文系统默认使用 GBK 编码，而 Python 脚本输出 UTF-8 字符
   - **解决方案**：Python 脚本强制 UTF-8 编码输出
   - **实现**：
     ```python
     import sys
     import io
     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
     sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
     ```

**修改文件**：`skills/baidu-search-1.1.2/scripts/search.py`

### 任务2：修复 Deep Research 技能 - Brave Search 代理问题

**描述**：Node.js 的 fetch API 默认不走系统代理，导致在需要代理的网络环境下无法访问 Brave Search API。

**问题诊断与修复**：

1. **代理不生效问题**
   - **现象**：系统已配置代理，但 Node.js fetch 请求不走代理
   - **原因**：Node.js 原生 fetch 不读取系统代理设置，需要显式配置
   - **解决方案**：使用 undici 库的 ProxyAgent 支持 HTTP/HTTPS 代理
   - **实现**：
     ```typescript
     import { ProxyAgent } from 'undici';
     const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY;
     const dispatcher = proxyUrl ? new ProxyAgent(proxyUrl) : undefined;
     const response = await fetch(url, { dispatcher } as any);
     ```

2. **代理端口自动检测**
   - **优化**：添加自动检测 Clash 代理端口（7890/7897）功能
   - **实现**：遍历常见代理端口，检测哪个端口可用

**修改文件**：`skills/deep-research/src/search-providers.ts`

### 任务3：创建 Gmail Reader 技能

**描述**：创建一个全新的技能，用于通过 IMAP 协议读取 Gmail 邮件。

**功能实现**：
- 使用 IMAP 协议连接 Gmail 服务器
- 支持读取最新邮件
- 支持读取未读邮件
- 支持搜索邮件
- 支持指定邮件 ID 读取

**输出格式**：JSON 格式，包含以下字段：
- `id`: 邮件 ID
- `subject`: 邮件主题
- `from`: 发件人
- `date`: 日期
- `body`: 邮件正文
- `is_read`: 是否已读

**技术栈**：
- Python 3
- `imaplib` 库用于 IMAP 连接
- `email` 库用于解析邮件内容

**创建文件**：
- `skills/gmail-reader/SKILL.md`
- `skills/gmail-reader/scripts/read_gmail.py`

### 任务4：查询密码箱获取 Gmail 账号

**描述**：从 vault 查询 Gmail 账号信息用于测试新创建的 Gmail Reader 技能。

**查询结果**：
- 账号：lu.***@gmail.com（已脱敏）
- 密码：已获取（安全存储）

## 关键决策与成果

| 决策/成果 | 说明 |
|-----------|------|
| 临时文件传递 JSON | 避免 Windows shell 引号转义问题，更可靠的参数传递方式 |
| 正则匹配 JSON | 解决格式化 JSON 跨行解析问题 |
| UTF-8 强制编码 | 解决 Windows 控制台编码问题 |
| undici ProxyAgent | 解决 Node.js fetch 不走系统代理的问题 |
| 代理端口自动检测 | 提升用户体验，无需手动配置代理端口 |
| 新技能 Gmail Reader | 扩展了邮件读取能力，支持 IMAP 协议 |

## 遇到的问题与解决方案

| 问题描述 | 原因分析 | 解决方案 | 结果 |
|---------|---------|---------|------|
| JSON 参数 shell 传递失败 | Windows 引号转义复杂 | 改用临时文件传递 | 已解决 |
| JSON 解析不完整 | 格式化结果跨多行 | 使用正则匹配完整 JSON | 已解决 |
| Unicode 输出乱码 | Windows 默认 GBK 编码 | Python 强制 UTF-8 输出 | 已解决 |
| Node.js fetch 不走代理 | 原生 fetch 不读系统代理 | 使用 undici ProxyAgent | 已解决 |

## 技术经验总结

### Windows 下 shell 参数传递 JSON 的坑
1. **引号转义**：PowerShell 对引号的转义规则复杂， `"` 和 `'` 混用容易出错
2. **特殊字符**：JSON 中的 `{}[]:,` 等特殊字符可能被 shell 解析
3. **最佳实践**：复杂参数优先使用临时文件传递，避免 shell 转义问题

### Node.js fetch 不走系统代理的解决方案
1. **undici 库**：Node.js 18+ 的 fetch 底层使用 undici，可通过 ProxyAgent 配置代理
2. **环境变量**：读取 `HTTPS_PROXY` 或 `HTTP_PROXY` 环境变量
3. **自动检测**：遍历常见代理端口（7890、7897 等），自动找到可用代理

### Python 脚本处理多字节字符的编码技巧
1. **强制 UTF-8**：在脚本开头重定向 stdout/stderr 为 UTF-8 编码
2. **环境变量**：设置 `PYTHONIOENCODING=utf-8` 环境变量
3. **文件编码**：打开文件时显式指定 `encoding='utf-8'`

## 修改的文件清单

```
skills/
├── baidu-search-1.1.2/
│   └── scripts/
│       └── search.py          # 修复 JSON 传递和编码问题
├── deep-research/
│   └── src/
│       └── search-providers.ts # 添加代理支持
└── gmail-reader/              # 新技能
    ├── SKILL.md
    └── scripts/
        └── read_gmail.py
```

## 备注

- Gmail Reader 技能已完成基础功能，后续可扩展支持更多邮件操作（如标记已读、删除等）
- Deep Research 技能的修复提升了在 Windows 环境下的稳定性
- 所有敏感信息（密码、API Key）已脱敏处理

---

**安全说明：** 本日志已自动过滤敏感信息（密码、API Key、手机号等），如需记录完整信息请手动补充。

*日志生成时间：2026-04-16 00:00:00*
