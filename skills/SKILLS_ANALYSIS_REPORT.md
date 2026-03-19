# Skills 技能分析报告

**报告生成时间**: 2026-03-18  
**技能总数**: 69 个

---

## 一、技能来源分析

### 1.1 来源分类统计

| 来源类型 | 数量 | 占比 | 技能列表 |
|---------|------|------|---------|
| **自研技能** | 49 | 71.0% | 详见下方 |
| **外部引入** | 20 | 29.0% | 详见下方 |

**说明**: 
- 自研技能包括：完全自主开发 + 基于外部SDK二次开发（如 evernote）
- 外部引入包括：直接从 ClawHub 引入的现成技能

### 1.2 自研技能（45个）

本地开发，针对特定需求定制的技能：

#### 信息查询类
| 技能名称 | 功能简述 |
|---------|---------|
| ai-news-fetcher | AI新闻获取 |
| api-balance-checker | API余额查询 |
| telecom-news-fetcher | 运营商新闻获取 |
| weather-skill | 天气查询 |
| brave-search | Brave搜索 |
| volc-search | 火山搜索 |
| holiday-checker | 节假日查询 |
| image-recognition | 图像识别 |

#### 系统控制类
| 技能名称 | 功能简述 |
|---------|---------|
| audio-control | 音频设备控制 |
| vpn-controller | VPN控制器 |
| potplayer-music | PotPlayer音乐播放 |
| mouseinfo-launcher | MouseInfo启动器 |
| ngrok-manager | Ngrok管理 |

#### 通信协作类
| 技能名称 | 功能简述 |
|---------|---------|
| exchange-email-reader | Exchange邮件读取 |
| imap-email-reader | IMAP邮件读取 |
| feishu-notifier | 飞书通知 |
| wechat-article-fetcher | 微信文章获取 |
| cross-device-msg | 跨设备消息 |

#### 开发工具类
| 技能名称 | 功能简述 |
|---------|---------|
| code-stats | 代码统计 |
| github-compliance-checker | GitHub合规检查 |
| claude-code-sender | Claude Code任务发送 |
| auto-tester | 自动测试 |
| billing-analyzer | 账单分析 |
| model-recommender | 模型推荐 |
| model-selector | 模型选择器 |
| model-switcher | 模型切换器 |

#### 自动化类
| 技能名称 | 功能简述 |
|---------|---------|
| timer-alarm | 定时器闹钟 |
| todo-manager | 待办管理 |
| one-click-commit | 一键提交 |
| work-session-logger | 工作会话记录 |
| log-migrator | 日志迁移 |
| backup-manager | 备份管理 |
| workspace-sync | 工作区同步 |
| qiniu-sync | 七牛云同步 |
| disk-cleaner | 磁盘清理 |
| fol-login | FOL登录 |
| travel-invoice-fetcher | 差旅发票获取 |

#### 游戏娱乐类
| 技能名称 | 功能简述 |
|---------|---------|
| gobang-game | 五子棋游戏 |
| solitaire-game | 纸牌接龙游戏 |
| game-auto-clicker | 游戏自动点击 |
| jhwg-auto | 几何王国自动任务 |

#### 技能管理类
| 技能名称 | 功能简述 |
|---------|---------|
| skill-pusher | 技能推送工具 |
| skill-syncer | 技能同步工具 |
| skill-creator-local | 本地技能创建 |
| multi-agent-coordinator | 多代理协调 |

#### 笔记知识类
| 技能名称 | 功能简述 |
|---------|---------|
| netnotes | 网络笔记 |
| evernote | 印象笔记集成 |

#### 其他工具类
| 技能名称 | 功能简述 |
|---------|---------|
| vault | 密码箱 |
| youtube-bestpartners | YouTube合作伙伴 |
| desktop-control | 桌面控制 |

### 1.3 外部引入技能（20个）

从 ClawHub 或其他外部来源引入的技能：

