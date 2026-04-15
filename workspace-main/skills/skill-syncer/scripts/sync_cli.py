#!/usr/bin/env python3
"""
技能同步命令行工具
提供命令行接口获取 GitHub 上的技能

使用方法:
    python sync_cli.py get todo-manager
    python sync_cli.py get-all
    python sync_cli.py preview multi-agent-coordinator
    python sync_cli.py list
"""

import sys
import argparse
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from sync_manager import SkillSyncManager, SyncResult


def format_sync_result(result: SyncResult) -> str:
    """格式化同步结果为可读文本"""
    lines = []

    # 标题
    lines.append(f"\n{'='*50}")
    lines.append(f"技能: {result.skill_name}")
    lines.append(f"{'='*50}")

    # 状态
    if not result.success:
        lines.append(f"状态: ❌ 失败")
        lines.append(f"错误: {result.error}")
    elif not result.updated:
        lines.append(f"状态: 🛡️ 跳过（已保护）")
    else:
        lines.append(f"状态: ✅ 成功")
        lines.append(f"变更文件: {result.files_changed} 个")
        lines.append(f"新增文件: {result.files_added} 个")

    # 备份信息
    if result.backup_path:
        lines.append(f"备份位置: {result.backup_path}")

    # 详情
    if result.details:
        lines.append(f"\n详情:")
        for detail in result.details[:10]:  # 最多显示10条
            lines.append(f"  - {detail}")
        if len(result.details) > 10:
            lines.append(f"  ... 还有 {len(result.details) - 10} 个文件")

    return "\n".join(lines)


def cmd_get(skill_name: str, dry_run: bool = False, force: bool = False):
    """获取单个技能"""
    syncer = SkillSyncManager()
    result = syncer.sync_skill(skill_name, dry_run, force)
    print(format_sync_result(result))

    return 0 if result.success else 1


def cmd_get_all(dry_run: bool = False, force: bool = False):
    """获取全部技能"""
    syncer = SkillSyncManager()
    results = syncer.sync_all_skills(dry_run, install_new=True, force=force)  # 安装新技能

    print("\n" + "="*50)
    print("批量技能同步结果")
    print("="*50)

    print(f"\n统计:")
    print(f"  总计: {results['total']} 个")
    print(f"  更新: {results['updated_count']} 个")
    print(f"  安装: {results['installed_count']} 个（新技能）")
    print(f"  失败: {results['failed_count']} 个")
    print(f"  跳过: {results['skipped_count']} 个（本地特有）")

    print(f"\n详情:")
    print(f"{'技能名称':<25} {'状态':<10} {'变更':<8} {'说明'}")
    print("-" * 70)

    for result in results['results']:
        if result.success:
            if result.files_added > 0 and not any("更新" in d for d in result.details):
                status_icon = "📦"
                status_text = "新安装"
            elif result.updated:
                status_icon = "✅"
                status_text = "已更新"
            else:
                status_icon = "🛡️"
                status_text = "已保护"
        else:
            status_icon = "❌"
            status_text = "失败"

        changed = str(result.files_changed + result.files_added) if result.updated else "-"

        detail = result.details[0] if result.details else ""
        if result.error:
            detail = result.error[:30]

        print(f"{result.skill_name:<25} {status_icon} {status_text:<6} {changed:<8} {detail}")

    return 0 if results['success'] else 1


def cmd_latest(dry_run: bool = False):
    """获取最新技能（新技能 + 有更新的技能）"""
    syncer = SkillSyncManager()
    results = syncer.get_latest_skills(dry_run)

    if dry_run:
        print("\n" + "="*50)
        print("最新技能预览")
        print("="*50)
        print(f"\n新技能 ({len(results['new_skills'])} 个):")
        for skill in results['new_skills'][:10]:
            print(f"  📦 {skill}")
        if len(results['new_skills']) > 10:
            print(f"  ... 还有 {len(results['new_skills']) - 10} 个")

        print(f"\n有更新的技能 ({len(results['update_skills'])} 个):")
        for skill in results['update_skills'][:10]:
            print(f"  ✅ {skill}")
        if len(results['update_skills']) > 10:
            print(f"  ... 还有 {len(results['update_skills']) - 10} 个")

        print(f"\n{results['message']}")
        return 0

    print("\n" + "="*50)
    print("获取最新技能结果")
    print("="*50)

    print(f"\n统计:")
    print(f"  总计: {results['total']} 个")
    print(f"  新安装: {results['new_count']} 个")
    print(f"  更新: {results['update_count']} 个")
    print(f"  成功: {results['success_count']} 个")
    print(f"  失败: {results['failed_count']} 个")

    if results['results']:
        print(f"\n详情:")
        print(f"{'技能名称':<25} {'状态':<10} {'说明'}")
        print("-" * 70)

        for result in results['results']:
            if result.success:
                if result.files_added > 0:
                    status_icon = "📦"
                    status_text = "新安装"
                elif result.updated:
                    status_icon = "✅"
                    status_text = "已更新"
                else:
                    status_icon = "🛡️"
                    status_text = "已保护"
            else:
                status_icon = "❌"
                status_text = "失败"

            detail = result.details[0] if result.details else ""
            if result.error:
                detail = result.error[:30]

            print(f"{result.skill_name:<25} {status_icon} {status_text:<6} {detail}")

    print(f"\n{results['message']}")
    return 0 if results['success'] else 1


