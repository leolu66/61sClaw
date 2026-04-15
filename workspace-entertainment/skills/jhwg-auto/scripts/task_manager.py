#!/usr/bin/env python3
"""
几何王国任务管理器
支持通过任务名称或数字编号启动任务
支持策略批量执行
"""

import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Tuple, List

# 脚本目录
SCRIPTS_DIR = Path(__file__).parent

# 任务定义：编号 -> (名称, 描述, 脚本文件名)
TASKS: Dict[int, Tuple[str, str, str]] = {
    1: ("PC端奖励", "领取PC端专属奖励", "task_pc_reward.py"),
    2: ("商店免费福利", "领取商店每日免费福利", "task_shop_free_reward.py"),
    3: ("终生卡奖励", "领取终生卡每日奖励", "task_lifetime_card.py"),
    4: ("巡逻奖励", "领取巡逻奖励（每日可定时领取）", "task_patrol_reward.py"),
    5: ("自动钓鱼", "开启自动钓鱼功能", "task_auto_fishing.py"),
    6: ("冒险试炼", "完成冒险试炼之地任务", "task_adventure_trial.py"),
    7: ("自动招募", "执行自动招募", "task_auto_recruit.py"),
    8: ("部落任务", "完成部落签到和子任务", "task_tribe.py"),
    9: ("更多领取", "领取邮件、好友赠送", "task_claim_more.py"),
    10: ("杂货铺宝箱", "领取杂货铺4个宝箱，每个3轮", "task_grocery_shop.py"),
    11: ("快速巡逻", "执行快速巡逻（每日有限制次数）", "task_quick_patrol.py"),
    12: ("竞技挑战", "竞技挑战碾压对手（3次）", "task_arena.py"),
    13: ("黑暗之门", "冒险任务-黑暗之门挑战", "task_dark_portal.py"),
}

# 策略定义（从配置文件加载）
STRATEGIES: Dict[str, Dict] = {}

# 任务名称到编号的映射
TASK_NAME_TO_ID: Dict[str, int] = {}
for task_id, (name, desc, filename) in TASKS.items():
    # 支持多种名称匹配
    TASK_NAME_TO_ID[name] = task_id
    TASK_NAME_TO_ID[name.lower()] = task_id
    TASK_NAME_TO_ID[name.replace("奖励", "").strip()] = task_id
    TASK_NAME_TO_ID[name.replace("任务", "").strip()] = task_id
    TASK_NAME_TO_ID[filename] = task_id
    TASK_NAME_TO_ID[filename.replace(".py", "")] = task_id
    
    # 添加简称
    if task_id == 1:
        TASK_NAME_TO_ID["pc"] = task_id
        TASK_NAME_TO_ID["pc端"] = task_id
        TASK_NAME_TO_ID["pc_reward"] = task_id
    elif task_id == 2:
        TASK_NAME_TO_ID["商店"] = task_id
        TASK_NAME_TO_ID["免费福利"] = task_id
        TASK_NAME_TO_ID["shop"] = task_id
    elif task_id == 3:
        TASK_NAME_TO_ID["终生卡"] = task_id
        TASK_NAME_TO_ID["终身卡"] = task_id
        TASK_NAME_TO_ID["lifetime"] = task_id
    elif task_id == 4:
        TASK_NAME_TO_ID["巡逻"] = task_id
        TASK_NAME_TO_ID["patrol"] = task_id
    elif task_id == 5:
        TASK_NAME_TO_ID["钓鱼"] = task_id
        TASK_NAME_TO_ID["fishing"] = task_id
    elif task_id == 6:
        TASK_NAME_TO_ID["冒险"] = task_id
        TASK_NAME_TO_ID["试炼"] = task_id
        TASK_NAME_TO_ID["adventure"] = task_id
    elif task_id == 7:
        TASK_NAME_TO_ID["招募"] = task_id
        TASK_NAME_TO_ID["recruit"] = task_id
    elif task_id == 8:
        TASK_NAME_TO_ID["部落"] = task_id
        TASK_NAME_TO_ID["tribe"] = task_id
    elif task_id == 9:
        TASK_NAME_TO_ID["更多"] = task_id
        TASK_NAME_TO_ID["邮件"] = task_id
        TASK_NAME_TO_ID["杂货铺"] = task_id
        TASK_NAME_TO_ID["claim_more"] = task_id
    elif task_id == 10:
        TASK_NAME_TO_ID["杂货铺宝箱"] = task_id
        TASK_NAME_TO_ID["宝箱"] = task_id
        TASK_NAME_TO_ID["grocery"] = task_id
        TASK_NAME_TO_ID["grocery_shop"] = task_id
    elif task_id == 11:
        TASK_NAME_TO_ID["快速巡逻"] = task_id
        TASK_NAME_TO_ID["快巡"] = task_id
        TASK_NAME_TO_ID["quick_patrol"] = task_id
    elif task_id == 12:
        TASK_NAME_TO_ID["竞技"] = task_id
        TASK_NAME_TO_ID["竞技挑战"] = task_id
        TASK_NAME_TO_ID["arena"] = task_id
    elif task_id == 13:
        TASK_NAME_TO_ID["黑暗之门"] = task_id
        TASK_NAME_TO_ID["dark_portal"] = task_id
        TASK_NAME_TO_ID["黑暗"] = task_id


