# -*- coding: utf-8 -*-
import pandas as pd
import os

# 读取数据
df = pd.read_csv('C:/Users/luzhe/.openclaw/workspace-main/datas/billing_2026-02-09_2026-02-28.csv')

# 日期维度聚合
daily_df = df.groupby('日期').agg({
    '费用(元)': 'sum',
    '请求次数': 'sum',
    '输入Token': 'sum',
    '输出Token': 'sum',
    '总Token': 'sum'
}).reset_index()

daily_df['IO比'] = daily_df.apply(
    lambda x: round(x['输入Token'] / x['输出Token'], 3) if x['输出Token'] > 0 else 0, 
    axis=1
)

# Top 5 高峰日
top5 = daily_df.nlargest(5, '费用(元)').copy()
avg_cost = daily_df['费用(元)'].mean()
avg_req = daily_df['请求次数'].mean()

# 添加星期
top5['星期'] = pd.to_datetime(top5['日期']).dt.day_name().str[:2]

# 偏差计算
top5['费用偏差%'] = ((top5['费用(元)'] - avg_cost) / avg_cost * 100).round(1)
top5['调用偏差%'] = ((top5['请求次数'] - avg_req) / avg_req * 100).round(1)

# 主要模型
main_models = []
for date in top5['日期']:
    day_data = df[df['日期'] == date].sort_values('费用(元)', ascending=False)
    main_models.append(day_data.iloc[0]['模型'])

top5['主要模型'] = main_models

# 使用模式
def classify_mode(io):
    if io < 0.01: return '阅读型'
    elif io < 0.05: return '均衡型'
    else: return '生成型'

top5['使用模式'] = top5['IO比'].apply(classify_mode)

# 模型维度
model_df = df.groupby('模型').agg({
    '费用(元)': 'sum',
    '请求次数': 'sum',
    '输入Token': 'sum',
    '输出Token': 'sum',
    '总Token': 'sum'
}).reset_index()

model_df['IO比'] = model_df.apply(
    lambda x: round(x['输入Token'] / x['输出Token'], 3) if x['输出Token'] > 0 else 0, 
    axis=1
)
model_df['单位成本'] = (model_df['费用(元)'] / (model_df['总Token'] / 1_000_000)).round(2)
model_df = model_df.sort_values('费用(元)', ascending=False)

# 性价比评级
def get_rating(cost):
    if cost <= 3: return '⭐⭐⭐⭐ 优秀'
    elif cost <= 6: return '⭐⭐⭐ 良好'
    elif cost <= 10: return '⭐⭐ 低效'
    else: return '⭐ 低效'

model_df['性价比'] = model_df['单位成本'].apply(get_rating)

# 周模式
daily_df['星期'] = pd.to_datetime(daily_df['日期']).dt.day_name()
weekly = daily_df.groupby('星期').agg({
    '费用(元)': ['sum', 'mean'],
    '请求次数': ['sum', 'mean'],
    'IO比': 'mean'
})
weekly.columns = ['总费用', '平均费用', '总次数', '平均次数', 'IO比']

# 总费用
total_cost = df['费用(元)'].sum()
total_requests = df['请求次数'].sum()

# 生成报告
report = f'''# 📊 模型账单深度分析报告

**数据范围**: {df['日期'].min()} 至 {df['日期'].max()}
**生成时间**: 2026-03-02

---

## 一、概览统计

| 指标 | 数值 |
|------|------|
| 总费用 | ¥{total_cost:.2f} |
| 总调用次数 | {total_requests:,} 次 |
| 日均费用 | ¥{avg_cost:.2f} |
| 平均 IO 比 | {daily_df["IO比"].mean():.3f} |

## 二、Top 5 消费高峰日深度分析

| 日期 | 星期 | 费用 | 偏差% | 次数 | 偏差% | IO比 | 模式 | 主要模型 |
|------|------|------|-------|------|-------|------|------|----------|
'''

for _, row in top5.iterrows():
    report += f"| {row['日期']} | {row['星期']} | ¥{row['费用(元)']:.2f} | {row['费用偏差%']:+} | {int(row['请求次数']):,} | {row['调用偏差%']:+} | {row['IO比']} | {row['使用模式']} | {row['主要模型']} |\n"