def cmd_preview(skill_name: str, force: bool = False):
    """预览变更"""
    print(f"\n[预览模式] 将显示 '{skill_name}' 的变更，但不会实际执行\n")
    return cmd_get(skill_name, dry_run=True, force=force)


def cmd_list():
    """列出技能"""
    syncer = SkillSyncManager()

    local_skills = syncer.get_local_skills()
    remote_skills = syncer.get_remote_skills()

    print("\n" + "="*50)
    print("技能列表")
    print("="*50)

    print(f"\n本地技能 ({len(local_skills)} 个):")
    for skill in local_skills:
        status = ""
        if skill in remote_skills:
            status = "[可同步]"
        else:
            status = "[本地特有]"
        print(f"  - {skill:<25} {status}")

    print(f"\n远程技能 ({len(remote_skills)} 个):")
    for skill in remote_skills:
        status = ""
        if skill not in local_skills:
            status = "[新技能]"
        print(f"  - {skill:<25} {status}")

    print(f"\n总结:")
    print(f"  本地特有: {len([s for s in local_skills if s not in remote_skills])} 个")
    print(f"  可同步: {len([s for s in local_skills if s in remote_skills])} 个")
    print(f"  远程新技能: {len([s for s in remote_skills if s not in local_skills])} 个")

    return 0


def cmd_status(skill_name: str):
    """查看技能状态"""
    syncer = SkillSyncManager()
    status = syncer.get_skill_status(skill_name)

    print(f"\n{'='*50}")
    print(f"技能状态: {skill_name}")
    print(f"{'='*50}")

    print(f"\n本地存在: {'✅ 是' if status['local_exists'] else '❌ 否'}")
    print(f"远程存在: {'✅ 是' if status['remote_exists'] else '❌ 否'}")

    if status['local_only']:
        print(f"\n类型: 🛡️ 本地特有技能（受保护）")
    elif status['remote_only']:
        print(f"\n类型: 📦 远程新技能（需手动安装）")
    elif status['can_sync']:
        print(f"\n类型: 🔄 可同步")
        print(f"远程文件数: {len(status['remote_files'])}")
    else:
        print(f"\n类型: ❌ 无法同步")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="从 GitHub 获取技能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python sync_cli.py get todo-manager
  python sync_cli.py get todo-manager --force
  python sync_cli.py get-all
  python sync_cli.py get-all --force
  python sync_cli.py latest
  python sync_cli.py latest --dry-run
  python sync_cli.py preview multi-agent-coordinator
  python sync_cli.py list
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # get 命令
    get_parser = subparsers.add_parser("get", help="获取单个技能")
    get_parser.add_argument("skill_name", help="技能名称")
    get_parser.add_argument("--dry-run", action="store_true", help="预览模式")
    get_parser.add_argument("--force", action="store_true", help="强制更新（覆盖本地特有技能保护）")

    # get-all 命令
    get_all_parser = subparsers.add_parser("get-all", help="获取全部技能")
    get_all_parser.add_argument("--dry-run", action="store_true", help="预览模式")
    get_all_parser.add_argument("--force", action="store_true", help="强制更新（覆盖本地特有技能保护）")

    # latest 命令
    latest_parser = subparsers.add_parser("latest", help="获取最新技能（新技能 + 有更新的技能）")
    latest_parser.add_argument("--dry-run", action="store_true", help="预览模式")

    # preview 命令
    preview_parser = subparsers.add_parser("preview", help="预览变更")
    preview_parser.add_argument("skill_name", help="技能名称")
    preview_parser.add_argument("--force", action="store_true", help="强制更新（覆盖本地特有技能保护）")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出技能")

    # status 命令
    status_parser = subparsers.add_parser("status", help="查看技能状态")
    status_parser.add_argument("skill_name", help="技能名称")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "get":
            return cmd_get(args.skill_name, args.dry_run, args.force)
        elif args.command == "get-all":
            return cmd_get_all(args.dry_run, args.force)
        elif args.command == "latest":
            return cmd_latest(args.dry_run)
        elif args.command == "preview":
            return cmd_preview(args.skill_name, args.force)
        elif args.command == "list":
            return cmd_list()
        elif args.command == "status":
            return cmd_status(args.skill_name)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        return 1
    except Exception as e:
        print(f"\n错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
