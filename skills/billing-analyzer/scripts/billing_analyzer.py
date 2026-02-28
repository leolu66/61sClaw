# -*- coding: utf-8 -*-
"""
模型账单分析工具
自动分析模型消费账单，生成分析报告和可视化图表
"""
import os
import sys
import io
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 修复stdout编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

class BillingAnalyzer:
    def __init__(self, filename, datas_dir=None, output_dir=None):
        """
        初始化分析器
        :param filename: 账单CSV文件名
        :param datas_dir: 数据文件目录，默认: ../datas/
        :param output_dir: 输出目录，默认: ../../../agfiles/billing_report/
        """
        self.filename = filename
        # 默认datas目录在workspace根目录下
        self.datas_dir = datas_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'datas')
        # 默认输出目录在workspace根目录的agfiles/billing_report下
        self.output_dir = output_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'agfiles', 'billing_report')
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'charts'), exist_ok=True)

        self.df = None
        self.analysis_results = {}
        
    def load_data(self):
        """加载CSV数据"""
        file_path = os.path.join(self.datas_dir, self.filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"账单文件不存在: {file_path}")
            
        self.df = pd.read_csv(file_path)
        print(f"✅ 加载数据成功，共 {len(self.df)} 条记录")
        return True
        
    def analyze(self):
        """执行全量分析"""
        if self.df is None:
            raise ValueError("请先加载数据")
            
        print("🔍 正在执行数据分析...")
        
        # 总统计
        total_cost = self.df['费用(元)'].sum()
        total_requests = self.df['请求次数'].sum()
        total_input_tokens = self.df['输入Token'].sum()
        total_output_tokens = self.df['输出Token'].sum()
        total_tokens = self.df['总Token'].sum()
        
        self.analysis_results['overview'] = {
            'total_cost': total_cost,
            'total_requests': total_requests,
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'total_tokens': total_tokens,
            'io_ratio': round(total_input_tokens / total_output_tokens, 1) if total_output_tokens > 0 else 0,
            'date_range': f"{self.df['日期'].min()} 到 {self.df['日期'].max()}"
        }
        
        # 模型维度统计
        model_stats = self.df.groupby('模型').agg({
            '费用(元)': 'sum',
            '请求次数': 'sum',
            '输入Token': 'sum',
            '输出Token': 'sum',
            '总Token': 'sum'
        }).sort_values('费用(元)', ascending=False)
        
        model_stats['占比'] = (model_stats['费用(元)'] / total_cost * 100).round(1)
        model_stats['单位成本(元/百万)'] = (model_stats['费用(元)'] / (model_stats['总Token'] / 1_000_000)).round(2)
        
        self.analysis_results['model_stats'] = model_stats
        
        # 日期维度统计
        daily_stats = self.df.groupby('日期').agg({
            '费用(元)': 'sum',
            '请求次数': 'sum',
            '总Token': 'sum'
        }).sort_index()
        
        self.analysis_results['daily_stats'] = daily_stats
        
        # 效率指标
        self.analysis_results['efficiency'] = {
            'avg_cost_per_request': round(total_cost / total_requests, 3),
            'avg_cost_per_million_tokens': round(total_cost / (total_tokens / 1_000_000), 2),
            'avg_tokens_per_request': round(total_tokens / total_requests),
            'industry_avg_cost': 7.0,  # 行业平均单位成本
            'cost_saving_potential': round((7.0 - (total_cost / (total_tokens / 1_000_000))) / 7.0 * 100, 1)
        }
        
        print("✅ 数据分析完成")
        return True
        
    def generate_charts(self):
        """生成可视化图表"""
        if not self.analysis_results:
            raise ValueError("请先执行分析")
            
        print("📊 正在生成图表...")
        charts_dir = os.path.join(self.output_dir, 'charts')
        model_stats = self.analysis_results['model_stats']
        daily_stats = self.analysis_results['daily_stats']
        
        # 1. 模型费用占比饼图
        plt.figure(figsize=(8, 8))
        # 合并占比小于3%的模型
        total_cost = self.analysis_results['overview']['total_cost']
        mask = model_stats['费用(元)'] / total_cost < 0.03
        other_cost = model_stats[mask]['费用(元)'].sum()
        main_stats = model_stats[~mask]
        if other_cost > 0:
            main_stats.loc['其他'] = {'费用(元)': other_cost}
            
        plt.pie(main_stats['费用(元)'].values, labels=main_stats.index, autopct='%1.1f%%', startangle=90)
        plt.title('各模型费用占比', fontsize=14)
        plt.axis('equal')
        plt.savefig(os.path.join(charts_dir, '1_模型费用占比.png'), dpi=100, bbox_inches='tight')
        plt.close()
        
        # 2. 三指标标准化趋势图
        plt.figure(figsize=(12, 6))
        # 归一化
        scaler = MinMaxScaler()
        daily_normalized = scaler.fit_transform(daily_stats)
        normalized_df = pd.DataFrame(daily_normalized, 
                                     columns=['费用_标准化', '调用次数_标准化', '总Token_标准化'],
                                     index=daily_stats.index)
        
        plt.plot(normalized_df.index, normalized_df['调用次数_标准化'], marker='o', linewidth=2, label='调用次数', color='#2E86AB')
        plt.plot(normalized_df.index, normalized_df['总Token_标准化'], marker='s', linewidth=2, label='Tokens总量', color='#A23B72')
        plt.plot(normalized_df.index, normalized_df['费用_标准化'], marker='^', linewidth=2, label='费用', color='#F18F01')
        
        plt.title('用量趋势图（标准化）', fontsize=14)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('标准化值 (0-1)', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(fontsize=12)
        plt.grid(alpha=0.3)
        plt.savefig(os.path.join(charts_dir, '2_用量趋势标准化.png'), dpi=100, bbox_inches='tight')
        plt.close()
        
        # 3. 模型维度三指标对比图
        plt.figure(figsize=(14, 8))
        # 模型维度归一化
        model_3d = model_stats[['请求次数', '总Token', '费用(元)']]
        scaler = MinMaxScaler()
        model_3d_normalized = scaler.fit_transform(model_3d)
        
        bar_width = 0.25
        x = np.arange(len(model_3d.index))
        
        plt.bar(x - bar_width, model_3d_normalized[:, 0], width=bar_width, label='调用次数', color='#2E86AB', alpha=0.8)
        plt.bar(x, model_3d_normalized[:, 1], width=bar_width, label='Tokens总量', color='#A23B72', alpha=0.8)
        plt.bar(x + bar_width, model_3d_normalized[:, 2], width=bar_width, label='费用', color='#F18F01', alpha=0.8)
        
        plt.title('模型维度三指标对比图（标准化）', fontsize=16)
        plt.xlabel('模型名称', fontsize=12)
        plt.ylabel('标准化值 (0-1)', fontsize=12)
        plt.xticks(x, model_3d.index, rotation=45)
        plt.legend(fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        plt.savefig(os.path.join(charts_dir, '3_模型三指标对比.png'), dpi=120, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 图表生成完成，已保存到: {charts_dir}")
        return True
        
    def generate_report(self, report_name=None):
        """生成分析报告"""
        if not self.analysis_results:
            raise ValueError("请先执行分析")
            
        print("📝 正在生成分析报告...")
        overview = self.analysis_results['overview']
        model_stats = self.analysis_results['model_stats']
        efficiency = self.analysis_results['efficiency']

        # 报告名称
        if not report_name:
            # 只使用文件名，不包含路径
            filename_only = os.path.basename(self.filename).replace('.csv', '')
            report_name = f"{filename_only}_分析报告.md"

        report_path = os.path.join(self.output_dir, report_name)
        
        # 生成报告内容
        content = f"""# 📊 模型账单分析报告
---

## 🔍 报告概览
| 项目 | 值 |
|------|-----|
| **统计周期** | {overview['date_range']} |
| **总费用** | ¥{overview['total_cost']:.2f} 元 |
| **总调用次数** | {overview['total_requests']:,} 次 |
| **总输入Tokens** | {overview['total_input_tokens']:,} Tokens |
| **总输出Tokens** | {overview['total_output_tokens']:,} Tokens |
| **总Tokens用量** | {overview['total_tokens']:,} Tokens |
| **输入输出比** | {overview['io_ratio']} : 1 |

---

## 📈 可视化分析
### 1. 各模型费用占比分析
![各模型费用占比](./charts/1_模型费用占比.png)
> **说明：** MiniMax和Kimi通常是成本主要构成，可查看占比判断结构是否合理。

---

### 2. 用量趋势标准化图
![用量趋势标准化](./charts/2_用量趋势标准化.png)
> **说明：** 调用次数、Tokens总量、费用三者趋势高度一致说明费用与用量匹配，无异常浪费。

---

### 3. 模型维度三指标对比图
![模型三指标对比](./charts/3_模型三指标对比.png)
> **说明：** 每个模型三根柱子（左：调用次数，中：Tokens总量，右：费用），对比可直观判断模型性价比。

---

## 📊 核心分析
### 1. 费用结构分析
| 模型名称 | 总费用(元) | 占比(%) | 调用次数 | 总Tokens(万) | 单位成本(元/百万) | 性价比评级 |
|----------|------------|---------|----------|--------------|------------------|------------|
"""

        # 添加模型表格
        for model, row in model_stats.iterrows():
            cost = row['费用(元)']
            pct = row['占比']
            req = row['请求次数']
            tokens = row['总Token'] / 10000
            unit_cost = row['单位成本(元/百万)']
            
            # 性价比评级
            if unit_cost <= 3:
                rating = "🟢 最优"
            elif unit_cost <= 8:
                rating = "🟡 良好"
            else:
                rating = "🔴 偏低"
                
            content += f"| **{model}** | {cost:.2f} | {pct} | {req:,} | {tokens:.1f} | {unit_cost:.2f} | {rating} |\n"

        # 效率分析
        content += f"""
---

### 2. 效率分析
| 指标 | 值 | 说明 |
|------|-----|------|
| **单次调用平均成本** | ¥{efficiency['avg_cost_per_request']:.3f} | 越低越好 |
| **平均单位成本** | ¥{efficiency['avg_cost_per_million_tokens']:.2f}元/百万Tokens | 行业平均约7元 |
| **单次调用平均Token** | {efficiency['avg_tokens_per_request']:,} | 反映任务类型 |
| **成本优化空间** | {efficiency['cost_saving_potential']}% | 对比行业平均 |

---

## 💡 优化建议
### 🔥 模型分层使用策略
| 任务类型 | 推荐模型 | 优势 |
|----------|----------|------|
| 简单任务（聊天、检索、摘要） | Qwen3.5-flash/plus | 性价比最高，节省70%+成本 |
| 普通复杂任务（编程、分析） | MiniMax-M2.5 | 能力强，成本低 |
| 长文本任务（>100万Token） | Kimi-K2.5 | 长上下文能力独一档 |
| 特殊复杂推理任务 | Claude/GPT | 能力最强，按需使用 |

---

## 🎯 总结
本次账单分析已完成，可根据以上分析优化模型使用策略，预计可降低30%+成本。

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*
*生成工具：OpenClaw Billing Analyzer 技能*
"""

        # 写入文件
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ 报告生成完成: {report_path}")
        return report_path
        
    def run_full_analysis(self, report_name=None):
        """执行全流程分析：加载→分析→生成图表→生成报告"""
        self.load_data()
        self.analyze()
        self.generate_charts()
        report_path = self.generate_report(report_name)
        return report_path


def main():
    if len(sys.argv) < 2:
        print("使用方法: python billing_analyzer.py <账单文件名> [报告名称]")
        print("示例: python billing_analyzer.py billing_2026-02.csv")
        sys.exit(1)
        
    filename = sys.argv[1]
    report_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        analyzer = BillingAnalyzer(filename)
        report_path = analyzer.run_full_analysis(report_name)
        print(f"\n🎉 全流程分析完成！报告路径: {report_path}")
        
        # 自动打开报告
        if sys.platform.startswith('win'):
            os.startfile(report_path)
        elif sys.platform.startswith('darwin'):
            os.system(f'open "{report_path}"')
        else:
            os.system(f'xdg-open "{report_path}"')
            
    except Exception as e:
        print(f"❌ 分析失败: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
