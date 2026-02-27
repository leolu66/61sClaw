# -*- coding: utf-8 -*-
"""创建 migrate_logs.bat 文件"""
bat_content = """@echo off
chcp 65001 >nul
echo ========================================
echo Log Archive Tool
echo Start Time: %date% %time%
echo ========================================
echo.

cd /d "%~dp0"

python migrate_logs.py

echo.
echo ========================================
echo End Time: %date% %time%
echo ========================================
pause
"""

bat_file = "skills/log-migrator/scripts/migrate_logs.bat"
with open(bat_file, 'w', encoding='utf-8') as f:
    f.write(bat_content)

print(f"已创建: {bat_file}")
