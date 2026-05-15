---
name: arch-diagram-generator
description: "根据文字描述自动生成专业架构图，输出暗色主题 HTML 文件。触发场景：生成架构图、画系统架构、画架构图、架构设计图、系统拓扑图、技术架构、微服务架构图、云架构图、网络拓扑图。"
---

# Arch Diagram Generator

## 需求说明（SRS）

### 触发条件
- "生成架构图"
- "画一个系统架构图"
- "画架构图"
- "画一个 XX 架构"
- "生成微服务架构图"
- "画技术架构"
- "画云架构/部署架构"

### 功能描述
根据用户文字描述，生成专业暗色主题架构图 HTML 文件（纯 HTML，无依赖，浏览器直接打开）。

### 输入/输出
- **输入**: 架构文字描述（组件列表、连接关系、技术栈）
- **输出**: HTML 文件，保存到 `output/` 目录

### 依赖条件
- Python 3.7+
- 无需任何外部 API Key
- 无需安装任何 npm 包

### 边界情况
- 描述模糊时，基于常见架构模式合理推断
- 组件过多（>15个）时分两层或多列排布
- 不确定的技术选型标注灰色（--color-default）

---

## 核心工作流

**不要用脚本生成 SVG，直接手写 SVG 代码！** 脚本只负责组装 HTML 框架。

工作流程：
1. 接收用户架构描述 → 分析组件、层次、连接关系
2. 按照下方规范手写 SVG 架构图
3. 手写 3 张 Summary Card HTML
4. 手写 Legend 条目
5. 调用 `scripts/generate_diagram.py` 组装最终 HTML

---

## SVG 架构图规范

### 画布设置

```svg
<svg viewBox="0 0 1000 {HEIGHT}" xmlns="http://www.w3.org/2000/svg"
     style="font-family:'JetBrains Mono','Consolas',monospace;">
  <defs>
    <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#64748b"/>
    </marker>
  </defs>
  <!-- 层次标签 -->
  <text x="20" y="30" font-size="14" fill="#475569" font-weight="bold">PRESENTATION</text>
  <!-- 组件和连线 -->
</svg>
```

HEIGHT 计算规则：每层约 120-150px + 层间 60-80px + padding 40px。3 层→约 500px，4 层→约 650px。

### 配色映射

| 类型 | 颜色 | HEX | 使用场景 |
|------|------|-----|---------|
| 前端/客户端 | Cyan | `#06b6d4` | React, Vue, iOS, Android, Web, 小程序 |
| 网关/代理 | Pink | `#ec4899` | API Gateway, Kong, Nginx, 负载均衡 |
| 后端服务 | Emerald | `#10b981` | Node.js, Go, Java, Python, Spring |
| 数据库 | Purple | `#a855f7` | PostgreSQL, MySQL, MongoDB, Redis |
| 消息队列 | Violet | `#8b5cf6` | Kafka, RabbitMQ, Pulsar, SQS |
| 云服务 | Amber | `#f59e0b` | AWS, CloudFront, Lambda, S3, DynamoDB |
| 安全/认证 | Rose | `#f43f5e` | JWT, OAuth, Cognito, Auth0, WAF |
| 存储/CDN | Indigo | `#6366f1` | S3, CDN, OSS, CloudFront |
| 监控/日志 | Lime | `#84cc16` | Prometheus, Grafana, ELK, Datadog |
| 缓存 | Teal | `#14b8a6` | Redis, Memcached |
| 默认/其他 | Slate | `#64748b` | 不确定类型时使用 |

### 组件模板（矩形卡片）

