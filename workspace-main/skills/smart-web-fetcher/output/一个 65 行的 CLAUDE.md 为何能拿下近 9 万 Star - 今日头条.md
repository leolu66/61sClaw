# 一个 65 行的 CLAUDE.md 为何能拿下近 9 万 Star

2026-04-28 04:40·[闻数起舞](/c/user/token/MS4wLjABAAAAtZ6rlaKmKrncOYzZMYeYwuA9BwyErktsBb-g5oE0lacH_ujIrXF6El-fLZkpamHZ/?source=tuwen_detail)

![](https://p26-sign.toutiaoimg.com/tos-cn-i-axegupay5k/50112eb174294bbc9232e3ed078f46ff~tplv-tt-origin-web:gif.jpeg?_iz=58558&from=article.pc_detail&lk3s=953192f4&x-expires=1778905611&x-signature=XTuPHpoyrS3bMCzhdUWBoee491g%3D)

Andrej Karpathy 是 AI 领域过去十年最具影响力的工程师与教育者之一。他在斯坦福读博师从李飞飞,期间设计并主讲了 CS231n, 这门课让一代深度学习从业者入门; 2015 年作为创始成员加入 OpenAI, 2017 年被 Elon Musk 招至特斯拉担任 AI 总监,主导 Autopilot 的纯视觉路线长达五年,之后短暂回到 OpenAI,2024 年离开并创立 AI 原生教育公司 Eureka Labs。让他真正"出圈"的是 micrograd、makemore、nanoGPT、llm.c 这一系列极简开源教学项目,以及配套的"Neural Networks: Zero to Hero" YouTube 课程——把神经网络从加减乘除一直讲到训练一个 GPT。他还提出了"Software 2.0/3.0"这套被广泛引用的框架,把"用神经网络权重写程序"和"用自然语言写程序"分别命名为软件演进的下一阶段。他在 X （twitter）上的影响力极大,一条随手发的工程观察就能在几天内被社区转化成工具和仓库——本文讨论的 andrej-karpathy-skills 就是最近一个典型例子。

---

# 一、先看结论

andrej-karpathy-skills 不是一个把 Karpathy 教学内容(nanoGPT、makemore、micrograd 等)封装成 Agent Skill 的项目,而是开发者 **Forrest Chang(张佳源)** 把 **Andrej Karpathy 在 2026 年 1 月 26 日发布的一条关于 LLM 编码缺陷的 X(Twitter)帖子**,提炼成的一份 **65 行 CLAUDE.md 文件 + 一个符合 Agent Skills 标准的 karpathy-guidelines Skill**。它的核心是 4 条用于约束 Claude Code、Cursor 等 AI 编码助手行为的原则,旨在解决 AI 写代码时"过度复杂化、隐藏假设、误改无关代码"等痛点。该项目自 2026 年 1 月 27 日创建以来,在 ClaudePluginHub 收录数据中已积累约 **90k stars /**,在 star-history 上的全球排名约 **#143**,并衍生出 Cursor/VS Code 移植版本。

需要特别澄清的一个误解:**Karpathy 本人并未参与、撰写或公开背书这个仓库**;它只是借用了 Karpathy 的观察与名字。

![](data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)

---

# 二、项目背景与定位

# 2.1 项目本身

仓库 README 的副标题就是定位:"A single CLAUDE.md file to improve Claude Code behavior, derived from Andrej Karpathy's observations on LLM coding pitfalls."(一份用于改善 Claude Code 行为的单文件 CLAUDE.md,源自 Andrej Karpathy 对 LLM 编码缺陷的观察)。

# 2.2 作者 Forrest Chang 是谁

Forrest Chang 的 GitHub 自我介绍是:**" Founder & CEO @ Multica | AI-native Builder"**,中文名 **Jiayuan Zhang(张佳源)**,X 账号为 @jiayuan\_jy。他的主线产品是 **Multica**——一个开源的"管理混合人 + Agent 工程团队"的平台,理念是"Your next 10 hires won't be human"。除了本仓库外,他过往作品还包括 roam-vim-mode、gptlang、programmer-soft-skills、  
practical-python-programming-cn、readbuidl 等。这意味着 andrej-karpathy-skills 对他而言更像是 Multica 的"前哨/品牌站"——README 顶部明确推广 Multica,plugin hub 描述里也保留了同样链接 。

我们在之前介绍过这个项目：从 Multics 到 Multica： AI 编码 Agent 的项目经理

# 2.3 为什么以 Andrej Karpathy 命名

Karpathy 是前 OpenAI 创始成员、前特斯拉 AI 高级总监、Eureka Labs 创始人,因 nanoGPT、micrograd、makemore、"Software 2.0/3.0"等工作而广为人知。

仓库的命名直接来自 Karpathy 在 2026 年 1 月 26 日发布的一条 X 帖子。Karpathy 在帖中描述自己在两个月内从"80% 手写 + 自动补全 / 20% Agent"切换到"80% Agent / 20% 手写",并系统点名了三类反复出现的失败模式 :

1. **静默错误假设**:"模型会替你做出错误假设并径直执行,不检查、不澄清、不暴露不一致、不展示 trade-off、不在该 push back 的时候 push back。"
2. **过度复杂化**:"它们特别喜欢把代码和 API 复杂化,堆叠抽象,不清理死代码……能用 100 行解决的问题写成 1000 行。"
3. **越权改动**:"它们仍然会作为副作用修改/删除自己并未真正理解的注释和代码,即便这些代码与任务正交。"

第二天(1 月 27 日)Forrest Chang 就把这些观察"翻译"成可执行的 4 条规则,以 Karpathy 命名仓库,但仓库本身与 Karpathy 没有任何官方合作关系 。

# 2.4 与 Anthropic Agent Skills 标准的关系

Anthropic 在 2025 年 10 月推出 **Agent Skills** 开放标准:Skill 是"包含一个 SKILL.md(YAML frontmatter + Markdown 指令)、可选 scripts/、references/、assets/ 子目录的文件夹",由 Claude.ai、Claude Code、Claude Agent SDK、Claude API 共同支持,并在 agentskills.io 作为开放规范进行维护 。

参考：MCP 与 Agent Skills：AI Agent 能力扩展的两块基石

andrej-karpathy-skills 就是这套标准的一个第三方 Skill 实现:它在 Claude Code Plugin Marketplace 和 ClaudePluginHub、LobeHub Skills Marketplace 上都登记为含 1 个 Skill(karpathy-guidelines)的插件,Skill 的描述完全符合 Anthropic 推荐的 "behavioral guideline"模式——"Use when writing, reviewing, or refactoring code to avoid overcomplication..." 。

# 2.5 它是不是"Karpathy 教学风格"的封装?

**不是**。它**不**让 Claude 写出"Karpathy 风格的 nanoGPT 代码",**不**生成解释教学内容,**不**包含   
micrograd/makemore/LLM101n 等 Karpathy 著名教程的内容。它纯粹是把 Karpathy 关于"如何让 LLM 写出合格代码"的元观察,变成一份给 AI Agent 阅读的行为约束。它是 **prompt-as-policy**,不是 **knowledge skill**。

---

# 三、项目要解决的问题

# 3.1 使用场景

任何用 Claude Code、Cursor、Copilot、Claude.ai 这类 AI 编码助手做**非平凡**任务的场景:bug 修复、添加新功能、跨文件重构、code review、PR 审阅等 。

# 3.2 解决的痛点

Reddit 社区(尤其 r/ClaudeAI 与 r/ClaudeCode)广泛使用 "the confident junior dev"(自信但不靠谱的初级工程师)来形容 AI 助手的典型病症:

* 让它修一个 bug,它把半个文件重写;
* 让它加一个简单功能,它建一整套抽象层;
* 让它给建议,它在错误假设上自信地一路狂奔 。

karpathy-guidelines 直接对准这三类病症,告诉模型:**说出你的假设、用最小改动、定义可验证的成功标准**。

# 3.3 教学型还是风格型?

它属于第三类:**行为/工程纪律型**。目标不是让 AI"教得更好"或"代码更像 Karpathy",而是让 AI 在实际工程中更克制、更可控,减少返工成本。

# 3.4 目标用户

按 LobeHub Marketplace 的定位:**起草 PR、写代码、做 code review、设计 refactor 的工程师**;尤其是以 AI 为主、人为辅的工作流(以及作者自家 Multica 这种"AI 同事"协作平台)的用户。

---

# 四、架构与设计

# 4.1 核心结构

仓库简单——核心就一个 CLAUDE.md,共约 **65 行无可执行代码** ;此外补充:

* EXAMPLES.md——给出"无约束模型 vs. 合规模型"的对照示例(如 "fix empty email crash":无约束版本会顺手改引号风格、加 type hints、加 docstring、加额外校验;合规版只改 2 行)Source;
* .cursor/rules/karpathy-guidelines.mdc——committed 的 Cursor 项目规则,使同一份指令在 Cursor 中也生效;
* CURSOR.md——讲解如何把这条规则迁移到其他 Cursor 项目;
* 一个符合 Agent Skills 规范的 Skill 目录 karpathy-guidelines/,即 ClaudePluginHub 中 "Skills (1)" 所指。

ClaudePluginHub 显示组件一览:**0 Commands / 0 Agents / 1 Skill / 0 Hooks / 0 MCP / 0 LSP / 0 Output Styles / 0 Themes / 0 Monitors**——这进一步说明它就是一个"纯 Skill"的极简包 。

# 4.2 唯一一个 Skill:karpathy-guidelines

LobeHub 与 ClaudePluginHub 收录的 Skill 元数据:

> **name:**
>
> karpathy-guidelines  
> **description:**
>
> Behavioral guidelines to reduce common LLM coding mistakes. Use when writing, reviewing, or refactoring code to avoid overcomplication, make surgical changes, surface assumptions, and define verifiable success criteria.

Skill 的内容由"四条原则"构成,严格对应 Karpathy 帖子的四个观察:

|  |  |  |
| --- | --- | --- |
| 原则 | 针对的失败模式 | 关键操作 |
| 1. Think Before Coding(先想再写) | 静默错误假设、隐藏困惑、缺失 trade-off | 显式陈述假设;不确定就发问;有歧义就枚举多种解释而非默选;遇到不清楚就停下命名问题 |
| 2. Simplicity First(简洁优先) | 过度复杂化、臃肿抽象 | 只写解决问题的最少代码;不为单点逻辑加抽象;不加未要求的"灵活性/可配置性";"200 行能写成 50 行就重写";自检"资深工程师会不会觉得过度复杂?" |
| 3. Surgical Changes(外科手术式改动) | 顺手改动正交代码 | 不"顺便改善"邻近代码、注释或格式;不重构没坏的东西;match 现有风格;发现无关死代码只提及不删除;每一行变更都能追溯到用户请求 |
| 4. Goal-Driven Execution(目标驱动) | 模糊指令导致反复澄清 | 把命令式任务改写成可验证目标(如"修 bug"→"先写复现测试,然后让它通过");多步任务用 "step → verify" 列表;弱标准("make it work")会让 LLM 死循环,强标准让它独立 loop |

# 4.3 表达形式

实现完全是 **Markdown 文档 + YAML frontmatter**,**没有任何运行时、依赖、脚本或代码** 。这与 Anthropic Agent Skills "渐进式披露(progressive disclosure)"的理念吻合:Claude 只在 session 开始时把元数据加载进系统 prompt,真正命中条件时才读入正文。

# 4.4 集成方式

* **Claude Code Plugin** —— /plugin marketplace add forrestchang/andrej-karpathy-skills 然后 /plugin install andrej-karpathy-skills@karpathy-skills,跨项目可用;
* **CLAUDE.md(逐项目)** —— 直接 curl 下载到项目根目录,或追加(>>)到已存在的 CLAUDE.md;
* **Cursor** —— 直接利用仓库自带的 .cursor/rules/karpathy-guidelines.mdc(或在其他项目中复制使用);
* **VS Code / Cursor 扩展** —— 由社区移植仓库 mbeijen/andrej-karpathy-skills-cursor-vscode 提供"一键导入"体验,并支持 alwaysApply: true 这种 frontmatter 选项 SourceSource。

---

# 总结：为什么一份 65 行的 Markdown 能值近 9 万 Star?

1. **格式套利**:正好踩中 Anthropic Agent Skills 标准化的发布窗口(2025 年 10 月),作为最早一批"非示例、面向真实工程纪律"的第三方 Skill,占据品类心智;
2. **名字红利**:借 Karpathy 的影响力把"AI 写代码的体验吐槽"凝固为可执行规则;
3. **多渠道兼容**:同一份内容以 CLAUDE.md / Cursor rule / Skill plugin 三种主流形式落地;
4. **极简 = 可读 = 可改**:65 行,任何人都能 fork 自定义;移植仓库的作者总结得最直白——"杠杆在指令本身,不在机制"
5. **作者运营**:Forrest Chang 把它作为 Multica 的入口产品,README 顶部直接引流,形成"小作品养大产品"的典型路径。

简而言之,它是 2026 年 Q1 的 AI 编码生态里一个"模因 + 标准 + 工程纪律"三者交汇的标本——**它不是一项技术发明,而是一份关于"如何与 AI 工程师协作"的最小化社会契约**。

---

# 参考来源

* forrestchang/andrej-karpathy-skills - GitHub README
* forrestchang (Jiayuan Zhang) - GitHub Profile
* andrej-karpathy-skills 在 ClaudePluginHub
* karpathy-guidelines 在 LobeHub Skills Marketplace
* Star History
* AlphaSignal: Karpathy-Inspired CLAUDE.md
* Antigravity: Karpathy's CLAUDE.md Skills File: The Complete Guide
* PyShine: Andrej Karpathy Skills
* todatabeyond: Turning Andrej Karpathy's LLM Coding Thoughts into CLAUDE.md
* OpenClawAPI(中文):Karpathy-guidelines 入门
* Anthropic Engineering: Equipping agents for the real world with Agent Skills
* Anthropic 官方文档: Agent Skills Overview
* Anthropic 官方文档: Using Agent Skills with the API
* agentskills.io 标准主页
* anthropics/skills 官方仓库
* Cursor/VSCode 移植: mbeijen/andrej-karpathy-skills-cursor-vscode
* Anthropic: Complete Guide to Building Skills for Claude (PDF)
* Karpathy blog
* Karpathy llm-wiki gist
* Hacker News: Software in the era of AI
* Lee Hanchung: Claude Agent Skills Deep Dive
* ClaudeWorld: Anthropic 官方 17 个 Skills 全指南
* wshobson/agents agent-skills 文档
* Apple Podcasts: GitHub Daily Trend: andrej-karpathy-skills 单集
