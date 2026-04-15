# Vault - 密码箱技能

安全存储和查询各平台的账号、密码、API Key 等敏感信息。

## 触发命令

**关键词触发**（匹配任意一个即触发）：
- `vault` / `密码箱` / `凭证` / `credentials`
- `查` / `查看` / `查询` + `[平台名]`
- `查一下` + `[平台名]`
- `[平台名]` + `的密码` / `密码是多少`
- `[平台名]` + `的token` / `的Token` / `的API Key` / `的api_key`
- `保存` / `更新` / `删除` + `[平台名]`
- `列出所有平台` / `vault list`

### "密码箱"关键词触发分析

**触发场景**：
1. **单独使用** - 用户说"密码箱"时，列出所有已保存的平台列表
2. **组合使用** - "密码箱" + 动作/平台名，如：
   - "密码箱查一下github" → 查询 GitHub 凭据
   - "密码箱保存知乎" → 保存知乎账号
   - "密码箱列出所有" → 列出所有平台

**匹配规则**：
- 消息包含"密码箱"关键词
- 优先级：高于通用对话，低于明确技能调用
- 上下文：在任意对话上下文中均可触发

**示例匹配**：
- "查一下zmp的密码" ✅
- "查github的token" ✅
- "zmp密码是多少" ✅
- "查看moonshot的api_key" ✅
- "密码箱" → 列出所有平台 ✅
- "密码箱查知乎" → 查询知乎凭据 ✅

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

## 扩展指南：添加新平台

vault 技能使用**预设平台模板**机制，如需添加新平台（如知乎、Twitter 等），需按以下步骤操作：

### 步骤1：在 PLATFORM_TEMPLATES 中添加平台模板

编辑 `scripts/vault.py`，在 `PLATFORM_TEMPLATES` 字典中添加新平台：

```python
"zhihu": {
    "name": "知乎",
    "category": "website",  # 分类：llm/cloud/api/code/email/website/other
    "icon": "📚",  # Emoji 图标
    "fields": [
        {"key": "url", "label": "网址", "type": "url", "isSensitive": False, "isRequired": False},
        {"key": "username", "label": "用户名", "type": "text", "isSensitive": False, "isRequired": True},
        {"key": "password", "label": "密码", "type": "password", "isSensitive": True, "isRequired": True}
    ]
}
```

**字段类型说明**：
| 类型 | 说明 | 示例 |
|------|------|------|
| `text` | 普通文本 | 用户名、手机号 |
| `password` | 密码（加密存储） | 登录密码 |
| `token` | API Token（加密存储） | API Key、Access Token |
| `url` | URL 地址 | 网址、控制台地址 |
| `email` | 邮箱地址 | 邮箱账号 |

**isSensitive 标记**：
- `True`：敏感字段，使用 AES-256-GCM 加密存储
- `False`：普通字段，明文存储

### 步骤2：加密敏感字段

使用 vault 的加密功能对密码等敏感字段加密：

```bash
cd ~/.openclaw/workspace-main/skills/vault
python -c "
import sys
sys.path.insert(0, 'scripts')
from vault import Vault
vault = Vault()
encrypted = vault._encrypt_sensitive('你的密码')
print(encrypted)
"
```

### 步骤3：写入 credentials.json

按以下 JSON 结构添加到 `~/.openclaw/vault/credentials.json`：

```json
"zhihu": {
  "id": "uuid-随机生成",
  "slug": "zhihu",
  "name": "知乎",
  "category": "website",
  "icon": "📚",
  "fields": [
    {"key": "url", "label": "网址", "type": "url", "isSensitive": false, "isRequired": false, "value": "https://www.zhihu.com"},
    {"key": "username", "label": "用户名", "type": "text", "isSensitive": false, "isRequired": true, "value": "18651870622"},
    {"key": "password", "label": "密码", "type": "password", "isSensitive": true, "isRequired": true, "value": "加密后的密码字符串"}
  ],
  "tags": [],
  "notes": "",
  "createdAt": "2026-03-17T13:05:00.000000",
  "updatedAt": "2026-03-17T13:05:00.000000"
}
```

### 步骤4：验证

```bash
vault get zhihu
```

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
| **知乎** | **website** | **url, username, password** |

## 安全说明

- 敏感字段（密码、密钥、token）使用 AES-256-GCM 加密
- 主密码用于派生加密密钥
- 建议定期备份 `credentials.json` 文件
