# Building Deep Research From Scratch

> Author: Samyak | Jun 8, 2025 | 4 min read
> Source: https://medium.com/@samyakb/building-deep-research-from-scratch-e6672d512192

---

Welcome to the first blog in the **"Build Deep Research From Scratch"** series. I will try to make this a beginner-friendly guide where you'll not only learn how *Deep Research works*, but also build your own simplified version step by step. We'll go **very slow**, assuming you're newbie to programming and not very confident with using things like git, github or usual commands that go into terminal.

![image-20260522170452268](E:\typora\images\image-20260522170452268.png)

## What is Deep Research?

Imagine you're trying to understand a topic like I did. For me it was **"Parkinson's early detection via wearable tech"**. Generally you would make a google/perplexity search along with that you would generally ask chatgpt, or claude hoping that the info you are looking for is in the training data. This had been my workflow and it works well but coming of deep-research has changed a lot of things and sped my process.

Instead of doing three different searches on pplx, Google and then Claude I now do a deepresearch query and get detailed report as I would have wanted.

> *Think of it as your personal researcher or that one friend you can do google-fu (Google fu is a term of the past it just means someone good at googling)*

Actually I suggest you guys if you haven't tried deep research yet.

![image-20260522170512025](E:\typora\images\image-20260522170512025.png)
*Deep research on ChatGPT*

![image-20260522170533847](E:\typora\images\image-20260522170533847.png)
*Deep research on Gemini*

## References that we will be using

There are two open-source implementations of Deep Research that you can look at right now:

- **[u14app/deep-research](https://github.com/u14app/deep-research)**: Typescript Implementation with a hosted link so you can try right away
- **[dzhng/deep-research](https://github.com/dzhng/deep-research)**: The repo above is inspired from this repo. Also a Typescript Implementation but no hosted link

We'll use **these as reference points** while building our toy version.

## What Will You Build?

By the end of this blog series, you'll have your own basic version of Deep Research that can:

- Accept a research query.
- Create a prompt for research plan as well as what search queries to make
- Run a web search using a third party API.
- Extract and summarize content.
- Save results in a report
- Let you track sources like a researcher would (Save citations).

And you'll learn:

- How to code from first principles.
- How to use Git and GitHub.
- How to write clear commit messages.
- How to explore other people's open-source code.

## Prerequisites

- basics of python3 (feel free to ask chatgpt ot explain stuff if you feel like stuff)
- good if you have done a quick crash course on git and github

> *I'll try to support both **Windows** and **Linux** users with tailored instruction*

## Your First Task

1. Bookmark or star these repos so you can refer back

   - [https://github.com/u14app/deep-research](https://github.com/u14app/deep-research)
   - [https://github.com/dzhng/deep-research](https://github.com/dzhng/deep-research)

2. Sign up for GitHub at [github.com](https://github.com/) if you haven't already.
3. Ask yourself: **What topic would I want my assistant to research for me?** We'll use this as your sample query in the coming posts. For me it was "Effectiveness of Accelerometry for Parkinson's disease"

## Best Practices (Start Early!)

- **Commit often, commit meaningfully**: Write messages like "feat: added search query input" instead of "changed stuff".
- **Don't skip small wins**: Getting Python to run is a *big deal* if it's your first time.
- **Read the README** of open-source projects you visit.
- **Ask why** each tool exists — that's the root of first-principles learning.

## TL;DR

- **Deep Research** helps automate smart internet research.
- You'll build a toy version — by learning slowly, the right way.
- You don't need to be great at coding yet — I'll try to help you step-by-step plus its the age of vibe coding so don't ya worry.
- In the next blog, we'll set up your tools and write your first code.

---

If you found this blog helpful please consider sharing it, re-tweeting it. or just interact with it. Drop a comment and an upvote.

If you think there's any problem you can DM me at [https://x.com/Samyak1729](https://x.com/Samyak1729)

**Next Blog: Setting Up Your Research Lab**

*Installing Python, Git, VS Code, and Writing Your First Line of Code*

---

*Tags: AI, Generative AI Tools, GenAI*
