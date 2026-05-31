---
name: smart-web-fetcher
description: "智能网页内容获取工具，自动适配不同类型网页。普通静态网页使用内置web_fetch工具快速提取内容，反爬/动态加载/需要交互的复杂网页自动使用playwright模拟浏览器操作获取完整内容。触发场景：获取网页内容、抓取网页信息、网页内容提取、爬取网页数据。"
---

# Smart Web Fetcher

## Overview
智能网页内容抓取工具，自动选择最优抓取策略：
- **普通静态网页**：使用内置 web_fetch 工具，快速高效提取 markdown 格式内容
- **复杂场景**（反爬限制/动态渲染/需要登录/需要交互）：自动切换到 playwright 模拟浏览器操作，绕过限制获取完整内容

## 核心功能
1. 自动识别网页类型，选择最优抓取方案
2. 支持自定义 User-Agent、请求头等参数
3. 支持模拟点击、滚动、输入等交互操作
4. 支持提取纯文本、markdown、HTML 等多种格式内容
5. 自动处理反爬验证、Cookie 管理
6. **自动提取网页标题生成文件名**，Windows 系统兼容（非法字符替换为 `-`）
7. **可指定输出目录**，默认输出到 `skills/smart-web-fetcher/output/`
8. **自动下载图片至本地**：在输出目录下创建 `images/` 文件夹，将网页中所有图片下载到本地，MD 文件中图片引用地址自动替换为本地路径
9. **文章主体提取**（Playwright 模式）：优先取 `article > main > [role=main]` 等语义化容器，减少页面 Chrome 噪声
10. **Markdown 噪声清理**：自动清除头部的导航链接、日期行、标签行等页面 Chrome
11. **语义化图片命名**：图片按 URL 原始文件名 > alt 文本 > hash 回退优先级命名，不再是纯 hash

## 快速使用

### 基础调用（自动生成文件名）
```bash
python scripts/fetch_web_content.py <网页URL>
```
会自动提取网页标题 → 生成 `标题.md` 保存到 `output/` 目录

### 指定输出目录
```bash
python scripts/fetch_web_content.py <网页URL> --output-dir D:\my_articles
```

### 指定完整输出路径
```bash
python scripts/fetch_web_content.py <网页URL> -o result.md
```

### 强制使用 playwright 模式
```bash
python scripts/fetch_web_content.py <网页URL> --mode playwright
```

### 复杂页面（接受Cookie+滚动+等待）
```bash
python scripts/fetch_web_content.py <网页URL> --mode playwright --click-selector "#accept-btn" --scroll --wait 5
```

### 全参数示例
```bash
python scripts/fetch_web_content.py https://www.toutiao.com/article/xxx \
    --mode playwright \
    --format markdown \
    --output-dir ./output \
    --wait 5 \
    --scroll \
    --click-selector ".close-btn" \
    --cookie "sessionid=abc123; token=xyz"
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 要抓取的网页URL | **必填** |
| `--mode` | 抓取模式：auto / web_fetch / playwright | auto |
| `--format` | 输出格式：markdown / text / html | markdown |
| `-o, --output` | 指定完整输出文件路径 | 自动生成 |
| `--output-dir` | 输出目录（不指定 -o 时有效） | `output/` |
| `--wait` | playwright 页面加载等待秒数 | 3 |
| `--cookie` | Cookie，格式 `"key1=val1; key2=val2"` | 无 |
| `--click-selector` | 页面加载后要点击的元素CSS选择器 | 无 |
| `--scroll` | 是否自动滚动加载全部内容 | 否 |
| `--no-images` | 不下载图片（仅提取文本） | 否 |
| `--no-truncate` | 不截断文章尾部噪声（保留评论区/推荐等） | 否 |

## 图片下载与本地化

默认情况下，抓取网页内容时会自动执行以下操作：

1. **提取图片 URL** — 支持 Markdown `![alt](url)`、HTML `<img src>`、微信 `data-src`/`data-croporisrc`、相对路径等格式
2. **下载到本地** — 在输出目录下创建 `images/` 文件夹，按**语义化规则**命名图片
3. **替换引用路径** — MD 文件中的图片地址自动改为 `images/文件名.扩展名`，支持**绝对/相对/路径多变体匹配**，确保不同引用形式的图片都能正确替换
4. **去重复用** — 同一张图片重复出现只下载一次；同名不同扩展名的文件自动跳过
5. **智能格式识别** — 根据 HTTP 响应的 Content-Type 自动修正扩展名（如 URL 无后缀也能正确识别）
6. **失败隔离** — 单张图片下载失败不影响整体流程，失败图片保留原 URL

### 语义化图片命名规则
图片名按以下优先级生成：
1. URL 中的原始文件名（如 `https://example.com/photo.jpg` → `photo.jpg`）
2. 图片 alt 文本（安全截取 ≤50 字符）
3. hash 回退（`a1b2c3d4.jpg`）

