# 基础技能清单（Base Skills Catalog）

**用途**：开发新技能前，先查看此清单，避免重复造轮子  
**更新日期**：2026-03-19  
**维护者**：小天才

---

## 🏗️ 分层模型

技能按功能分为三层，开发时应遵循分层设计原则：

| 层级 | 定义 | 特征 | 设计原则 |
|------|------|------|----------|
| **L1 基础设施层** | 系统级、公共性、基础性能力 | 被上层技能依赖，提供通用服务 | **必须复用**，禁止重复开发 |
| **L2 平台服务层** | 中间件、工具类、通用服务 | 封装特定领域能力，可复用 | **优先复用**，可扩展增强 |
| **L3 业务应用层** | 业务型、个性化、场景化能力 | 直接面向用户，解决具体问题 | 可个性化，但应依赖下层 |

### 分层设计原则

```
┌─────────────────────────────────────┐
│  L3 业务应用层 (Business Layer)      │  ← 直接面向用户，个性化业务逻辑
│  - travel-invoice-fetcher           │
│  - jhwg-auto                        │
│  - ai-news-fetcher                  │
├─────────────────────────────────────┤
│  L2 平台服务层 (Platform Layer)      │  ← 通用服务，可复用工具
│  - pdf-extract, excel-xlsx          │
│  - imap-email-reader, browser       │
│  - work-session-logger              │
├─────────────────────────────────────┤
│  L1 基础设施层 (Infrastructure)      │  ← 基础能力，必须复用
│  - vault (凭据管理)                  │
│  - desktop-control (系统控制)        │
│  - ngrok-manager (网络基础设施)      │
└─────────────────────────────────────┘
```

**核心原则**：
1. **下层不依赖上层** - L1 不能调用 L3
2. **上层可依赖下层** - L3 可以调用 L1、L2
3. **同层可组合** - L2 技能可以组合使用
4. **禁止平级重复** - 同一层相似功能应合并

---

## L1 基础设施层（必须复用）

> **原则**：这些技能提供基础能力，开发新技能时必须复用，禁止重复实现

| 技能名 | 功能 | 使用场景 | 层级 |
|--------|------|----------|------|
| **vault** | 凭据/密码统一管理 | 所有需要密码/Key的场景 | L1 |
| **desktop-control** | 系统级桌面控制 | 模拟键鼠、窗口操作 | L1 |
| **ngrok-manager** | 网络穿透基础设施 | 临时公网访问本地服务 | L1 |
| **cross-device-msg** | 跨设备通信基础设施 | 多设备消息传递 | L1 |

---

## L2 平台服务层（优先复用）

> **原则**：这些技能封装特定领域能力，开发时应优先复用，可在其基础上扩展

### 2.1 网络与通信服务

| 技能名 | 功能 | 使用场景 | 层级 |
|--------|------|----------|------|
| **browser** | 浏览器自动化（Playwright） | 网页访问、点击、表单填写 | L2 |
| **exchange-email-reader** | Exchange/Outlook 邮箱读取 | 公司邮件读取 | L2 |
| **imap-email-reader** | IMAP 邮箱通用读取 | QQ邮箱、Gmail等通用邮件读取 | L2 |
| **feishu-notifier** | 飞书消息推送服务 | 主动通知用户 | L2 |

### 2.2 文档处理服务

| 技能名 | 功能 | 使用场景 | 层级 |
|--------|------|----------|------|
| **pdf-extract** | PDF 文本提取服务 | 读取 PDF 内容、发票识别 | L2 |
| **excel-xlsx** | Excel 读写服务 | 生成报表、读取数据 | L2 |
| **word-docx** | Word 文档读写服务 | 生成文档、模板填充 | L2 |
| **powerpoint-pptx** | PPT 读写服务 | 生成演示文稿 | L2 |
| **video-transcript-downloader** | 视频字幕下载服务 | 下载 YouTube/B站字幕 | L2 |

### 2.3 认证与登录服务

| 技能名 | 功能 | 使用场景 | 层级 |
|--------|------|----------|------|
| **fol-login** | FOL 财务系统登录服务 | 公司报销系统登录 | L2 |
| **github-compliance-checker** | GitHub 合规检查服务 | 提交前检查敏感信息 | L2 |

### 2.4 日志与记录服务

| 技能名 | 功能 | 使用场景 | 层级 |
|--------|------|----------|------|
| **work-session-logger** | 工作日志记录服务 | 会话总结、记忆写入 | L2 |
| **log-migrator** | 日志归档备份服务 | 日志迁移、快速备份 | L2 |
| **one-click-commit** | 一键提交服务 | 整合日志+记忆+GitHub同步 | L2 |
| **self-improving-agent** | 自我改进记录服务 | 记录错误、学习、功能请求 | L2 |

### 2.5 自动化与工具服务

| 技能名 | 功能 | 使用场景 | 层级 |
|--------|------|----------|------|
| **claude-code-sender** | 子代理任务发送服务 | 向 Claude Code 发送任务 | L2 |
| **multi-agent-coordinator** | 多智能体协调服务 | 复杂任务调度 | L2 |
| **mouseinfo-launcher** | 鼠标坐标获取服务 | 获取屏幕坐标、取色 | L2 |
| **image-recognition** | 图像识别服务 | OCR、截图分析 | L2 |

### 2.6 搜索与信息获取服务

| 技能名 | 功能 | 使用场景 | 层级 |
|--------|------|----------|------|
| **baidu-search** | 百度搜索服务 | 中文搜索（默认首选） | L2 |
| **brave-search** | Brave 搜索服务 | 英文/国际搜索 | L2 |
| **volc-search** | 火山引擎搜索服务 | 融合搜索 | L2 |
| **weather-skill** | 天气查询服务 | 实时天气和预报 | L2 |