```svg
<!-- 矩形背景 -->
<rect x="{X}" y="{Y}" width="200" height="70" rx="10"
      fill="{COLOR}" fill-opacity="0.12" stroke="{COLOR}" stroke-width="1.5"/>
<!-- 图标(2字符) -->
<text x="{X+20}" y="{Y+35}" font-size="22" fill="{COLOR}">{ICON}</text>
<!-- 组件名称 -->
<text x="{X+52}" y="{Y+28}" font-size="13" font-weight="bold" fill="#e2e8f0">{NAME}</text>
<!-- 技术说明 -->
<text x="{X+52}" y="{Y+48}" font-size="11" fill="#64748b">{TECH}</text>
```

组件宽度：180-220px，高度：60-80px。X 间距：260-300px，Y 间距：130-160px。

### 图标映射

| 组件类型 | 图标(emoji) | 组件类型 | 图标(emoji) |
|----------|------------|----------|------------|
| Frontend/Web | 🌐 | API/Gateway | 🚪 |
| Mobile | 📱 | Database | 🗄️ |
| Cache | ⚡ | Message Queue | 📨 |
| Auth/Security | 🔐 | Storage/CDN | 💾 |
| Monitoring | 📊 | Cloud/Infra | ☁️ |
| Microservice | ⚙️ | Load Balancer | ⚖️ |
| CI/CD | 🔄 | DNS | 🔗 |

### 连接线（箭头）

```svg
<!-- 直线箭头 -->
<line x1="{X1}" y1="{Y1}" x2="{X2}" y2="{Y2}"
      stroke="#334155" stroke-width="2" marker-end="url(#arrowhead)"/>

<!-- 直角折线（用在层次之间的数据流） -->
<polyline points="{X1},{Y1} {X1},{Y_MID} {X2},{Y_MID} {X2},{Y2}"
          fill="none" stroke="#334155" stroke-width="1.5" marker-end="url(#arrowhead)"/>

<!-- 双向连接 -->
<line x1="{X1}" y1="{Y1}" x2="{X2}" y2="{Y2}"
      stroke="#334155" stroke-width="1.5" stroke-dasharray="6,3"
      marker-start="url(#arrowhead-rev)" marker-end="url(#arrowhead)"/>
```

连接线颜色用 `#334155`（border色），不要用太亮的颜色。

**⚠️ 坐标检查**：生成连线后必须验证每条线的起点/终点坐标：
- 起点 = 源组件的底部中心 (x+w/2, y+h)
- 终点 = 目标组件的顶部中心 (x+w/2, y)
- 如果源和目标 X 坐标不同，使用折线或斜线连接

### 布局规范

**分层排布**（从上到下）：
- Y=60~80：层次标签（PRESENTATION / GATEWAY / APPLICATION / DATA / INFRASTRUCTURE）
- 每层 Y 间距 130-160px
- 同层组件水平均匀分布，X 从 40 开始，间距 260-300px

**层次顺序**：
1. **PRESENTATION** - 前端/客户端 (Cyan)
2. **GATEWAY** - 网关/负载均衡 (Pink)
3. **APPLICATION** - 后端服务/微服务 (Emerald)
4. **MESSAGING** - 消息队列 (Violet，可选)
5. **DATA** - 数据库/缓存/存储 (Purple/Teal/Indigo)
6. **INFRASTRUCTURE** - 云服务/K8s/监控 (Amber/Lime)

### 层间数据流标注

在层间中间位置添加小字数据流说明：

```svg
<text x="{X}" y="{Y}" font-size="10" fill="#475569" text-anchor="middle">REST / GraphQL</text>
```

---

## Summary Card 规范

每张卡片格式如下（始终生成 3 张）：

```json
{
  "icon": "🔧",
  "title": "技术栈",
  "desc": "描述该架构使用的核心技术栈",
  "tags": ["React", "Node.js", "PostgreSQL"]
}
```

**3 张卡片主题建议**：
- 卡片 1：技术栈概览（关键组件列表）
- 卡片 2：数据流/通信方式（REST/gRPC/消息队列）
- 卡片 3：部署/扩展方式（K8s/Docker/云服务）

---

## Legend 规范

每项格式：`(颜色HEX, 文字说明)`

