# Skills 目录

本目录包含 **70+** 个 Agent 技能，用于扩展 AI 助手的能力。

## 📊 技能分类统计

| 分类 | 数量 | 说明 |
|------|------|------|
| 信息查询 | 12 | 天气、新闻、搜索等 |
| 文件处理 | 8 | PDF、Excel、Word、PPT 等 |
| 系统控制 | 8 | 音频、桌面、VPN 等 |
| 通信协作 | 6 | 邮件、飞书、微信等 |
| 开发工具 | 10 | 代码统计、GitHub、测试等 |
| 游戏娱乐 | 4 | 五子棋、纸牌等 |
| 自动化 | 12 | 定时器、自动点击、同步等 |
| 其他 | 10 | 笔记、发票、视频等 |

---

## 🔍 常用技能速查

### 信息查询类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| weather-skill | "北京天气怎么样" | 查询实时天气和预报 |
| ai-news-fetcher | "获取AI新闻" | 获取AI行业最新资讯 |
| telecom-news-fetcher | "运营商新闻" | 获取运营商行业新闻 |
| brave-search | "Brave Search xxx" | 网页搜索 |
| baidu-search | "搜索 xxx" | 百度搜索 |
| volc-search | "火山搜索 xxx" | 火山引擎搜索 |
| api-balance-checker | "查余额" | 查询API平台余额 |
| holiday-checker | "节假日查询" | 查询节假日安排 |

### 文件处理类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| pdf-extract | "提取PDF内容" | PDF文本提取 |
| excel-xlsx | "处理Excel" | Excel文件读写 |
| word-docx | "处理Word" | Word文件读写 |
| powerpoint-pptx | "处理PPT" | PowerPoint文件读写 |
| video-transcript-downloader | "下载视频字幕" | 下载视频字幕/转录 |
| image-recognition | "识别图片" | 图像识别分析 |

### 系统控制类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| audio-control | "静音"/"音量调节" | 音频设备控制 |
| desktop-control | "桌面控制" | 桌面操作控制 |
| vpn-controller | "开启VPN"/"关闭VPN" | VPN控制 |
| potplayer-music | "播放音乐" | PotPlayer音乐播放 |
| mouseinfo-launcher | "启动mouseinfo" | 获取鼠标坐标和颜色 |
| playwright-1.0.3 | "浏览器自动化" | Playwright浏览器控制 |
| ngrok-manager | "管理ngrok" | Ngrok隧道管理 |
| sonoscli | "控制Sonos" | Sonos音响控制 |

### 通信协作类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| exchange-email-reader | "读取邮件" | Exchange/Outlook邮件读取 |
| imap-email-reader | "IMAP邮件" | IMAP邮件读取 |
| imap-smtp-email | "发送邮件" | IMAP/SMTP邮件收发 |
| feishu-notifier | "/小飞 xxx" | 飞书消息推送 |
| wechat-article-fetcher | "获取公众号文章" | 微信公众号文章获取 |
| cross-device-msg | "跨设备消息" | 跨设备消息同步 |

### 开发工具类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| code-stats | "代码统计" | 统计技能和GitHub活跃度 |
| github-compliance-checker | "检查GitHub合规性" | 检查隐私文件上传合规 |
| claude-code-sender | "发送Claude任务" | 向Claude Code发送任务 |
| skill-creator-local | "创建技能" | 创建新Skill |
| skill-pusher | "推送技能" | 推送Skill到目标Agent |
| skill-syncer | "获取技能" | 从远程同步Skill |
| skill-finder | "查找技能" | 查找可用Skill |
| auto-tester | "自动测试" | 自动化测试 |
| billing-analyzer | "分析账单" | 模型账单分析 |
| ontology-1.0.4 | "本体管理" | 本体/知识图谱管理 |

### 游戏娱乐类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| gobang-game | "玩五子棋" | 五子棋游戏 |
| solitaire-game | "玩纸牌" | 纸牌接龙游戏 |
| game-auto-clicker | "自动点击" | 游戏自动点击 |
| jhwg-auto | "代玩几何王国" | 几何王国自动任务 |

### 自动化类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| timer-alarm | "设置闹钟" | 定时器和闹钟管理 |
| todo-manager | "待办管理" | 待办任务管理 |
| one-click-commit | "一键提交" | 整合日志、记忆、GitHub提交 |
| work-session-logger | "记录工作日志" | 工作会话日志记录 |
| log-migrator | "归档日志" | 日志归档和备份 |
| backup-manager | "备份管理" | 文件备份管理 |
| workspace-sync | "同步工作区" | 工作区同步 |
| qiniu-sync | "七牛同步" | 七牛云同步 |
| disk-cleaner | "清理C盘" | C盘空间清理分析 |
| agent-browser-clawdbot-0.1.0 | "浏览器控制" | 浏览器自动化控制 |
| fol-login | "FOL登录" | FOL系统登录 |
| travel-invoice-fetcher | "获取差旅发票" | 差旅发票获取 |

### 其他工具类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| getnote | "记笔记" | Get笔记记录和查询 |
| netnotes | "网络笔记" | 网络笔记管理 |
| summarize | "总结文本" | 文本摘要生成 |
| data-analysis | "数据分析" | 数据分析处理 |
| command-center | "命令中心" | 命令集中管理 |
| vault | "密码箱" | 敏感信息存储 |
| model-selector | "换模型" | 模型选择切换 |
| model-recommender | "推荐模型" | 模型推荐 |
| model-switcher | "切换模型" | 自动模型切换 |
| multi-agent-coordinator | "多代理协调" | 多Agent任务协调 |

### 自我改进类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| self-improving-agent | "记录学习" | 学习记录和错误修正（旧版） |
| self-improving-proactive | "自我反思" | 主动自我改进（新版） |

---

## 🛠 技能管理

### 推送技能

```bash
# 批量推送所有技能
python skills/skill-pusher/scripts/push_skill.py
```

### 技能分类配置

`skills/skill-pusher/skill-categories.json`

---

## 📝 开发规范

- `SKILL_DO.md` - 技能开发规范
- `SKILL_TEMPLATE.md` - 技能模板

---

*最后更新：2026-03-18 | 共 70+ 个技能*
