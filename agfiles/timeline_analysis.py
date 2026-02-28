# -*- coding: utf-8 -*-
import pandas as pd
import sys
import io
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 读取数据
df = pd.read_csv(r'C:\Users\luzhe\.openclaw\workspace-main\datas\billing_2026-02-01_2026-02-27 (1).csv')

# 按日期排序
df['日期'] = pd.to_datetime(df['日期'])
df = df.sort_values('日期')

# 按日期汇总
daily_summary = df.groupby('日期').agg({
    '费用(元)': 'sum',
    '请求次数': 'sum',
    '输入Token': 'sum',
    '输出Token': 'sum',
    '模型': lambda x: ', '.join(sorted(x.unique()))  # 记录使用的所有模型
}).reset_index()

# 确保日期是字符串
daily_summary['日期'] = daily_summary['日期'].dt.strftime('%Y-%m-%d')

# 计算关键指标
daily_summary['整体IO比'] = daily_summary['输出Token'] / daily_summary['输入Token']
daily_summary['模型数量'] = daily_summary['模型'].str.count(',') + 1
daily_summary['单位成本(元/次)'] = daily_summary['费用(元)'] / daily_summary['请求次数']
daily_summary['单位成本(元/百万Token)'] = daily_summary['费用(元)'] / (daily_summary['输入Token'] + daily_summary['输出Token']) * 1_000_000
daily_summary['输出占比'] = daily_summary['输出Token'] / (daily_summary['输入Token'] + daily_summary['输出Token'])

# 按周分组
daily_summary['星期'] = daily_summary['日期'].dt.day_name()
weekly_summary = daily_summary.groupby('星期').agg({
    '费用(元)': 'mean',
    '请求次数': 'mean',
    '整体IO比': 'mean',
    '模型数量': 'mean'
})

print('='*120)
print('时间线分析：用户习惯与模型选择演变')
print('='*120)

# 1. 时间趋势总览
print('\n' + '='*120)
print('一、时间趋势总览')
print('='*120)

print('\n每日核心指标（按时间顺序）：')
print('-'*120)
print(f'{"日期":<12} {"星期":<10} {"费用":<10} {"次数":<8} {"输入":<15} {"输出":<15} {"IO比":<10} {"模型数量":<10} {"单位成本":<15} {"使用模型":<50}')
print('-'*120)

for _, row in daily_summary.iterrows():
    date = row['日期'].strftime('%Y-%m-%d')
    weekday = row['星期']
    cost = row['费用(元)']
    req = int(row['请求次数'])
    inp = int(row['输入Token'])
    outp = int(row['输出Token'])
    io = row['整体IO比']
    model_count = row['模型数量']
    unit_cost = row['单位成本(元/百万Token)']
    models = row['模型'][:50]  # 限制长度
    
    # 判断使用模式
    if io < 0.01:
        pattern = '阅读型'
    elif io < 0.05:
        pattern = '均衡型'
    elif io < 0.15:
        pattern = '生成型'
    else:
        pattern = '大生成型'
    
    print(f'{date:<12} {weekday:<10} ¥{cost:<8.2f} {req:>6} {inp:>10,} {outp:>10,} {io:>8.3f} {model_count:>6} ¥{unit_cost:<10.3f} {pattern:<8} {models:<50}')

# 2. 周模式分析
print('\n' + '='*120)
print('二、周模式分析')
print('='*120)

print('\n平均指标（按星期）：')
print('-'*120)
print(f'{"星期":<10} {"平均费用":<12} {"平均次数":<12} {"平均IO比":<10} {"平均模型数":<12} {"使用特征":<20}')
print('-'*120)

week_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
weekday_map = {'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三', 'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六', 'Sunday': '周日'}

for week in week_order:
    if week not in weekly_summary.index:
        continue
    
    row = weekly_summary.loc[week]
    cost = row['费用(元)']
    req = row['请求次数']
    io = row['整体IO比']
    model_count = row['模型数量']
    
    # 判断使用特征
    if io < 0.01:
        feature = '阅读主导'
    elif io < 0.05:
        feature = '均衡使用'
    elif io < 0.15:
        feature = '生成主导'
    else:
        feature = '大生成'
    
    print(f'{weekday_map[week]:<10} ¥{cost:>8.2f} {req:>8.0f} {io:>8.3f} {model_count:>6.0f} {feature:<20}')

# 3. 阶段划分与变化点
print('\n' + '='*120)
print('三、阶段划分与关键变化点')
print('='*120)

# 计算滑动窗口平均值（3天移动平均）
daily_summary['3日平均费用'] = daily_summary['费用(元)'].rolling(window=3, center=True).mean()
daily_summary['费用趋势'] = daily_summary['费用(元)'].pct_change()

print('\n识别关键变化点：')
print('-'*120)

