---
name: billing-analyzer
description: 模型账单自动分析工具。自动分析模型消费CSV账单，生成多维度数据分析、可视化图表和专业分析报告。当用户提供账单文件，需要分析模型消费情况、成本优化建议时使用此技能。
triggers:
  - 分析账单
  - 账单分析
  - 生成账单报告
  - 模型消费分析
  - 成本分析
  - 查看账单
---

# 模型账单分析技能

自动处理模型消费账单CSV文件，一站式生成分析报告和可视化图表。

## 脚本路径

- 主脚本：`C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\billing_analyzer.py`

## 依赖安装

```bash
pip install pandas matplotlib scikit-learn
```

## 使用方法

### 快速使用
```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\billing_analyzer.py" <账单文件名>
```

### 指定报告名称
```bash
python "C:\Users\luzhe\.openclaw\workspace-main\skills\billing-analyzer\scripts\billing_analyzer.py" <账单文件名> <报告名称>
```

### 示例
```bash
# 分析2月账单，自动生成报告
python billing_analyzer.py billing_2026-02-01_2026-02-26.csv

# 自定义报告名称
python billing_analyzer.py billing_2026-02.csv 2026年2月账单分析报告.md
```

## 输出内容
分析完成后自动生成以下内容：
1. **分析报告**：Markdown格式的专业分析报告，包含概览、可视化图表、核心分析、优化建议
2. **可视化图表**：3张核心分析图表
   - 1_模型费用占比.png
   - 2_用量趋势标准化.png
   - 3_模型三指标对比.png
3. **自动打开**：报告生成后自动在默认编辑器打开

## 支持的CSV格式
账单CSV需要包含以下字段：
| 字段名 | 类型 | 说明 |
|--------|------|------|
| 日期 | 字符串 | 格式：YYYY-MM-DD |
| 模型 | 字符串 | 模型名称 |
| 请求次数 | 整数 | 该日该模型调用次数 |
| 输入Token | 整数 | 输入Token总量 |
| 输出Token | 整数 | 输出Token总量 |
| 总Token | 整数 | 总Token量 |
| 费用(元) | 浮点数 | 消费金额 |

## 分析维度
1. **概览统计**：总费用、总调用次数、总Tokens、输入输出比
2. **模型维度分析**：各模型费用占比、调用次数、单位成本、性价比评级
3. **时间维度分析**：每日消费趋势、峰值分析
4. **效率分析**：单次调用成本、单位Token成本、优化空间
5. **优化建议**：模型分层使用策略、成本优化方案

## 输出路径
所有分析结果保存在：`./agfiles/billing_report/` 目录下
- 分析报告：`./agfiles/billing_report/<报告名称>_分析报告.md`
- 可视化图表：`./agfiles/billing_report/charts/`

## 示例输出
```
✅ 加载数据成功，共 45 条记录
🔍 正在执行数据分析...
✅ 数据分析完成
📊 正在生成图表...
✅ 图表生成完成，已保存到: ./output/charts
📝 正在生成分析报告...
✅ 报告生成完成: ./output/billing_2026-02_分析报告.md

🎉 全流程分析完成！报告路径: ./output/billing_2026-02_分析报告.md
```