def load_strategies():
    """从配置文件加载策略"""
    global STRATEGIES
    config_path = SCRIPTS_DIR / "config.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                STRATEGIES = config.get('strategies', {})
        except Exception as e:
            print(f"加载策略配置失败: {e}")
            STRATEGIES = {}
    
    # 如果配置文件没有策略，使用默认策略
    if not STRATEGIES:
        STRATEGIES = {
            "all": {
                "name": "全部任务",
                "description": "执行所有9个任务",
                "tasks": [1, 2, 3, 4, 5, 6, 7, 8, 9],
                "delay_between": 3
            },
            "daily": {
                "name": "日常任务",
                "description": "每日必做的基础任务",
                "tasks": [1, 2, 3, 4, 5, 7, 9],
                "delay_between": 2
            },
            "quick": {
                "name": "快速任务",
                "description": "耗时最短的几个任务",
                "tasks": [1, 2, 3, 4],
                "delay_between": 1
            }
        }


def list_tasks():
    """列出所有可用任务"""
    print("=" * 70)
    print("几何王国 - 可用任务列表")
    print("=" * 70)
    print()
    
    for task_id, (name, desc, filename) in TASKS.items():
        print(f"  [{task_id}] {name}")
        print(f"      {desc}")
        print(f"      脚本: {filename}")
        print()
    
    print("=" * 70)


def list_strategies():
    """列出所有可用策略"""
    load_strategies()
    
    print("=" * 70)
    print("几何王国 - 可用策略列表")
    print("=" * 70)
    print()
    
    for strategy_id, strategy in STRATEGIES.items():
        print(f"  [{strategy_id}] {strategy['name']}")
        print(f"      {strategy['description']}")
        print(f"      包含任务: {', '.join(map(str, strategy['tasks']))}")
        print(f"      任务间隔: {strategy.get('delay_between', 2)}秒")
        print()
    
    print("=" * 70)


def run_task(task_id: int) -> int:
    """
    运行指定编号的任务
    
    Args:
        task_id: 任务编号
        
    Returns:
        子进程返回码
    """
    if task_id not in TASKS:
        print(f"错误: 未知的任务编号 {task_id}")
        print(f"   请使用 1-{max(TASKS.keys())} 之间的编号")
        return 1
    
    name, desc, filename = TASKS[task_id]
    script_path = SCRIPTS_DIR / filename
    
    print()
    print("=" * 70)
    print(f"启动任务 [{task_id}]: {name}")
    print(f"描述: {desc}")
    print(f"脚本: {filename}")
    print("=" * 70)
    print()
    
    try:
        # 使用子进程运行任务脚本
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=SCRIPTS_DIR,
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"启动任务失败: {e}")
        return 1


