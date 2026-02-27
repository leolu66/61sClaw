---
name: telecom-news-fetcher
description: 获取运营商行业新闻和通信类微信公众号文章。当用户需要查询运营商新闻、通信行业资讯时使用此技能。支持从C114通信网等网站获取新闻，支持获取指定公众号的文章。
triggers:
  - 获取运营商新闻
  - 通信新闻
  - 运营商资讯
  - 查一下通信新闻
  - telecom news
  - 获取公众号文章
  - 查一下公众号
  - 读取公众号
---

# 运营商新闻获取器

用于获取运营商行业新闻和微信公众号文章。

## 脚本路径

- 主入口：`C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py`
- C114爬虫：`C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\spiders\c114_spider.py`
- 配置文件：`C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\config.json`

## 支持的来源

### 🌐 网站

- C114通信网 (c114.com.cn) - 通信行业权威门户 ✅ 已支持

### 📱 微信公众号

- 通信敢言 - 用户提供
- 更多公众号待添加...

## 使用方法

### 获取所有新闻

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py"
```

### 指定获取数量

```bash
# 每来源获取10条
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --limit 10

# 简写
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" -n 10
```

### 只获取特定网站

```bash
# 只获取C114
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --sources c114
```

### 不获取公众号

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --no-wechat
```

### 保存到文件

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --output telecom_news.md
```

## 配置说明

编辑 `config.json` 文件可修改以下配置：

### 启用/禁用来源

```json
"sources": {
  "c114": {
    "enabled": true,  // 改为 false 禁用
    "limit": 10
  }
}
```

### 添加更多公众号

```json
"wechat": {
  "accounts": [
    "通信敢言",
    "运营商观察",
    "通信世界"
  ]
}
```

## 输出示例

```markdown
## 📡 运营商新闻 [2026-02-27 22:14]

### 🌐 网站新闻

**来源：C114通信网**

- [中国移动启动2026年通感一体项目招标](https://www.c114.com.cn/news/...)
  📅 2/27 · 🔗 阅读全文

- [中国联通发布最新5G基站建设计划](https://www.c114.com.cn/news/...)
  📅 2/26 · 🔗 阅读全文

### 📱 公众号精选

**来源：通信敢言**

- 深度：运营商数字化转型之路
- 5G时代运营商的机遇与挑战

---
*由 OpenClaw 运营商新闻技能自动生成*
```

## 依赖安装

首次使用前需要安装依赖：

```bash
pip install requests beautifulsoup4
```

## 扩展开发

### 添加新网站爬虫

1. 在 `spiders/` 目录下创建新的爬虫文件，如 `newsite_spider.py`
2. 参考 `c114_spider.py` 的结构实现 `fetch_newsite_news()` 函数
3. 在 `fetch_telecom_news.py` 中导入并调用
4. 在 `config.json` 中添加站点配置

### 添加新公众号

直接在 `config.json` 的 `wechat.accounts` 数组中添加公众号名称即可。
