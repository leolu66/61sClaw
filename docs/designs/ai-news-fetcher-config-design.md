# AI新闻获取器 - 配置化设计方案

_版本: 2026-03-09_  
_状态: 设计中_

---

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│ 配置管理层 (YAML)                                        │
├─────────────────────────────────────────────────────────┤
│ site-configs/                                           │
│ ├── qbitai.yaml          # 量子位 - 标准站点             │
│ ├── zhidx.yaml           # 智东西 - 复杂站点             │
│ ├── 36kr.yaml            # 36氪 - 有反爬措施             │
│ └── _template.yaml       # 新站点配置模板                │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 采集引擎层 (SpiderEngine)                                │
├─────────────────────────────────────────────────────────┤
│ ├── 配置加载器 (ConfigLoader)                            │
│ │   └── 支持热更新 (文件监听/定时刷新)                    │
│ ├── 站点路由器 (SiteRouter)                              │
│ │   ├── 标准站点 → 通用提取器 (GenericExtractor)         │
│ │   └── 复杂站点 → 自定义提取器 (CustomExtractor)        │
│ ├── 请求调度器 (RequestScheduler)                        │
│ │   └── 频率控制、重试机制、代理支持                      │
│ ├── 页面下载器 (PageDownloader)                          │
│ │   └── requests / playwright 双模式                     │
│ ├── 字段提取器 (FieldExtractor)                          │
│ │   └── CSS Selector / XPath 双支持                      │
│ ├── 反爬检测器 (AntiCrawlDetector)                       │
│ └── 站点状态监控 (SiteStatusMonitor)                     │
└─────────────────────────────────────────────────────────┘
```

---

## 配置字段规范

### 基础站点信息

```yaml
site:
  name: "站点中文名"           # 必填
  base_url: "https://..."      # 必填
  enabled: true                # 是否启用
```

### 抓取配置

```yaml
fetch:
  method: "requests"           # requests / playwright
  encoding: "utf-8"            # 页面编码
  headers:                     # 自定义请求头
    User-Agent: "..."
  
  strategy:                    # 抓取策略
    requests_per_minute: 10    # 每分钟最大请求数
    delay_between_requests: 6  # 请求间隔（秒）
    max_retries: 3             # 失败重试次数
    retry_delay: 30            # 重试间隔（秒）
    timeout: 15                # 请求超时（秒）
  
  playwright:                  # Playwright专用配置
    headless: true
    wait_for: "networkidle"
    wait_timeout: 30000
```

### 选择器配置（支持双模式）

```yaml
selectors:
  # 新闻列表容器
  container:
    css: "div.article-list"                    # 首选：CSS Selector
    xpath: "//div[@class='article-list']"      # 备选：XPath
  
  # 单条新闻结构（相对于container）
  item: "div.article-item"
  
  # 各字段提取
  fields:
    title:
      primary:                                 # 主选择器（CSS）
        selector: "h2 a"
        attribute: "text"                      # text / href / src
      fallback:                                # 备选选择器（XPath）
        selector: "//h2/a/text()"
      example: "新闻标题示例"
      
    link:
      primary:
        selector: "h2 a"
        attribute: "href"
      transform: "absolute_url"                # 转换方式
      example: "https://..."
      
    summary:
      primary:
        selector: ".excerpt"
        attribute: "text"
        max_length: 200                        # 最大长度限制
      example: "摘要内容..."
      
    time:
      primary:
        selector: "time"
        attribute: "text"
      fallback:
        selector: "//time/text()"
      example: "15小时前"
```

### 反爬措施记录

```yaml
anti_crawl:
  detected: false              # 是否检测到反爬
  type: ""                     # 反爬类型：滑块验证/验证码/频率限制
  trigger_condition: ""        # 触发条件
  recovery_time: ""            # 恢复方式
  bypass_method: ""            # 绕过方法
  status: "normal"             # 当前状态：normal/degraded/blocked
  
  mitigation:                  # 应对策略
    enabled: true
    cooldown_minutes: 60       # 触发后冷却时间
    alternative_sources: []    # 替代数据源
    manual_intervention: false # 是否需要人工介入
```

### 数据过滤

```yaml
filters:
  min_title_length: 10         # 标题最小长度
  link_pattern: "/\d+/"        # 链接匹配正则
  exclude_keywords: ["广告"]    # 排除关键词
```

### 提取器选择

```yaml
extractor: "default"           # default / custom_xxx
```

---

## 现有站点配置反推

### 量子位 (qbitai.yaml)

```yaml
site:
  name: "量子位"
  base_url: "https://www.qbitai.com"
  enabled: true

fetch:
  method: "requests"
  encoding: "utf-8"
  
  strategy:
    requests_per_minute: 10
    delay_between_requests: 6
    max_retries: 3

