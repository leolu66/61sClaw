# -*- coding: utf-8 -*-

"""
模型账单分析工具（完整版）

自动分析模型消费账单，生成分析报告和可视化图表
包含：基础分析 + 深度洞察

"""

import os
import sys
import io
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 修复 stdout 编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def load_config():
    """加载配置文件"""
    # 配置文件路径：技能目录下的 config.json
    skill_dir = Path(__file__).parent.parent
    config_path = skill_dir / "config.json"
    
    default_config = {
        "output_dir": "./billing_report",
        "shared_output_dir": None
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                
                # 处理相对路径
                for key in ['output_dir', 'shared_output_dir']:
                    if config.get(key) and not os.path.isabs(config[key]):
                        # 相对路径：基于技能目录
                        config[key] = str(skill_dir / config[key])
                
                return config
        except Exception as e:
            print(f"[警告] 读取配置文件失败: {e}，使用默认配置")
    
    return default_config


class BillingAnalyzer:
    def __init__(self, filename, datas_dir=None, output_dir=None, use_shared=False):
        """
        初始化分析器
        :param filename: 账单 CSV 文件名
        :param datas_dir: 数据文件目录，默认：当前工作目录
        :param output_dir: 输出目录，默认：从配置文件读取
        :param use_shared: 是否使用共享输出目录（从配置文件读取）
        """
        self.filename = filename
        
        # 加载配置
        config = load_config()
        
        # 数据目录
        if datas_dir:
            self.datas_dir = datas_dir
        else:
            self.datas_dir = os.getcwd()
        
        # 输出目录（优先级：传入参数 > 共享配置 > 默认配置）
        if output_dir:
            self.output_dir = output_dir
        elif use_shared and config.get('shared_output_dir'):
            self.output_dir = config['shared_output_dir']
        else:
            self.output_dir = config.get('output_dir', './billing_report')
        
        # 确保目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'charts'), exist_ok=True)

        self.df = None
        self.analysis_results = {}
        self.timestamp = None
        
    def load_data(self):
        """加载 CSV 数据"""
        file_path = os.path.join(self.datas_dir, self.filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"账单文件不存在：{file_path}")
            
        self.df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # 重命名列（按位置映射，兼容带缓存Token的新格式）
        if len(self.df.columns) >= 10:
            # 新格式：多了缓存Token字段
            expected_cols = ['日期', '模型', '请求次数', '输入 Token', '输出 Token', '缓存 Token', '总 Token', '计费方式', '价格详情', '费用 (元)']
            self.df = self.df.iloc[:, :10]
            self.df.columns = expected_cols
        elif len(self.df.columns) >= 9:
            # 旧格式：无缓存Token
            expected_cols = ['日期', '模型', '请求次数', '输入 Token', '输出 Token', '总 Token', '计费方式', '价格详情', '费用 (元)']
            self.df = self.df.iloc[:, :9]
            self.df.columns = expected_cols
        
        print(f"[OK] 加载数据成功，共 {len(self.df)} 条记录")
        return True
        
    def analyze(self):
        """执行全量分析（基础 + 深度）"""
        if self.df is None:
            raise ValueError("请先加载数据")
        
        # 统一日期格式为 datetime
        self.df['日期'] = pd.to_datetime(self.df['日期'])
            
        print("正在执行数据分析...")
        
        # ========== 基础分析 ==========
        total_cost = self.df['费用 (元)'].sum()
        total_requests = self.df['请求次数'].sum()
        total_input_tokens = self.df['输入 Token'].sum()
        total_output_tokens = self.df['输出 Token'].sum()
        total_tokens = self.df['总 Token'].sum()
        
        self.analysis_results['overview'] = {
            'total_cost': total_cost,
            'total_requests': total_requests,
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'total_tokens': total_tokens,
            'io_ratio': round(total_input_tokens / total_output_tokens, 1) if total_output_tokens > 0 else 0,
            'date_range': f"{self.df['日期'].min()} 到 {self.df['日期'].max()}"
        }
        
        model_stats = self.df.groupby('模型').agg({
            '费用 (元)': 'sum',
            '请求次数': 'sum',
            '输入 Token': 'sum',
            '输出 Token': 'sum',
            '总 Token': 'sum'
        }).sort_values('费用 (元)', ascending=False)
        
        model_stats['占比'] = (model_stats['费用 (元)'] / total_cost * 100).round(1)
        model_stats['单位成本 (元/百万)'] = (model_stats['费用 (元)'] / (model_stats['总 Token'] / 1_000_000)).round(2)
        
        self.analysis_results['model_stats'] = model_stats
        
        daily_stats = self.df.groupby('日期').agg({
            '费用 (元)': 'sum',
            '请求次数': 'sum',
            '输入 Token': 'sum',
            '输出 Token': 'sum',
            '总 Token': 'sum'
        }).sort_index()
        
        self.analysis_results['daily_stats'] = daily_stats
        
        self.analysis_results['efficiency'] = {
            'avg_cost_per_request': round(total_cost / total_requests, 3),
            'avg_cost_per_million_tokens': round(total_cost / (total_tokens / 1_000_000), 2),
            'avg_tokens_per_request': round(total_tokens / total_requests),
            'industry_avg_cost': 7.0,
            'cost_saving_potential': round((7.0 - (total_cost / (total_tokens / 1_000_000))) / 7.0 * 100, 1)
        }
        
        # ========== 深度洞察 ==========
        print("正在执行深度分析...")
        
        # 1. Top 5 高峰日
        daily_with_date = daily_stats.reset_index()
        daily_with_date['日期'] = pd.to_datetime(daily_with_date['日期'])
        avg_cost = daily_with_date['费用 (元)'].mean()
        peak_days = daily_with_date.nlargest(5, '费用 (元)')
        
        peak_days_data = []
        for _, row in peak_days.iterrows():
            io_ratio = row['输入 Token'] / row['输出 Token'] if row['输出 Token'] > 0 else 0
            day_data = self.df[self.df['日期'] == row['日期']]
            top_model = day_data.groupby('模型')['费用 (元)'].sum().idxmax() if len(day_data) > 0 else 'N/A'
            
            peak_days_data.append({
                '日期': row['日期'].strftime('%Y-%m-%d'),
                '费用': row['费用 (元)'],
                '偏差%': round((row['费用 (元)'] - avg_cost) / avg_cost * 100, 1),
                '次数': int(row['请求次数']),
                'IO 比': round(io_ratio, 1),
                '主要模型': top_model
            })
        
        self.analysis_results['peak_days'] = peak_days_data
        
        # 1.5 异常日检测（费用跃迁，只统计增长超过60%的，减少的去掉）
        daily_with_date_sorted = daily_with_date.sort_values('日期')
        daily_with_date_sorted['费用变化率'] = daily_with_date_sorted['费用 (元)'].pct_change() * 100
        
        # 找出异常跃迁（日费用增长超过60%）
        anomaly_days = daily_with_date_sorted[daily_with_date_sorted['费用变化率'] > 60]
        
        anomaly_data = []
        for _, row in anomaly_days.iterrows():
            prev_day = daily_with_date_sorted[daily_with_date_sorted['日期'] == row['日期'] - pd.Timedelta(days=1)]
            if len(prev_day) > 0 and prev_day['费用 (元)'].values[0] > 0:
                prev_cost = prev_day['费用 (元)'].values[0]
                prev_tokens = prev_day['总 Token'].values[0] if '总 Token' in prev_day.columns else (prev_day['输入 Token'].values[0] + prev_day['输出 Token'].values[0])
                
                day_data = self.df[self.df['日期'] == row['日期']]
                if len(day_data) > 0:
                    model_cost = day_data.groupby('模型')['费用 (元)'].sum().sort_values(ascending=False)
                    if len(model_cost) > 0:
                        top_model = model_cost.index[0]  # 取费用最高的模型
                    else:
                        top_model = 'N/A'
                    
                    # 计算 I/O 总量
                    day_tokens = day_data['输入 Token'].sum() + day_data['输出 Token'].sum()
                    prev_tokens = prev_day['输入 Token'].values[0] + prev_day['输出 Token'].values[0]
                    
                    # 计算增长幅度
                    cost_growth = row['费用变化率']
                    token_growth = ((day_tokens - prev_tokens) / prev_tokens * 100) if prev_tokens > 0 else 0
                    
                    # 判断原因：I/O 增长幅度小于价格增长幅度 → 模型切换；反之 → 使用量增加
                    if cost_growth > token_growth * 1.5:
                        reason = '模型切换'
                    else:
                        reason = '使用量增加'
                else:
                    top_model = 'N/A'
                    reason = '未知'
                
                anomaly_data.append({
                    '日期': row['日期'].strftime('%Y-%m-%d'),
                    '费用': round(row['费用 (元)'], 2),
                    '前日费用': round(prev_cost, 2),
                    '增长幅度': round(row['费用变化率'], 1),
                    '主要模型': top_model,
                    '原因': reason
                })
        
        self.analysis_results['anomaly_days'] = anomaly_data
        
        # 1.6 量纲极值分析（只分析最大值，包含日期和当日最大模型）
        extreme_analysis = {}
        
        # 费用最大值
        max_cost_day = daily_with_date.loc[daily_with_date['费用 (元)'].idxmax()]
        max_cost_day_data = self.df[self.df['日期'] == max_cost_day['日期']]
        if len(max_cost_day_data) > 0:
            cost_models = max_cost_day_data.groupby('模型')['费用 (元)'].sum().sort_values(ascending=False)
            top_cost_models = ', '.join(cost_models.head(2).index.tolist())
        else:
            top_cost_models = 'N/A'
        
        extreme_analysis['费用'] = {
            'max': {
                '模型': top_cost_models,
                '值': round(max_cost_day['费用 (元)'], 2),
                '日期': max_cost_day['日期'].strftime('%Y-%m-%d')
            }
        }
        
        # 调用次数最大值
        max_req_day = daily_with_date.loc[daily_with_date['请求次数'].idxmax()]
        max_req_day_data = self.df[self.df['日期'] == max_req_day['日期']]
        if len(max_req_day_data) > 0:
            req_models = max_req_day_data.groupby('模型')['请求次数'].sum().sort_values(ascending=False)
            top_req_models = ', '.join(req_models.head(2).index.tolist())
        else:
            top_req_models = 'N/A'
        
        extreme_analysis['调用次数'] = {
            'max': {
                '模型': top_req_models,
                '值': int(max_req_day['请求次数']),
                '日期': max_req_day['日期'].strftime('%Y-%m-%d')
            }
        }
        
        # 输入Token最大值
        max_input_day = daily_with_date.loc[daily_with_date['输入 Token'].idxmax()]
        max_input_day_data = self.df[self.df['日期'] == max_input_day['日期']]
        if len(max_input_day_data) > 0:
            input_models = max_input_day_data.groupby('模型')['输入 Token'].sum().sort_values(ascending=False)
            top_input_models = ', '.join(input_models.head(2).index.tolist())
        else:
            top_input_models = 'N/A'
        
        extreme_analysis['输入Token'] = {
            'max': {
                '模型': top_input_models,
                '值': int(max_input_day['输入 Token']),
                '日期': max_input_day['日期'].strftime('%Y-%m-%d')
            }
        }
        
        # 输出Token最大值
        max_output_day = daily_with_date.loc[daily_with_date['输出 Token'].idxmax()]
        max_output_day_data = self.df[self.df['日期'] == max_output_day['日期']]
        if len(max_output_day_data) > 0:
            output_models = max_output_day_data.groupby('模型')['输出 Token'].sum().sort_values(ascending=False)
            top_output_models = ', '.join(output_models.head(2).index.tolist())
        else:
            top_output_models = 'N/A'
        
        extreme_analysis['输出Token'] = {
            'max': {
                '模型': top_output_models,
                '值': int(max_output_day['输出 Token']),
                '日期': max_output_day['日期'].strftime('%Y-%m-%d')
            }
        }
        
        self.analysis_results['extreme_analysis'] = extreme_analysis
        
        # 2. IO 比趋势分析
        daily_with_io = self.df.groupby('日期').agg({
            '输入 Token': 'sum', '输出 Token': 'sum', '费用 (元)': 'sum'
        }).reset_index()
        daily_with_io['IO 比'] = (daily_with_io['输入 Token'] / daily_with_io['输出 Token']).round(3)
        daily_with_io['日期'] = pd.to_datetime(daily_with_io['日期'])
        daily_with_io = daily_with_io.sort_values('日期')
        
        n = len(daily_with_io)
        if n >= 4:
            early_io = daily_with_io.head(n//2)['IO 比'].mean()
            late_io = daily_with_io.tail(n//2)['IO 比'].mean()
            if late_io > early_io * 1.3:
                trend = '显著上升（转向阅读/分析型任务）'
            elif late_io < early_io * 0.7:
                trend = '显著下降（转向生成/输出型任务）'
            elif late_io > early_io * 1.1:
                trend = '小幅上升'
            elif late_io < early_io * 0.9:
                trend = '小幅下降'
            else:
                trend = '基本平稳'
        else:
            early_io = late_io = daily_with_io['IO 比'].mean()
            trend = '数据不足'
        
        self.analysis_results['io_trend'] = {
            'early_avg': round(early_io, 1),
            'late_avg': round(late_io, 1),
            'trend': trend,
            'daily': daily_with_io
        }
        
        # 3. 模型归因分析
        total_cost = self.df['费用 (元)'].sum()
        total_requests = self.df['请求次数'].sum()
        total_input = self.df['输入 Token'].sum()
        total_output = self.df['输出 Token'].sum()
        
        model_analysis = []
        for model in self.df['模型'].unique():
            model_data = self.df[self.df['模型'] == model]
            model_io = model_data['输入 Token'].sum() / model_data['输出 Token'].sum() if model_data['输出 Token'].sum() > 0 else 0
            model_unit_cost = model_data['费用 (元)'].sum() / (model_data['总 Token'].sum() / 1_000_000)
            
            model_analysis.append({
                '模型': model,
                '费用占比': round((model_data['费用 (元)'].sum() / total_cost * 100), 1),
                '调用量占比': round((model_data['请求次数'].sum() / total_requests * 100), 1),
                '输入占比': round((model_data['输入 Token'].sum() / total_input * 100), 1),
                '输出占比': round((model_data['输出 Token'].sum() / total_output * 100), 1),
                'IO 比': round(model_io, 1),
                '单位成本': round(model_unit_cost, 2)
            })
        
        self.analysis_results['model_attribution'] = pd.DataFrame(model_analysis).sort_values('费用占比', ascending=False)
        
        # 4. 模型驱动因素分析（只有费用占比 >= 5% 的模型才做判断）
        total_cost = self.df['费用 (元)'].sum()
        model_io_profile = self.df.groupby('模型').apply(
            lambda x: pd.Series({
                '平均 IO 比': x['输入 Token'].sum() / x['输出 Token'].sum() if x['输出 Token'].sum() > 0 else 0,
                'IO 标准差': (x['输入 Token'].std() / x['输出 Token'].std()) if x['输出 Token'].std() > 0 and x['输出 Token'].std() != 0 else 0,
                '费用': x['费用 (元)'].sum(),
                '费用占比': x['费用 (元)'].sum() / total_cost * 100
            }),
            include_groups=False
        ).reset_index()
        
        # 只有费用占比 >= 5% 的模型才做主导因素判断
        model_io_profile['主导因素'] = model_io_profile.apply(
            lambda row: '数据不足' if row['费用占比'] < 5 else 
                       ('模型特性' if row['IO 标准差'] < row['平均 IO 比'] * 0.5 else '用户习惯'),
            axis=1
        )
        
        self.analysis_results['model_driver'] = model_io_profile
        
        # 5. 周模式分析
        self.df['星期数字'] = pd.to_datetime(self.df['日期']).dt.dayofweek
        weekly = self.df.groupby('星期数字').agg({
            '费用 (元)': ['sum', 'mean'], 
            '请求次数': 'sum'
        }).reset_index()
        weekly.columns = ['星期', '总费用', '平均费用', '总次数']
        weekly['星期名'] = weekly['星期'].apply(lambda x: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][x])
        self.analysis_results['weekly'] = weekly.sort_values('星期')
        
        print("[OK] 数据分析完成（基础 + 深度）")
        return True
        
    def generate_charts(self):
        """生成可视化图表（基础 3 张 + 深度 4 张）"""
        if not self.analysis_results:
            raise ValueError("请先执行分析")
            
        print("正在生成图表...")
        
        if self.timestamp is None:
            self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        charts_dir = os.path.join(self.output_dir, 'charts', self.timestamp)
        os.makedirs(charts_dir, exist_ok=True)

        model_stats = self.analysis_results['model_stats']
        daily_stats = self.analysis_results['daily_stats']
        
        # ========== 基础图表 ==========
        # 1. 模型费用占比饼图
        plt.figure(figsize=(8, 8))
        total_cost = self.analysis_results['overview']['total_cost']
        mask = model_stats['费用 (元)'] / total_cost < 0.03
        other_cost = model_stats[mask]['费用 (元)'].sum()
        main_stats = model_stats[~mask].copy()
        if other_cost > 0:
            other_row = pd.DataFrame({'费用 (元)': [other_cost]}, index=['其他'])
            main_stats = pd.concat([main_stats, other_row])
            
        plt.pie(main_stats['费用 (元)'].values, labels=main_stats.index, autopct='%1.1f%%', startangle=90)
        plt.title('各模型费用占比', fontsize=14)
        plt.axis('equal')
        plt.savefig(os.path.join(charts_dir, f'1_模型费用占比_{self.timestamp}.png'), dpi=100, bbox_inches='tight')
        plt.close()
        
        # 2. 四指标标准化趋势图
        plt.figure(figsize=(14, 7))

        scaler_cost = MinMaxScaler()
        scaler_req = MinMaxScaler()
        scaler_input = MinMaxScaler()
        scaler_output = MinMaxScaler()

        cost_norm = scaler_cost.fit_transform(daily_stats[['费用 (元)']]).flatten()
        req_norm = scaler_req.fit_transform(daily_stats[['请求次数']]).flatten()
        input_norm = scaler_input.fit_transform(daily_stats[['输入 Token']]).flatten()
        output_norm = scaler_output.fit_transform(daily_stats[['输出 Token']]).flatten()

        normalized_df = pd.DataFrame({
            '费用_标准化': cost_norm,
            '调用次数_标准化': req_norm,
            '输入 Token_标准化': input_norm,
            '输出 Token_标准化': output_norm
        }, index=daily_stats.index)

        plt.plot(normalized_df.index, normalized_df['调用次数_标准化'],
                marker='o', linewidth=2, label='调用次数', color='#2E86AB', alpha=0.8)
        plt.plot(normalized_df.index, normalized_df['输入 Token_标准化'],
                marker='s', linewidth=2, label='输入 Token(百万)', color='#A23B72', alpha=0.8)
        plt.plot(normalized_df.index, normalized_df['输出 Token_标准化'],
                marker='^', linewidth=2, label='输出 Token(百万)', color='#FF6B6B', alpha=0.8)
        plt.plot(normalized_df.index, normalized_df['费用_标准化'],
                marker='d', linewidth=2, label='费用 (元)', color='#F18F01', alpha=0.8)

        # 标注最高点
        max_req_idx = normalized_df['调用次数_标准化'].idxmax()
        max_req_val = normalized_df['调用次数_标准化'].max()
        max_req_raw = daily_stats.loc[max_req_idx, '请求次数']
        plt.text(max_req_idx, max_req_val, f'{max_req_raw:,.0f}',
                fontsize=9, color='#2E86AB', fontweight='bold',
                ha='center', va='bottom', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        max_input_idx = normalized_df['输入 Token_标准化'].idxmax()
        max_input_val = normalized_df['输入 Token_标准化'].max()
        max_input_raw = daily_stats.loc[max_input_idx, '输入 Token'] / 1_000_000
        offset = 0.05 if max_input_idx == max_req_idx else 0
        plt.text(max_input_idx, max_input_val + offset, f'{max_input_raw:.1f}M',
                fontsize=9, color='#A23B72', fontweight='bold',
                ha='center', va='bottom', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        max_output_idx = normalized_df['输出 Token_标准化'].idxmax()
        max_output_val = normalized_df['输出 Token_标准化'].max()
        max_output_raw = daily_stats.loc[max_output_idx, '输出 Token'] / 1_000_000
        offset = 0.10 if max_output_idx in [max_input_idx, max_req_idx] else 0
        plt.text(max_output_idx, max_output_val + offset, f'{max_output_raw:.1f}M',
                fontsize=9, color='#FF6B6B', fontweight='bold',
                ha='center', va='bottom', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        max_cost_idx = normalized_df['费用_标准化'].idxmax()
        max_cost_val = normalized_df['费用_标准化'].max()
        max_cost_raw = daily_stats.loc[max_cost_idx, '费用 (元)']
        offset = 0.05 if max_cost_idx in [max_output_idx, max_input_idx, max_req_idx] else 0
        plt.text(max_cost_idx, max_cost_val + offset, f'CNY {max_cost_raw:.2f}',
                fontsize=10, color='#FF0000', fontweight='bold',
                ha='center', va='bottom', bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9))

        plt.title('用量趋势图（标准化）', fontsize=16, fontweight='bold')
        plt.xlabel('日期', fontsize=13)
        plt.ylabel('标准化值 (0-1)', fontsize=13)
        plt.xticks(rotation=45, ha='right')
        plt.legend(fontsize=11, loc='best', framealpha=0.9)
        plt.grid(alpha=0.3, linestyle='--')
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, f'2_用量趋势标准化_{self.timestamp}.png'), dpi=120, bbox_inches='tight')
        plt.close()
        
        # 3. 模型维度三指标对比图
        plt.figure(figsize=(14, 8))
        model_3d = model_stats[['请求次数', '总 Token', '费用 (元)']]
        scaler = MinMaxScaler()
        model_3d_normalized = scaler.fit_transform(model_3d)
        
        bar_width = 0.25
        x = np.arange(len(model_3d.index))
        
        plt.bar(x - bar_width, model_3d_normalized[:, 0], width=bar_width, label='调用次数', color='#2E86AB', alpha=0.8)
        plt.bar(x, model_3d_normalized[:, 1], width=bar_width, label='Tokens 总量', color='#A23B72', alpha=0.8)
        plt.bar(x + bar_width, model_3d_normalized[:, 2], width=bar_width, label='费用', color='#F18F01', alpha=0.8)
        
        plt.title('模型维度三指标对比图（标准化）', fontsize=16)
        plt.xlabel('模型名称', fontsize=12)
        plt.ylabel('标准化值 (0-1)', fontsize=12)
        plt.xticks(x, model_3d.index, rotation=45)
        plt.legend(fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        plt.savefig(os.path.join(charts_dir, f'3_模型三指标对比_{self.timestamp}.png'), dpi=120, bbox_inches='tight')
        plt.close()
        
        # ========== 深度图表 ==========
        # 4. Top 5 高峰日
        if self.analysis_results.get('peak_days'):
            plt.figure(figsize=(10, 6))
            peak_df = pd.DataFrame(self.analysis_results['peak_days'])
            bars = plt.bar(range(len(peak_df)), peak_df['费用'], color='#FF6B6B', alpha=0.8)
            plt.xticks(range(len(peak_df)), peak_df['日期'], rotation=30, ha='right')
            plt.title('Top 5 消费高峰日', fontsize=14, fontweight='bold')
            plt.ylabel('费用 (CNY)', fontsize=12)
            plt.grid(axis='y', alpha=0.3)
            
            for bar, val in zip(bars, peak_df['费用']):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                        f'{val:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, f'4_Top5 高峰日_{self.timestamp}.png'), dpi=150, bbox_inches='tight')
            plt.close()
        
        # 5. IO 比趋势图
        if self.analysis_results.get('io_trend') and self.analysis_results['io_trend']['daily'] is not None:
            daily_df = self.analysis_results['io_trend']['daily']
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            color1 = '#2E86AB'
            ax1.set_xlabel('日期', fontsize=12)
            ax1.set_ylabel('IO 比', color=color1, fontsize=12)
            ax1.plot(daily_df['日期'], daily_df['IO 比'], marker='o', color=color1, linewidth=2, label='IO 比')
            ax1.tick_params(axis='y', labelcolor=color1)
            ax1.axhline(y=self.analysis_results['io_trend']['early_avg'], color=color1, linestyle='--', alpha=0.5, label=f'前半均值{self.analysis_results["io_trend"]["early_avg"]:.1f}')
            ax1.axhline(y=self.analysis_results['io_trend']['late_avg'], color='#FF6B6B', linestyle='--', alpha=0.5, label=f'后半均值{self.analysis_results["io_trend"]["late_avg"]:.1f}')
            
            ax2 = ax1.twinx()
            color2 = '#F18F01'
            ax2.set_ylabel('费用 (CNY)', color=color2, fontsize=12)
            ax2.bar(daily_df['日期'], daily_df['费用 (元)'], alpha=0.3, color=color2, label='日费用')
            ax2.tick_params(axis='y', labelcolor=color2)
            
            plt.title(f'IO 比趋势（{self.analysis_results["io_trend"]["trend"]}）', fontsize=14, fontweight='bold')
            fig.tight_layout()
            plt.legend(loc='upper left')
            plt.savefig(os.path.join(charts_dir, f'5_IO 比趋势_{self.timestamp}.png'), dpi=150, bbox_inches='tight')
            plt.close()
        
        # 6. 模型归因分析
        if self.analysis_results.get('model_attribution') is not None:
            attr_df = self.analysis_results['model_attribution']
            main_models = attr_df[attr_df['费用占比'] > 1].sort_values('费用占比', ascending=False)
            
            if len(main_models) > 0:
                x = range(len(main_models))
                width = 0.2
                
                fig, ax = plt.subplots(figsize=(14, 7))
                
                ax.bar([i - 1.5*width for i in x], main_models['费用占比'], width, label='费用%', color='#F18F01')
                ax.bar([i - 0.5*width for i in x], main_models['调用量占比'], width, label='调用量%', color='#2E86AB')
                ax.bar([i + 0.5*width for i in x], main_models['输入占比'], width, label='输入%', color='#A23B72')
                ax.bar([i + 1.5*width for i in x], main_models['输出占比'], width, label='输出%', color='#06A77D')
                
                ax.set_xlabel('模型', fontsize=12)
                ax.set_ylabel('占比 (%)', fontsize=12)
                ax.set_title('模型选择对 4 个量纲的影响', fontsize=14, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels([m[:15] for m in main_models['模型']], rotation=30, ha='right')
                ax.legend()
                ax.grid(axis='y', alpha=0.3)
                
                plt.tight_layout()
                plt.savefig(os.path.join(charts_dir, f'6_模型归因_{self.timestamp}.png'), dpi=150, bbox_inches='tight')
                plt.close()
        
        # 7. 周模式
        if self.analysis_results.get('weekly') is not None:
            weekly_df = self.analysis_results['weekly']
            plt.figure(figsize=(10, 5))
            
            bars = plt.bar(weekly_df['星期名'], weekly_df['平均费用'],
                          color=plt.cm.RdYlGn(weekly_df['平均费用']/weekly_df['平均费用'].max()),
                          alpha=0.8)
            
            plt.title('周消费模式', fontsize=14, fontweight='bold')
            plt.ylabel('日均费用 (CNY)', fontsize=12)
            plt.xticks(rotation=30)
            plt.grid(axis='y', alpha=0.3)
            
            for bar, val in zip(bars, weekly_df['平均费用']):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                        f'{val:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, f'7_周模式_{self.timestamp}.png'), dpi=150, bbox_inches='tight')
            plt.close()
        
        print(f"[OK] 图表生成完成（7 张），已保存到：{charts_dir}")
        return True
        
    def generate_report(self, report_name=None):
        """生成分析报告（包含深度洞察）"""
        if not self.analysis_results:
            raise ValueError("请先执行分析")
            
        print("正在生成分析报告...")
        
        if self.timestamp is None:
            self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        overview = self.analysis_results['overview']
        model_stats = self.analysis_results['model_stats']
        efficiency = self.analysis_results['efficiency']
        
        # 计算统计天数
        start_dt = self.df['日期'].min()
        end_dt = self.df['日期'].max()
        stats_days = (end_dt - start_dt).days + 1

        if not report_name:
            # 默认报告名：ZD-日期范围.md
            date_range = self.analysis_results['overview']['date_range']
            # 从日期范围提取开始和结束日期
            try:
                start_date = pd.to_datetime(self.df['日期'].min()).strftime('%m%d')
                end_date = pd.to_datetime(self.df['日期'].max()).strftime('%m%d')
                report_name = f"ZD-{start_date}-{end_date}.md"
            except:
                # 如果提取失败，使用默认名
                report_name = f"ZD-{self.timestamp}.md"
        elif not report_name.endswith('.md'):
            # 确保有 .md 后缀
            report_name = f"{report_name}.md"

        report_path = os.path.join(self.output_dir, report_name)
        
        content = f"""# 模型账单分析报告

---

## 报告概览

**统计周期**: {overview['date_range']} （共 {stats_days} 天）

| 项目 | 总数值 | 日均数值 | 单位 |
|------|-----|-----|------|
| **总费用** | CNY {overview['total_cost']:.2f} | CNY {overview['total_cost']/stats_days:.2f} | 元 |
| **总调用次数** | {overview['total_requests']:,} | {round(overview['total_requests']/stats_days):,} | 次 |
| **总输入 Tokens** | {overview['total_input_tokens']/1_000_000:.2f} | {overview['total_input_tokens']/1_000_000/stats_days:.2f} | 百万 Tokens |
| **总输出 Tokens** | {overview['total_output_tokens']/1_000_000:.2f} | {overview['total_output_tokens']/1_000_000/stats_days:.2f} | 百万 Tokens |
| **总 Tokens 用量** | {overview['total_tokens']/1_000_000:.2f} | {overview['total_tokens']/1_000_000/stats_days:.2f} | 百万 Tokens |
| **输入输出比** | {overview['io_ratio']} | - | |

> 注：单位成本行业平均约 7 元/百万 Tokens，成本优化空间{efficiency['cost_saving_potential']}%。

---

## 可视化分析

### 1. 各模型费用占比分析

![各模型费用占比](./charts/{self.timestamp}/1_模型费用占比_{self.timestamp}.png)

> 说明：MiniMax 和 Kimi 通常是成本主要构成，可查看占比判断结构是否合理。

---

### 2. 用量趋势标准化图

![用量趋势标准化](./charts/{self.timestamp}/2_用量趋势标准化_{self.timestamp}.png)

> 说明：展示调用次数、输入 Token、输出 Token、费用四个指标的标准化趋势。

---

### 3. 模型维度三指标对比图

![模型三指标对比](./charts/{self.timestamp}/3_模型三指标对比_{self.timestamp}.png)

> 说明：每个模型三根柱子（左：调用次数，中：Tokens 总量，右：费用）。

---

## 核心分析

### 1. 费用结构分析

| 模型名称 | 总费用 (元) | 占比 (%) | 调用次数 | 单次成本 (分/次) | 总 Tokens(百万) | 单位成本 (元/百万) | 性价比评级 |
|----------|------------|---------|----------|----------------|--------------|------------------|------------|
"""

        top5_stats = model_stats.head(5)
        for model, row in top5_stats.iterrows():
            cost = row['费用 (元)']
            pct = row['占比']
            req = row['请求次数']
            tokens = row['总 Token'] / 1_000_000
            unit_cost = row['单位成本 (元/百万)']
            
            if unit_cost <= 3:
                rating = "[OK] 最优"
            elif unit_cost <= 8:
                rating = "[INFO] 良好"
            else:
                rating = "[WARN] 偏低"
                
            cost_per_call = (cost * 100) / req if req > 0 else 0
            content += f"| **{model}** | {cost:.2f} | {pct} | {int(req):,} | {cost_per_call:.2f} | {tokens:.2f} | {unit_cost:.2f} | {rating} |\n"

        content += f"""

---

### 2. 效率分析

| 指标 | 值 | 说明 |
|------|-----|------|
| **单次调用平均成本** | CNY {efficiency['avg_cost_per_request']:.3f} | 越低越好 |
| **平均单位成本** | CNY {efficiency['avg_cost_per_million_tokens']:.2f}元/百万 Tokens | 行业平均约 7 元 |
| **单次调用平均 Token** | {efficiency['avg_tokens_per_request']:,} | 反映任务类型 |
| **成本优化空间** | {efficiency['cost_saving_potential']}% | 对比行业平均 |

> 注：效率分析展示了整体成本效益，根据任务类型选择合适的模型，可节省 30-50% 成本。

---

## 优化建议

### 模型分层使用策略

| 任务类型 | 推荐模型 | 优势 |
|----------|----------|------|
| 简单任务（聊天、检索、摘要） | Qwen3.5-flash/plus | 性价比最高，节省 70%+ 成本 |
| 普通复杂任务（编程、分析） | MiniMax-M2.5 | 能力强，成本低 |
| 长文本任务（>100 万 Token） | Kimi-K2.5 | 长上下文能力独一档 |
| 特殊复杂推理任务 | Claude/GPT | 能力最强，按需使用 |

> 注：下表仅列出费用 Top 5 模型，完整模型列表见深度洞察章节。

---

## 深度洞察

### Top 5 消费高峰日

![高峰日](./charts/{self.timestamp}/4_Top5 高峰日_{self.timestamp}.png)

"""
        
        if self.analysis_results.get('peak_days'):
            peak_df = pd.DataFrame(self.analysis_results['peak_days'])
            content += "**关键发现**：\n\n"
            content += f"- 高峰日平均 **CNY {peak_df['费用'].mean():.1f}**，比日均高 **{peak_df['偏差%'].mean():+.1f}%**\n"
            content += f"- 最高峰：**{peak_df.iloc[0]['日期']}**（CNY {peak_df.iloc[0]['费用']:.1f}）\n"
            content += f"- 主要驱动模型：**{peak_df.iloc[0]['主要模型']}**\n\n"
        
        content += f"""
### 用户习惯演变（IO 比趋势）

![IO 比趋势](./charts/{self.timestamp}/5_IO 比趋势_{self.timestamp}.png)

"""
        
        if self.analysis_results.get('io_trend'):
            io = self.analysis_results['io_trend']
            content += "**关键发现**：\n\n"
            content += f"- IO 比从 **{io['early_avg']:.1f}** 变化到 **{io['late_avg']:.1f}**\n"
            content += f"- 趋势：**{io['trend']}**\n"
            
            if '阅读' in io['trend'] or '上升' in io['trend']:
                content += "- [INFO] **解读**：IO 比上升说明输入增多，用户更多在进行文档阅读、代码审查、资料分析等任务\n"
            elif '生成' in io['trend'] or '下降' in io['trend']:
                content += "- [INFO] **解读**：IO 比下降说明输出增多，用户更多在进行代码生成、内容创作、批量输出等任务\n"
            else:
                content += "- [INFO] **解读**：IO 比平稳说明用户任务类型保持稳定\n"
            content += "\n"
        
        content += f"""
### 模型选择的多维影响

![模型归因](./charts/{self.timestamp}/6_模型归因_{self.timestamp}.png)

"""
        
        if self.analysis_results.get('model_attribution') is not None:
            attr_df = self.analysis_results['model_attribution']
            main_models = attr_df[attr_df['费用占比'] > 5]
            
            content += "**关键发现**：\n\n"
            
            for _, row in main_models.iterrows():
                if abs(row['费用占比'] - row['调用量占比']) < 5:
                    pattern = '线性'
                    desc = '费用与调用量成正比，属于常规使用'
                elif row['费用占比'] > row['调用量占比'] * 1.5:
                    pattern = '高成本'
                    desc = '单位成本高，建议优化'
                else:
                    pattern = '低成本'
                    desc = '单位成本低，性价比高'
                
                content += f"- **{row['模型']}**：费用{row['费用占比']}%，调用{row['调用量占比']}%，IO 比{row['IO 比']} -> **{pattern}模式**（{desc}）\n"
            
            content += "\n**模型切换 vs 用户习惯**：\n\n"
            
            if self.analysis_results.get('model_driver') is not None:
                driver_df = self.analysis_results['model_driver']
                model_driven = driver_df[driver_df['主导因素'] == '模型特性']['模型'].tolist()
                habit_driven = driver_df[driver_df['主导因素'] == '用户习惯']['模型'].tolist()
                data_insufficient = driver_df[driver_df['主导因素'] == '数据不足']['模型'].tolist()
                
                if model_driven:
                    content += f"- [INFO] **模型特性主导**：{', '.join(model_driven[:5])}（IO 比稳定，由模型能力决定）\n"
                if habit_driven:
                    content += f"- [INFO] **用户习惯主导**：{', '.join(habit_driven[:5])}（IO 比波动大，反映任务类型变化）\n"
                if data_insufficient:
                    content += f"- [INFO] **数据不足**：{', '.join(data_insufficient[:5])}（调用次数 < 10，无法判断）\n"
            
            # 异常日检测
            if self.analysis_results.get('anomaly_days'):
                content += "\n### 异常费用跃迁\n\n"
                for anomaly in self.analysis_results['anomaly_days']:
                    reason = anomaly.get('原因', '未知')
                    content += f"- **{anomaly['日期']}**：费用 CNY {anomaly['费用']}（+{anomaly['增长幅度']}%，前日 CNY {anomaly['前日费用']}），主要模型：{anomaly['主要模型']}，原因：{reason}\n"
                content += "\n"
            
            # 量纲极值分析（只显示最大值）
            if self.analysis_results.get('extreme_analysis'):
                content += "### 各维度最大值\n\n"
                content += "| 维度 | 日期 | 使用模型 | 最大值 |\n"
                content += "|------|------|----------|--------|\n"
                
                extreme = self.analysis_results['extreme_analysis']
                for dim, data in extreme.items():
                    content += f"| {dim} | {data['max']['日期']} | {data['max']['模型']} | {data['max']['值']:,} |\n"
                
                content += "\n"
            
            content += "\n"
        
        content += f"""
### 周消费模式

![周模式](./charts/{self.timestamp}/7_周模式_{self.timestamp}.png)

"""

        if self.analysis_results.get('weekly') is not None:
            weekly_df = self.analysis_results['weekly']
            busiest = weekly_df.loc[weekly_df['平均费用'].idxmax()]
            quietest = weekly_df.loc[weekly_df['平均费用'].idxmin()]
            
            content += "**关键发现**：\n\n"
            content += f"- 最忙：**{busiest['星期名']}**（日均 CNY {busiest['平均费用']:.1f}）\n"
            content += f"- 最闲：**{quietest['星期名']}**（日均 CNY {quietest['平均费用']:.1f}）\n\n"
        
        content += """
### 行动建议

1. **模型优化**：将高成本模型的部分任务迁移到 QWen-Plus/MiniMax-M2.5
2. **习惯调整**：
"""
        if self.analysis_results.get('io_trend') and '上升' in self.analysis_results['io_trend'].get('trend', ''):
            content += "   - IO 比上升期：优先使用 QWen-Plus（阅读型任务性价比高）\n"
        else:
            content += "   - 生成型任务：使用 MiniMax-M2.5（生成能力强，成本低）\n"
        content += "3. **监控告警**：单日>CNY 100 时检查异常批量任务\n\n"
        
        content += f"""
---

## 总结

本次账单分析已完成，包含基础分析和深度洞察。可根据以上分析优化模型使用策略，预计可降低 30%+ 成本。

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*
*生成工具：OpenClaw Billing Analyzer 技能（完整版）*
"""

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"[OK] 报告生成完成：{report_path}")
        return report_path
        
    def run_full_analysis(self, report_name=None):
        """执行全流程分析：加载→分析→生成图表→生成报告"""
        self.load_data()
        self.analyze()
        self.generate_charts()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        report_path = self.generate_report(report_name)
        return report_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='模型账单分析工具')
    parser.add_argument('filename', help='账单 CSV 文件名')
    parser.add_argument('report_name', nargs='?', help='报告名称（可选）')
    parser.add_argument('--output-dir', '-o', help='输出目录（覆盖配置）')
    parser.add_argument('--datas-dir', '-d', help='数据文件目录')
    parser.add_argument('--shared', '-s', action='store_true', help='使用共享输出目录')
    
    args = parser.parse_args()
    
    try:
        analyzer = BillingAnalyzer(
            args.filename,
            datas_dir=args.datas_dir,
            output_dir=args.output_dir,
            use_shared=args.shared
        )
        report_path = analyzer.run_full_analysis(args.report_name)
        print(f"\n[OK] 全流程分析完成！报告路径：{report_path}")
        
    except Exception as e:
        print(f"[ERROR] 分析失败：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
