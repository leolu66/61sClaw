# Vault - 密码箱技能

安全存储和查询各平台的账号、密码、API Key 等敏感信息。

## 触发命令

- `vault` / `密码箱` / `凭证` / `credentials`
- `保存 [平台名] 的 [字段]` - 保存凭据
- `查询 [平台名]` / `查看 [平台名]` - 查询凭据
- `列出所有平台` / `vault list` - 列出所有平台
- `更新 [平台名]` - 更新凭据
- `删除 [平台名]` - 删除凭据

## 功能

- **保存凭据** - 安全存储平台账号信息（敏感字段自动加密）
- **查询凭据** - 按平台名称快速查找
- **列出平台** - 查看所有已保存的平台列表
- **更新凭据** - 修改已有凭据
- **删除凭据** - 删除指定平台的凭据

## 存储位置

- **数据文件**: `~/.openclaw/vault/credentials.json`
- **主密码**: `768211` (用于加密敏感字段)

## 预设平台

| 平台 | 分类 | 字段 |
|------|------|------|
| 智谱 AI | llm | api_key |
| Moonshot (Kimi) | llm | api_key |
| 火山引擎 | cloud | username, password, app_key, access_key_id, secret_access_key, account_id |
| WhaleCloud Lab | llm | api_key |
| 阿里云 | cloud | access_key_id, access_key_secret |
| 飞书 | api | app_id, app_secret, bot_token |
| GitHub | code | username, token |
| 七牛云 | cloud | access_key, secret_key, bucket |
| Brave Search | api | api_key |
| 和风天气 | api | api_key |

## 安全说明

- 敏感字段（密码、密钥、token）使用 AES-256-GCM 加密
- 主密码用于派生加密密钥
- 建议定期备份 `credentials.json` 文件
