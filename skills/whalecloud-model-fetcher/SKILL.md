---
name: whalecloud-model-fetcher
description: |
  爬取 WhaleCloud Lab 的所有模型信息，生成详细的模型列表报告。
  
  **触发指令：**
  - "获取 WhaleCloud 模型列表"
  - "爬取鲸云模型信息"
  - "WhaleCloud 模型报告"
  - "获取模型列表"
---

# WhaleCloud 模型信息获取器

爬取 WhaleCloud Lab 平台上的所有模型信息，包括模型名称、简介、能力标签等，生成结构化的模型列表报告。

## 需求说明（SRS）

### 触发条件
用户说什么话会触发此技能：
- "获取 WhaleCloud 模型列表"
- "爬取鲸云模型信息"
- "WhaleCloud 模型报告"
- "获取模型列表"
- "whalecloud 有哪些模型"

### 功能描述
1. 自动登录 WhaleCloud Lab 平台（使用 API Key）
2. 访问模型信息页面：https://lab.iwhalecloud.com/gpt-proxy/console/model-info
3. 爬取所有模型卡片信息
4. 按模型类型分组（国产商用、国外商用、多模态、文生图等）
5. 生成结构化的 JSON 报告和 Markdown 汇总报告

### 输入/输出
- **输入**: 无需额外输入，自动执行
- **输出**: 
  - JSON 格式的完整模型数据（`output/models_data.json`）
  - Markdown 格式的汇总报告（`output/models_report.md`）

### 依赖条件
- Python 3.8+
- Playwright (`pip install playwright`)
- Chrome 浏览器
- WhaleCloud Lab API Key（已硬编码在脚本中）

### 边界情况
- 如果未登录，自动使用 API Key 登录
- 如果 Chrome 未在调试模式运行，自动启动
- 网络超时处理

---

## 使用方法

### 基本用法

```bash
python scripts/fetch_models.py
```

### 输出文件

执行后会生成以下文件：
- `output/models_data.json` - 完整的模型数据（JSON 格式）
- `output/models_report.md` - 格式化的 Markdown 报告

---

## 相关文件

- `scripts/fetch_models.py` - 主脚本
- `output/models_data.json` - 输出数据
- `output/models_report.md` - 输出报告

---

## 注意事项

- 首次运行可能需要安装 Playwright：`playwright install chromium`
- 脚本会自动管理 Chrome 的启动和关闭
- 登录状态会保留，下次运行无需重新登录
- 完整爬取约需 30-60 秒

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

### GitHub 同步
- [x] 已提交并推送
- [x] 无隐私文件泄露
- [x] 推送到 main 分支

**状态**: ✅ 完成
