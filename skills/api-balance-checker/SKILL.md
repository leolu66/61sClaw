---
name: api-balance-checker
description: |
  查询多个 API 平台的余额和用量信息。支持通过已登录的 Chrome 浏览器访问各平台 Dashboard 获取数据。
  
  **重要：每次查询都是实时的！** 直接从各平台 Dashboard 获取最新数据，本地数据库仅用于历史对比。
  
  **基本查询**（查余额、查 wc 余额、查鲸云余额、查基本余额、公司余额）：
  - 只查询 WhaleCloud Lab（鲸云实验室）的余额
  
  **全部查询**（查全部余额、查所有余额）：
  - 查询 WhaleCloud Lab、智谱 AI（Zhipu）、Moonshot（Kimi）全部平台的余额
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

## 前置条件

1. **启动 Chrome 调试模式**：
   ```bash
   python C:\Users\luzhe\.openclaw\skills\api-balance-checker\scripts\launch_chrome.py
   ```
   或手动启动：
   ```
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
   ```

2. **在 Chrome 中登录各平台**（需要先手动登录一次）：
   - WhaleCloud: https://lab.iwhalecloud.com/gpt-proxy/console/dashboard
   - 智谱 AI: https://open.bigmodel.cn/
   - Moonshot: https://platform.moonshot.cn/

## 使用方法

### 基本查询（仅 WhaleCloud Lab）

```bash
python C:\Users\luzhe\.openclaw\skills\api-balance-checker\scripts\query_balance.py whalecloud
```

或使用简化入口：
```bash
python C:\Users\luzhe\.openclaw\skills\api-balance-checker\scripts\query_basic.py
```

### 全部查询（全部平台）

```bash
python C:\Users\luzhe\.openclaw\skills\api-balance-checker\scripts\query_balance.py whalecloud zhipu moonshot
```

或使用简化入口：
```bash
python C:\Users\luzhe\.openclaw\skills\api-balance-checker\scripts\query_all.py
```

## 触发指令

- **基本查询**：`查余额`、`查 wc 余额`、`查鲸云余额`、`查基本余额`、`公司余额` → 只查询 WhaleCloud Lab
- **全部查询**：`查全部余额`、`查所有余额` → 查询全部平台（WhaleCloud + 智谱 AI + Moonshot）

## 注意事项

- Chrome 调试端口默认为 9222
- 首次使用需要先手动登录各平台
- 如果登录状态失效，需要重新手动登录
- 查询结果会保存到 `C:/Users/luzhe/Pictures/api_balances.json`
- **每次查询都是实时的，不会使用缓存**

