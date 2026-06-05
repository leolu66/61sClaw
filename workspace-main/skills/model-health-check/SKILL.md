---
name: model-health-check
description: 检测 WhaleCloud 模型服务健康状态。对所有配置的 whalecloud provider 下的模型进行 API 可用性检查，返回响应时间和错误信息。当用户说"检查模型状态"、"模型健康检查"、"API 可用性"、"WhaleCloud 状态"时触发。
---

# Model Health Check

检测 WhaleCloud 模型服务的健康状态，包括 API 可用性和响应时间。

## 功能

- 自动读取 OpenClaw 配置中的 whalecloud provider
- 检测所有配置的模型（MiniMax、Doubao、Kimi、QWen、GLM、DeepSeek 等）
- 记录每个模型的响应时间（毫秒）
- 支持 Anthropic Messages API 和 OpenAI Completions API 格式
- 输出 JSON 格式的详细结果
- 统计正常/异常/跳过的模型数量

## 使用方法

### 直接运行脚本

```bash
python skills/model-health-check/scripts/health_check.py
```

### 通过 Agent 调用

在对话中说：
- "检查模型状态"
- "模型健康检查"
- "WhaleCloud 状态"
- "API 可用性检查"

Agent 会自动执行健康检查脚本并返回结果。

## 输出示例

```
=== 模型服务健康检查 (WhaleCloud) ===

🔍 Checking whalecloud (anthropic-messages) - 12 models...
   ✅ MiniMax M2.7: ok (1547ms)
   ✅ Doubao Seed 2.0 Pro: ok (2015ms)
   ❌ QWen 3.6 Plus: error (52ms)
   ...

=== 检查完成 ===

📊 统计: 总计 12 个模型
   ✅ 正常: 10
   ❌ 异常: 2
   ⚠️  跳过: 0
```

## 检测逻辑

1. **读取配置**：从 `~/.openclaw/openclaw.json` 读取 `models.providers.whalecloud`
2. **获取 API Key**：从配置文件或环境变量读取
3. **发送测试请求**：向每个模型发送最小化的 chat 请求
4. **记录结果**：状态码、响应时间、错误信息
5. **输出报告**：JSON 格式 + 人类可读的统计

## 故障排查

### API Key 未找到

如果提示 "API key not found"，检查：
- `openclaw.json` 中 `models.providers.whalecloud.apiKey` 是否配置
- 或设置环境变量 `WHALECLOUD_API_KEY`

### 模型返回 404

可能原因：
- 模型 ID 不正确
- WhaleCloud API 端点变更
- 模型已下线

### 超时或连接失败

- 检查网络连接
- 确认 WhaleCloud API 地址可达
- 查看是否有代理配置问题

## 资源文件

- `scripts/health_check.py` - 主检测脚本，可独立运行
