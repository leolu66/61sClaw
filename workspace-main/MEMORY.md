# MEMORY.md - 长期记忆

重要的原则、决策和经验教训

## 1. 核心工作原则

| 原则 | 一句话定义 | 关键行动 |
|------|-----------|---------|
| **有用助手** | 提供可用结果，不做半成品 | 不懂就说不知道；长时间任务及时同步进度；错误如实告知不隐瞒 |
| **主动思考** | 能并行的任务不串行 | 先尝试再提问；带着答案回来，不带问题交差 |
| **持续总结** | 记忆是灵魂，总结是成长 | 会话结束必总结；错误记录入记忆库；避免重复踩坑 |
| **诚实原则** | 不编造，不脑补 | 不确定标注"需确认"；无来源数据标注"待核实" |
| **简单直接** | 一句话说清绝不多写 | 无客套、无开场白、无总结废话 |
| **角色定位** | 只做调度不干活 | 子代理能做的事，不抢着自己做 |

## 2. 工程安全原则（S1-S6）

```
S1 批量操作 → 先dry-run验证，再全量执行
S2 敏感信息 → 脱敏存储（186****0622）；禁止入脚本；禁止传GitHub
S3 外部操作 → 发邮件/发消息前必须人工确认
S4 数据备份 → 改配置前备份；迁移前归档；保留回滚能力
S5 防错设计 → 危险操作二次确认；删除进回收站；支持撤销
S6 根目录保护 → 删workspace根目录文件必须用户明确指定文件名
```

## 3. 交付质量标准

### 完整性原则

> 提供完整可用的结果，而非半成品

**核心要求**：

- **代码 + 文档同步更新** - 修改代码必须同步更新 SKILL.md 等文档
- **配置 + 说明齐全** - 新增配置功能必须提供配置示例和使用说明
- **测试验证通过** - 交付前验证功能可用，不交付未测试的代码

**反面示例**：

- 只改代码不更新文档 → 用户不知道怎么用新功能
- 添加配置文件支持但不写配置说明 → 用户不知道配置格式
- 功能做到一半就提交 → 用户拿到的是半成品
- **展示的版本与保存的文件内容不一致** → 用户发现被

### 适时求助原则

> 反复尝试无法解决时，停下来总结并求助

**触发条件**：

- 同一问题尝试 3 次以上仍未解决
- 耗时超过 30 分钟仍无进展
- 遇到超出能力范围的技术障碍

**应对方式**：

- 停止继续尝试，避免无效消耗
- 总结当前情况：已尝试的方法、遇到的问题、错误信息
- 清晰描述问题，向用户求助
- 提供可选方案，让用户决策

**反面示例**：

- 反复尝试同一种方法，期望不同结果
- 不总结情况，直接说"我做不了"
- 耗时 1 小时仍在原地打转

**正面示例**：

- "尝试了 A、B、C 三种方法，都遇到 X 错误，需要您协助检查 Y 配置"
- "这个问题涉及 Z 技术，超出当前能力范围，建议寻求专业支持"

## 4. 复杂任务处理

```
分析 → 先分析问题，做任务处理的方案和计划
协作 → 复杂度超预期时，先暂停，同用户讨论策略
拆解 → 复杂任务拆小步骤，子任务独立验证
验证 → 每层修完验证端到端，不局部通过即认为全通
梳理 → 局部修复时，先要梳理当前架构和流程，不要改一个问题带出新问题
反馈 → 处理过程要有提醒，不静默失败
```

## 5. 系统设计原则

| 原则 | 核心要求 |
|------|---------|
| **分层设计** | 底层简单可靠，上层组装灵活，层间不耦合 |
| **领域先行** | 先有模型再写代码，先画大图再切模块 |
| **防污染** | 系统输出不反噬输入；后台前台物理隔离 |
| **可维护** | 技能修改必同步更新文档；代码自解释 |
| **标准化输出** | 脚本输出JSON → 上层定模板 → 大模型格式化 |

## 6. 技术经验库

### Windows 下 shell 参数传递 JSON 的坑
| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 引号转义失败 | PowerShell 对 `"` 和 `'` 的转义规则复杂 | 改用临时文件传递 JSON 参数 |
| JSON 解析不完整 | 格式化结果跨多行 | 使用 `re.search(r'\[.*\]', text, re.DOTALL)` 匹配完整 JSON |
| Unicode 输出乱码 | Windows 默认 GBK 编码 | Python 强制 UTF-8：`sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` |

