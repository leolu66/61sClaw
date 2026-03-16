# 技能目录

本目录包含 52 个 OpenClaw 技能，按功能分类整理。

## 快速导航

- [AI/模型相关](#aimo-xing-xiang-guan) - 6 个
- [信息获取](#xin-xi-huo-qu) - 10 个
- [系统工具](#xi-tong-gong-ju) - 10 个
- [游戏娱乐](#you-xi-yu-le) - 4 个
- [工作流/自动化](#gong-zuo-liu-zi-dong-hua) - 11 个
- [其他](#qi-ta) - 7 个
- [技能开发/管理](#ji-neng-kai-fa-guan-li) - 4 个

---

## AI/模型相关

| 技能名 | 描述 | 触发词 |
|--------|------|--------|
| **api-balance-checker** | 查询 API 平台余额和用量 | `查余额`、`查全部余额` |
| **billing-analyzer** | 分析模型消费账单 | `分析账单` |
| **claude-code-sender** | 向 Claude Code 发送协同任务 | `发送claude任务` |
| **model-recommender** | 模型推荐 | - |
| **model-selector** | 交互式模型选择器 | `换模型`、`切换模型` |
| **model-switcher** | 自动切换快慢模型 | - |

## 信息获取

| 技能名 | 描述 | 触发词 |
|--------|------|--------|
| **ai-news-fetcher** | 获取 AI 科技新闻 | `获取AI新闻` |
| **brave-search** | 网页搜索 | `搜索 xxx` |
| **exchange-email-reader** | 读取 Exchange 邮件 | `查看邮件` |
| **imap-email-reader** | 读取 IMAP 邮箱 | `查看IMAP邮件` |
| **netnotes** | 互联网笔记本（网页收藏） | `收藏网页` |
| **telecom-news-fetcher** | 获取运营商新闻 | `获取运营商新闻` |
| **travel-invoice-fetcher** | 差旅发票抓取 | `抓取发票` |
| **volc-search** | 火山引擎搜索 | `火山搜索` |
| **weather-skill** | 查询天气 | `北京天气` |
| **wechat-article-fetcher** | 获取公众号文章 | `获取公众号文章` |

## 系统工具

| 技能名 | 描述 | 触发词 |
|--------|------|--------|
| **audio-control** | 音频设备控制 | `静音`、`取消静音` |
| **backup-manager** | 备份管理 | - |
| **disk-cleaner** | C 盘清理分析 | `清理C盘` |
| **github-compliance-checker** | GitHub 合规检查 | `检查GitHub` |
| **holiday-checker** | 节假日查询 | `查假期` |
| **mouseinfo-launcher** | 鼠标坐标取色工具 | `启动mouseinfo` |
| **ngrok-manager** | Ngrok 隧道管理 | `启动ngrok` |
| **potplayer-music** | PotPlayer 音乐播放 | `播放音乐` |
| **vpn-controller** | VPN 控制 | `开启VPN` |
| **vault** | 密码管理 | - |

## 游戏娱乐

| 技能名 | 描述 | 触发词 |
|--------|------|--------|
| **game-auto-clicker** | 游戏自动点击 | - |
| **gobang-game** | 五子棋游戏 | `玩五子棋` |
| **jhwg-auto** | 几何王国自动任务 | `代玩几何王国` |
| **solitaire-game** | 纸牌接龙 | `玩纸牌` |

## 工作流/自动化

| 技能名 | 描述 | 触发词 |
|--------|------|--------|
| **auto-tester** | 自动化测试 | - |
| **code-stats** | 代码统计 | `代码统计` |
| **cross-device-msg** | 跨设备消息 | - |
| **feishu-notifier** | 飞书消息推送 | `/小飞 xxx` |
| **fol-login** | FOL 财务系统登录 | `登录FOL` |
| **image-recognition** | 图像识别 | `识别图片` |
| **log-migrator** | 日志归档备份 | - |
| **multi-agent-coordinator** | 多智能体协调器 | - |
| **one-click-commit** | 一键提交 | `提交`、`一键提交` |
| **timer-alarm** | 定时器和闹钟 | `设置闹钟` |
| **work-session-logger** | 工作日志记录 | `记录工作日志` |

## 其他

| 技能名 | 描述 | 触发词 |
|--------|------|--------|
| **ai-news-fetcher-old** | AI 新闻获取（旧版备份） | - |
| **qiniu-sync** | 七牛云同步 | - |
| **skill-pusher** | 技能推送 | `推送技能` |
| **skill-syncer** | 技能同步 | `获取xxx技能` |
| **todo-manager** | 待办管理 | `查看待办` |
| **workspace-sync** | 工作区同步 | - |
| **youtube-bestpartners** | YouTube 工具 | - |

---

## 技能开发/管理

| 技能名 | 描述 | 触发词 |
|--------|------|--------|
| **skill-creator-local** | 本地技能创建工具 | `创建技能` |
| **logs** | 日志管理 | - |

---

## 技能开发规范

每个技能目录结构：

```
skill-name/
├── SKILL.md          # 技能说明文档（必须）
├── scripts/          # 脚本文件
├── references/       # 参考资料
├── assets/           # 静态资源
└── data/             # 运行时数据（可选）
```

---

*最后更新：2026-03-16 | 共 52 个技能*