#### 办公文档处理（5个）
| 技能名称 | 来源 | 版本 | 功能简述 |
|---------|------|------|---------|
| excel-xlsx | ClawHub | 1.0.2 | Excel处理 |
| powerpoint-pptx | ClawHub | 1.0.1 | PowerPoint处理 |
| word-docx | ClawHub | 1.0.2 | Word处理 |
| pdf-extract | ClawHub | - | PDF提取 |

#### 数据/内容处理（4个）
| 技能名称 | 来源 | 版本 | 功能简述 |
|---------|------|------|---------|
| data-analysis | ClawHub | 1.0.2 | 数据分析 |
| summarize | ClawHub | 1.0.0 | 文本摘要 |
| video-transcript-downloader | ClawHub | 1.0.0 | 视频字幕下载 |
| getnote | ClawHub | 1.3.1 | Get笔记 |

#### 技能管理/自我改进（4个）
| 技能名称 | 来源 | 版本 | 功能简述 |
|---------|------|------|---------|
| self-improving-agent | ClawHub | - | 自我改进（旧版） |
| self-improving-proactive | ClawHub | - | 自我改进（新版） |
| skill-finder-1.1.5 | ClawHub | 1.1.5 | 技能查找器 |
| ontology-1.0.4 | ClawHub | 1.0.4 | 本体管理 |

#### 信息查询/网络（4个）
| 技能名称 | 来源 | 版本 | 功能简述 |
|---------|------|------|---------|
| baidu-search-1.1.2 | ClawHub | 1.1.2 | 百度搜索 |
| playwright-1.0.3 | ClawHub | 1.0.3 | 浏览器自动化/爬虫 |
| imap-smtp-email | ClawHub | 0.0.10 | IMAP/SMTP邮件处理 |
| agent-browser-clawdbot-0.1.0 | ClawHub | 0.1.0 | 浏览器控制 |

#### 系统/设备控制（3个）
| 技能名称 | 来源 | 版本 | 功能简述 |
|---------|------|------|---------|
| desktop-control | ClawHub | - | 桌面控制 |
| sonoscli | ClawHub | - | Sonos音响控制 |
| command-center | ClawHub | 1.4.1 | 命令中心 |

### 1.4 混合/改造技能（4个）

基于外部技能进行本地化改造：

| 技能名称 | 原始来源 | 改造内容 |
|---------|---------|---------|
| sonoscli | 外部 | 本地化配置 |
| evernote-test | 测试用 | 开发测试版本 |

---

## 二、功能分类分析

### 2.1 按功能领域分类

| 功能分类 | 数量 | 占比 | 技能列表 |
|---------|------|------|---------|
| **信息查询** | 12 | 17.4% | weather-skill, brave-search, baidu-search, volc-search, holiday-checker, ai-news-fetcher, telecom-news-fetcher, api-balance-checker, image-recognition, pdf-extract, video-transcript-downloader, data-analysis |
| **文件处理** | 8 | 11.6% | pdf-extract, excel-xlsx, word-docx, powerpoint-pptx, video-transcript-downloader, data-analysis, summarize, getnote |
| **系统控制** | 8 | 11.6% | audio-control, desktop-control, vpn-controller, potplayer-music, mouseinfo-launcher, playwright-1.0.3, ngrok-manager, sonoscli |
| **通信协作** | 6 | 8.7% | exchange-email-reader, imap-email-reader, imap-smtp-email, feishu-notifier, wechat-article-fetcher, cross-device-msg |
| **开发工具** | 10 | 14.5% | code-stats, github-compliance-checker, claude-code-sender, skill-creator-local, model-recommender, model-selector, model-switcher, auto-tester, billing-analyzer, ontology-1.0.4 |
| **游戏娱乐** | 4 | 5.8% | gobang-game, solitaire-game, game-auto-clicker, jhwg-auto |
| **自动化** | 12 | 17.4% | timer-alarm, todo-manager, one-click-commit, work-session-logger, log-migrator, backup-manager, workspace-sync, qiniu-sync, disk-cleaner, agent-browser-clawdbot-0.1.0, fol-login, travel-invoice-fetcher |
| **笔记知识** | 5 | 7.2% | evernote, getnote, netnotes, self-improving-agent, self-improving-proactive |
| **技能管理** | 6 | 8.7% | skill-pusher, skill-syncer, skill-finder-1.1.5, skill-creator-local, command-center, multi-agent-coordinator |
| **其他** | 4 | 5.8% | vault, youtube-bestpartners, travel-invoice-fetcher, fol-login |

