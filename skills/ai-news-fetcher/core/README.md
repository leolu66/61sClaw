# AI新闻获取器 - 配置化版本

## 核心模块

### 1. ConfigLoader - 配置加载器
- 文件: `core/config_loader.py`
- 功能: 加载YAML配置，支持热更新

### 2. BaseExtractor - 基础提取器
- 文件: `core/extractor.py`
- 功能: CSS Selector和XPath提取

### 3. SpiderEngine - 采集引擎
- 文件: `core/spider_engine.py`
- 功能: 整合配置、下载、提取

## 站点配置

| 站点 | 文件 | 方法 | 状态 |
|------|------|------|------|
| 量子位 | `site-configs/qbitai.yaml` | requests | ✅ 已配置 |
| AI科技评论 | `site-configs/leiphone.yaml` | requests | ✅ 已配置 |
| 极客公园 | `site-configs/geekpark.yaml` | requests | ✅ 已配置 |
| AiBase | `site-configs/aibase.yaml` | playwright | ✅ 已配置 |
| 智东西 | `site-configs/zhidx.yaml` | custom | ✅ 已配置 |
| 36氪 | `site-configs/36kr.yaml` | playwright | ✅ 已配置 |
| InfoQ | `site-configs/infoq.yaml` | custom | ✅ 已配置 |

## 使用方法

```python
from core.spider_engine import SpiderEngine

# 创建引擎
engine = SpiderEngine("site-configs")

# 抓取单个站点
articles = engine.fetch_site("qbitai", limit=5)

# 抓取所有站点
results = engine.fetch_all(limit=5)
```

## 测试

```bash
cd skills/ai-news-fetcher/core
python spider_engine.py
```
