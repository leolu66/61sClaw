---
name: wechat-article-fetcher
description: 获取微信公众号文章列表。当用户需要查询公众号文章、获取微信公众号内容、批量获取文章链接时使用此技能。支持两种方案：1) 搜狗搜索（无需登录，数据较旧）2) 公众号后台接口（需要扫码登录，数据实时完整）。
triggers:
  - 读取微信公众号
  - 读公众号
  - 查阅公众号
  - read wechat
  - 获取公众号文章
  - 公众号文章获取
  - 查询微信公众号
  - 查看公众号
---

# 微信公众号文章获取工具

通过公众号名称获取近期文章列表。支持两种方案：

## 方案对比

| 方案 | 数据新鲜度 | 需要登录 | 适用场景 |
|------|-----------|----------|----------|
| **搜狗搜索** | ⭐⭐ 较旧 | ❌ 不需要 | 快速查询、无需配置 |
| **公众号后台** | ⭐⭐⭐⭐⭐ 实时 | ✅ 需要 | 完整数据、大量采集 |

## 脚本路径

- 搜狗方案：`C:\Users\luzhe\.openclaw\workspace-main\skills\wechat-article-fetcher\scripts\fetch_articles.py`
- 后台方案：`C:\Users\luzhe\.openclaw\workspace-main\skills\wechat-article-fetcher\scripts\fetch_articles_v2.py`

---

## 方案1：搜狗搜索（简单快速）

无需登录，直接搜索，但数据可能较旧。

### 使用方法

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\wechat-article-fetcher\scripts\fetch_articles.py" <公众号名称>
```

### 示例

```bash
# 获取机器之心最近10篇文章
python "C:\Users\luzhe\.openclaw\workspace-main\skills\wechat-article-fetcher\scripts\fetch_articles.py" "机器之心"

# 获取5篇文章并保存到文件
python "C:\Users\luzhe\.openclaw\workspace-main\skills\wechat-article-fetcher\scripts\fetch_articles.py" "量子位" -n 5 -o articles.json
```

---

## 方案2：公众号后台接口（推荐）

**数据实时、完整**，但需要先扫码登录获取凭证。

### 前置条件

1. **注册一个微信公众号**（订阅号/服务号均可）
   - 前往 https://mp.weixin.qq.com 注册
   - 已有公众号可跳过

2. **扫码登录获取凭证**
   - 访问 https://mp.weixin.qq.com
   - 使用微信扫码登录
   - 按 F12 打开开发者工具
   - 在 Network 面板找到任意请求，复制 Cookie 和 Token

### 使用方法

```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\wechat-article-fetcher\scripts\fetch_articles_v2.py" <公众号名称> -c "cookie字符串" -t "token"
```

### 示例

```bash
# 获取公众号文章（使用真实凭证）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\wechat-article-fetcher\scripts\fetch.py" "苏哲管理咨询" -c "wxt_articles_v2okenkey=xxx; wxuin=xxx; ..." -t "1234567890"

# 保存结果
python "C:\Users\luzhe\.openclaw\workspace-main\skills\wechat-article-fetcher\scripts\fetch_articles_v2.py" "机器之心" -o output.json
```

---

## 批量获取

使用 `batch_fetch.py` 批量获取多个公众号文章：

```bash
# 批量获取（搜狗方案）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\wechat-article-fetcher\scripts\batch_fetch.py" "公众号1" "公众号2" "公众号3"

# 批量获取并保存
python "C:\Users\luzhe\.openclaw\workspace-main\skills\wechat-article-fetcher\scripts\batch_fetch.py" "机器之心" "量子位" -o ./output/
```

## 注意事项

- 搜狗搜索有频率限制，建议添加延时
- 公众号后台接口需要妥善保管 Cookie 和 Token
- 批量获取时建议使用搜狗方案，避免频繁登录