### Node.js fetch 不走系统代理的解决方案
```typescript
import { ProxyAgent } from 'undici';
const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY;
const dispatcher = proxyUrl ? new ProxyAgent(proxyUrl) : undefined;
const response = await fetch(url, { dispatcher } as any);
```
- 自动检测 Clash 代理端口：遍历 7890、7897 等常见端口

### Python 脚本处理多字节字符的编码技巧
```python
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

### DeepSeek V4 + Claude Code 集成报错解决方案
| 问题 | 报错信息 | 解决方案 |
|------|----------|---------|
| 模型切换后上下文压缩失败 | `Error during compaction: API Error: 400 {"error":{"message":"The content[].thinking in the thinking mode must be passed back to the API."}}` | 在Claude Code配置中添加三个环境变量：<br>1. `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1"`<br>2. `CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK: "1"`<br>3. `CLAUDE_CODE_EFFORT_LEVEL: "max"` |
| GLM切换到DeepSeek V4仍报错 | 模型上下文不兼容 | 属于已知bug，暂不支持无缝切换，切换后建议重启会话 |
| LiteLLM代理下多轮对话失败 | `DeepseekException - {"error":{"message":"The `reasoning_content` in the thinking mode must be passed back to the API."}}` | 原因：DeepSeek V4默认开启思维模式，要求多轮对话必须回传之前返回的`reasoning_content`字段，而LiteLLM默认会自动删除该字段。<br>解决方案：升级LiteLLM到v1.83.12+版本（官方已通过#26660 PR修复），或手动修改LiteLLM代码保留reasoning_content字段。 |

### 关键词匹配逻辑经验
| 场景 | 问题 | 解决方案 |
|------|------|---------|
| 运营商名称匹配 | "中国联通"匹配不到"海南联通" | 添加简写关键词："联通"、"移动"、"电信"、"铁塔" |
| 中文关键词 | lower()对中文无效，但无害 | 简写形式比完整形式更重要，覆盖更多变体 |

### 前端调试经验（2026-05-12）
| 问题 | 原因 | 解决方案 |
|------|------|---------|
| HTML PPT 空白页 | CSS `display: none !important` 优先级高于 JS `element.style.display = 'block'` | 移除 CSS 中的 display 规则，JS 全权控制 |
| Shadow DOM 自定义元素在 file:// 下不兼容 | Web Component 的 `:scope` 选择器 + `connectedCallback` 时序在本地协议下行为不确定 | 替换为 `<div>` + vanilla JS，避免 Shadow DOM |
| JS 语法错误导致静默失败 | `try{}catch(e){}` 被误截断为 `try{}`（缺 catch） | 使用更简洁的 IIFE + 直接 `element.style` 操作，减少依赖 |

### 文章尾部截断安全策略（smart-web-fetcher v3）
| 原则 | 说明 |
|------|------|
| 关键词定位 + 段落分析 > 单一规则 | 先用关键词找尾部区域，再分析段落结构找精确边界 |
| 安全优先 | 4道检查防线：截断点太靠前❌ / 弱标记+正文密度低❌ / 噪声不明显❌ / 删除太少❌ |
| 避免泛化关键词 | "更多"、"关闭"等词在平台UI中无处不在，不能用做尾部标记 |
| 正文密度检测 | 弱标记前25行内正文<3行 → 标记嵌在UI中，放弃截断 |
| 强/弱标记分级 | reference/end_marker=高权重(9-10)，attribution=中(7-8)，social/meta=低(3-5) |

### PPT 生成路径对比（2026-05-14 更新）
| 路径 | 格式 | 可靠性 | 适用场景 |
|------|------|--------|---------|
| python-pptx 原生创建 | .pptx | ★★★★★ | 需要真实可编辑PPTX时首选 |
| html-ppt-skill | .html | ★★★★ | 技术分享、有现成模板时 |
| guizang-ppt-skill | .html | ★★★★ | 杂志风、设计感强的场景 |
| huashu-design | .html | ★★★ | 高保真设计Demo（需注意兼容性） |
| **slideflow-ppt HTML→PPTX** | .pptx | ★★★★ | 3种格式自动检测，Playwright渲染+DOM重建，文字可编辑 |

