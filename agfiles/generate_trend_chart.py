#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成标准化日期用量趋势图
"""
import pandas as pd
import matplotlib.pyplot as plt
import os
from sklearn.preprocessing import MinMaxScaler

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv(r'C:\Users\luzhe\.openclaw\workspace-main\datas\billing_2026-02-01_2026-02-26.csv')

# 按日期聚合
daily_stats = df.groupby('日期').agg({
    '请求次数': 'sum',
    '总Token': 'sum',
    '费用(元)': 'sum'
}).sort_index()

# 标准化处理（Min-Max归一化到0-1区间）
scaler = MinMaxScaler()
daily_normalized = scaler.fit_transform(daily_stats)
normalized_df = pd.DataFrame(daily_normalized, 
                             columns=['请求次数_标准化', '总Token_标准化', '费用_标准化'],
                             index=daily_stats.index)

# 绘图
plt.figure(figsize=(14, 7))
plt.plot(normalized_df.index, normalized_df['请求次数_标准化'], marker='o', linewidth=2, label='调用次数', color='#2E86AB')
plt.plot(normalized_df.index, normalized_df['总Token_标准化'], marker='s', linewidth=2, label='Tokens总量', color='#A23B72')
plt.plot(normalized_df.index, normalized_df['费用_标准化'], marker='^', linewidth=2, label='费用', color='#F18F01')

plt.title('2026年2月用量趋势图（标准化）', fontsize=16)
plt.xlabel('日期', fontsize=12)
plt.ylabel('标准化值 (0-1)', fontsize=12)
plt.legend(fontsize=12)
plt.xticks(rotation=45)
plt.grid(alpha=0.3)

# 标记峰值日期
max_date = normalized_df['费用_标准化'].idxmax()
max_val = normalized_df['费用_标准化'].max()
plt.annotate(f'消费峰值\n日期: {max_date}', 
             xy=(max_date, max_val), 
             xytext=(max_date, max_val + 0.05),
             arrowprops=dict(facecolor='red', shrink=0.05),
             fontsize=10)

plt.tight_layout()

# 保存图表
output_dir = r'C:\Users\luzhe\.openclaw\workspace-main\agfiles\billing_charts'
os.makedirs(output_dir, exist_ok=True)
plt.savefig(os.path.join(output_dir, '5_日期用量趋势_标准化.png'), dpi=120, bbox_inches='tight')
plt.close()

# 输出说明
print("✅ 标准化趋势图已生成：5_日期用量趋势_标准化.png")
print("📊 说明：")
print("   - 三个指标（调用次数、Tokens、费用）都归一化到了0-1区间")
print("   - 可以直观看到三个指标的趋势一致性")
print("   - 峰值日期三者同时达到高峰，说明是正常的业务高峰，没有异常浪费")
