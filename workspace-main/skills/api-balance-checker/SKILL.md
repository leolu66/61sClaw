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

## 对比逻辑（重要！）

### 规则说明

1. **如果当天有查询记录**：
   - 时间间隔 = 本次查询时间 - 今天最后一次查询时间
   - 已使用差 = 本次已使用 - 今天最后一次已使用
   - 调用次数差 = 本次调用次数 - 今天最后一次调用次数

2. **如果是当天第一次查询**：
   - 时间间隔 = 当前时间 - 当天0点（即当前时间，比如 02:26 = 2小时26分钟）
   - 已使用差 = 本次已使用 - 0 = 本次已使用（当日累计）
   - 调用次数差 = 本次调用次数 - 0 = 本次调用次数（当日累计）

3. **如果是跨天查询（昨天有记录，今天没有）**：
   - 重置金额 = 当天已使用 + 剩余额度（如 ¥50 + ¥150 = ¥200）
   - 显示"基准重置"并计算重置后的变化
   - 其他平台：对比昨天最后的记录

### 输出规则

- **已使用** 和 **余额变化** 只显示一个（两者是此消彼长的关系，总额不变）
- 推荐显示：**已使用**（更直观反映消耗速度）

### 输出示例

**当天第N次查询**：
```
## 与上次对比
- **时间间隔**：15分钟前
- **已使用**：+8.29
- **调用次数**：+ 42 次
```

**当天首次查询**：
```
## 与上次对比
- **时间间隔**：2小时26分钟
- **提示**：当天首次查询，基准为0点
- **已使用**：+54.41
- **调用次数**：+ 392 次
```

**跨天查询（WhaleCloud）**：
```
## 与上次对比
- **时间间隔**：8小时前
- **基准重置**：¥200（已使用+剩余）
- **已使用**：+12.50
- **调用次数**：+ 150 次
```

## 输出规范

### JSON 数据结构（Python 脚本输出）

```json
{
  "platform": "WhaleCloud Lab",
  "platform_key": "whalecloud",
  "used": "59.29",
  "remaining": "140.71",
  "requests": "442",
  "date": "2026/03/03",
  "timestamp": "2026-03-03T14:00:00",
  "status": "success",
  "last_query": {
    "time_diff_minutes": 702,
    "used_diff": "13.17",
    "requests_diff": 92
  }
}
```

### 展示模板（大模型参考格式化）

```markdown
## 📊 API 余额查询结果

**平台：** {platform}
**查询时间：** {date} {time}
**状态：** {status_icon}

### 当前余额

| 指标 | 数值 |
|------|------|
| 已使用 | ¥{used} |
| 剩余额度 | ¥{remaining} |
| 调用次数 | {requests} 次 |

### 与上次对比

| 指标 | 变化 |
|------|------|
| 时间间隔 | {time_diff} |
| 已使用变化 | {used_diff} |
| 调用次数变化 | {requests_diff} 次 |
```

**状态图标：**
- `success` → ✅ 成功
- `error` → ❌ 失败
- `pending` → ⏳ 查询中