selectors:
  container:
    css: "body > div.main > div.content > div"
  
  item: "article, .article-item, .post-item"
  
  fields:
    title:
      primary:
        selector: "h2 a, h3 a, .post-title a"
        attribute: "text"
      example: "高中生AI创业，现在只招龙虾员工：每月成本2800"
      
    link:
      primary:
        selector: "h2 a, h3 a, .post-title a"
        attribute: "href"
      transform: "absolute_url"
      pattern: "/\d{4}/\d{2}/\d+\.html"
      
    summary:
      primary:
        selector: ".post-excerpt, .excerpt, p"
        attribute: "text"
        max_length: 200
      
    time:
      primary:
        selector: "time, .post-time, .date"
        attribute: "text"
      fallback:
        selector: "//time/text()"

anti_crawl:
  detected: false
  status: "normal"

extractor: "default"
```

### 智东西 (zhidx.yaml)

```yaml
site:
  name: "智东西"
  base_url: "https://zhidx.com"
  enabled: true

fetch:
  method: "requests"
  encoding: "utf-8"

selectors:
  container:
    css: "ul.news-list, body > div.container > div.main > ul"
  
  item: "li, .news-item, .article-item"
  
  fields:
    title:
      primary:
        selector: ".info-left-title a, h3.title a"
        attribute: "text"
      
    link:
      primary:
        selector: ".info-left-title a, h3.title a"
        attribute: "href"
      
    summary:
      primary:
        selector: ".info-left-desc, .summary, .excerpt"
        attribute: "text"
        max_length: 200
      
    time:
      primary:
        selector: ".ilr-time, .time, .publish-time"
        attribute: "text"

# 智东西需要自定义提取器
extractor: "zhidx"
```

### 36氪 (36kr.yaml) - 有反爬

```yaml
site:
  name: "36氪"
  base_url: "https://36kr.com"
  enabled: true

fetch:
  method: "playwright"         # 需要动态渲染
  
  strategy:
    requests_per_minute: 5     # 降低频率
    delay_between_requests: 12
    max_retries: 2

anti_crawl:
  detected: true
  type: "滑块验证"
  trigger_condition: "短时间多次查询"
  recovery_time: "一段时间后自动恢复"
  bypass_method: "降低频率，每小时最多抓取一次"
  status: "degraded"
  
  mitigation:
    enabled: true
    cooldown_minutes: 60
    manual_intervention: true

extractor: "default"
```

---

## 新站点配置引导流程

### 步骤1：基础信息

```
请输入站点名称（中文）: [量子位]
请输入站点URL: [https://www.qbitai.com]
是否需要动态渲染（Playwright）? [y/N]
```

### 步骤2：新闻列表定位

```
请在浏览器中打开目标页面，右键点击新闻列表区域，选择"检查"
复制新闻列表容器的 CSS Selector 或 XPath

新闻列表容器 CSS Selector: [div.content > div.article-list]
新闻列表容器 XPath（可选）: [//div[@class='article-list']]
单条新闻结构: [div.article-item]
```

### 步骤3：字段定位

```
对于每条新闻，请提供以下字段的选择器：

标题:
  CSS Selector: [h2 a]
  示例值: [高中生AI创业，现在只招龙虾员工：每月成本2800]

链接:
  CSS Selector: [h2 a]
  属性: [href]
  示例值: [https://www.qbitai.com/2026/03/384797.html]

摘要（可选）:
  CSS Selector: [.excerpt]
  示例值: [全龙虾公司，还设了好几个部门]

时间（可选）:
  CSS Selector: [time]
  示例值: [15小时前]
```

### 步骤4：反爬检测

```
是否检测到反爬措施? [y/N]
  反爬类型: [滑块验证/验证码/频率限制/其他]
  触发条件: [短时间多次查询]
  建议抓取频率: [每小时1次]
```

### 步骤5：生成配置

```
正在生成配置文件: site-configs/[站点英文名].yaml

配置预览:
[显示生成的YAML内容]

是否保存? [Y/n]
```

### 步骤6：测试验证

```
正在测试配置...
✓ 页面下载成功
✓ 列表容器定位成功，找到 10 条新闻
✓ 标题提取成功: "..."
✓ 链接提取成功: "..."
⚠ 摘要提取失败，使用空值
✓ 时间提取成功: "..."

测试结果: 5/6 字段正常，建议检查摘要选择器
```

---

## 待办任务

- [ ] 实现 ConfigLoader 配置加载器
- [ ] 实现 GenericExtractor 通用提取器
- [ ] 实现 SpiderEngine 采集引擎
- [ ] 实现配置热更新机制
- [ ] 实现反爬检测和应对
- [ ] 实现新站点配置引导工具
- [ ] 迁移现有站点到 YAML 配置
- [ ] 编写配置模板和文档

---

*更新日期: 2026-03-09*  
*关联技能: ai-news-fetcher*
