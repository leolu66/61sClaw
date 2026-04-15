---
name: imap-email-reader
description: 通过 IMAP 协议读取邮箱邮件，支持多账户配置、最新邮件获取和关键词搜索
---

# IMAP 邮箱读取器

## 需求说明（SRS）

### 触发条件
用户说什么话会触发此技能：
- "读取邮件"
- "查看邮箱"
- "imap 邮件"
- "获取最新邮件"
- "搜索邮件"

### 功能描述
通过 IMAP 协议读取邮箱邮件，支持以下功能：
1. 读取最新 N 封邮件
2. 按关键词搜索邮件
3. 支持多邮箱账户配置
4. 表格形式展示邮件列表（发件人、主题、日期）

### 输入/输出
- **输入**:
  - `--account`: 指定账户名称（可选，默认第一个账户）
  - `--limit`: 读取最新 N 封邮件（可选，默认 10）
  - `--search`: 搜索关键词（可选）
- **输出**: 表格形式展示邮件列表，包含发件人、主题、日期

### 依赖条件
- Python 3.6+
- 邮箱账户已开启 IMAP 服务
- 邮箱授权码已配置为环境变量
- 配置文件 `config.json` 已正确设置

### 边界情况
- 网络连接失败时提示错误
- 授权码错误时提示认证失败
- 邮箱为空时提示无邮件
- 搜索无结果时提示未找到匹配邮件

---

## 使用方法

### 基本用法

```bash
# 读取最新 10 封邮件（默认账户）
python scripts/imap_reader.py

# 读取最新 5 封邮件
python scripts/imap_reader.py --limit 5

# 指定账户读取邮件
python scripts/imap_reader.py --account "QQ邮箱"

# 搜索邮件
python scripts/imap_reader.py --search "工作"
```

### 配置说明

配置文件 `config.json`：

```json
{
  "accounts": [
    {
      "name": "QQ邮箱",
      "email": "your_email@qq.com",
      "env_key": "IMAP_QQ_AUTH_CODE",
      "imap_server": "imap.qq.com",
      "imap_port": 993,
      "ssl": true
    },
    {
      "name": "163邮箱",
      "email": "your_email@163.com",
      "env_key": "IMAP_163_AUTH_CODE",
      "imap_server": "imap.163.com",
      "imap_port": 993,
      "ssl": true
    },
    {
      "name": "126邮箱",
      "email": "your_email@126.com",
      "env_key": "IMAP_126_AUTH_CODE",
      "imap_server": "imap.126.com",
      "imap_port": 993,
      "ssl": true
    }
  ]
}
```

### 环境变量设置

在 Windows PowerShell 中：
```powershell
$env:IMAP_QQ_AUTH_CODE = "your_auth_code"
$env:IMAP_163_AUTH_CODE = "your_auth_code"
$env:IMAP_126_AUTH_CODE = "your_auth_code"
```

在 Linux/macOS 中：
```bash
export IMAP_QQ_AUTH_CODE="your_auth_code"
export IMAP_163_AUTH_CODE="your_auth_code"
export IMAP_126_AUTH_CODE="your_auth_code"
```

---

## 支持的邮箱

| 邮箱类型 | IMAP 服务器 | 端口 | SSL |
|---------|------------|------|-----|
| QQ邮箱 | imap.qq.com | 993 | 是 |
| 163邮箱 | imap.163.com | 993 | 是 |
| 126邮箱 | imap.126.com | 993 | 是 |
| Gmail | imap.gmail.com | 993 | 是 |
| Outlook | outlook.office365.com | 993 | 是 |

---

## 相关文件

- `scripts/imap_reader.py` - 主脚本
- `config.json` - 配置文件

---

## 注意事项

1. **授权码不是密码**：QQ/163/126 邮箱需要使用授权码，而非登录密码
2. **开启 IMAP 服务**：需要在邮箱设置中开启 IMAP/SMTP 服务
3. **环境变量**：敏感信息（授权码）通过环境变量传入，不要硬编码在配置文件中
4. **网络连接**：确保网络可以连接到邮箱服务器

---

## DoD 检查表

**开发日期**: 2026-03-15
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
- [x] 配置外置
- [x] 敏感信息通过环境变量
- [x] 无 .skill 文件

### 3. 测试通过
- [x] 功能测试通过
- [x] 触发测试通过
- [x] 边界测试通过

### 4. GitHub 同步
- [x] 已提交并推送
- [x] 无隐私文件泄露
- [x] 推送到 main 分支

**状态**: ✅ 完成
