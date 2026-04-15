# 微信公众号文章获取工具 v2.0

基于模块化设计的微信公众号文章获取工具，支持智能数量策略、按日期分目录存储、自动生成总结报告。

## 新功能特性

### 1. 按日期分目录存储
- 自动在 `D:\anthropic\wechat` 下创建日期子目录（如 `20260218`）
- 当天多次运行，同名文件直接覆盖
- 便于按日期管理和归档

### 2. 智能数量策略
- **发布频繁**（最近3天≥3篇）：获取最多10篇
- **发布不频繁**（最近3天<3篇）：仅获取最近3天的文章
- 避免获取过时内容，节省时间和存储

### 3. 公众号总结报告
每个公众号处理完成后，自动生成总结报告：
- 文章清单（含标题、链接、发布时间）
- 每篇文章的AI摘要
- 保存为 `{公众号名}_总结.md`

## 架构设计

```
main.py (主程序)
  ├── config.py (配置管理)
  ├── article_list_fetcher.py (列表获取 - 智能数量)
  ├── article_content_reader.py (内容读取)
  ├── article_saver.py (文件保存 - 日期子目录)
  ├── article_summarizer.py (文章总结)
  └── report_generator.py (报告生成)
```

## 使用方法

### 1. 基础使用（使用配置文件中的凭证）

```bash
cd scripts
python main.py
```

### 2. 交互式输入凭证（推荐）

每次运行时提示输入新的 Cookie 和 Token，避免凭证过期问题：

```bash
python main.py --prompt
# 或简写
python main.py -p
```

运行后会提示：
```
============================================================
微信凭证输入
============================================================
提示: Cookie 和 Token 有效期较短，过期后需要重新获取
获取方式: 访问 https://mp.weixin.qq.com -> 扫码登录 -> F12开发者工具
============================================================

请输入 Cookie (直接回车使用配置文件中的值): 
请输入 Token (直接回车使用配置文件中的值): 
```

### 3. 命令行参数方式

```bash
# 直接通过命令行参数传入
python main.py --cookie "your_cookie" --token "your_token"
```

### 4. 运行模式

#### 4.1 批次处理模式（默认）

自动或手动调度处理多个公众号：

```bash
# 自动调度（每批处理完自动继续）
python main.py --mode batch --schedule auto

# 手动调度（每批处理完等待确认）
python main.py --mode batch --schedule manual
# 或简写
python main.py -m batch -s manual
```

手动调度流程：
1. 显示当前批次要处理的公众号
2. 提示：`是否处理该批次？(y[是]/n[跳过]/q[退出]):`
3. 处理完成后提示：`按回车继续下一批次，或输入 q 退出`

#### 4.2 单公众号模式

只处理指定的一个公众号：

```bash
# 处理单个公众号
python main.py --mode single --account "新智元"
# 或简写
python main.py -m single -a "新智元"
```

#### 4.3 进度保存

程序会自动保存处理进度到 `.progress.json` 文件：
- 已完成的公众号不会重复处理
- 失败的公众号可以重新处理
- 随时中断，下次自动继续

### 5. 总结报告生成

支持独立生成或重新生成公众号总结报告：

```bash
# 生成单个公众号的总结报告
python main.py --mode summary --account "新智元"
python main.py -m summary -a "InfoQ"

# 批量生成所有公众号的总结报告
python main.py --mode summary-all
python main.py -m summary-all
```

**使用场景：**
- 文章已下载但总结报告丢失或需要更新
- 想重新生成所有公众号的总结报告
- 单独为某个公众号补充生成总结

### 6. 主汇总报告生成

生成包含所有公众号文章的主汇总报告：

```bash
# 生成主汇总报告
python main.py --mode master-summary
python main.py -m master-summary
```

**报告特点：**
- 文件名格式：`Summary_YYYYMMDD_HHMM.md`
- 包含所有公众号列表（表格形式）
- 每个公众号的文章列表（表格形式）
- 点击公众号名称可打开对应的总结报告
- 点击文章标题可打开原文链接

**报告结构：**
```markdown
# 微信公众号文章汇总报告

## 公众号列表
| 序号 | 公众号 | 文章数 | 总结报告 |
|------|--------|--------|----------|
| 1 | 新智元 | 10 | [新智元_总结.md](./新智元_总结.md) |
| 2 | InfoQ | 10 | [InfoQ_总结.md](./InfoQ_总结.md) |
...

## 文章详情
### 新智元
| 序号 | 文章标题 | 发布时间 |
|------|----------|----------|
| 1 | [文章标题](原文链接) | 2026-02-17 |
...
```

### 7. 使用示例

```bash
# 示例1：自动批次处理（推荐日常使用）
python main.py

# 示例2：手动控制每批处理
python main.py -s manual

# 示例3：只处理单个公众号
python main.py -m single -a "InfoQ"

# 示例4：每批2个公众号，手动调度
python main.py -b 2 -s manual

# 示例5：更新凭证后手动处理
python main.py -p -s manual

# 示例6：生成单个公众号总结报告
python main.py -m summary -a "新智元"

# 示例7：批量生成所有公众号总结报告
python main.py -m summary-all

# 示例8：生成主汇总报告
python main.py -m master-summary
```