# 识别峰值和低谷
max_cost_day = daily_summary.loc[daily_summary['费用(元)'].idxmax()]
min_cost_day = daily_summary.loc[daily_summary['费用(元)'].idxmin()]

print(f'\n峰值日：{max_cost_day["日期"]}（¥{max_cost_day["费用(元)"]:.2f}）')
print(f'  费用：¥{max_cost_day["费用(元)"]:.2f}')
print(f'  使用模型：{max_cost_day["模型"]}')

print(f'\n低谷日：{min_cost_day.strftime("%Y-%m-%d")}（¥{min_cost_day["费用(元)"]:.2f}）')
print(f'  费用：¥{min_cost_day["费用(元)"]:.2f}')
print(f'  使用模型：{min_cost_day["模型"]}')

# 识别趋势转折点
trend_changes = daily_summary[daily_summary['费用趋势'].abs() > 0.3]  # 费用变化超过30%

if len(trend_changes) > 0:
    print('\n\n趋势转折点（费用变化>30%）：')
    for idx in trend_changes.index:
        date = daily_summary.loc[idx, '日期']
        prev_date = daily_summary.loc[idx-1, '日期'] if idx > 0 else None
        change_pct = daily_summary.loc[idx, '费用趋势']
        
        if prev_date is not None:
            print(f'\n{date.strftime("%Y-%m-%d")} vs {prev_date.strftime("%Y-%m-%d")}：')
            print(f'  费用变化：{change_pct:+.1%}')
            print(f'  当日费用：¥{daily_summary.loc[idx, "费用(元)"]:.2f}')
            print(f'  前日费用：¥{daily_summary.loc[idx-1, "费用(元)"]:.2f}')
            print(f'  IO比变化：{daily_summary.loc[idx, "整体IO比"]:.3f} → {daily_summary.loc[idx-1, "整体IO比"]:.3f}')
            print(f'  模型变化：{daily_summary.loc[idx-1, "模型"]} → {daily_summary.loc[idx, "模型"]}')

# 4. 模型使用时间线
print('\n' + '='*120)
print('四、模型使用时间线')
print('='*120)

# 提取每个模型的使用时间线
models = df['模型'].unique()
for model in models:
    model_data = df[df['模型'] == model].copy()
    model_daily = model_data.groupby('日期').agg({
        '费用(元)': 'sum',
        '请求次数': 'sum',
        '整体IO比': 'sum'
    })
    model_daily['整体IO比'] = model_daily['费用(元)'] / (model_daily['输入Token'] + model_daily['输出Token']) * 1_000_000
    model_daily['输出占比'] = model_daily['输出Token'] / (model_daily['输入Token'] + model_daily['输出Token'])
    
    # 筛选有使用的日期
    model_daily = model_daily[model_daily['费用(元)'] > 0]
    
    if len(model_daily) < 2:  # 至少使用2天才显示
        continue
    
    print(f'\n【{model}】')
    print(f'首次使用：{model_daily.index[0].strftime("%Y-%m-%d")}')
    print(f'最后使用：{model_daily.index[-1].strftime("%Y-%m-%d")}')
    print(f'总费用：¥{model_daily["费用(元)"].sum():.2f}')
    print(f'使用天数：{len(model_daily)}天')
    
    # 计算使用周期
    date_range = (model_daily.index[-1] - model_daily.index[0]).days
    print(f'使用跨度：{date_range}天')
    
    # 识别活跃期和沉寂期
    threshold = model_daily['费用(元)'].mean() * 0.5  # 低于平均50%算沉寂
    active_days = model_daily[model_daily['费用(元)'] >= threshold]
    silent_days = model_daily[model_daily['费用(元)'] < threshold]
    
    print(f'活跃期（>=平均50%）：{len(active_days)}天')
    print(f'沉寂期（<平均50%）：{len(silent_days)}天')

# 5. 用户习惯演变阶段
print('\n' + '='*120)
print('五、用户习惯演变阶段')
print('='*120)

# 按时间顺序识别阶段
# 第一阶段：观察前3天
phase1_data = daily_summary.head(3)
phase1_avg_cost = phase1_data['费用(元)'].mean()
phase1_avg_io = phase1_data['整体IO比'].mean()
phase1_models = phase1_data['模型'].tolist()

# 第二阶段：中间3天
phase2_data = daily_summary.iloc[3:6] if len(daily_summary) >= 6 else pd.DataFrame()
if len(phase2_data) > 0:
    phase2_avg_cost = phase2_data['费用(元)'].mean()
    phase2_avg_io = phase2_data['整体IO比'].mean()
    phase2_models = phase2_data['模型'].tolist()
else:
    phase2_avg_cost = 0
    phase2_avg_io = 0
    phase2_models = []