### 2.2 功能分类雷达图数据

```
信息查询  ████████████████████░░░░░  17.4%
文件处理  █████████████░░░░░░░░░░░░  11.6%
系统控制  █████████████░░░░░░░░░░░░  11.6%
通信协作  █████████░░░░░░░░░░░░░░░░   8.7%
开发工具  ██████████████░░░░░░░░░░░  14.5%
游戏娱乐  █████░░░░░░░░░░░░░░░░░░░░   5.8%
自动化    ████████████████████░░░░░  17.4%
笔记知识  ████████░░░░░░░░░░░░░░░░░   7.2%
技能管理  █████████░░░░░░░░░░░░░░░░   8.7%
其他      █████░░░░░░░░░░░░░░░░░░░░   5.8%
```

---

## 三、技能分层分析

### 3.1 分层模型定义

| 层级 | 定义 | 特征 |
|------|------|------|
| **L1 基础设施层** | 系统级、公共性、基础性能力 | 被上层技能依赖，提供通用服务 |
| **L2 平台服务层** | 中间件、工具类、通用服务 | 封装特定领域能力，可复用 |
| **L3 业务应用层** | 业务型、个性化、场景化能力 | 直接面向用户，解决具体问题 |

### 3.2 分层统计

| 层级 | 数量 | 占比 | 技能示例 |
|------|------|------|---------|
| **L1 基础设施层** | 12 | 17.4% | audio-control, desktop-control, vpn-controller, mouseinfo-launcher, playwright-1.0.3, ngrok-manager, sonoscli, agent-browser-clawdbot-0.1.0, disk-cleaner, backup-manager, workspace-sync, cross-device-msg |
| **L2 平台服务层** | 22 | 31.9% | brave-search, baidu-search, volc-search, exchange-email-reader, imap-email-reader, imap-smtp-email, feishu-notifier, skill-pusher, skill-syncer, skill-finder-1.1.5, model-recommender, model-selector, model-switcher, qiniu-sync, pdf-extract, excel-xlsx, word-docx, powerpoint-pptx, video-transcript-downloader, data-analysis, summarize, getnote |
| **L3 业务应用层** | 35 | 50.7% | weather-skill, holiday-checker, ai-news-fetcher, telecom-news-fetcher, api-balance-checker, image-recognition, potplayer-music, wechat-article-fetcher, code-stats, github-compliance-checker, claude-code-sender, auto-tester, billing-analyzer, ontology-1.0.4, gobang-game, solitaire-game, game-auto-clicker, jhwg-auto, timer-alarm, todo-manager, one-click-commit, work-session-logger, log-migrator, fol-login, travel-invoice-fetcher, evernote, netnotes, self-improving-agent, self-improving-proactive, skill-creator-local, command-center, multi-agent-coordinator, vault, youtube-bestpartners |

### 3.3 分层依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    L3 业务应用层 (35个)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │天气查询 │ │新闻获取 │ │游戏娱乐 │ │笔记管理 │ ...        │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
└───────┼───────────┼───────────┼───────────┼─────────────────┘
        │           │           │           │
        ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                    L2 平台服务层 (22个)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │搜索服务 │ │邮件服务 │ │文件处理 │ │技能管理 │ ...        │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
