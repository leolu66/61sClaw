---
name: Powerpoint / PPTX
slug: powerpoint-pptx
version: 1.1.0
homepage: https://clawic.com/skills/powerpoint-pptx
description: "Create, inspect, and edit Microsoft PowerPoint presentations. Supports two paths: (A) zero-code HTML→PPTX conversion via iSpring Suite / dom-to-pptx / online tools; (B) code-driven creation via python-pptx / BeautifulSoup / Aspose.Slides. Use when the task involves PowerPoint or `.pptx`; layouts, placeholders, notes, charts, or template fidelity matter; or converting existing HTML slides to editable PPTX."
changelog: v1.1.0 — Added HTML→PPTX conversion paths (zero-code tools + code solutions), comparison table, decision tree, and integration with huashu-design export pipeline.
metadata: {"clawdbot":{"emoji":"📊","requires":{"bins":[]},"os":["linux","darwin","win32"]}}
---

## When to Use

Use when the main artifact is a Microsoft PowerPoint presentation or `.pptx` deck, especially when layouts, templates, placeholders, notes, comments, charts, extraction, editing, or final visual quality matter.

Also use when converting existing HTML/CSS content into editable PPTX — see the [HTML → PPTX Conversion](#html--pptx-conversion) section below.

---

## HTML → PPTX Conversion

When you already have HTML slides (from `html-ppt-skill`, `guizang-ppt-skill`, or `huashu-design`), there are two paths to `.pptx`:

### Path A: 零代码工具（快速、保真度高）

| 工具 | 方式 | 优点 | 缺点 |
|------|------|------|------|
| **iSpring Suite** | PowerPoint 插件，内置浏览器引擎渲染 HTML+CSS | 样式还原最好（渐变/阴影/圆角），原生可编辑 PPTX | 收费，仅 Windows |
| **dom-to-pptx** | 在线工具（https://dom-to-pptx.vercel.app/），粘贴 HTML+CSS → 下载 PPTX | 开源免费，解析 DOM + 计算真实 CSS，矢量级可编辑 | 需在线访问 |
| **Sharayeh** | AI 在线转换，粘贴 HTML/URL → PPTX | 免费，零代码 | 复杂 CSS 易失真 |
| **CloudConvert** | 上传 HTML（ZIP 打包 CSS）→ 选 PPTX | 通用格式转换 | 复杂 CSS 易失真 |

**dom-to-pptx 代码版**（适合批量/自动化）：
```html
<script src="https://unpkg.com/dom-to-pptx@1.1.5/dist/index.browser.min.js"></script>
<script>
const el = document.querySelector('#deck');  // 你的 HTML 容器
domToPptx.convert(el, {
  outputType: 'blob',
  svgAsVector: true          // SVG 转矢量，可编辑
}).then(blob => {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'output.pptx';
  a.click();
});
</script>
```

### Path B: 代码方案（精准控制、批量/复杂样式）

| 方案 | 技术栈 | 适用场景 | 复杂度 |
|------|--------|---------|--------|
| **python-pptx 原生创建** | `pip install python-pptx` | 从零生成，内容驱动 | ★★☆ |
| **BeautifulSoup + python-pptx** | 解析 HTML 标签 + 样式映射 → PPTX | HTML 内容提取后重建 | ★★★ |
| **huashu-design export** | `scripts/export_deck_pptx.mjs`（pptxygenjs） | 符合 4 条硬约束的 HTML deck | ★★★★ |
| **Aspose.Slides** | 商用库，`new Presentation("input.html", LoadFormat.Html)` | 全格式支持，复杂布局 | ★★（收费） |

**Path B Python 示例**（BeautifulSoup 解析 HTML → python-pptx 映射样式）：
```python
from bs4 import BeautifulSoup
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

with open('slides.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

prs = Presentation()
style_map = {
    'h1': {'size': Pt(36), 'color': RGBColor(44, 62, 80), 'bold': True},
    'p':  {'size': Pt(24), 'color': RGBColor(52, 73, 94)}
}

for section in soup.find_all('section'):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    h1 = section.find('h1')
    if h1:
        slide.shapes.title.text = h1.text
        for run in slide.shapes.title.text_frame.paragraphs[0].runs:
            run.font.size = style_map['h1']['size']
            run.font.color.rgb = style_map['h1']['color']
            run.font.bold = style_map['h1']['bold']
    p = section.find('p')
    if p:
        content = slide.placeholders[1]
        content.text = p.text
        for run in content.text_frame.paragraphs[0].runs:
            run.font.size = style_map['p']['size']
            run.font.color.rgb = style_map['p']['color']

prs.save('output.pptx')
```

### 决策树：选哪条路？

```
已有 HTML 内容？
├── 是 → 追求保真度？
│   ├── 是 → iSpring Suite（Windows） / dom-to-pptx（在线）
│   └── 否 → BeautifulSoup + python-pptx（牺牲样式，保留文本）
└── 否 → 从零创建？
    ├── 内容固定 → python-pptx 原生创建 ★★★★★（最可靠）
    └── 需要模板 → 先做模板库盘点，再填充内容
```

> ⚠️ **HTML→PPTX 的本质限制**：CSS 渐变 / 阴影 / 复杂布局在转换中极易丢失。如果设计保真度是硬需求，优先用 python-pptx 从零创建；如果已有 HTML 且只需要文本+基础样式，用 BeautifulSoup 提取最稳。

## Core Rules

### 1. Choose the workflow before touching the deck

- Reading text, editing an existing deck, rebuilding from a template, and creating from scratch are different jobs with different failure modes.
- For text extraction or inspection, read the deck before editing it.
- Text extraction plus thumbnail-style visual inspection is safer than editing from shape assumptions alone.
- For template-driven work, inventory the deck before replacing content.
- For deep edits, remember a `.pptx` file is OOXML with separate parts for slides, layouts, masters, media, notes, and comments.
- If a template exists, template fidelity beats generic slide-design instincts.
- Reusing or duplicating a good existing slide is often safer than rebuilding it and hoping the theme still matches.

### 2. Inventory the deck before replacing content

- Count the reusable layouts, real placeholders, notes, comments, media, and recurring typography or color patterns first.
- Placeholder indexes and layout indexes are not portable assumptions.
- Inspect the actual slide or template before targeting title, body, chart, or image shapes.
- Speaker notes, comments, and linked assets can live outside the visible slide surface.
- A missing or wrong placeholder target can silently land content in the wrong box or wrong layer.
- Master and layout settings can override local slide edits, so the visible problem is not always on the slide you are editing.

### 3. Match content to the actual placeholders

- Count the actual content pieces before choosing a layout.
- Pick layouts based on the real number of ideas, columns, images, or charts the slide needs.
- Do not force two ideas into a three-column slide or cram dense text under a chart.
- Category counts and data series lengths must match or charts will break in ugly ways.
- Explicit sizing beats wishful thinking: text boxes, images, and charts need real space, not "it should fit".
- Do not choose a layout with more placeholders than the content can meaningfully fill.
- Quote layouts are for real quotes, and image-led layouts are for slides that actually have images.
- For chart-, table-, or image-heavy slides, full-slide or two-column layouts are usually safer than stacking dense text above the visual.

### 4. Preserve the deck's visual language

- Theme, master, and layout files usually decide fonts, colors, and hierarchy more than any one slide does.
- Start from the deck's actual theme, fonts, spacing, and aspect ratio instead of improvising a new style.
- Reuse the deck's own alignment and spacing system instead of inventing a second visual language.
- Use common fonts for portability and strong contrast for readability.
- Preserve the template's visual logic first; originality matters less than not breaking the deck's existing language.
- Combining slides from multiple sources requires normalizing themes, masters, and alignment afterward.

### 5. Run content QA and visual QA separately

- Text overflow, bad alignment, clipped shapes, weak contrast, and placeholder leftovers are normal first-pass failures.
- Run both content QA and visual QA; missing text and broken layout are different failure classes.
- Render or inspect the actual deck output before delivery when layout matters.
- Search for leftover template junk, sample labels, and placeholder text before calling the deck finished.
- Check notes, comments, labels, legends, and chart/table semantics separately from the visual pass.
- A deck can pass text extraction and still fail on overlap, clipping, wrong theme inheritance, or broken notes.
- Thumbnail grids and rendered slides usually reveal layout bugs faster than code or text inspection.
- Assume the first render is wrong and do at least one fix-and-verify cycle before calling the deck finished.
- Re-check affected slides after each fix because one spacing change often creates another issue.

### 6. Keep decks portable and review-safe

- Template masters can override direct edits in surprising ways.
- Complex effects may degrade across PowerPoint, LibreOffice, and conversion pipelines, so keep important content robust without them.
- Image sizing, font substitution, and placeholder mismatch are common reasons a deck looks good in code and bad on screen.
- Notes, comments, linked media, and merged decks can stay broken even when the visible slide looks fine.

## Common Traps

- Placeholder text and sample charts often survive template reuse if not explicitly replaced.
- Directly editing one slide can fail if the real issue lives in the master or layout.
- Charts, icons, and text boxes need enough space; near-collisions are usually visible only after rendering.
- Layout indexes vary by template, so built-in assumptions from one deck often break in another.
- A missing placeholder or wrong shape target can silently put content in the wrong place.
- Counting the text ideas after choosing the layout usually leads to empty placeholders, weak hierarchy, or leftover template junk.
- Font substitution can move line breaks and wreck careful spacing.
- Speaker notes, comments, and linked media can stay broken even when the visible slide looks fine.
- A deck can pass text inspection and still fail visually because of overlap, contrast, or edge clipping.
- Editing from one slide alone can miss the real source of truth in the theme, master, or layout definitions.
- Choosing a quote, comparison, or multi-column layout without matching content usually makes the deck look templated rather than intentional.
- Combining or duplicating slides without checking masters and themes can create subtle inconsistency slide by slide.
- Aspect-ratio mismatches like `16:9` versus `4:3` can shift every placement decision even when each slide looks locally reasonable.

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `html-ppt-skill` — 36-theme HTML PPT generator（可转换为 PPTX）
- `guizang-ppt-skill` — 杂志风 HTML PPT（WebGL 背景）
- `huashu-design` — 高保真 HTML 设计（含 PPTX 导出脚本 `export_deck_pptx.mjs`）
- `documents` — Document workflows that often feed presentation content.
- `design` — Visual direction and layout decisions.
- `brief` — Concise business messaging for slide narratives.

## Feedback

- If useful: `clawhub star powerpoint-pptx`
- Stay updated: `clawhub sync`