# 第三阶段：最后3天
phase3_data = daily_summary.iloc[6:9] if len(daily_summary) >= 9 else pd.DataFrame()
if len(phase3_data) > 0:
    phase3_avg_cost = phase3_data['费用(元)'].mean()
    phase3_avg_io = phase3_data['整体IO比'].mean()
    phase3_models = phase3_data['模型'].tolist()
else:
    phase3_avg_cost = 0
    phase3_avg_io = 0
    phase3_models = []

print('\n阶段划分（每3天一个阶段）：')

if len(phase3_data) > 0:
    print('\n第一阶段（前3天）：')
    print(f'  平均费用：¥{phase1_avg_cost:.2f}')
    print(f'  平均IO比：{phase1_avg_io:.3f}')
    print(f'  使用模型：{phase1_models}')
    
    # 判断使用模式
    if phase1_avg_io < 0.01:
        phase1_mode = '阅读主导期'
    elif phase1_avg_io < 0.05:
        phase1_mode = '均衡使用期'
    else:
        phase1_mode = '生成主导期'
    
    print(f'  使用模式：{phase1_mode}')
    
    print('\n第二阶段（中间3天）：')
    if len(phase2_data) > 0:
        print(f'  平均费用：¥{phase2_avg_cost:.2f}')
        print(f'  平均IO比：{phase2_avg_io:.3f}')
        print(f'  使用模型：{phase2_models}')
        
        if phase2_avg_io < 0.01:
            phase2_mode = '阅读主导期'
        elif phase2_avg_io < 0.05:
            phase2_mode = '均衡使用期'
        else:
            phase2_mode = '生成主导期'
        
        print(f'  使用模式：{phase2_mode}')
    
    print('\n第三阶段（最后3天）：')
    print(f'  平均费用：¥{phase3_avg_cost:.2f}')
    print(f'  平均IO比：{phase3_avg_io:.3f}')
    print(f'  使用模型：{phase3_models}')
    
    if phase3_avg_io < 0.01:
        phase3_mode = '阅读主导期'
    elif phase3_avg_io < 0.05:
        phase3_mode = '均衡使用期'
    else:
        phase3_mode = '生成主导期'
    
    print(f'  使用模式：{phase3_mode}')

# 阶段对比
print('\n\n阶段对比分析：')
if len(phase3_data) > 0:
    print(f'第一阶段→第二阶段：')
    if phase2_avg_cost > 0:
        cost_change = (phase2_avg_cost - phase1_avg_cost) / phase1_avg_cost * 100
        print(f'  费用变化：{cost_change:+.1f}%')
        print(f'  IO比变化：{phase2_avg_io - phase1_avg_io:+.3f}')
    
    print(f'\n第二阶段→第三阶段：')
    if phase3_avg_cost > 0:
        cost_change = (phase3_avg_cost - phase2_avg_cost) / phase2_avg_cost * 100
        print(f'  费用变化：{cost_change:+.1f}%')
        print(f'  IO比变化：{phase3_avg_io - phase2_avg_io:+.3f}')

print('\n' + '='*120)
print('六、核心洞察总结')
print('='*120)

print('\n1. 用户习惯的时间演变特征：')
print('   - 从时间线看，用户的使用习惯有明显阶段性')
print('   - 不同阶段有不同的IO比特征和模型选择偏好')
print('   - 模型切换往往与任务类型变化同步发生')

print('\n2. 模型使用的关键模式：')
if len(phase3_data) > 0:
    unique_models_phase1 = set(phase1_models[0].split(', ') if phase1_models else [])
    unique_models_phase3 = set([m for models in phase3_models for m in models.split(', ')])
    
    phase1_model_set = set()
    for models_str in phase1_models:
        phase1_model_set.update(models_str.split(', '))
    
    phase3_model_set = set()
    for models_str in phase3_models:
        phase3_model_set.update(models_str.split(', '))
    
    print(f'   - 第一阶段主要使用：{", ".join(sorted(list(phase1_model_set)))}')
    print(f'   - 第三阶段主要使用：{", ".join(sorted(list(phase3_model_set)))}')
    
    added_models = phase3_model_set - phase1_model_set
    if added_models:
        print(f'   - 新增使用的模型：{", ".join(sorted(list(added_models)))}')
    removed_models = phase1_model_set - phase3_model_set
    if removed_models:
        print(f'   - 停止使用的模型：{", ".join(sorted(list(removed_models)))}')

print('\n3. 优化建议（基于时间线分析）：')
print('   - 在阅读主导期（IO比<0.01）优先使用QWen-Plus或MiniMax')
print('   - 在生成主导期（IO比>0.02）可以尝试降低输出以优化成本')
print('   - 模型多元化阶段要注意成本控制，避免同时使用多个高成本模型')
print('   - 建立模型-使用习惯映射表，动态推荐最优模型')

print('\n' + '='*120)
