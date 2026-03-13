# NetNotes - 互联网笔记本

一个智能的互联网文章收藏和管理工具，支持自动抓取、分类和归档网页内容。

---

## 需求说明（SRS）

### 触发条件
用户说什么话会触发此技能：
- "保存这篇文章"
- "收藏网页"
- "添加到笔记本"
- "netnotes"
- "互联网笔记本"

### 功能描述
NetNotes 帮助用户收藏和管理互联网文章：
1. 接收网页URL，自动抓取正文内容
2. 处理反爬机制（使用Playwright）
3. 将内容转换为Markdown格式
4. 使用大模型自动分析并推荐分类
5. 用户确认后保存到对应专题笔记本
6. 记录文章元数据到SQLite数据库

### 输入/输出
- **输入**: 网页URL（支持大多数新闻网站、博客等）
- **输出**: 
  - Markdown格式文章文件（保存在对应专题目录）
  - 数据库记录（包含时间、URL、标题、分类、摘要）

### 依赖条件
- Python 3.8+
- playwright (`pip install playwright` 且 `playwright install`)
- requests, beautifulsoup4, markdownify
- SQLite3（Python内置）

### 边界情况
- **反爬网站**: 使用Playwright模拟浏览器获取
- **动态内容**: 等待页面加载完成后再提取
- **提取失败**: 提示用户并提供手动保存选项
- **重复文章**: 根据URL去重，提示用户已存在
- **分类不确定**: 提供"其他"分类作为兜底

---

## 使用方法

### 基本用法

```bash
# 保存一篇文章
python scripts/main.py <网页URL>

# 示例
python scripts/main.py "https://example.com/article"
```

### 交互流程

1. **提供URL**: 用户发送网页链接
2. **自动抓取**: 系统抓取正文内容
3. **智能分类**: 大模型分析内容并推荐分类
4. **用户确认**: 显示推荐分类，等待用户确认或修改
5. **保存归档**: 确认后保存到对应目录并记录数据库

### 笔记本分类

默认创建以下专题笔记本：
1. **AI** - 人工智能相关文章
2. **运营商** - 通信运营商行业资讯
3. **管理** - 管理方法论、领导力等
4. **社会生活** - 社会热点、生活感悟
5. **技术其他** - 其他技术类文章
6. **其他** - 无法分类的内容

---

## 目录结构

```
skills/netnotes/
├── SKILL.md              # 本文件
├── scripts/
│   ├── main.py           # 主程序入口
│   ├── crawler.py        # 网页抓取模块
│   ├── classifier.py     # 文章分类模块
│   └── database.py       # 数据库操作模块
├── notebooks/            # 笔记本目录（自动创建）
│   ├── AI/
│   ├── 运营商/
│   ├── 管理/
│   ├── 社会生活/
│   ├── 技术其他/
│   └── 其他/
└── data/
    └── netnotes.db       # SQLite数据库
```

---

## 数据库结构

**articles表**:
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    summary TEXT,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 注意事项

- 首次使用会自动创建目录结构和数据库
- 文章文件名使用网页标题（自动清理非法字符）
- 相同URL的文章不会重复保存
- 摘要由大模型生成，不超过100字

---

## DoD 检查表

**开发日期**: 2026-03-13
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
- [x] 配置外置（如需要）
- [x] 无 .skill 文件

### 3. 测试通过
- [x] 功能测试通过
- [x] 触发测试通过
- [x] 边界测试通过

### 4. GitHub 同步
- [x] 已提交并推送
- [x] 无隐私文件泄露
- [x] 推送到 main

**状态**: ✅ 完成
