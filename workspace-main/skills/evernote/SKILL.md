---
name: evernote
description: |
  印象笔记（Evernote/Yinxiang）集成技能，支持创建笔记、搜索笔记、管理笔记本和标签。
  触发词："记到印象笔记"、"查找印象笔记"、"印象笔记笔记本"
triggers:
  - "记到印象笔记"
  - "查找印象笔记"
  - "印象笔记笔记本"
  - "印象笔记标签"
  - "evernote"
version: 1.0.0
---

# 印象笔记技能

集成印象笔记（Evernote/Yinxiang），支持笔记的创建、搜索、查看和管理。

## 触发方式

| 用户说 | 动作 |
|--------|------|
| "记到印象笔记：今天的工作总结" | 创建新笔记 |
| "查找印象笔记：项目计划" | 搜索笔记 |
| "列出印象笔记笔记本" | 查看所有笔记本 |
| "印象笔记标签" | 查看所有标签 |

## 使用方法

### 1. 创建笔记

> 👤 记到印象笔记：今天完成了技能开发，修复了3个bug
>
> 🤖 已创建笔记：《工作记录》

支持设置笔记本和标签：
> 👤 记到印象笔记/工作日志 #开发：完成了Evernote技能开发

### 2. 搜索笔记

> 👤 查找印象笔记：项目计划
>
> 🤖 找到 3 条笔记：
> 1. 项目计划-2026Q1
> 2. 项目进度跟踪
> 3. 项目会议纪要

### 3. 查看笔记本

> 👤 列出印象笔记笔记本
>
> 🤖 共有 5 个笔记本：
> - 工作日志
> - 项目资料
> - 学习笔记
> - 待办事项
> - 归档

### 4. 管理标签

> 👤 印象笔记标签
>
> 🤖 共有 8 个标签：
> - 工作
> - 学习
> - 生活

## CLI 命令

```bash
# 测试连接
python scripts/evernote_cli.py test

# 创建笔记
python scripts/evernote_cli.py create "标题" "内容" --notebook "笔记本" --tags "标签1,标签2"

# 更新笔记
python scripts/evernote_cli.py update <guid> --title "新标题" --content "新内容"

# 删除笔记
python scripts/evernote_cli.py delete <guid>

# 获取笔记详情
python scripts/evernote_cli.py get <guid>

# 列出笔记本
python scripts/evernote_cli.py notebooks

# 搜索笔记
python scripts/evernote_cli.py search "关键词" --max 10

# 列出标签
python scripts/evernote_cli.py tags

# 创建标签
python scripts/evernote_cli.py create-tag "标签名"
```

## 配置

### 环境变量

```bash
# 印象笔记 Developer Token
export EVERNOTE_TOKEN="S=s19:U=..."

# NoteStore URL（中国版印象笔记）
export EVERNOTE_NOTESTORE_URL="https://app.yinxiang.com/shard/s19/notestore"
```

### 获取 Developer Token

1. 访问 https://app.yinxiang.com/DeveloperToken.action
2. 登录印象笔记账号
3. 复制 Developer Token
4. 设置环境变量

## 功能列表

- [x] 创建笔记
- [x] 更新笔记
- [x] 删除笔记
- [x] 获取笔记详情
- [x] 搜索笔记
- [x] 列出笔记本
- [x] 列出标签
- [x] 创建标签

## 技术实现

- 基于 Evernote Thrift API
- 支持 ENML 格式内容
- 自动处理时间戳和哈希
- 支持笔记本和标签管理

## 注意事项

- Token 有效期至 2026-03-25，过期后需要重新生成
- 请妥善保管 Token，不要泄露给他人
- 支持富文本内容（HTML/ENML 格式）
- 删除的笔记会移动到废纸篓，不会永久删除

## 依赖

- Python 3.7+
- thrift

## 文件结构

```
evernote/
├── SKILL.md              # 技能说明
├── scripts/
│   └── evernote_cli.py   # CLI 脚本
└── lib/
    ├── client.py         # 主客户端
    └── evernote/
        └── edam/
            ├── type/     # 类型定义
            └── notestore/ # NoteStore 客户端
```

## License

MIT
