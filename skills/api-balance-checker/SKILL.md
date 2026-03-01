---
name: api-balance-checker
description: |
  查询多个 API 平台的余额和用量信息。支持通过已登录的 Chrome 浏览器访问各平台 Dashboard 获取数据。
  
  **重要：每次查询都是实时的！** 直接从各平台 Dashboard 获取最新数据，本地数据库仅用于历史对比。

  **触发指令：**
  - `查余额`、`查 wc 余额`、`查鲸云余额` → 只查询 WhaleCloud Lab
  - `查全部余额`、`查所有余额` → 查询全部平台（WhaleCloud + 智谱 AI + Moonshot）
---

# API Balance Checker

查询多个 API 平台的账户余额和用量信息。

## 💡 重要说明

**每次查询都是实时的！** 

- ✅ 通过 Playwright 自动化访问各平台 Dashboard，获取最新余额数据
- ✅ 不会使用缓存或本地记录代替实时查询
- 📊 本地数据库仅用于保存历史记录，方便对比变化趋势
- 📈 每次查询后会自动显示与上次的差异（余额变化、使用量变化等）

## 支持的平台

| 平台 | 说明 |
|------|------|
| WhaleCloud Lab | 鲸云实验室，代理多种大模型 API |
| Zhipu (智谱 AI) | 智谱 AI GLM 系列模型 |
| Moonshot (月之暗面) | Kimi 系列模型 |

## 使用方法

### 查询 WhaleCloud 余额

```bash
python C:\Users\luzhe\.openclaw\workspace-main\skills\api-balance-checker\scripts\query_balance.py whalecloud
```

### 查询全部平台余额

```bash
python C:\Users\luzhe\.openclaw\workspace-main\skills\api-balance-checker\scripts\query_balance.py whalecloud zhipu moonshot
```

## 登录状态

首次查询时，脚本会自动打开 Chrome 并进入登录页面，请登录各平台。登录状态会保留，下次查询无需重新登录。

## 注意事项

- Chrome 调试端口默认为 9222
- 登录状态失效后，需要重新手动登录
- 查询结果会保存到 `C:/Users/luzhe/Pictures/api_balances.json`
