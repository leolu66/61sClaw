# Skills 目录

本目录包含 **88+** 个核心 Agent 技能，用于扩展 AI 助手的能力。

> 娱乐技能请查看 `workspace-entertainment/skills/`

## 📊 技能分类统计

| 分类 | 数量 | 说明 |
|------|------|------|
| 信息查询 | 12 | 天气、新闻、搜索等 |
| 文件处理 | 10 | PDF、Excel、Word、图片、PPT等 |
| 系统控制 | 10 | 音频、桌面、VPN、TTS等 |
| 通信协作 | 7 | 邮件、飞书、腾讯会议、微信等 |
| 开发工具 | 12 | 代码统计、GitHub、测试、技能管理等 |
| PPT/演示 | 4 | HTML PPT 生成、PPTX 创建/转换 |
| 内容提取 | 3 | 网页抓取、视频转录、文档转换 |
| 游戏娱乐 | 0 | 已移至 workspace-entertainment |
| 自动化 | 12 | 定时器、自动点击、同步、备份等 |
| 设计/原型 | 1 | 高保真 HTML 设计/原型/动画 |
| 审计安全 | 1 | 技能规范检查、隐私安全扫描 |
| 深度研究 | 1 | 自动化深度研究报告 |
| 其他 | 15 | 笔记、发票、多代理协调等 |

---

## 🔍 常用技能速查

### 信息查询类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| weather-skill | "北京天气怎么样" | 查询实时天气和预报 |
| ai-news-fetcher | "获取AI新闻" | 获取AI行业最新资讯 |
| telecom-news-fetcher | "运营商新闻" | 获取运营商行业新闻 |
| brave-search | "Brave Search xxx" | 网页搜索（英文/国际） |
| baidu-search-1.1.2 | "搜索 xxx" | 百度搜索（国内优先） |
| volc-search | "火山搜索 xxx" | 火山引擎搜索 |
| api-balance-checker | "查余额" | 查询API平台余额 |
| holiday-checker | "节假日查询" | 查询节假日安排 |
| whalecloud-model-fetcher | "模型列表" | 获取鲸云可用模型列表 |

### 文件处理类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| pdf-extract | "提取PDF内容" | PDF文本提取 |
| excel-xlsx | "处理Excel" | Excel文件读写 |
| word-docx | "处理Word" | Word文件读写 |
| docx-to-markdown | "Word转Markdown" | DOCX文档转Markdown格式 |
| markitdown | "文档转Markdown" | PDF/Word/Excel/PPT/图片→Markdown（微软开源） |
| powerpoint-pptx | "处理PPT" | PowerPoint 创建/编辑/HTML→PPTX转换（v1.1.0） |
| imagemagick-cli | "图片处理" | 图片格式转换、裁剪、压缩等 |
| image-recognition | "识别图片" | 图像识别分析 |

### PPT / 演示类 🆕

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| html-ppt-skill | "做一份PPT" / "slides" | HTML PPT Studio — 36主题+31布局+47动效+演讲者模式 |
| guizang-ppt-skill | "杂志风PPT" | 电子杂志×电子墨水 WebGL HTML PPT |
| huashu-design | "做原型" / "设计Demo" | 高保真HTML设计/幻灯片/原型/动画+PPTX导出 |
| powerpoint-pptx | "生成PPTX" | 原生.pptx创建+HTML→PPTX转换（dom-to-pptx/iSpring/python-pptx） |

### 内容提取类 🆕

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| smart-web-fetcher | "提取网页内容" | 智能网页抓取（auto web_fetch/playwright）+图片本地化+尾部截断v3 |
| video-extractor | "提取视频内容" / "转文字" | 国产视频平台语音转录（yt-dlp+Whisper） |
| video-transcript-downloader | "下载视频字幕" | 下载视频字幕/转录 |

### 系统控制类

| 技能 | 触发方式 | 功能 |
|------|------|------|
| audio-control | "静音"/"音量调节" | 音频设备控制 |
| vpn-controller | "开启VPN"/"关闭VPN" | VPN控制（Clash for Windows） |
| mouseinfo-launcher | "启动mouseinfo" | 获取鼠标坐标和颜色 |
| playwright-1.0.3 | "浏览器自动化" | Playwright浏览器控制 |
| ngrok-manager | "管理ngrok" | Ngrok隧道管理 |
| edge-tts / elevenlabs-tts / windows-tts | "语音合成" | 文本转语音 |
| disk-cleaner | "清理C盘" | C盘空间清理分析 |

