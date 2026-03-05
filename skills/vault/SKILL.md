# Vault - 密码箱技能

安全存储和查询各平台的账号、密码、API Key 等敏感信息。

## 触发命令

- `vault` / `密码箱` / `凭证` / `credentials`
- `查 [平台名] 的 [字段]` / `查看 [平台名] 的 [字段]` - 查询指定字段
- `保存 [平台名] 的 [字段]` - 保存凭据
- `查询 [平台名]` / `查看 [平台名]` - 查询凭据
- `列出所有平台` / `vault list` - 列出所有平台
- `更新 [平台名]` - 更新凭据
- `删除 [平台名]` - 删除凭据

## 使用示例

### 查询 GitHub Token
```
用户: 查github的token
助手: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 查询邮箱密码
```
用户: 查邮箱密码
助手: Luzh1103!（公司邮箱密码，默认）

用户: 查网易邮箱密码
助手: luz8853（网易邮箱密码）

用户: 查公司邮箱密码
助手: Luzh1103!（公司邮箱密码）
```

**注意**：`查邮箱密码` 默认查询**公司邮箱**密码，如需查询其他邮箱请指定平台名。

### 查询 API Key
```
用户: 查智谱的api_key
助手: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

用户: 查看moonshot的api_key
助手: sk-kimi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 列出所有平台
```
用户: 密码箱
助手: [显示所有已保存的平台列表]
```

## 敏感信息查询规范

**以下敏感信息必须通过密码箱查询，禁止直接存储在其他位置：**

| 敏感信息类型 | 示例 | 查询示例 |
|-------------|------|---------|
| **用户名** | Username, Account | `查github的username` |
| **密码** | Password, 登录密码 | `查github的password` |
| **邮箱密码** | 公司邮箱、网易邮箱 | `查邮箱密码`（默认公司邮箱）<br>`查网易邮箱密码`<br>`查公司邮箱密码` |
| **Token** | Access Token, Private Token | `查github的token` |
| **API Key** | API Key, Secret Key | `查智谱的api_key` |
| **身份证号** | 身份证、ID Card | `查个人信息的身份证` |
| **手机号** | 电话、手机 | `查个人信息的手机号` |
| **密钥** | Secret, Key | `查阿里云的access_key_secret` |
| **授权码** | Auth Code, 验证码 | `查飞书的app_secret` |

**注意**：
- 敏感字段（密码、密钥、token）使用 AES-256-GCM 加密存储
- 查询时只返回纯值，无引号、无套话、无格式符号
- 目的：便于直接复制使用

## 功能

- **保存凭据** - 安全存储平台账号信息（敏感字段自动加密）
- **查询凭据** - 按平台名称快速查找
- **列出平台** - 查看所有已保存的平台列表
- **更新凭据** - 修改已有凭据
- **删除凭据** - 删除指定平台的凭据

## 存储位置

- **数据文件**: `~/.openclaw/vault/credentials.json`
- **主密码**: 存储在 Windows 凭据管理器中（首次使用需手动添加）

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
