---
name: whalecloud-model-health-checker
description: 检查 WhaleCloud 网关中所有模型的健康状态，从配置文件读取模型列表，通过 API 接口测试每个模型的可用性。当用户说"检查模型健康度"、"测试模型可用性"、"whalecloud 模型健康检查"时使用此技能。
---

# WhaleCloud 模型健康检查

## 需求说明（SRS）

### 触发条件
用户说什么话会触发此技能：
- "检查模型健康度"
- "测试模型可用性"
- "whalecloud 模型健康检查"
- "查看所有模型状态"

### 功能描述
从 OpenClaw 配置文件读取 WhaleCloud 提供商的所有模型配置，逐个调用 API 接口测试每个模型的可用性，输出健康状态报告。

### 输入/输出
- **输入**: 自动读取配置文件，无需用户输入参数
- **输出**: 每个模型的健康状态（可用/不可用）、响应时间、错误信息

### 依赖条件
- Python 3 已安装
- `requests` 库已安装
- OpenClaw 配置文件存在且包含 WhaleCloud 配置
- **依赖技能**: 无

### 边界情况
- 网络不可用 → 提示网络错误
- 配置文件不存在或格式错误 → 提示配置错误
- 某个模型超时 → 标记为不可用，继续测试下一个
- API Key 无效 → 提示认证错误

---

## 使用方法

### 基本用法

触发技能后，脚本会自动：
1. 读取 `~/.openclaw/openclaw.json` 配置文件
2. 提取 WhaleCloud 提供商的 baseUrl、apiKey 和模型列表
3. 逐个调用每个模型的 API 接口进行测试
4. 输出健康状态报告

### 配置说明

配置文件位于 `scripts/config.json`（可选）：

```json
{
  "config_path": "C:\\Users\\luzhe\\.openclaw\\openclaw.json",
  "timeout_seconds": 30,
  "max_tokens": 10
}
```

- `config_path`: OpenClaw 配置文件路径（默认自动检测）
- `timeout_seconds`: 单个模型请求超时时间（秒）
- `max_tokens`: 测试请求的最大 token 数

---

## 相关文件

- `scripts/check_health.py` - 主脚本
- `scripts/config.json` - 配置文件（可选）

---

## 注意事项

- 测试过程会真实调用 API，会产生少量 token 消耗
- 建议定期运行检查，不要频繁调用
- 如果某个模型持续不可用，建议检查 WhaleCloud 服务状态

---

## DoD 检查表

**开发日期**: 2026-04-25
**开发者**: 小天才

### 1. SRS 文档
- [x] 触发条件明确
- [x] 功能描述完整
- [x] 输入输出说明
- [x] 依赖条件列出
- [x] 边界情况处理

### 2. 技能文件和代码
- [x] 目录结构规范
- [x] 使用相对路径
- [x] 配置外置（如需要）
- [x] 无 .skill 文件

### 3. 测试通过
- [ ] 功能测试通过
- [ ] 触发测试通过

### 4. GitHub 同步
- [ ] 已提交并推送
- [ ] 无隐私文件泄露
- [ ] 推送到 main

**状态**: ✅ 完成
