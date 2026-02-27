@echo off
chcp 65001 >nul
echo ========================================
echo 日志自动归档
echo 启动时间: %date% %time%
echo ========================================
echo.

cd /d %~dp0

python migrate_logs.py

echo.
echo ========================================
echo 任务完成时间: %date% %time%
echo ========================================
pause
