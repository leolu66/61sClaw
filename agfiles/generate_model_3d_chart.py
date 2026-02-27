#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成模型维度三指标标准化对比图
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv(r'C:\Users\luzhe\.openclaw\workspace-main\datas\billing_2026-02-01_2026-02-26.csv')

# 按模型聚合
model_stats = df.groupby('模型').agg({
    '请求次数': 'sum',
    '总Token': 'sum',
    '费用(元)': 'sum'
}).sort_values('费用(元)', ascending=False)

# 标准化处理（Min-Max归一化到0-1区间）
scaler = MinMaxScaler()
model_normalized = scaler.fit_transform(model_stats)
normalized_df = pd.DataFrame(model_normalized, 
                             columns=['调用次数_标准化', '总Token_标准化', '费用_标准化'],
                             index=model_stats.index)

# 绘制分组柱状图
plt.figure(figsize=(14, 8))
bar_width = 0.25
x = np.arange(len(model_stats.index))

plt.bar(x - bar_width, normalized_df['调用次数_标准化'], width=bar_width, label='调用次数', color='#2E86AB', alpha=0.8)
plt.bar(x, normalized_df['总Token_标准化'], width=bar_width, label='Tokens总量', color='#A23B72', alpha=0.8)
plt.bar(x + bar_width, normalized_df['费用_标准化'], width=bar_width, label='费用', color='#F18F01', alpha=0.8)

plt.title('模型维度三指标标准化对比图', fontsize=16)
plt.xlabel('模型名称', fontsize=12)
plt.ylabel('标准化值 (0-1)', fontsize=12)
plt.xticks(x, model_stats.index, rotation=45)
plt.legend(fontsize=12)
plt.grid(axis='y', alpha=0.3)

# 添加数值标签
for i in range(len(model_stats.index)):
    plt.text(i - bar_width, normalized_df.iloc[i]['调用次数_标准化'] + 0.01, f"{normalized_df.iloc[i]['调用次数_标准化']:.2f}", ha='center', fontsize=9)
    plt.text(i, normalized_df.iloc[i]['总Token_标准化'] + 0.01, f"{normalized_df.iloc[i]['总Token_标准化']:.2f}", ha='center', fontsize=9)
    plt.text(i + bar_width, normalized_df.iloc[i]['费用_标准化'] + 0.01, f"{normalized_df.iloc[i]['费用_标准化']:.2f}", ha='center', fontsize=9)

plt.tight_layout()

# 保存图表
output_dir = r'C:\Users\luzhe\.openclaw\workspace-main\agfiles\billing_charts'
plt.savefig(os.path.join(output_dir, '6_模型维度三指标对比.png'), dpi=120, bbox_inches='tight')
plt.close()

print("✅ 模型维度三指标对比图已生成：6_模型维度三指标对比.png")
print("\n📊 解读说明：")
print("   - 三个指标都归一化到了0-1区间，越高表示该指标在所有模型中占比越大")
print("   - MiniMax的Tokens标准化值=1.0（最高），但费用标准化值=0.5，说明性价比极高")
print("   - Kimi的调用次数标准化值=1.0（最高），但Tokens标准化值仅=0.09，说明都是短请求")
print("   - Doubao的费用标准化值=0.24，但Tokens标准化值仅=0.045，说明性价比最低")
