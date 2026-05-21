# -*- coding: utf-8 -*-
"""
运营商新闻采集系统 - 主入口
"""
import sys
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import asyncio
import os

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import List, Any
from datetime import datetime
from common.models import UserQuery, SystemResult, TaskNode
from bootstrap.loader import get_knowledge_base
from planner.planner import TaskPlanner
from collector.engine import AdaptiveCollectionEngine
from storage.manager import StorageManager
from assembler.assembler import ReportAssembler


class TelecomNewsFetcher:
    """运营商新闻采集系统主类"""
    
    def __init__(self):
        self.kb = None
        self.planner = None
        self.collector = None
        self.storage = None
        self.assembler = None
        
    async def initialize(self):
        """初始化系统"""
        print("[INIT] 正在初始化系统...")
        
        # 加载Bootstrap知识库
        print("[INIT] 加载知识库...")
        self.kb = get_knowledge_base()
        print(f"  [OK] 知识库版本: {self.kb.version}")
        print(f"  [OK] 运营商: {list(self.kb.operators.keys())}")
        print(f"  [OK] 模板数: {len(self.kb.task_templates)}")
        
        # 初始化规划器
        print("[INIT] 初始化任务规划器...")
        self.planner = TaskPlanner(self.kb)
        
        # 初始化采集引擎
        print("[INIT] 初始化采集引擎...")
        self.collector = AdaptiveCollectionEngine()
        
        # 初始化存储管理器
        print("[INIT] 初始化存储管理器...")
        self.storage = StorageManager()
        
        # 初始化报告汇编器
        print("[INIT] 初始化报告汇编器...")
        self.assembler = ReportAssembler()
        
        print("[INIT] 系统初始化完成\n")
        
    async def process(self, query_text: str) -> SystemResult:
        """
        处理用户查询
        
        Args:
            query_text: 用户查询文本
            
        Returns:
            SystemResult: 处理结果
        """
        print(f"[QUERY] 用户查询: {query_text}")
        
        # 创建查询对象
        query = UserQuery(text=query_text)
        
        # M1: 任务分解
        print("\n[PLANNER] M1: 任务分解...")
        plan_result = await self.planner.execute(query)
        
        # 检查是否有执行错误
        if plan_result.error:
            return SystemResult(
                success=False,
                error=f"任务分解失败: {plan_result.error}"
            )
        
        task_tree = plan_result.output
        
        # 打印反思结果
        if plan_result.reflection:
            print(f"\n[REFLECTION] 反思结果:")
            print(f"  成功: {plan_result.reflection.success}")
            if plan_result.reflection.issues:
                print(f"  问题: {plan_result.reflection.issues}")
            if plan_result.reflection.suggestions:
                print(f"  建议: {plan_result.reflection.suggestions}")
        
        # 打印任务树
        print(f"\n[STATS] 任务树统计:")
        if task_tree.stats:
            print(f"  总任务数: {task_tree.stats.total_tasks}")
            print(f"  最大深度: {task_tree.stats.max_depth}")
            print(f"  预估耗时: {task_tree.stats.estimated_duration:.0f}秒")
            print(f"  按层级分布: {task_tree.stats.by_level}")
            print(f"  按来源分布: {task_tree.stats.by_source}")
        
        print(f"\n[TREE] 任务树结构:")
        self._print_task_tree(task_tree.root)
        
        # M2: 采集执行
        print("\n[COLLECTOR] M2: 采集执行...")
        all_items = []
        
        # 遍历任务树，执行叶子节点
        leaf_tasks = self._get_leaf_tasks(task_tree.root)
        print(f"  发现 {len(leaf_tasks)} 个采集任务")
        
        for i, task in enumerate(leaf_tasks[:3], 1):  # 限制最多3个任务
            print(f"\n  [Task {i}/{min(len(leaf_tasks), 3)}] source_id={task.source_id}, type={task.type}")
            print(f"    关键词: {task.keywords[:3]}...")
            
            collect_result = await self.collector.execute(task)
            
            if collect_result.error:
                print(f"    [ERROR] {collect_result.error}")
            else:
                items = collect_result.output or []
                print(f"    [OK] 获取 {len(items)} 条新闻")
                all_items.extend(items)
        
        print(f"\n[SUMMARY] 共采集 {len(all_items)} 条新闻")
        
        # M3: 存储管理
        print("\n[STORAGE] M3: 存储管理...")
        storage_result = await self.storage.execute(all_items)
        
        if storage_result.error:
            print(f"  [ERROR] 存储失败: {storage_result.error}")
        else:
            print(f"  [OK] 存储完成，共 {len(storage_result.output)} 条")
        
        # M4: 报告生成
        print("\n[ASSEMBLER] M4: 报告生成...")
        report_result = await self.assembler.execute((all_items, query))
        
        if report_result.error:
            print(f"  [ERROR] 报告生成失败: {report_result.error}")
        else:
            print(f"  [OK] 报告生成完成")
            # 保存报告
            report_path = f"output/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_result.output)
            print(f"  [OK] 报告已保存: {report_path}")
        
        # 返回结果
        return SystemResult(
            success=True,
            report=report_result.output if not report_result.error else None,
            statistics={
                'task_count': task_tree.stats.total_tasks if task_tree.stats else 0,
                'max_depth': task_tree.stats.max_depth if task_tree.stats else 0,
                'collected_items': len(all_items),
                'stored_items': len(storage_result.output) if not storage_result.error else 0
            }
        )
    
    def _print_task_tree(self, node, indent=0):
        """打印任务树"""
        prefix = "  " * indent
        info = f"[{node.type}]"
        
        if node.operator:
            info += f" {node.operator}"
        if node.source_id:
            info += f" | {node.source_id}"
        if node.keywords:
            keywords_str = ", ".join(node.keywords[:3])
            if len(node.keywords) > 3:
                keywords_str += f"...({len(node.keywords)}个)"
            info += f" | 关键词: {keywords_str}"
        
        print(f"{prefix}{info}")
        print(f"{prefix}  └─ {node.description}")
        
        for child in node.children:
            self._print_task_tree(child, indent + 1)
    
    def _get_leaf_tasks(self, node: TaskNode) -> List[TaskNode]:
        """获取所有叶子任务"""
        if not node.children:
            return [node]
        
        leaves = []
        for child in node.children:
            leaves.extend(self._get_leaf_tasks(child))
        return leaves


async def main():
    """主函数"""
    # 创建系统实例
    fetcher = TelecomNewsFetcher()
    
    # 初始化
    await fetcher.initialize()
    
    # 测试查询
    test_queries = [
        "查一下中国移动最近AI方面的新闻",
    ]
    
    for query_text in test_queries:
        print("=" * 60)
        result = await fetcher.process(query_text)
        
        if result.success:
            print(f"\n[RESULT] 处理成功")
        else:
            print(f"\n[ERROR] 处理失败")
            print(f"错误详情: {result.error}")
        
        print("\n")


if __name__ == "__main__":
    asyncio.run(main())
