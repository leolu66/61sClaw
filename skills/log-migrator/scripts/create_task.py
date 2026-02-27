#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建日志迁移定时任务
使用 Windows 任务计划程序 API 创建定时任务
"""
import subprocess
import sys

# 解决 Windows 中文编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def delete_old_task(task_name):
    """删除旧任务"""
    try:
        result = subprocess.run(
            f'schtasks /Delete /TN "{task_name}" /F',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0 or 'ERROR: 找不到任务' in result.stderr:
            print(f"✅ 旧任务已清理: {task_name}")
        return True
    except Exception as e:
        print(f"⚠️  清理旧任务时出错: {e}")
        return False


def create_scheduled_task(task_name, script_path):
    """创建定时任务"""
    try:
        # 创建任务命令
        cmd = f'schtasks /Create /TN "{task_name}" /TR "{script_path}" /SC DAILY /ST 23:20 /RU "SYSTEM" /RL HIGHEST /F'
        print(f"执行命令: {cmd}")
        print()

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        print(f"返回码: {result.returncode}")
        print(f"标准输出:\n{result.stdout}")

        if result.returncode == 0:
            print("\n✅ 定时任务创建成功！")
            print("=" * 60)
            print(f"任务名称: {task_name}")
            print("执行时间: 每天 23:20")
            print(f"执行脚本: {script_path}")
            print("归档目录: D:\\openclaw\\logs\\daily\\archive")
            print("=" * 60)
            print("\n提示: 可以在 '任务计划程序' 中查看和管理此任务")
            print("\n是否打开任务计划程序？(Y/N): ", end='')
            choice = input().strip().upper()
            if choice == 'Y':
                subprocess.run('taskschd.msc', shell=True)
            return True
        else:
            print("\n❌ 定时任务创建失败！")
            print("=" * 60)
            print(f"错误信息:\n{result.stderr}")
            print("=" * 60)
            print("\n请手动创建任务:")
            print("1. 打开 '任务计划程序' (taskschd.msc)")
            print("2. 创建基本任务")
            print("3. 设置:")
            print("   - 程序: " + script_path)
            print("   - 起始于: " + script_path.replace("migrate_logs.bat", ""))
            print("   - 触发器: 每天 23:20")
            print("   - 使用最高权限运行")
            return False

    except Exception as e:
        print(f"\n❌ 创建任务时出错: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("创建日志自动归档定时任务")
    print("=" * 60)
    print()

    task_name = "LogMigrator"
    script_path = r"C:\Users\luzhe\.openclaw\workspace-main\skills\log-migrator\scripts\migrate_logs.bat"

    # 删除旧任务
    print("[1/3] 删除旧任务...")
    delete_old_task(task_name)
    print()

    # 创建新任务
    print("[2/3] 创建新任务...")
    print()
    success = create_scheduled_task(task_name, script_path)
    print()

    # 完成
    if success:
        print("[3/3] 完成！")
    else:
        print("[3/3] 失败！")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