def run_strategy(strategy_id: str) -> int:
    """
    运行指定策略
    
    Args:
        strategy_id: 策略ID
        
    Returns:
        执行结果，0表示成功
    """
    load_strategies()
    
    if strategy_id not in STRATEGIES:
        print(f"错误: 未知的策略 '{strategy_id}'")
        print()
        print("可用策略:")
        list_strategies()
        return 1
    
    strategy = STRATEGIES[strategy_id]
    tasks = strategy['tasks']
    delay = strategy.get('delay_between', 2)
    
    print()
    print("=" * 70)
    print(f"启动策略: {strategy['name']}")
    print(f"描述: {strategy['description']}")
    print(f"包含任务: {tasks}")
    print(f"任务间隔: {delay}秒")
    print("=" * 70)
    print()
    
    success_count = 0
    fail_count = 0
    
    for i, task_id in enumerate(tasks, 1):
        print()
        print(f">>> 策略进度: {i}/{len(tasks)} <<<")
        
        return_code = run_task(task_id)
        
        if return_code == 0:
            success_count += 1
        else:
            fail_count += 1
            print(f"任务 {task_id} 执行失败或被终止")
        
        # 如果不是最后一个任务，等待一段时间
        if i < len(tasks):
            print(f"\n[等待] {delay}秒后继续下一个任务...")
            time.sleep(delay)
    
    print()
    print("=" * 70)
    print(f"策略执行完成: {strategy['name']}")
    print(f"成功: {success_count} | 失败: {fail_count} | 总计: {len(tasks)}")
    print("=" * 70)
    
    return 0 if fail_count == 0 else 1


def parse_task_identifier(identifier: str) -> int:
    """
    解析任务标识符（编号或名称）
    
    Args:
        identifier: 用户输入的标识符
        
    Returns:
        任务编号，如果无法解析则返回 -1
    """
    # 尝试作为数字解析
    try:
        task_id = int(identifier)
        if task_id in TASKS:
            return task_id
    except ValueError:
        pass
    
    # 尝试作为名称解析
    identifier_lower = identifier.lower().strip()
    if identifier_lower in TASK_NAME_TO_ID:
        return TASK_NAME_TO_ID[identifier_lower]
    
    # 模糊匹配
    for name, task_id in TASK_NAME_TO_ID.items():
        if identifier_lower in name.lower() or name.lower() in identifier_lower:
            return task_id
    
    return -1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='几何王国任务管理器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 列出任务和策略
  python task_manager.py --list
  python task_manager.py --strategies
  
  # 执行单个任务
  python task_manager.py 1              # 通过编号
  python task_manager.py PC端奖励       # 通过名称
  python task_manager.py pc             # 通过简称
  
  # 执行策略
  python task_manager.py --strategy all     # 全部任务
  python task_manager.py --strategy daily   # 日常任务
  python task_manager.py --strategy quick   # 快速任务
        '''
    )
    
    parser.add_argument(
        'task',
        nargs='?',
        help='任务编号或任务名称'
    )
    
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='列出所有可用任务'
    )
    
    parser.add_argument(
        '-s', '--strategies',
        action='store_true',
        help='列出所有可用策略'
    )
    
    parser.add_argument(
        '--strategy',
        metavar='ID',
        help='执行指定策略 (all/daily/quick/challenge/resource)'
    )
    
    args = parser.parse_args()
    
    # 列出策略
    if args.strategies:
        list_strategies()
        return 0
    
    # 列出任务
    if args.list:
        list_tasks()
        return 0
    
    # 执行策略
    if args.strategy:
        return_code = run_strategy(args.strategy)
        return return_code
    
    # 如果没有参数，显示帮助
    if args.task is None:
        parser.print_help()
        print()
        list_tasks()
        print()
        list_strategies()
        return 0
    
    # 解析并运行单个任务
    task_id = parse_task_identifier(args.task)
    
    if task_id == -1:
        print(f"错误: 无法识别任务 '{args.task}'")
        print()
        print("可用任务:")
        list_tasks()
        return 1
    
    # 运行任务
    return_code = run_task(task_id)
    
    if return_code == 0:
        print()
        print("任务执行成功!")
    else:
        print()
        print(f"任务执行失败或被终止 (返回码: {return_code})")
    
    return return_code


if __name__ == '__main__':
    sys.exit(main())
