# -*- coding: utf-8 -*-
"""
模型账单深度分析工具（增强版 v2）
改进点：
1. 增加 IO 比趋势分析（反映用户习惯：阅读型 vs 生成型）
2. 增加模型归因分析（4 个量纲：费用、调用量、输入、输出）
3. 区分模型切换 vs 用户习惯引起の変化
4. 用 CNY 替代 ¥ 符号
"""
import os
import sys
import io
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# 中文显示支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 修复编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class DeepInsightAnalyzer:
    """深度洞察分析器"""
    
    def __init__(self, filename, datas_dir=None, output_dir=None):
        self.filename = filename
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.datas_dir = datas_dir or os.path.join(workspace_root, 'datas')
        self.output_dir = output_dir or os.path.join(workspace_root, 'agfiles', 'billing_report')
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'charts'), exist_ok=True)
        
        self.df = None
        self.results = {}
        
    def load_data(self):
        """加载 CSV 数据"""
        file_path = os.path.join(self.datas_dir, self.filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"账单文件不存在：{file_path}")
        
        self.df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # 重命名列
        col_mapping = {
            self.df.columns[0]: '日期',
            self.df.columns[1]: '模型',
            self.df.columns[2]: '请求次数',
            self.df.columns[3]: '输入 Token',
            self.df.columns[4]: '输出 Token',
            self.df.columns[5]: '总 Token',
            self.df.columns[6]: '计费方式',
            self.df.columns[7]: '价格详情',
            self.df.columns[8]: '费用 (元)'
        }
        self.df = self.df.rename(columns=col_mapping)
        
        self.df['日期'] = pd.to_datetime(self.df['日期'])
        self.df['星期数字'] = self.df['日期'].dt.dayofweek
        self.df['IO 比'] = (self.df['输入 Token'] / self.df['输出 Token']).round(3)
        self.df['单位成本'] = (self.df['费用 (元)'] / (self.df['总 Token'] / 1_000_000)).round(2)
        
        print(f"✅ 加载数据成功，共 {len(self.df)} 条记录")
        return True
    
    def analyze(self):
        """执行深度分析"""
        # 1. Top 5 高峰日
        daily_stats = self.df.groupby('日期').agg({
            '费用 (元)': 'sum', '请求次数': 'sum',
            '输入 Token': 'sum', '输出 Token': 'sum'
        }).reset_index()
        
        avg_cost = daily_stats['费用 (元)'].mean()
        peak_days = daily_stats.nlargest(5, '费用 (元)')
        
        self.results['peak_days'] = []
        for _, row in peak_days.iterrows():
            io_ratio = row['输入 Token'] / row['输出 Token'] if row['输出 Token'] > 0 else 0
            day_data = self.df[self.df['日期'] == row['日期']]
            top_model = day_data.groupby('模型')['费用 (元)'].sum().idxmax()
            
            self.results['peak_days'].append({
                '日期': row['日期'].strftime('%Y-%m-%d'),
                '费用': row['费用 (元)'],
                '偏差%': ((row['费用 (元)'] - avg_cost) / avg_cost * 100).round(1),
                '次数': int(row['请求次数']),
                'IO 比': round(io_ratio, 1),
                '主要模型': top_model
            })
        
        # 2. IO 比时间线趋势（用户习惯变化）
        daily_with_io = self.df.groupby('日期').agg({
            '输入 Token': 'sum', '输出 Token': 'sum', '费用 (元)': 'sum'
        }).reset_index()
        daily_with_io['IO 比'] = (daily_with_io['输入 Token'] / daily_with_io['输出 Token']).round(3)
        daily_with_io['日期'] = pd.to_datetime(daily_with_io['日期'])
        daily_with_io = daily_with_io.sort_values('日期')
        
        # 计算趋势
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
        
        self.results['io_trend'] = {
            'early_avg': round(early_io, 1),
            'late_avg': round(late_io, 1),
            'trend': trend,
            'daily': daily_with_io
        }
        
        # 3. 模型归因分析（4 个量纲）
        total_cost = self.df['费用 (元)'].sum()
        total_requests = self.df['请求次数'].sum()
        total_input = self.df['输入 Token'].sum()
        total_output = self.df['输出 Token'].sum()
        
        model_analysis = []
        for model in self.df['模型'].unique():
            model_data = self.df[self.df['模型'] == model]
            
            model_analysis.append({
                '模型': model,
                '费用占比': (model_data['费用 (元)'].sum() / total_cost * 100).round(1),
                '调用量占比': (model_data['请求次数'].sum() / total_requests * 100).round(1),
                '输入占比': (model_data['输入 Token'].sum() / total_input * 100).round(1),
                '输出占比': (model_data['输出 Token'].sum() / total_output * 100).round(1),
                'IO 比': model_data['IO 比'].mean().round(1),
                '单位成本': model_data['单位成本'].mean().round(2)
            })
        
        self.results['model_attribution'] = pd.DataFrame(model_analysis).sort_values('费用占比', ascending=False)
        
        # 4. 模型 - 习惯归因（区分模型特性 vs 用户习惯）
        # 计算每个模型的典型 IO 比范围
        model_io_profile = self.df.groupby('模型')['IO 比'].agg(['mean', 'std']).reset_index()
        model_io_profile.columns = ['模型', '平均 IO 比', 'IO 标准差']
        
        # 判断：如果模型 IO 比稳定（标准差小），说明是模型特性主导
        # 如果 IO 比波动大，说明用户习惯变化主导
        model_io_profile['主导因素'] = model_io_profile.apply(
            lambda row: '模型特性' if row['IO 标准差'] < row['平均 IO 比'] * 0.5 else '用户习惯',
            axis=1
        )
        
        self.results['model_driver'] = model_io_profile
        
        # 5. 周模式
        weekly = self.df.groupby('星期数字').agg({'费用 (元)': ['sum', 'mean'], '请求次数': 'sum'}).reset_index()
        weekly.columns = ['星期', '总费用', '平均费用', '总次数']
        weekly['星期名'] = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        self.results['weekly'] = weekly.sort_values('星期')
        
        return self.results
    
    def generate_charts(self):
        """生成深度分析图表"""
        charts_dir = os.path.join(self.output_dir, 'charts')
        
        # 图表 1: Top 5 高峰日
        if self.results.get('peak_days'):
            plt.figure(figsize=(10, 6))
            peak_df = pd.DataFrame(self.results['peak_days'])
            bars = plt.bar(range(len(peak_df)), peak_df['费用'], color='#FF6B6B', alpha=0.8)
            plt.xticks(range(len(peak_df)), peak_df['日期'], rotation=30, ha='right')
            plt.title('Top 5 消费高峰日', fontsize=14, fontweight='bold')
            plt.ylabel('费用 (CNY)', fontsize=12)
            plt.grid(axis='y', alpha=0.3)
            
            for bar, val in zip(bars, peak_df['费用']):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                        f'{val:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, '7_Top5 高峰日.png'), dpi=150, bbox_inches='tight')
            plt.close()
        
        # 图表 2: IO 比趋势
        if self.results.get('io_trend') and self.results['io_trend']['daily'] is not None:
            daily_df = self.results['io_trend']['daily']
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            color1 = '#2E86AB'
            ax1.set_xlabel('日期', fontsize=12)
            ax1.set_ylabel('IO 比', color=color1, fontsize=12)
            ax1.plot(daily_df['日期'], daily_df['IO 比'], marker='o', color=color1, linewidth=2, label='IO 比')
            ax1.tick_params(axis='y', labelcolor=color1)
            ax1.axhline(y=self.results['io_trend']['early_avg'], color=color1, linestyle='--', alpha=0.5, label=f'前半均值{self.results["io_trend"]["early_avg"]:.1f}')
            ax1.axhline(y=self.results['io_trend']['late_avg'], color='#FF6B6B', linestyle='--', alpha=0.5, label=f'后半均值{self.results["io_trend"]["late_avg"]:.1f}')
            
            ax2 = ax1.twinx()
            color2 = '#F18F01'
            ax2.set_ylabel('费用 (CNY)', color=color2, fontsize=12)
            ax2.bar(daily_df['日期'], daily_df['费用 (元)'], alpha=0.3, color=color2, label='日费用')
            ax2.tick_params(axis='y', labelcolor=color2)
            
            plt.title(f'IO 比趋势（{self.results["io_trend"]["trend"]}）', fontsize=14, fontweight='bold')
            fig.tight_layout()
            plt.legend(loc='upper left')
            plt.savefig(os.path.join(charts_dir, '8_IO 比趋势.png'), dpi=150, bbox_inches='tight')
            plt.close()
        
        # 图表 3: 模型归因分析
        if self.results.get('model_attribution') is not None:
            attr_df = self.results['model_attribution']
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
                plt.savefig(os.path.join(charts_dir, '9_模型归因.png'), dpi=150, bbox_inches='tight')
                plt.close()
        
        # 图表 4: 周模式
        if self.results.get('weekly') is not None:
            weekly_df = self.results['weekly']
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
            plt.savefig(os.path.join(charts_dir, '10_周模式.png'), dpi=150, bbox_inches='tight')
            plt.close()
        
        print(f"✅ 生成 4 张深度分析图表")
    
    def generate_insight_chapter(self):
        """生成深度洞察章节"""
        chapter = []
        chapter.append("\n\n---\n\n")
        chapter.append("## 🔍 深度洞察\n\n")
        
        # 1. IO 比趋势
        chapter.append("### 📈 用户习惯演变（IO 比趋势）\n\n")
        chapter.append("![IO 比趋势](./charts/8_IO 比趋势.png)\n\n")
        
        if self.results.get('io_trend'):
            io = self.results['io_trend']
            chapter.append("**关键发现**：\n\n")
            chapter.append(f"- IO 比从 **{io['early_avg']:.1f}** 变化到 **{io['late_avg']:.1f}**\n")
            chapter.append(f"- 趋势：**{io['trend']}**\n")
            
            # IO 比含义解释
            if '阅读' in io['trend'] or '上升' in io['trend']:
                chapter.append("- 📖 **解读**：IO 比上升说明输入增多，用户更多在进行文档阅读、代码审查、资料分析等任务\n")
            elif '生成' in io['trend'] or '下降' in io['trend']:
                chapter.append("- ✍️ **解读**：IO 比下降说明输出增多，用户更多在进行代码生成、内容创作、批量输出等任务\n")
            else:
                chapter.append("- 📊 **解读**：IO 比平稳说明用户任务类型保持稳定\n")
            chapter.append("\n")
        
        # 2. 模型归因分析
        chapter.append("### 🎯 模型选择的多维影响\n\n")
        chapter.append("![模型归因](./charts/9_模型归因.png)\n\n")
        
        if self.results.get('model_attribution') is not None:
            attr_df = self.results['model_attribution']
            main_models = attr_df[attr_df['费用占比'] > 5]
            
            chapter.append("**关键发现**：\n\n")
            
            # 分析每个主要模型的 4 个量纲差异
            for _, row in main_models.iterrows():
                # 判断量纲差异
                if abs(row['费用占比'] - row['调用量占比']) < 5:
                    pattern = '线性'
                    desc = '费用与调用量成正比，属于常规使用'
                elif row['费用占比'] > row['调用量占比'] * 1.5:
                    pattern = '高成本'
                    desc = '单位成本高，建议优化'
                else:
                    pattern = '低成本'
                    desc = '单位成本低，性价比高'
                
                chapter.append(f"- **{row['模型']}**：费用{row['费用占比']}%，调用{row['调用量占比']}%，IO 比{row['IO 比']} → **{pattern}模式**（{desc}）\n")
            
            chapter.append("\n**模型切换 vs 用户习惯**：\n\n")
            
            if self.results.get('model_driver') is not None:
                driver_df = self.results['model_driver']
                model_driven = driver_df[driver_df['主导因素'] == '模型特性']['模型'].tolist()
                habit_driven = driver_df[driver_df['主导因素'] == '用户习惯']['模型'].tolist()
                
                if model_driven:
                    chapter.append(f"- 🔧 **模型特性主导**：{', '.join(model_driven[:5])}（IO 比稳定，由模型能力决定）\n")
                if habit_driven:
                    chapter.append(f"- 👤 **用户习惯主导**：{', '.join(habit_driven[:5])}（IO 比波动大，反映任务类型变化）\n")
            
            chapter.append("\n")
        
        # 3. Top 5 高峰日
        chapter.append("### 📅 Top 5 消费高峰日\n\n")
        chapter.append("![高峰日](./charts/7_Top5 高峰日.png)\n\n")
        
        if self.results.get('peak_days'):
            peak_df = pd.DataFrame(self.results['peak_days'])
            chapter.append("**关键发现**：\n\n")
            chapter.append(f"- 高峰日平均 **CNY {peak_df['费用'].mean():.1f}**，比日均高 **{peak_df['偏差%'].mean():+.1f}%**\n")
            chapter.append(f"- 最高峰：**{peak_df.iloc[0]['日期']}**（CNY {peak_df.iloc[0]['费用']:.1f}）\n")
            chapter.append(f"- 主要驱动模型：**{peak_df['主要模型'].mode().iloc[0] if len(peak_df) > 0 else 'N/A'}**\n\n")
        
        # 4. 周模式
        chapter.append("### 📊 周消费模式\n\n")
        chapter.append("![周模式](./charts/10_周模式.png)\n\n")
        
        if self.results.get('weekly') is not None:
            weekly_df = self.results['weekly']
            busiest = weekly_df.loc[weekly_df['平均费用'].idxmax()]
            quietest = weekly_df.loc[weekly_df['平均费用'].idxmin()]
            
            chapter.append("**关键发现**：\n\n")
            chapter.append(f"- 最忙：**{busiest['星期名']}**（日均 CNY {busiest['平均费用']:.1f}）\n")
            chapter.append(f"- 最闲：**{quietest['星期名']}**（日均 CNY {quietest['平均费用']:.1f}）\n\n")
        
        # 5. 行动建议
        chapter.append("### 💡 行动建议\n\n")
        chapter.append("1. **模型优化**：将高成本模型的部分任务迁移到 QWen-Plus/MiniMax-M2.5\n")
        chapter.append("2. **习惯调整**：\n")
        if self.results.get('io_trend') and '上升' in self.results['io_trend'].get('trend', ''):
            chapter.append("   - IO 比上升期：优先使用 QWen-Plus（阅读型任务性价比高）\n")
        else:
            chapter.append("   - 生成型任务：使用 MiniMax-M2.5（生成能力强，成本低）\n")
        chapter.append("3. **监控告警**：单日>CNY 100 时检查异常批量任务\n\n")
        
        return ''.join(chapter)
    
    def add_table_notes(self, content):
        """在三个表格后添加注释"""
        marker1 = '| **glm-4.7** | 4.91 | 0.6 | 39 | 12.59 | 1.07 | 4.59 | 🟡 良好 |'
        content = content.replace(marker1, marker1 + '\n\n> **注：** 下表仅列出费用 Top 5 模型，完整模型列表见深度洞察章节。')
        marker2 = '| **成本优化空间** | 40.9% | 对比行业平均 |'
        content = content.replace(marker2, marker2 + '\n\n> **注：** 效率分析展示了整体成本效益，行业平均约 7 元/百万 Tokens。')
        marker3 = '| 特殊复杂推理任务 | Claude/GPT | 能力最强，按需使用 |'
        content = content.replace(marker3, marker3 + '\n\n> **注：** 根据任务类型选择合适的模型，可节省 30-50% 成本。')
        return content
    
    def run(self):
        """执行完整流程"""
        print("🚀 开始深度分析...\n")
        
        self.load_data()
        self.analyze()
        self.generate_charts()
        
        # 生成深度洞察章节
        insight_md = self.generate_insight_chapter()
        
        # 读取原有报告
        base_report = os.path.join(self.output_dir, self.filename.replace('.csv', '_分析报告.md'))
        if os.path.exists(base_report):
            with open(base_report, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在总结之前插入
            
            content = self.add_table_notes(content)
            content = content.replace('## 🎯 总结', insight_md + '\n## 🎯 总结')
            
            # Define deep report path
            deep_report = os.path.join(self.output_dir, self.filename.replace('.csv', '_深度分析.md'))
            
            # 保存
        
            with open(deep_report, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 深度报告已生成：{deep_report}")
        else:
            print(f"⚠️ 未找到基础报告：{base_report}")
            print("   请先运行 billing_analyzer.py 生成基础报告")
        
        print("\n🎉 深度分析完成！")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法：python billing_analyzer_deep.py <账单 CSV 文件名>")
        sys.exit(1)
    
    filename = sys.argv[1]
    analyzer = DeepInsightAnalyzer(filename)
    analyzer.run()