### 通信协作类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| exchange-email-reader | "读取邮件" | Exchange/Outlook邮件读取 |
| imap-email-reader | "IMAP邮件" | IMAP邮件读取 |
| imap-smtp-email | "发送邮件" | IMAP/SMTP邮件收发 |
| feishu-notifier | "/小飞 xxx" | 飞书消息推送 |
| tencent-meeting-mcp | "预定腾讯会议" | 腾讯会议管理 |
| wechat-article-fetcher | "获取公众号文章" | 微信公众号文章获取 |
| cross-device-msg | "跨设备消息" | 跨设备消息同步 |

### 开发工具类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| code-stats | "代码统计" | 统计技能和GitHub活跃度 |
| github-compliance-checker | "检查GitHub合规性" | 检查隐私文件上传合规 |
| validator-audit 🆕 | "验证审核" / "审计GitHub" | 技能规范+隐私安全+GitHub合规审计 |
| claude-code-sender | "发送Claude任务" | 向Claude Code发送任务 |
| skill-creator-local | "创建技能" | 创建新Skill（本地定制版） |
| skill-syncer | "获取xxx技能" | 从远程同步Skill |
| skill-finder-1.1.5 | "查找技能" | 查找可用Skill |
| foreign-skill-cleaner | "清理国外技能" | 批量移除不适合国内的技能 |
| auto-tester | "自动测试" | 自动化测试 |
| billing-analyzer | "分析账单" | 模型账单分析 |
| token-counter | "统计Token" | 计算文本Token数量 |

### 设计 / 原型类 🆕

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| huashu-design | "做原型" / "设计Demo" | 高保真HTML设计变体+UX评审+动画导出MP4/GIF |

### 审计安全类 🆕

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| validator-audit | "验证审核" / "审计GitHub" | 技能规范检查+隐私泄露扫描+GitHub合规审计 |

### 深度研究类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| deep-research | "深度研究 xxx" | 自动化深度研究报告生成 |

### 游戏娱乐类

> 已移至 `workspace-entertainment/skills/`

| 技能 | 位置 | 功能 |
|------|------|------|
| gobang-game | workspace-entertainment | 五子棋游戏 |
| solitaire-game | workspace-entertainment | 纸牌接龙游戏 |
| jhwg-auto | workspace-entertainment | 几何王国自动任务 |
| potplayer-music | workspace-entertainment | 音乐播放控制 |

### 自动化类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| timer-alarm | "设置15分钟闹钟" | 定时器和闹钟管理 |
| todo-manager | "添加待办" | 待办任务管理 |
| one-click-commit | "一键提交" | 整合日志、记忆、GitHub提交 |
| work-session-logger | "记录工作日志" | 工作会话日志记录 |
| log-migrator | "归档日志" | 日志归档和备份 |
| backup-manager | "备份管理" | 文件备份管理 |
| workspace-sync | "同步工作区" | 工作区同步 |
| qiniu-sync | "七牛同步" | 七牛云同步 |
| agent-browser-clawdbot-0.1.0 | "浏览器控制" | 浏览器自动化控制 |
| fol-login | "FOL登录" | FOL系统登录 |
| travel-invoice-fetcher | "获取差旅发票" | 差旅发票自动获取 |

### 其他工具类

| 技能 | 触发方式 | 功能 |
|------|---------|------|
| getnote | "记笔记" | Get笔记记录和查询 |
| netnotes | "网络笔记" | 网络笔记管理 |
| data-analysis | "数据分析" | 数据分析处理 |
| command-center | "命令中心" | 命令集中管理 |
| vault | "密码箱" | 敏感信息存储 |
| model-selector | "换模型" | 模型选择切换 |
| model-recommender | "推荐模型" | 模型推荐 |
| model-switcher | "切换模型" | 自动根据任务复杂度切换模型 |
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

## 🔒 GitHub 安全提醒

- `logs/` 和 `memory/` 已在 `.gitignore` 中排除，**禁止**用 `git add -f` 强制添加
- 提交前请确认无 API Key / Token / 密码泄露
- 使用 `validator-audit` 技能定期审计

---

*最后更新：2026-05-12 | 共 88+ 个核心技能 | 娱乐技能见 workspace-entertainment*
