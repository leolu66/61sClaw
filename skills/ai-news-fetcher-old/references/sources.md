# AI新闻源参考

## 已支持的网站

### 1. 机器之心 (jiqizhixin.com)
- **类型**: 国内领先的AI媒体
- **内容特点**: AI研究论文解读、行业分析、技术教程
- **更新频率**: 每日多更
- **RSS**: https://www.jiqizhixin.com/rss

### 2. 量子位 (qbitai.com)
- **类型**: 知名科技媒体
- **内容特点**: AI新闻快讯、产品评测、公司动态
- **更新频率**: 每日多更
- **特点**: 报道速度快，覆盖面广

### 3. InfoQ中国 (infoq.cn)
- **类型**: 技术社区媒体
- **内容特点**: 深度技术文章、架构设计、AI工程实践
- **更新频率**: 每日更新
- **目标读者**: 技术开发者、架构师

### 4. 智东西 (zhidx.com)
- **类型**: 智能产业媒体
- **内容特点**: AI产业报道、公司分析、投资动态
- **更新频率**: 每日更新
- **特点**: 偏产业和商业视角

### 5. AI科技评论 (leiphone.com)
- **类型**: 雷锋网旗下AI频道
- **内容特点**: AI学术动态、技术趋势、行业评论
- **更新频率**: 每日更新

## 备选网站（可扩展）

### 国内
- **36氪AI**: 36kr.com/search/articles/AI
- **钛媒体AI**: tmtpost.com
- **虎嗅**: huxiu.com
- **差评**: chaping.cn

### 国际（英文）
- **TechCrunch**: techcrunch.com/category/artificial-intelligence/
- **The Verge AI**: theverge.com/ai-artificial-intelligence
- **MIT Technology Review**: technologyreview.com
- **VentureBeat AI**: venturebeat.com/ai/

## 技术说明

### 爬虫策略
1. 使用requests获取网页HTML
2. 使用BeautifulSoup解析内容
3. 适配各网站的DOM结构变化
4. 处理相对链接转换为绝对链接

### 反爬处理
- 设置合理的User-Agent
- 控制请求频率
- 处理编码问题
- 超时重试机制

### 扩展新网站

如需添加新网站，在`scripts/fetch_ai_news.py`中的`SOURCES`字典添加配置:

```python
"网站名称": {
    "url": "https://example.com/",
    "selector": {
        "articles": "文章容器选择器",
        "title": "标题选择器",
        "link": "链接选择器",
        "summary": "摘要选择器",
        "time": "时间选择器"
    }
}
```
