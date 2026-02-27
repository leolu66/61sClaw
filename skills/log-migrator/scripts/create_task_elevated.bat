@echo off
chcp 65001 >nul
echo ========================================
echo 创建日志迁移定时任务
echo ========================================
echo.
echo 此脚本需要管理员权限才能创建定时任务
echo.

cd /d "%~dp0"
echo 当前目录: %CD%
echo.

echo 正在尝试以管理员权限运行 Python 脚本...
echo.

powershell -Command "Start-Process python -ArgumentList 'create_task.py' -Verb RunAs -WorkingDirectory '%CD%'"

echo.
echo ========================================
echo 如果没有弹出权限请求，请手动执行以下步骤：
echo.
echo 1. 右键点击 create_task.py
echo 2. 选择"以管理员身份运行"
echo.
echo ========================================
pause
