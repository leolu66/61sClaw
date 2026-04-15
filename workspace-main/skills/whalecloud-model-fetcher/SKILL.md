---
name: whalecloud-model-fetcher
description: |
  爬取 WhaleCloud Lab 的所有模型信息，生成详细的模型列表报告，支持查询单个模型详情和模糊搜索模型列表。
  
  **触发指令：**
  - "获取 WhaleCloud 模型列表" - 爬取所有模型
  - "爬取鲸云模型信息" - 爬取所有模型
  - "WhaleCloud 模型报告" - 爬取所有模型
  - "获取模型列表" - 爬取所有模型
  - "查询模型 xxx" - 查询单个模型详情
  - "查询模型详情 xxx" - 查询单个模型详情
  - "model info xxx" - 查询单个模型详情
  - "查询模型列表 xxx" - 模糊搜索模型列表
  - "搜索模型 xxx" - 模糊搜索模型列表
  - "models list xxx" - 模糊搜索模型列表
---

# WhaleCloud 模型信息获取器

爬取 WhaleCloud Lab 平台上的所有模型信息，包括模型名称、简介、能力标签等，生成结构化的模型列表报告。

## 功能概述

本技能提供四个核心功能：

1. **获取全部模型列表** - 爬取 WhaleCloud Lab 平台上的所有模型信息，生成完整的模型报告
2. **查询单个模型详情** - 实时查询指定模型的详细信息，支持与本地数据比对并更新
3. **模糊搜索模型列表** - 根据关键词搜索匹配的模型列表，支持选择后查询详情
4. **模型筛选和推荐** - 基于能力标签、上架时间、价格、上下文长度等多维度筛选和分析模型

---

## 需求说明（SRS）

### 功能一：获取全部模型列表

#### 触发条件
- "获取 WhaleCloud 模型列表"
- "爬取鲸云模型信息"
- "WhaleCloud 模型报告"
- "获取模型列表"
- "whalecloud 有哪些模型"

#### 功能描述
1. 自动登录 WhaleCloud Lab 平台（使用 API Key）
2. 访问模型信息页面：https://lab.iwhalecloud.com/gpt-proxy/console/model-info
3. 爬取所有模型卡片信息
4. 按模型类型分组（国产商用、国外商用、多模态、文生图等）
5. 生成结构化的 JSON 报告和 Markdown 汇总报告

#### 输出文件
- `output/models_data_full.json` - 完整的模型数据（JSON 格式）
- `output/models_report_full.md` - 格式化的 Markdown 报告

---

### 功能二：查询单个模型详情

#### 触发条件
- "查询模型 xxx"
- "查询模型详情 xxx"
- "model info xxx"
- "查一下 xxx 模型"

#### 功能描述
1. 启动浏览器，实时访问 WhaleCloud Lab 平台
2. 在页面上搜索并匹配指定模型
3. 进入模型详情页，提取完整信息（价格、规格、能力标签等）
4. 与本地缓存数据比对（如果存在）
5. 如有差异，提示用户确认后更新本地数据

#### 输出格式
```
🤖 模型详情: DeepSeek-R1

📋 基本信息
   模型ID: deepseek-r1-250528
   编码: deepseek-r1-250528
   简介: 后端对接火山云、算能的DeepSeek R1模型

💰 价格信息
   输入: ¥4 元/M tokens
   输出: ¥16 元/M tokens
   缓存: ¥0.8 元/M tokens
   计费方式: 按量计费

⚙️ 技术规格
   上下文长度: 128K
   最大输出: 32K
   上架时间: 2025-05-28

🏷️ 能力标签: 深度思考、文本生成、工具调用、结构化输出、长上下文
```

#### 数据比对
当检测到本地数据与实时数据不一致时，会显示差异对比：
```
⚠️  字段变更:
字段         本地数据                   最新数据
----------------------------------------------------------------------
输入价格      ¥2 元/M tokens            → ¥4 元/M tokens
输出价格      ¥8 元/M tokens            → ¥16 元/M tokens
```

#### 边界情况
- **模型不存在**：提示"未找到模型 xxx，请检查模型名称"
- **多个匹配**：列出所有匹配项，让用户选择更精确的名称
- **本地数据不存在**：仅显示查询结果，不提示比对
- **数据一致**：显示"✅ 数据一致，无需更新"

---

### 功能三：模糊搜索模型列表

#### 触发条件
- "查询模型列表 xxx"
- "搜索模型 xxx"
- "models list xxx"
- "查找模型 xxx"

