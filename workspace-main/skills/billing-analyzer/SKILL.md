---
name: billing-analyzer
description: 模型账单自动分析工具。自动分析模型消费 CSV 账单，生成多维度数据分析、可视化图表和专业分析报告。
triggers:
  - 分析账单
  - 账单分析
  - 生成账单报告
  - 模型消费分析
  - 成本分析
---

# 模型账单分析技能

自动处理模型消费账单 CSV 文件，一站式生成分析报告和可视化图表。

**重要：区分两个不同意图：**

1. **生成账单报告** - 用户想分析新的账单数据，运行完整分析流程（加载→分析→生成图表→生成报告）
2. **查看账单** - 用户想看已有的账单报告，直接显示报告内容，如果不存在则提示

## 路径配置规范

本技能遵循**技能自包含**原则，支持**配置文件**方式设置路径。

### 配置文件

`config.json`（位于技能目录）：

```json
{
  "output_dir": "./billing_report",
  "shared_output_dir": "D:\\projects\\workspace\\shared\\output\\billing_report"
}
```

**配置说明**：
- `output_dir` - 默认输出目录（支持相对路径，相对于技能目录）
- `shared_output_dir` - 共享输出目录（用于多智能体协作）

### 使用方式

```bash
# 方式1：使用默认配置（当前目录/billing_report/）
python billing_analyzer.py billing.csv

# 方式2：使用共享输出目录（从配置读取）
python billing_analyzer.py billing.csv --shared

# 方式3：指定输出目录（覆盖配置）
python billing_analyzer.py billing.csv --output-dir ./my_report

# 方式4：指定数据目录和输出目录
python billing_analyzer.py billing.csv --datas-dir D:\input --output-dir D:\output
```

### 路径优先级

1. 命令行参数 `--output-dir`（最高优先级）
2. `--shared` 参数 → 使用 `shared_output_dir` 配置
3. 配置文件中的 `output_dir`
4. 默认：`./billing_report/`（技能目录下）

---

## 意图识别

| 用户意图 | 典型表述 | 处理逻辑 |
|---------|---------|---------|
| 生成报告 | "生成账单报告"、"分析账单"、"账单分析"、"生成报告" | 运行完整分析流程 |
| 查看报告 | "看账单"、"查看账单"、"显示账单"、"账单呢" | 直接读取并显示报告文件 |

---

## 功能说明

## 脚本路径

- 主脚本：`C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\billing_analyzer.py`

## 依赖安装

```bash
pip install pandas matplotlib scikit-learn
```

## 使用方法

### 生成账单报告（完整分析）

```bash
# 快速分析
python "C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\billing_analyzer.py" <账单文件名>

# 指定报告名称
python "C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\billing_analyzer.py" <账单文件名> <报告名称>
```

**示例：**
```bash
# 分析 2 月账单，自动生成报告
python billing_analyzer.py billing_2026-02-01_2026-02-26.csv

# 使用共享目录（多智能体协作）
python billing_analyzer.py billing_2026-02-01_2026-02-26.csv --shared

# 自定义报告名称
python billing_analyzer.py billing_2026-02.csv 2026年2月账单分析报告.md
```

### 查看账单报告（读取已有报告）

**渠道区分处理：**

```bash
# 方式 1：使用 --channel 参数（推荐，自动区分）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\view_report.py" --channel webchat
python "C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\view_report.py" --channel feishu

# 方式 2：手动指定行为（兼容旧用法）
# WebChat/计算机渠道：直接用系统默认应用打开报告
python "C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\view_report.py"

# 飞书渠道：读取并输出报告内容（用于总结）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\view_report.py" --summarize

# 列出所有报告
python "C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\view_report.py" --list
```

**处理逻辑：**

1. **WebChat/计算机渠道**（`--channel webchat` 或无参数）：
   - 直接用系统默认应用打开报告文件（.md 用 Markdown 编辑器打开）
   - 输出：`✅ 已打开账单报告：<文件名>`

2. **飞书渠道**（`--channel feishu` 或 `--summarize`）：
   - 读取报告文件内容
   - 总结报告要点，组织成易读的文本格式
   - 输出完整报告内容供用户查看
   - 如果不存在则提示

3. **无报告时**：
   - 提示用户需要先生成报告

**输出示例（WebChat 渠道）：**
```
✅ 已打开账单报告：billing_2026-02-01_2026-02-27 (1)_分析报告.md
```

**输出示例（飞书渠道）：**
```
[完整报告内容...]
```

**输出示例（无报告时）：**
```
❌ 报告目录中没有找到账单报告文件
```

---

## 输出内容

### 生成报告输出

分析完成后自动生成以下内容：
1. **分析报告**：Markdown 格式的专业分析报告，包含概览、可视化图表、核心分析、优化建议
2. **可视化图表**：7 张分析图表
   - 1_模型费用占比.png
   - 2_用量趋势标准化.png - 四指标趋势（调用次数、输入 Token、输出 Token、费用）
   - 3_模型三指标对比.png
   - 4_Top5 高峰日.png
   - 5_IO 比趋势.png
   - 6_模型归因.png
   - 7_周模式.png
3. **自动命名**：报告名格式 `ZD-开始日期-结束日期.md`

**图表说明：**
- **用量趋势标准化图**：展示调用次数、输入 Token、输出 Token、费用四个指标的标准化趋势（0-1）。纵坐标已标准化，不同量级的指标在同一区段内，便于对比趋势变化。输入/输出分开显示，可清晰看出两者使用情况。

### 查看报告输出

- 如果存在最新报告：显示报告完整内容
- 如果不存在报告：提示用户需要先生成报告

## 支持的 CSV 格式
账单 CSV 需要包含以下字段：
| 字段名 | 类型 | 说明 |
|--------|------|------|
| 日期 | 字符串 | 格式：YYYY-MM-DD |
| 模型 | 字符串 | 模型名称 |
| 请求次数 | 整数 | 该日该模型调用次数 |
| 输入 Token | 整数 | 输入 Token 总量 |
| 输出 Token | 整数 | 输出 Token 总量 |
| 总 Token | 整数 | 总 Token 量 |
| 费用 (元) | 浮点数 | 消费金额 |

## 分析维度
1. **概览统计**：总费用、总调用次数、总 Tokens、输入输出比
2. **模型维度分析**：各模型费用占比、调用次数、单位成本、性价比评级
3. **时间维度分析**：每日消费趋势、峰值分析
4. **效率分析**：单次调用成本、单位 Token 成本、优化空间
5. **深度洞察**：IO 比趋势、模型归因、周模式、异常检测
6. **优化建议**：模型分层使用策略、成本优化方案

## 输出路径
- **默认**：`./billing_report/`（基于当前工作目录或配置）
- **共享目录**：`D:\projects\workspace\shared\output\billing_report`（使用 `--shared` 参数）
- **图表**：`./billing_report/charts/`

## 示例输出
```
✅ 加载数据成功，共 64 条记录
🔍 正在执行数据分析...
✅ 数据分析完成（基础 + 深度）
📊 正在生成图表...
✅ 图表生成完成（7 张），已保存到：./billing_report/charts/20260305_1415
📝 正在生成分析报告...
✅ 报告生成完成：./billing_report/ZD-0210-0304.md

🎉 全流程分析完成！报告路径：./billing_report/ZD-0210-0304.md
```
