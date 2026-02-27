@echo off
echo ========================================
echo 创建日志迁移定时任务
echo ========================================
echo.
echo 此脚本需要管理员权限才能创建定时任务
echo.

echo 正在尝试以管理员权限重新运行...
echo.

powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %~dp0 && python create_task.py' -Verb RunAs"

echo.
echo 如果没有弹出权限请求，请：
echo 1. 右键点击此文件
echo 2. 选择"以管理员身份运行"
echo.
pause