---

## L3 业务应用层（个性化业务）

> **原则**：直接面向用户，解决具体业务问题。应依赖 L1/L2 层，避免重复实现基础能力

### 3.1 信息聚合类

| 技能名 | 功能 | 依赖的L2服务 | 层级 |
|--------|------|--------------|------|
| **ai-news-fetcher** | AI 新闻获取 | baidu-search/brave-search | L3 |
| **telecom-news-fetcher** | 运营商新闻获取 | baidu-search | L3 |
| **wechat-article-fetcher** | 微信公众号文章获取 | browser | L3 |

### 3.2 办公效率类

| 技能名 | 功能 | 依赖的L2服务 | 层级 |
|--------|------|--------------|------|
| **todo-manager** | 任务管理 | work-session-logger | L3 |
| **timer-alarm** | 定时器和闹钟 | - | L3 |
| **holiday-checker** | 节假日查询 | - | L3 |
| **code-stats** | 代码统计 | - | L3 |

### 3.3 财务报销类

| 技能名 | 功能 | 依赖的L2服务 | 层级 |
|--------|------|--------------|------|
| **travel-invoice-fetcher** | 差旅发票抓取与报销 | fol-login, imap-email-reader, excel-xlsx | L3 |
| **billing-analyzer** | 账单分析 | excel-xlsx | L3 |
| **api-balance-checker** | API 余额查询 | browser | L3 |

### 3.4 游戏娱乐类

| 技能名 | 功能 | 依赖的L2服务 | 层级 |
|--------|------|--------------|------|
| **potplayer-music** | 音乐播放 | - | L3 |
| **gobang-game** | 五子棋游戏 | browser | L3 |
| **solitaire-game** | 纸牌接龙 | browser | L3 |
| **jhwg-auto** | 几何王国自动点击 | desktop-control, image-recognition | L3 |

### 3.5 系统工具类

| 技能名 | 功能 | 依赖的L2服务 | 层级 |
|--------|------|--------------|------|
| **vpn-controller** | VPN 控制 | desktop-control | L3 |
| **audio-control** | 音频设备控制 | desktop-control | L3 |
| **disk-cleaner** | C 盘清理 | - | L3 |
| **backup-manager** | 备份管理 | - | L3 |
| **model-selector** | 模型选择 | - | L3 |
| **model-switcher** | 模型自动切换 | - | L3 |

---

## 🎯 分层设计示例

### 示例 1：开发 travel-invoice-fetcher（L3 业务应用）

**正确设计**：
```
travel-invoice-fetcher (L3)
    ├── 依赖 fol-login (L2) → 登录 FOL 系统
    ├── 依赖 imap-email-reader (L2) → 读取发票邮件
    ├── 依赖 excel-xlsx (L2) → 生成报销单
    └── 依赖 vault (L1) → 获取邮箱密码
```

**错误设计**：
```
travel-invoice-fetcher (L3)
    ├── 自己实现邮箱登录 ❌
    ├── 自己实现 PDF 解析 ❌
    └── 自己实现 Excel 生成 ❌
```

### 示例 2：开发 ai-news-fetcher（L3 业务应用）

**正确设计**：
```
ai-news-fetcher (L3)
    ├── 依赖 baidu-search (L2) → 搜索新闻
    ├── 依赖 browser (L2) → 抓取网页内容
    └── 依赖 feishu-notifier (L2) → 推送结果
```

### 示例 3：扩展 pdf-extract（L2 平台服务）

**场景**：需要增加发票专用解析

**正确设计**：
```
pdf-extract (L2) ← 扩展新增发票解析模块
    └── 被 travel-invoice-fetcher (L3) 调用
```

**而不是**：
```
travel-invoice-fetcher (L3) 里自己实现发票解析 ❌
```

---

## 📝 使用示例

### 场景 1：开发一个"发票识别"技能

**不要**：重新实现 PDF 读取和 OCR
**应该**：
1. 查看 `pdf-extract` 技能如何提取 PDF 文本
2. 参考 `image-recognition` 的 OCR 实现
3. 使用 `excel-xlsx` 生成报表

### 场景 2：开发一个"自动报销"技能

**不要**：重新实现邮箱登录和 FOL 登录
**应该**：
1. 复用 `imap-email-reader` 读取发票邮件
2. 调用 `fol-login` 登录报销系统
3. 使用 `vault` 管理凭据

### 场景 3：开发一个"日报生成"技能

**不要**：重新实现日志写入和 GitHub 提交
**应该**：
1. 调用 `work-session-logger` 记录工作
2. 使用 `one-click-commit` 同步到 GitHub

---

## 🔄 维护说明

**新增技能时**：
1. 判断是否为"基础能力"
2. 更新此清单，添加到对应分类
3. 在 SKILL.md 中标注"可被其他技能引用"

**发现重复功能时**：
1. 标记待合并的技能
2. 逐步迁移到统一实现
3. 更新引用此技能的文档

---

## 📌 引用此文档

在 SKILL.md 中添加：
```markdown
## 依赖技能
- 复用 [pdf-extract](../pdf-extract/SKILL.md) 的 PDF 读取功能
- 参考 [excel-xlsx](../excel-xlsx/SKILL.md) 的 Excel 生成逻辑
```

---

**相关文档**：
- [SKILL_DO.md](./SKILL_DO.md) - 技能开发规范
- [SKILL_TEMPLATE.md](./SKILL_TEMPLATE.md) - 技能模板