#### 功能描述
1. 启动浏览器，实时访问 WhaleCloud Lab 平台
2. 根据关键词模糊匹配所有模型名称
3. 返回编号列表，显示模型名称和简介
4. 支持选择编号后直接查询详情

#### 输出格式
```
找到 5 个匹配 "kimi" 的模型：

[1] kimi-k2
    对应模型【kimi-k2】...
[2] kimi-k2-thinking
    对应模型【kimi-k2-thinking】...
[3] kimi-k2-thinking-turbo
    对应模型【kimi-k2-thinking-turbo】...
[4] kimi-k2-turbo
    对应模型【kimi-k2-turbo】...
[5] kimi-k2.5
    对应模型【kimi-k2.5】...

输入编号查询详情 (1-5), 或输入 0 取消:
```

#### 交互流程
```
用户: 查询模型列表 kimi
系统: 显示匹配列表 [1]-[5]
用户: 3
系统: 调用查询详情显示 kimi-k2-thinking-turbo 的完整信息
```

#### 边界情况
- **无匹配**：提示"未找到匹配 xxx 的模型"
- **单个匹配**：可直接显示详情或提示用户确认
- **多个匹配**：列出所有匹配项供选择

---

## 使用方法

### 功能一：获取全部模型列表

```bash
python scripts/fetch_models.py
```

输出文件：
- `output/models_data_full.json` - 完整的模型数据（JSON 格式）
- `output/models_report_full.md` - 格式化的 Markdown 报告

### 功能二：查询单个模型详情

```bash
python scripts/query_model.py "模型名称"
```

示例：
```bash
python scripts/query_model.py "DeepSeek-R1"
python scripts/query_model.py "deepseek"
python scripts/query_model.py "GPT-4o"
```

参数说明：
- `模型名称` - 支持精确匹配或模糊匹配
- `--update` - 自动更新本地数据（不询问确认）

示例（自动更新）：
```bash
python scripts/query_model.py "DeepSeek-R1" --update
```

### 功能三：模糊搜索模型列表

```bash
python scripts/list_models.py "关键词"
```

示例：
```bash
python scripts/list_models.py "kimi"
python scripts/list_models.py "deepseek"
python scripts/list_models.py "gpt"
```

参数说明：
- `关键词` - 支持模糊匹配模型名称
- `--select <编号>` - 直接选择指定编号查询详情

示例（直接选择）：
```bash
python scripts/list_models.py "kimi" --select 3
```

---

## 相关文件

- `scripts/fetch_models.py` - 获取全部模型列表脚本
- `scripts/query_model.py` - 查询单个模型详情脚本
- `scripts/list_models.py` - 模糊搜索模型列表脚本（新增）
- `output/models_data_full.json` - 完整模型数据
- `output/models_report_full.md` - Markdown 格式报告

---

## 注意事项

- 首次运行可能需要安装 Playwright：`playwright install chromium`
- 脚本会自动管理 Chrome 的启动和关闭
- 登录状态会保留，下次运行无需重新登录
- 完整爬取约需 30-60 秒
- 单个模型查询约需 10-20 秒
- 模型列表搜索约需 15-30 秒
- 查询模型时会自动与本地数据比对，如有变更会提示更新

---

## DoD 检查表

**开发日期**: 2026-04-04
**开发者**: 小天才

### 开发前检查
- [x] 已查看现有技能列表，确认无重复功能
- [x] 已阅读相关技能 SKILL.md，了解可复用组件（参考了 api-balance-checker）
- [x] 已决定是扩展还是新建（新建独立技能）

### 开发检查
- [x] SRS 文档完整（触发条件、功能、输入输出、依赖、边界）
- [x] 技能文件结构规范
- [x] 代码使用相对路径
- [x] 配置外置（如需要）
- [x] 功能测试通过
- [x] 触发测试通过
- [x] 无 .skill 文件

### 功能更新记录

**2026-04-06**: 新增查询单个模型详情功能
- 新增 `scripts/query_model.py` 脚本
- 支持实时爬取单个模型信息
- 支持与本地数据比对并更新
- 更新 SKILL.md 文档

**2026-04-06**: 新增模糊搜索模型列表功能
- 新增 `scripts/list_models.py` 脚本
- 支持根据关键词模糊匹配模型列表
- 支持选择编号后查询详情
- 更新 SKILL.md 文档

---

## GitHub 同步
- [x] 已提交并推送
- [x] 无隐私文件泄露
- [x] 推送到 main 分支

**状态**: ✅ 完成