```python
legend = [
    ("#06b6d4", "Frontend"),
    ("#10b981", "Backend"),
    ("#a855f7", "Database"),
    ("#f59e0b", "Cloud"),
]
```

---

## 使用方法

### 基本调用

直接对 AI 描述架构：

> 画一个 Web 应用架构图：React 前端 + Node.js API + PostgreSQL 数据库 + Redis 缓存 + JWT 认证

AI 会：
1. 分析架构层次
2. 生成 SVG 图 + Summary Cards + Legend
3. 调用组装脚本输出 HTML

### 组装命令

```bash
python scripts/generate_diagram.py '{"title":"My Architecture","svg":"<svg>...</svg>","cards":[...],"legend":[...]}'
```

参数 JSON：
```json
{
  "title": "架构图标题",
  "svg": "<svg>完整SVG代码</svg>",
  "cards": [
    {"icon": "🔧", "title": "标题", "desc": "描述", "tags": ["tag1", "tag2"]}
  ],
  "legend": [["#06b6d4", "Frontend"], ["#10b981", "Backend"]],
  "output": "output/可选指定路径.html"
}
```

---

## 完整示例

输入描述：
> 标准 Web 应用：React 前端 + Node.js/Express API + PostgreSQL 数据库 + Redis 缓存 + JWT 认证

对应生成逻辑：

```
层次分析:
  1. PRESENTATION: React (Cyan)
  2. APPLICATION: Node.js/Express (Emerald) + JWT Auth (Rose)
  3. DATA: PostgreSQL (Purple) + Redis (Teal)

SVG 布局:
  Y=60:  PRESENTATION 标签
  Y=90:  React 组件 (x=400, w=200)
  Y=180: APPLICATION 标签
  Y=210: JWT 组件 (x=160, w=150) + Express API 组件 (x=500, w=200)
  Y=320: DATA 标签
  Y=350: PostgreSQL (x=280, w=200) + Redis (x=560, w=180)

连线:
  React → API (向下的直线)
  React → JWT (认证请求)
  API → PostgreSQL (数据读写)
  API → Redis (缓存读写)
```

---

## 快速参考卡片

```
配色: Cyan=前端  Emerald=后端  Purple=数据库  Amber=云  Rose=安全  Violet=消息
组件: 矩形圆角 rx=10  宽180-220  高60-80  间距260-300(水平) 130-160(垂直)
图标: 2字符 emoji 在组件内左上角
连线: stroke=#334155  stroke-width=1.5-2  带箭头 marker-end
层次: PRESENTATION → GATEWAY → APPLICATION → DATA → INFRASTRUCTURE
画布: viewBox="0 0 1000 {HEIGHT}"  HEIGHT=层数×150+80
```

---

## 相关文件

- `scripts/generate_diagram.py` - HTML 组装脚本
- `assets/template.html` - 暗色主题 HTML 模板
- `output/` - 生成的架构图保存目录

---

## 注意事项

- **不要用脚本生成 SVG**，直接手写 SVG 代码——这样更可控、更精确
- SVG 代码放在 JSON 字符串中时，内部双引号换成单引号
- 组件名超过 12 字符时缩减或换行，避免超出矩形
- 双向数据流用虚线箭头（stroke-dasharray="6,3"）
- 字体统一用 JetBrains Mono，fallback Consolas

---

## DoD 检查表

**开发日期**: 2026-05-15
**开发者**: 小天才

### 开发前检查
- [x] 已查看现有技能列表，确认无重复功能
- [x] 已阅读相关技能 SKILL.md
- [x] 已决定新建（独立功能，无现存类似技能）

### 开发检查
- [x] SRS 文档完整
- [x] 技能文件结构规范
- [x] 代码使用相对路径
- [x] 配置外置，无敏感信息
- [x] 无 .skill 文件
- [x] 无隐私文件
- [x] SKILL.md 包含使用示例和 SVG 规范

**状态**: ✅ 完成
