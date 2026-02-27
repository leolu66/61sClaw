# -*- coding: utf-8 -*-
"""创建正确的 migrate_logs.bat 文件"""
import os

bat_content = """@echo off
chcp 65001 >nul
echo ========================================
echo 日志自动归档
echo 启动时间: %date% %time%
echo ========================================
echo.

cd /d "%~dp0"

python migrate_logs.py

echo.
echo ========================================
echo 任务完成时间: #date% %time%
echo ========================================
pause
"""

bat_file = "skills/log-migrator/scripts/migrate_logs.bat"
with open(bat_file, 'w', encoding='utf-8') as f:
    f.write(bat_content)

print(f"已创建: {bat_file}")
print("文件内容:")
print(bat_content)
