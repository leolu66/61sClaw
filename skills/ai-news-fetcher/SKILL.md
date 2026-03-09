---
name: ai-news-fetcher
description: 获取国内权威AI科技网站的最新新闻，并以带摘要的卡片形式展示。当用户询问"获取AI新闻"、"最新AI资讯"、"科技新闻"、"AI动态"、"有什么AI新闻"时使用此skill。支持从机器之心、量子位、InfoQ等国内主流AI媒体获取新闻。
---

# AI新闻获取器（整合版）

基于 YAML 配置的通用新闻采集框架，结合旧版的 Skill 接口和新版的配置驱动引擎。

## 核心特性

- **配置驱动采集** - 使用 YAML 配置站点，支持 XPath/CSS/Regex/JSON SSR 多种提取方式
- **智能缓存机制** - 4小时内重复查询自动从缓存读取，避免重复抓取
- **Markdown 输出** - 表格形式展示，标题带链接，摘要自动截断
- **多站点支持** - 机器之心、量子位、InfoQ、36氪、智东西、雷锋网、AI基地

## 脚本路径

`C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\fetch_ai_news.py`

## 支持的网站

| 中文名 | 配置名 | 状态 |
|--------|--------|------|
| 量子位 | qbitai | ✅ |
| InfoQ中国 | infoq | ✅ |
| 智东西 | zhidx | ✅ |
| AI科技评论/雷锋网 | leiphone | ✅ |
| 36氪 | 36kr | ✅ |
| AiBase | aibase | ✅ |
| 极客公园 | geekpark | ✅ |
| 机器之心 | jiqizhixin | ✅ |

## 使用方法

### 直接运行获取所有新闻

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\fetch_ai_news.py"
```

**缓存机制：**
- 默认自动保存到 `logs/daily/ai-news-YYYYMMDD-HH.md`
- 4小时内重复查询会直接从缓存读取，不会重新抓取
- 新闻标题已添加链接，方便点击查看详情

### 常用参数

- `--limit N`: 每个网站获取N条新闻（默认5条）
- `--sources 网站名1,网站名2`: 指定特定网站
- `--output 文件.md`: 额外保存到指定文件
- `--no-cache`: 强制刷新，忽略缓存
- `--cache-hours N`: 设置缓存有效期（默认4小时）

### 示例命令

```bash
# 获取每个网站10条新闻
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\fetch_ai_news.py" --limit 10

# 只获取量子位和InfoQ的新闻
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\fetch_ai_news.py" --sources 量子位,InfoQ

# 强制刷新（忽略缓存）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\fetch_ai_news.py" --no-cache

# 保存到指定文件（同时仍会缓存）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\ai-news-fetcher\fetch_ai_news.py" --output ai_news.md
```

## 输出格式

输出为Markdown格式，包含：

### 1. 结果汇总表格
| 来源 | 获取数量 | 链接 |
| ---------- | -------- | ------- |
| 量子位 | 5条 | [qbitai.com](https://www.qbitai.com) |
| InfoQ | 5条 | [infoq.cn](https://www.infoq.cn) |
| ... | ... | ... |

### 2. 每个来源的详细表格
| 序号 | 标题 | 摘要 | 更新时间 |
| ---- | ---- | ---- | -------- |
| 1 | [新闻标题](链接) | 摘要内容... | 7小时前 |
| 2 | [新闻标题](链接) | 摘要内容... | 昨天 |

**特点：**
- 标题带可点击链接
- 摘要限制50字，超出用...截断
- 时间显示为相对时间（刚刚、7小时前、昨天）
- 表格形式清晰易读

## 项目结构

```
ai-news-fetcher/
├── fetch_ai_news.py        # 主入口（整合版）
├── spider_cli.py           # 命令行工具（测试/调试）
├── main.py                 # 原版主入口
├── spider/                 # 核心采集引擎
│   ├── config_loader.py    # YAML配置加载
│   ├── extractors.py       # 字段提取器
│   ├── engine.py           # 采集引擎
│   ├── monitor.py          # 监控告警
│   └── storage.py          # 数据存储
├── site-configs/           # 站点配置（YAML）
│   ├── _template.yaml      # 配置模板
│   ├── jiqizhixin.yaml     # 机器之心（已禁用）
│   ├── qbitai.yaml         # 量子位
│   ├── infoq.yaml          # InfoQ
│   ├── 36kr.yaml           # 36氪
│   ├── zhidx.yaml          # 智东西
│   ├── leiphone.yaml       # 雷锋网
│   ├── aibase.yaml         # AI基地
│   └── geekpark.yaml       # 极客公园
├── cache/                  # 缓存目录
└── output/                 # 输出目录
```

## 添加新站点

1. 复制模板创建配置：
   ```bash
   cp site-configs/_template.yaml site-configs/mynews.yaml
   ```

2. 编辑配置，填写站点信息和选择器

3. 测试配置：
   ```bash
   python spider_cli.py test mynews
   ```

4. 启用站点：`enabled: true`

## 依赖安装

首次使用前需要安装依赖：

```bash
pip install -r requirements.txt
```

**主要依赖：**
- `aiohttp` - 异步HTTP请求
- `lxml` - HTML/XML解析
- `click` - 命令行工具
- `pyyaml` - YAML配置解析

## 调试工具

使用 `spider_cli.py` 进行配置测试和调试：

```bash
# 测试站点配置
python spider_cli.py test qbitai

# 测试特定字段
python spider_cli.py test qbitai --field title

# 测试详情页
python spider_cli.py test qbitai --detail --url "https://..."

# 列出所有站点
python spider_cli.py list-sites

# 探测网页结构
python spider_cli.py probe "https://example.com"
```

## 与旧版的区别

| 特性 | 旧版 | 新版（整合版） |
|------|------|----------------|
| 采集方式 | 硬编码 Python | YAML 配置驱动 |
| 添加新站点 | 修改代码 | 添加 YAML 配置 |
| 缓存机制 | ✅ 4小时文件缓存 | ✅ 保留 |
| Markdown输出 | ✅ 表格格式 | ✅ 保留 |
| 时间格式化 | ✅ 相对时间 | ✅ 保留 |
| 摘要截断 | ✅ 30字限制 | ✅ 保留 |
| Skill触发 | ✅ 自动触发 | ✅ 保留 |

## License

MIT