```json
{
  "accounts": [
    {"name": "究模智", "enabled": true},
    {"name": "新智元", "enabled": true},
    {"name": "智猩猩AI", "enabled": true},
    {"name": "苏哲管理咨询", "enabled": true},
    {"name": "架构师", "enabled": true},
    {"name": "PaperAgent", "enabled": true},
    {"name": "腾讯研究院", "enabled": true},
    {"name": "AI寒武纪", "enabled": true},
    {"name": "InfoQ", "enabled": true},
    {"name": "刘邦学AI", "enabled": true},
    {"name": "投资界", "enabled": true},
    {"name": "亿欧网", "enabled": true},
    {"name": "智能体AI", "enabled": true},
    {"name": "深思圈", "enabled": true}
  ],
  "fetch": {
    "min_articles": 3,        // 最少文章数
    "max_articles": 10,       // 最多文章数
    "days_threshold": 3,      // 天数阈值（3天）
    "random_order": true,     // 随机顺序（反爬）
    "min_delay": 2,           // 最小延迟（秒）
    "max_delay": 5            // 最大延迟（秒）
  },
  "output": {
    "base_dir": "D:\\anthropic\\wechat",
    "use_date_subdir": true,  // 使用日期子目录
    "naming_pattern": "{account}_{title}.md"
  }
}
```

### 3. 环境变量方式（推荐）

```bash
# Windows PowerShell
$env:WECHAT_COOKIE="your_cookie"
$env:WECHAT_TOKEN="your_token"
python main.py
```

## 输出示例

```
============================================================
微信公众号文章获取工具 v2.0
============================================================

[配置] 目标公众号: 究模智, 新智元, 智猩猩AI, ... (14个)
[配置] 智能数量策略: 最少3篇 / 最多10篇
[配置] 天数阈值: 3天
[输出] 目录: D:\anthropic\wechat\20260218
[配置] 已启用随机获取顺序

============================================================
[处理] 公众号: 新智元
============================================================
[搜索] 正在查找公众号: 新智元
[成功] 找到公众号: 新智元
       微信号: AI_era
[获取] 正在读取文章列表 (智能数量)...
       发布频率较低，仅返回最近3天的 5 篇
[完成] 成功获取 5 篇文章

[1/5] 春晚机器人炸翻全球，10亿人围观零翻车...
  [访问] http://mp.weixin.qq.com/s?...
  [成功] 春晚机器人炸翻全球，10亿人围观...

...

[总结] 正在生成 新智元 的文章总结报告...
[完成] 总结报告已保存: 新智元_总结.md

============================================================
📊 执行报告
============================================================
总计: 86 篇
成功: 84 篇
失败: 2 篇
============================================================

[报告] 总报告已保存: D:\anthropic\wechat\20260218\report.json
```

## 输出目录结构

```
D:\anthropic\wechat\
├── 20260218\                    # 日期子目录
│   ├── 新智元\                  # 公众号子目录
│   │   ├── 春晚机器人炸翻全球.md
│   │   ├── Anthropic预警成真.md
│   │   └── ...
│   ├── 究模智\                  # 公众号子目录
│   │   ├── 重磅！OpenClaw创始人.md
│   │   └── ...
│   ├── 新智元_总结.md           # 公众号总结报告（在日期目录下）
│   ├── 究模智_总结.md
│   ├── ...
│   └── report.json              # 总执行报告
├── 20260217\                    # 历史日期
│   └── ...
└── ...
```

## 公众号总结报告格式

```markdown
# 新智元 - 文章总结报告

**生成时间**: 2026-02-18 10:35
**文章数量**: 5 篇

---

## 文章清单

1. [春晚机器人炸翻全球，10亿人围观零翻车！](http://mp.weixin.qq.com/s?...)
   - 发布时间: 02-17 14:53
2. [Anthropic预警成真！AI写长文网暴人类工程师](http://mp.weixin.qq.com/s?...)
   - 发布时间: 02-17 14:53
...

---

## 文章摘要

### 1. 春晚机器人炸翻全球，10亿人围观零翻车！

中国春晚机器人表演引发全球关注，展示了人形机器人的最新进展...

### 2. Anthropic预警成真！AI写长文网暴人类工程师

Anthropic的研究显示，AI可能产生意外的负面行为...

---

*本报告由自动化工具生成*
```

## 依赖安装

```bash
pip install playwright requests
playwright install chromium
```

## 注意事项

1. Cookie 和 Token 有效期较短，过期后需要重新获取
2. 智能数量策略会自动调整获取数量，避免过时内容
3. 每天首次运行会创建新的日期子目录
4. 同一公众号多次运行，总结报告会被覆盖