### Smart Web Fetcher 图片本地化方案
```python
# MD5 哈希命名 + Content-Type 智能扩展名
url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
ext = Path(url.split('?')[0].split('#')[0]).suffix.lower()
# 若 URL 无后缀，根据 HTTP Content-Type 修正
ct_to_ext = {'image/jpeg': '.jpg', 'image/png': '.png', ...}
```
- 防重复：同一 URL 多次出现只下载一次
- 懒加载修复：playwright 中 JS 替换 `data-src` → `src` 后再用 markdownify 转换
- Windows 文件名兼容：非法字符 `\/:*?"<>|` 替换为 `-`，多连字符合并，超 200 字符截断

## 7. Agent 工作空间管理

### 技能隔离原则
- 每个 Agent 的技能应位于自己的 workspace 内
- 避免在不同 workspace 间复制技能文件
- 技能路径解析错误时，检查是否有重复副本

### 跨 Agent 技能调用
- 当前 Agent 无法直接 spawn 其他 Agent 时，手动读取目标 workspace 的 SKILL.md
- 记录技能映射关系，如：播放音乐 → workspace-entertainment/potplayer-music

### 深度研究任务处理
- **用户要求深度研究时** → 调用 Deep Research 技能（`skills/deep-research`）
- **禁止行为** → 不要直接用 `web_fetch` 手动搜索拼凑报告
- **原因** → Deep Research 技能有自动保存、结构化输出、递归搜索等完整能力
- **输出位置** → 研究报告自动保存到 `skills/deep-research/output/{标题}.md`

## 8. slideflow-ppt 技能

### 技能概览
- **位置**: `skills/slideflow-ppt/`
- **项目**: `repos/SlideFlow/` (xiaoyesoso/SlideFlow, MIT)
- **功能 A**: AI 自动生成 PPT（LangGraph 编排 + DuckDuckGo 搜索 + HTML 模板 + PPTX 转换）
- **功能 B**: HTML 多页转 PPTX（3 种格式自动检测 + Playwright 渲染 + DOM 重建）

### HTML→PPTX 三种格式适配
| 格式 | 结构 | 导航 | 要点 |
|------|------|------|------|
| huashu-design | `#deck > .slide-page` | display:block/none | CSS 全内联，无需额外处理 |
| html-ppt-skill | `.deck > section.slide` | .is-active + opacity | 外部 CSS 需本地化或注入 |
| guizang-ppt | `#deck > .slide` | translateX | WebGL 背景、Hero 页、Google Fonts |

### 模型配置
- SlideFlow 用 `openai.AsyncOpenAI()`，配置从 `config/config.json` 读取
- WhaleCloud DeepSeek V4 Pro 通过 `/gpt-proxy/v1` (OpenAI 兼容端点) 接入
- 命令行参数优先级: `--model/--base-url/--api-key` > skill config > env > project config

### HTML 转换技术要点
- Playwright 打开 HTML 用 `wait_until="domcontentloaded"` 避免 Google Fonts 卡死
- 外部 CSS 注入: `page.add_style_tag(content="...")` 可动态添加关键 CSS 规则
- 文字隐藏取背景: 注入 `<style id=_bg_hide>*{color:transparent}</style>` → 截图 → 再移除
- 字体映射: Google Fonts → 系统字体（微软雅黑/SimSun/Georgia/Consolas）

## 9. Obsidian LLM Wiki 相关

### 常用库路径
- 默认库: `D:\Users\luzhe\Documents\llm-wiki`（不是 `Documents\Obsidian Vault`）
- Wiki 三层架构: `raw/`（不可变）→ `wiki/`（LLM维护）← `AGENTS.md`（Schema）

### ingest 协议
- 新素材摄入流程: 复制到 raw/ → 创建 sources/ 摘要 → 提取 concepts/ entities/ → 更新 index/overview/log
- 知识复利: 每条新素材不只是存摘要，要更新所有相关页面，建立交叉引用
- 每个 wiki 页面顶部必须有 one-line summary

## 10. 技术经验更新

### config.patch 限制
| 问题 | 原因 | 解决方案 |
|------|------|---------|
| gateway config.patch 报 protected paths | plugins.allow、models.providers.*.apiKey 等路径受保护 | 直接编辑 openclaw.json 或使用 openclaw config set |
| openclaw channels add 被 SIGKILL | 命令过程中 gateway 检测配置变更自动重启 | 手动编辑 JSON 完成 channel/plugin 配置 |

### QQ Bot 配置参考
- 配置格式: channels.qqbot.appId + clientSecret（顶层）
- 多账号: accounts.<name>.appId + clientSecret
- 插件需加入 plugins.allow 白名单 + plugins.entries 启用


