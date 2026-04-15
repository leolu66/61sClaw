---
name: telecom-news-fetcher
description: 获取运营商行业新闻和通信类微信公众号文章。支持中国移动、中国电信、中国联通、中国铁塔四大运营商的最新新闻查询。当用户需要查询运营商新闻、通信行业资讯、运营商动态时使用此技能。支持从C114通信网、运营商官网、权威媒体等多渠道获取新闻，支持按时间范围、运营商、新闻类型筛选。
triggers:
  - 获取运营商新闻
  - 通信新闻
  - 运营商资讯
  - 查一下通信新闻
  - telecom news
  - 获取公众号文章
  - 查一下公众号
  - 读取公众号
  - 中国移动最新消息
  - 中国电信新闻
  - 中国联通动态
  - 中国铁塔资讯
---

# 运营商新闻获取器

用于获取四大运营商（中国移动、中国电信、中国联通、中国铁塔）的最新行业新闻，支持多渠道检索、交叉验证、结构化输出。

## 支持的运营商

| 运营商 | 核心关键词 |
|--------|-----------|
| 中国移动 | 中国移动、中移动、China Mobile |
| 中国电信 | 中国电信、中电信、China Telecom |
| 中国联通 | 中国联通、中联通、China Unicom |
| 中国铁塔 | 中国铁塔、中铁塔、China Tower |

## 脚本路径

- 主入口：`C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py`
- C114爬虫：`C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\spiders\c114_spider.py`
- 配置文件：`C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\config.json`

## 支持的来源（优先级排序）

### 🌐 官方渠道
- 四大运营商官网新闻中心、官方APP公告
- 官方微博/微信公众号

### 📰 中央媒体
- 新华社、人民日报、央视新闻、光明日报

### 📡 行业媒体
- C114通信网 (c114.com.cn) - 通信行业权威门户 ✅ 已支持
- 通信世界网、人民邮电报

### 📊 综合/财经平台
- 百度新闻、头条新闻、新浪财经
- 东方财富网、同花顺财经

### 📱 微信公众号
- 通信敢言、运营商观察、通信世界
- 四大运营商官方公众号

## 使用方法

### 基础用法（默认最近7天，全运营商）
```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py"
```

### 指定运营商
```bash
# 只获取中国移动新闻
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --operator 中国移动

# 支持多运营商：中国移动,中国电信
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --operator 中国移动,中国电信
```

### 指定时间范围
```bash
# 最近3天
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --days 3

# 最近30天
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --days 30

# 指定日期范围
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --start 2026-04-01 --end 2026-04-12
```

### 指定获取数量
```bash
# 每来源获取10条
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --limit 10

# 简写
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" -n 10
```

### 只获取特定来源
```bash
# 只获取C114
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --sources c114

# 多来源：c114,official
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --sources c114,official
```

### 筛选新闻类型
```bash
# 只获取技术创新类新闻
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --type 技术创新

# 支持类型：业务动态,政策公告,技术创新,战略合作,重大事件,财务数据
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --type 业务动态,战略合作
```

### 不获取公众号
```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --no-wechat
```

### 保存到文件
```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\telecom-news-fetcher\scripts\fetch_telecom_news.py" --output telecom_news.md
```

## 核心能力说明

### 搜索策略
采用「核心词+扩展词+限定词」三层关键词结构：
- 核心词：运营商名称及别名
- 扩展词：业务动态、5G-A、算力网络、资费调整、AI、战略合作等
- 限定词：时间范围、来源渠道

### 信息筛选标准（优先级排序）
1. **时效性**：严格限定在目标时间范围内，排除过时信息
2. **权威性**：优先选择官方发布和权威媒体报道，标注可信度得分
3. **相关性**：剔除与目标运营商无直接关联的新闻
4. **完整性**：优先选择包含完整要素（时间、地点、事件、影响）的报道

### 质量评分体系
| 评分维度 | 评分标准 |
|---------|---------|
| 可信度 | 官方渠道(5分) > 中央媒体(4分) > 行业媒体(3分) > 综合平台(2分) > 自媒体(1分) |
| 重要性 | 重大战略(5分) > 全国性政策(4分) > 技术创新(3分) > 区域动态(2分) > 常规活动(1分) |
| 时效性 | 当天(5分) > 3天内(4分) > 7天内(3分) > 15天内(2分) > 30天内(1分) |

### 交叉验证机制
- 重要新闻（如全国性业务调整）至少通过2个独立权威渠道核实
- 信息冲突时标注差异，优先参考官方公告
- 非官方消息标注「未经官方证实，仅供参考」

## 配置说明

编辑 `config.json` 文件可修改以下配置：

### 启用/禁用来源
```json
"sources": {
  "c114": {
    "enabled": true,  // 改为 false 禁用
    "limit": 10,
    "priority": 3
  },
  "china_mobile_official": {
    "enabled": true,
    "url": "https://www.10086.cn/aboutus/news/index.html",
    "priority": 5
  }
}
```

### 关键词配置
```json
"keywords": {
  "业务动态": ["套餐调整", "5G-A", "算力网络", "云服务", "数据中心"],
  "政策公告": ["业务关停", "资费调整", "服务升级", "新规"],
  "技术创新": ["AI", "物联网", "6G研发", "网络切片"],
  "战略合作": ["联合", "合作", "签约", "共建"],
  "重大事件": ["系统升级", "安全事件", "社会责任"]
}
```

### 添加更多公众号
```json
"wechat": {
  "accounts": [
    "通信敢言",
    "运营商观察",
    "通信世界",
    "中国移动",
    "中国电信",
    "中国联通",
    "中国铁塔"
  ]
}
```

## 输出格式（结构化）
每条新闻包含以下字段：
- **标题**：核心内容，加粗关键信息
- **发布时间**：精确到日/时
- **信息来源**：标注渠道及可信度
- **核心摘要**：100-200字概括主要内容、关键数据、影响范围
- **原文链接**：可访问的新闻链接
- **标签分类**：标注新闻类型

### 输出示例
```markdown
## 📡 运营商新闻 [2026-04-12 15:30] | 最近7天 · 全运营商

### 🔝 重要新闻（按优先级排序）

#### 1. [中国移动发布5G-A商用部署计划，年内建设10万基站](https://www.10086.cn/aboutus/news/20260412.html)
📅 2026-04-12 · 📢 来源：中国移动官网（可信度：5分）
📝 摘要：中国移动宣布2026年将投入200亿元建设10万个5G-A基站，覆盖全国主要城市，实现下行万兆、上行千兆的网络能力，同时发布12款5G-A终端产品。
🏷️ 标签：技术创新 · 业务动态

#### 2. [中国电信与阿里云签署战略合作协议，共建算力网络](https://www.c114.com.cn/news/123456.html)
📅 2026-04-10 · 📢 来源：C114通信网（可信度：3分）
📝 摘要：双方将在算力调度、云网融合、AI应用等领域展开深度合作，计划3年内建成覆盖全国的分布式算力网络节点，为企业用户提供一体化算力服务。
🏷️ 标签：战略合作 · 技术创新

### 📊 分类统计
- 业务动态：3条 · 技术创新：4条 · 战略合作：2条
- 中国移动：5条 · 中国电信：2条 · 中国联通：1条 · 中国铁塔：1条

---
*由 OpenClaw 运营商新闻技能自动生成 · 共检索8个来源，交叉验证通过率92%*
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
