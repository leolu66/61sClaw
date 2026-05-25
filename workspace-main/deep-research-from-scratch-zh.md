# 从零开始构建 Deep Research（深度研究）

> 作者：Samyak | 2025年6月8日 | 阅读时间约4分钟
> 原文：https://medium.com/@samyakb/building-deep-research-from-scratch-e6672d512192

---

欢迎来到 **"从零构建 Deep Research"** 系列的第一篇博客。我会尽量把它写成一份面向初学者的指南，在这里你不仅能了解 *Deep Research 是如何工作的*，还能一步步搭建出自己的简化版本。我们会**放慢节奏**，假设你是编程新手，对 git、github 或终端常用命令还不太熟悉。

![Deep Research Banner](https://miro.medium.com/v2/resize:fit:700/1*WEcV2fqU0tOXBjcXQ3oxag.jpeg)

## 什么是 Deep Research？

想象一下，你像我一样想要深入了解某个主题。对我来说，这个主题是 **"通过可穿戴技术早期检测帕金森病"**。通常你会用 Google/Perplexity 搜索，同时问一下 ChatGPT 或 Claude，希望它们训练数据中有你要的信息。这曾是我的工作流，效果也不错，但 deep research 的出现大大改变并加速了这一过程。

我不再需要在 pplx、Google 和 Claude 之间做三次不同的搜索，而是直接提出一个深度研究查询，就能得到一份我想要的详细报告。

> *把它想象成你的私人研究员，或者那个你很擅长 Google 搜索的朋友（Google fu 是过去的说法，意思就是善于用 Google 查找资料的人）*

如果你还没试过 deep research，我强烈建议你去体验一下。

![ChatGPT Deep Research](https://miro.medium.com/v2/resize:fit:412/1*FYFrwmbRsadAPWHvBWJiHQ.png)
*ChatGPT 上的 Deep Research*

![Gemini Deep Research](https://miro.medium.com/v2/resize:fit:453/1*AfpYVgTRMTuAe5Hbo3EVFA.png)
*Gemini 上的 Deep Research*

## 我们将参考的项目

目前有两个开源的 Deep Research 实现可以参考：

- **[u14app/deep-research](https://github.com/u14app/deep-research)**：TypeScript 实现，附带托管链接，可以直接上手体验
- **[dzhng/deep-research](https://github.com/dzhng/deep-research)**：上面那个仓库受此启发。同样是 TypeScript 实现，但没有托管链接

我们会**以这些为参考**来搭建我们的玩具版。

## 你将构建什么？

在本系列博客结束时，你将拥有一个自己的基础版 Deep Research，它能：

- 接收一个研究问题
- 生成研究计划的提示词，以及要执行的搜索查询
- 通过第三方 API 进行网络搜索
- 提取并总结内容
- 将结果保存为报告
- 像真正的研究员一样追踪信息来源（保存引用）

你还会学到：

- 如何从第一原理出发编写代码
- 如何使用 Git 和 GitHub
- 如何写出清晰的提交信息
- 如何阅读和理解其他人的开源代码

## 前置知识

- Python3 基础（如果有不懂的地方，可以随时问 ChatGPT 解释）
- 最好对 Git 和 GitHub 做过快速入门学习

> *我会尽量为 **Windows** 和 **Linux** 用户提供针对性的说明*

## 你的第一项任务

1. 收藏或 Star 以下仓库，方便后续参考

   - [https://github.com/u14app/deep-research](https://github.com/u14app/deep-research)
   - [https://github.com/dzhng/deep-research](https://github.com/dzhng/deep-research)

2. 如果还没有 GitHub 账号，在 [github.com](https://github.com/) 注册一个。
3. 问自己：**我想让助手帮我研究什么主题？** 后续我们会把它作为示例查询来用。对我来说，这个主题是"加速度测量在帕金森病中的有效性"。

## 最佳实践（趁早养成！）

- **频繁且有意义的提交**：写像 "feat: added search query input" 这样的信息，而不是 "changed stuff"。
- **不要忽视小胜利**：如果这是你第一次，能让 Python 跑起来本身就是**了不起的成就**。
- **阅读你访问的开源项目的 README**。
- **追问每个工具存在的原因**——这是第一原理学习的根源。

## 快速总结

- **Deep Research** 帮助你自动化智能化的互联网研究。
- 你将搭建一个玩具版——以正确的方式循序渐进地学习。
- 你不需要有多好的编程基础——我会一步步帮你，况且现在是"氛围编程"（vibe coding）的时代，不用担心。
- 下一篇博客中，我们将配置工具并编写你的第一行代码。

---

如果你觉得这篇博客有帮助，请考虑分享或转发。也欢迎留言和点赞。

有任何问题，可以通过 [https://x.com/Samyak1729](https://x.com/Samyak1729) 私信我。

**下一篇：搭建你的研究实验室**

*安装 Python、Git、VS Code，并编写你的第一行代码*

---

*标签：AI, 生成式 AI 工具, GenAI*
