# -*- coding: utf-8 -*-
"""使用 Python 直接创建 Windows 定时任务，跳过 bat 文件"""
import subprocess
import sys

# 解决 Windows 中文编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def create_task_directly():
    """直接使用 Python 创建定时任务，不依赖 bat 文件"""
    task_name = "LogMigrator"
    script_dir = r"C:\Users\luzhe\.openclaw\workspace-main\skills\log-migrator\scripts"
    python_exe = r"python.exe"
    python_script = r"migrate_logs.py"

    # 删除旧任务
    print(f"[1/3] 删除旧任务: {task_name}")
    result = subprocess.run(
        f'schtasks /Delete /TN "{task_name}" /F',
        shell=True,
        capture_output=True,
        text=True
    )
    print(result.stdout)

    # 创建新任务
    print(f"[2/3] 创建新任务")
    cmd = (
        f'schtasks /Create /TN "{task_name}" '
        f'/TR "{script_dir}\\{python_exe}" '
        f'/ARG "{python_script}" '
        f'/SC DAILY '
        f'/ST 23:20 '
        f'/RU "SYSTEM" '
        '/RL HIGHEST '
        '/F'
    )

    print(f"执行命令: {cmd}")
    print()

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print(f"标准错误:\n{result.stderr}")

    if result.returncode == 0:
        print("\n✅ 定时任务创建成功！")
        print("=" * 60)
        print(f"任务名称: {task_name}")
        print("执行时间: 每天 23:20")
        print(f"命令: {script_dir}\\{python_exe} {python_script}")
        print("归档目录: D:\\openclaw\\logs\\daily\\archive")
        print("=" * 60)

        # 自动打开任务计划程序
        print("\n是否打开任务计划程序查看任务？(Y/N): ", end='')
        choice = input().strip().upper()
        if choice == 'Y':
            subprocess.run('taskschd.msc', shell=True)
    else:
        print("\n稍后可以在任务计划程序中查看任务")
    else:
        print("\n❌ 定时任务创建失败！")
        print("=" * 60)
        print("\n手动创建步骤:")
        print("1. 按 Win+R，输入 taskschd.msc")
        print("2. 创建基本任务")
        print("3. 程序/触发器: 每天 23:20")
        print("4. 操作:")
        print(f"   程序: {python_exe}")
        print(f"   参数: {python_script}")
        print(f"   起始于: {script_dir}")
        print("5. 使用最高权限运行")

    print()
    print("=" * 60)

if __name__ == "__main__":
    create_task_directly()
