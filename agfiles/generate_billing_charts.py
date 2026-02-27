#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成模型账单分析图表
"""
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv(r'C:\Users\luzhe\.openclaw\workspace-main\datas\billing_2026-02-01_2026-02-26.csv')

# 输出目录
output_dir = r'C:\Users\luzhe\.openclaw\workspace-main\agfiles\billing_charts'
os.makedirs(output_dir, exist_ok=True)

# ------------------------------
# 图表1: 各模型费用占比饼图
# ------------------------------
plt.figure(figsize=(8, 8))
model_cost = df.groupby('模型')['费用(元)'].sum().sort_values(ascending=False)
plt.pie(model_cost.values, labels=model_cost.index, autopct='%1.1f%%', startangle=90)
plt.title('2026年2月各模型费用占比', fontsize=14)
plt.axis('equal')
plt.savefig(os.path.join(output_dir, '1_模型费用占比.png'), dpi=100, bbox_inches='tight')
plt.close()

# ------------------------------
# 图表2: 每日消费趋势折线图
# ------------------------------
plt.figure(figsize=(12, 6))
daily_cost = df.groupby('日期')['费用(元)'].sum().sort_index()
plt.plot(daily_cost.index, daily_cost.values, marker='o', linewidth=2, color='#2E86AB')
plt.title('每日消费趋势 (2026年2月)', fontsize=14)
plt.xlabel('日期', fontsize=12)
plt.ylabel('费用 (元)', fontsize=12)
plt.xticks(rotation=45)
plt.grid(alpha=0.3)
# 标记最高点
max_day = daily_cost.idxmax()
max_cost = daily_cost.max()
plt.annotate(f'峰值: ¥{max_cost:.1f}\n日期: {max_day}', 
             xy=(max_day, max_cost), 
             xytext=(max_day, max_cost + 5),
             arrowprops=dict(facecolor='red', shrink=0.05))
plt.savefig(os.path.join(output_dir, '2_每日消费趋势.png'), dpi=100, bbox_inches='tight')
plt.close()

# ------------------------------
# 图表3: 各模型调用次数柱状图
# ------------------------------
plt.figure(figsize=(10, 6))
model_requests = df.groupby('模型')['请求次数'].sum().sort_values(ascending=False)
plt.bar(model_requests.index, model_requests.values, color='#A23B72')
plt.title('各模型总调用次数', fontsize=14)
plt.xlabel('模型', fontsize=12)
plt.ylabel('调用次数', fontsize=12)
plt.xticks(rotation=45)
plt.grid(axis='y', alpha=0.3)
# 添加数值标签
for i, v in enumerate(model_requests.values):
    plt.text(i, v + 50, str(v), ha='center')
plt.savefig(os.path.join(output_dir, '3_各模型调用次数.png'), dpi=100, bbox_inches='tight')
plt.close()

# ------------------------------
# 图表4: 费用汇总柱状图
# ------------------------------
plt.figure(figsize=(10, 6))
model_cost_sorted = model_cost.sort_values(ascending=False)
plt.bar(model_cost_sorted.index, model_cost_sorted.values, color='#F18F01')
plt.title('各模型总费用 (元)', fontsize=14)
plt.xlabel('模型', fontsize=12)
plt.ylabel('总费用 (元)', fontsize=12)
plt.xticks(rotation=45)
plt.grid(axis='y', alpha=0.3)
# 添加数值标签
for i, v in enumerate(model_cost_sorted.values):
    plt.text(i, v + 2, f'¥{v:.1f}', ha='center')
plt.savefig(os.path.join(output_dir, '4_各模型总费用.png'), dpi=100, bbox_inches='tight')
plt.close()

print(f"✅ 图表生成完成，已保存到: {output_dir}")
print("生成的图表：")
print("1. 1_模型费用占比.png")
print("2. 2_每日消费趋势.png")
print("3. 3_各模型调用次数.png")
print("4. 4_各模型总费用.png")