自动处理文件名冲突（追加 `_2`、`_3`...），确保唯一性。

### 禁用图片下载
```bash
python scripts/fetch_web_content.py <URL> --no-images
```

## Markdown 页面 Chrome 噪声清理

Playwright 模式支持文章主体内容提取和 Markdown 噪声自动清理：

### 文章主体提取
- Playwright 模式优先选取语义化容器：`article > main > [role=main] > .post-content > body`
- 避免将侧边栏、导航栏、页脚等无关内容转换为 Markdown
- 仅在主体内容不足时回退到 `document.body`

### Markdown 头部噪声清理
自动删除 Markdown 输出头部（前 15 行内）的页面 Chrome：
- 导航链接（`[返回博客](url)`、`[Back to blog](url)`、`[首页](url)` 等）
- 纯日期行（`2026-05-30`、`2026/05/30`）
- 标签行（`AI Agent 多智能体 架构设计` 等元数据）

仅在标题行（`# 标题`）之前或紧接其后的区域执行清理，不会误删正文内容。

## 文件命名规则

- 自动提取网页 `<title>` 标签或 markdown 第一个 `# 标题`
- Windows 非法字符（`\ / : * ? " < > |`）自动替换为 `-`
- 多个连续 `-` 合并为一个
- 文件名超过 200 字符自动截断
- 未提取到标题时，从 URL 中取最后一段作为后备文件名

## 文章尾部截断

默认开启：自动检测并删除文章尾部噪声（评论区、推荐内容、广告、页面 chrome 等）。

### 安全策略（三阶段）

**阶段1：关键词定位尾部区域**
用高可靠性关键词找到文章尾部的大致位置：

| 优先级 | 关键词类型 | 示例 |
|--------|-----------|------|
| ★★★ 强标记 | 参考/来源 | `参考资料`、`参考文献`、`参考链接` |
| ★★★ 强标记 | 明确结束 | `--- END ---`、`（全文完）`、`结尾` |
| ★★ 强标记 | 版权归属 | `本文来自`、`本文转载自`、`授权发布` |
| ★ 弱标记 | 编者信息 | `编辑：`、`责任编辑：`、`作者：` |
| ★ 弱标记 | 平台尾部 | `暂无留言`、`关注该公众号`、`微信扫一扫` |

邻近的多个标记会聚合成一个「尾部候选区域」，优先选择包含强标记的区域。

**阶段2：段落分析找精确边界**
在尾部区域内：
- **往前扫描**：找最后一个实质性内容段落的结束位置（行长≥25、含中文/英文句子、非URL、非噪声）
- **往后保留**：包含合理的引用链接（URL）和版权归属行
- **噪声排除**：微信赞赏UI（`喜欢作者`、`赞赏金额`）、页面搜索框等平台UI行不会被当作正文

**阶段3：安全检查**——不确定就保留
| 检查项 | 条件 | 动作 |
|--------|------|------|
| 截断点太靠前 | < 文档 6% | 放弃截断 |
| 弱标记+内容密度低 | 标记前 25 行内 < 3 行正文 | 放弃截断（标记嵌在平台UI中） |
| 弱标记+噪声不明确 | 截断点后 30 行内 < 3 条噪声 | 放弃截断 |
| 删除量太少 | < 文档 2% 或 < 10 行 | 放弃截断 |

### 禁用截断
```bash
python scripts/fetch_web_content.py <URL> --no-truncate
```

## Structuring This Skill

Workflow-Based

## Workflow Decision Tree

1. 用户提供 URL → 判断是否需要特殊交互（点击/滚动/登录）
2. 无交互 → 优先 `web_fetch`（快速） → 成功则输出
3. 有交互 / web_fetch 失败 → 自动 `playwright`（模拟浏览器） → 输出
4. Playwright 模式：提取文章主体内容（`article > main > body`）→ 修复懒加载图片 → 收集图片 URL
5. 提取网页标题 → 生成 Windows 兼容文件名
6. [图片模式] 语义化命名图片 → 下载到本地 `images/` → 多变体替换引用路径
7. [Markdown 模式] 清理头部导航/日期/标签等 Chrome 噪声
8. 安全截断文章尾部噪声（评论区/推荐/广告等）→ 保存到指定目录

## Resources

### scripts/
- `fetch_web_content.py` — 主抓取脚本，支持 web_fetch / playwright 双模式

### output/
默认输出目录（自动创建），抓取结果文件保存在此。