report += f'''
### 高峰日特征分析

**{top5.iloc[0]['日期']}（{top5.iloc[0]['星期']}）**:
- 费用 ¥{top5.iloc[0]['费用(元)']:.2f}（{top5.iloc[0]['费用偏差%']:+}% vs 日均），调用 {int(top5.iloc[0]['请求次数']):,} 次
- 使用模式：**{top5.iloc[0]['使用模式']}**（IO比={top5.iloc[0]['IO比']}）
- 主要模型：{top5.iloc[0]['主要模型']}

## 三、模型选择的多维度影响分析

| 模型 | 总费用 | 占比% | 总次数 | IO比 | 单位成本 | 性价比 |
|------|--------|-------|--------|------|----------|--------|
'''

for _, row in model_df.head(10).iterrows():
    pct = row['费用(元)'] / total_cost * 100
    report += f"| {row['模型']} | ¥{row['费用(元)']:.2f} | {pct:.1f}% | {int(row['请求次数']):,} | {row['IO比']} | ¥{row['单位成本']:.2f} | {row['性价比']} |\n"

# 获取各模型数据
mm = model_df[model_df['模型']=='MiniMax-M2.5'].iloc[0]
kimi = model_df[model_df['模型']=='kimi-k2.5'].iloc[0]
dbp = model_df[model_df['模型']=='doubao-seed-2.0-pro'].iloc[0]
qwp = model_df[model_df['模型']=='qwen3.5-plus'].iloc[0]

report += f'''
### 模型效率洞察

**MiniMax-M2.5**:
- 总费用 ¥{mm['费用(元)']:.2f}，调用 {int(mm['请求次数']):,} 次
- 单位成本：¥{mm['单位成本']:.2f}/百万 Tokens

**Kimi-K2.5**:
- 总费用 ¥{kimi['费用(元)']:.2f}，调用 {int(kimi['请求次数']):,} 次
- 单位成本：¥{kimi['单位成本']:.2f}/百万 Tokens

**Doubao-Pro**:
- 总费用 ¥{dbp['费用(元)']:.2f}，调用 {int(dbp['请求次数']):,} 次
- 单位成本：¥{dbp['单位成本']:.2f}/百万 Tokens

**Qwen-Plus**:
- 总费用 ¥{qwp['费用(元)']:.2f}，调用 {int(qwp['请求次数']):,} 次
- 单位成本：¥{qwp['单位成本']:.2f}/百万 Tokens

## 四、周模式分析

| 星期 | 总费用 | 平均费用 | 总次数 | 平均次数 | IO比 |
|------|--------|----------|--------|----------|------|
'''

week_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
week_cn = {'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三', 'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六', 'Sunday': '周日'}
for day in week_order:
    if day in weekly.index:
        row = weekly.loc[day]
        report += f"| {week_cn[day]} | ¥{row['总费用']:.2f} | ¥{row['平均费用']:.2f} | {int(row['总次数']):,} | {int(row['平均次数']):,} | {row['IO比']:.1f} |\n"

report += f'''
## 五、优化建议

### 立即可执行

1. **限制高成本模型使用**:
   - doubao-seed-2.0-pro（¥{dbp['单位成本']:.2f}/百万）建议限制在极复杂推理场景
   - kimi-k2.5（¥{kimi['单位成本']:.2f}/百万）建议限制在极复杂推理场景

2. **提升高性价比模型占比**:
   - qwen3.5-flash（¥1.31/百万）建议提升使用比例
   - MiniMax-M2.5（¥2.34/百万）建议提升至 60%+

3. **基于 IO 比的动态模型选择**:
   - IO比 < 0.01（阅读型）: 优先使用 QWen-Plus
   - IO比 0.01-0.05（均衡型）: 使用 MiniMax-M2.5
   - IO比 > 0.05（生成型）: 使用 MiniMax-M2.5 或 Kimi

### 成本监控预警

- 🔴 单位成本 > ¥8: 触发优化建议
- 🔴 单日费用 > ¥100: 检查异常批量任务
- 🔴 单一模型占比 > 80%: 建议多元化

---

*报告生成时间：2026-03-02 02:10*
'''

# 写入文件
output_path = 'C:/Users/luzhe/.openclaw/workspace-main/agfiles/billing_report/billing_2026-02-09_2026-02-28_深度分析.md'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(report)

print('Done:', output_path)