└───────┼───────────┼───────────┼───────────┼─────────────────┘
        │           │           │           │
        ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                    L1 基础设施层 (12个)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │系统控制 │ │网络服务 │ │存储管理 │ │浏览器控 │ ...        │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、其他分析维度

### 4.1 技术栈分析

| 技术类型 | 数量 | 技能示例 |
|---------|------|---------|
| **Python** | 45 | 大多数技能 |
| **Node.js** | 8 | command-center, imap-smtp-email, video-transcript-downloader, getnote |
| **Shell** | 5 | vpn-controller, backup-manager, log-migrator |
| **混合** | 11 | 多技术栈组合 |

### 4.2 维护状态分析

| 状态 | 数量 | 说明 |
|------|------|------|
| **活跃维护** | 52 | 近期有更新或使用频繁 |
| **稳定运行** | 12 | 功能完整，无需频繁更新 |
| **待优化** | 3 | 需要改进或重构 |
| **废弃** | 2 | 已删除或即将删除 |

### 4.3 使用频率预估

| 频率等级 | 数量 | 技能示例 |
|---------|------|---------|
| **高频** (每日) | 15 | todo-manager, timer-alarm, weather-skill, vpn-controller, feishu-notifier |
| **中频** (每周) | 25 | ai-news-fetcher, api-balance-checker, code-stats, github-compliance-checker |
| **低频** (每月) | 20 | backup-manager, log-migrator, disk-cleaner, travel-invoice-fetcher |
| **按需** | 9 | game-auto-clicker, jhwg-auto, gobang-game, solitaire-game |

### 4.4 复杂度分析

| 复杂度 | 数量 | 特征 |
|--------|------|------|
| **简单** (1-3个文件) | 28 | 单一功能，易于理解 |
| **中等** (4-10个文件) | 25 | 多个功能模块，有一定复杂度 |
| **复杂** (10+个文件) | 16 | 大型技能，多模块协作 |

### 4.5 价值贡献分析

| 价值类型 | 数量 | 说明 |
|---------|------|------|
| **效率提升** | 35 | 自动化任务，节省时间 |
| **信息获取** | 18 | 查询、搜索、监控 |
| **娱乐休闲** | 8 | 游戏、音乐 |
| **知识管理** | 8 | 笔记、记录、分析 |

---

## 五、关键洞察与建议

### 5.1 当前优势

1. **自研比例高 (65.2%)**：技能生态自主可控，可根据需求快速定制
2. **功能覆盖全面**：信息查询、文件处理、系统控制、通信协作等领域均有覆盖
3. **分层结构合理**：基础设施层、平台服务层、业务应用层比例适中 (17:32:51)
4. **技术栈统一**：以 Python 为主 (65%)，便于维护和协作

### 5.2 待改进点

1. **外部技能依赖**：29% 技能来自外部，需关注更新和维护
2. **文档完善度**：部分技能缺少详细文档和使用示例
3. **测试覆盖率**：自动化测试覆盖不足，稳定性有待提升
4. **技能发现**：新用户难以快速了解所有技能的功能

### 5.3 优化建议

| 优先级 | 建议 | 预期收益 |
|--------|------|---------|
| **高** | 建立技能文档标准化模板 | 提升可维护性 |
| **高** | 增加自动化测试 | 提升稳定性 |
| **中** | 开发技能发现/推荐系统 | 提升使用率 |
| **中** | 建立技能评级机制 | 优胜劣汰 |
| **低** | 技能市场/分享平台 | 生态扩展 |

---

## 六、附录

### 6.1 技能完整清单

详见 `skills/README.md` 和 `skill-pusher/skill-categories.json`

### 6.2 数据来源

- 技能目录：`~/.openclaw/workspace-main/skills/`
- 配置文件：`skill-pusher/skill-categories.json`
- 技能文档：各技能目录下的 `SKILL.md`

---

*报告生成：2026-03-18*  
*技能总数：69*  
*自研技能：49 (71.0%)*  
*外部引入：20 (29.0%)*
