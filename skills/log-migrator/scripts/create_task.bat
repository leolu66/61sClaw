@echo off
chcp 65001 >nul

echo ========================================
echo 创建日志自动归档定时任务
echo ========================================
echo.

echo [1/3] 删除旧任务...
schtasks /Delete /TN "日志自动归档" /F >nul 2>&1

echo [2/3] 创建新任务...
schtasks /Create /TN "日志自动归档" ^
  /TR "C:\Users\luzhe\.openclaw\workspace-main\skills\log-migrator\scripts\migrate_logs.bat" ^
  /SC DAILY ^
  /ST 23:20 ^
  /RU "SYSTEM" ^
  /RL HIGHEST ^
  /F

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [3/3] 任务创建成功！
    echo ========================================
    echo 任务名称: 日志自动归档
    echo 执行时间: 每天 23:20
    echo 归档目录: D:\openclaw\logs\daily\archive
    echo.
    echo 提示: 可以在 '任务计划程序' 中查看和管理此任务
    echo.
    echo 打开任务计划程序...
    taskschd.msc
) else (
    echo.
    echo ========================================
    echo [3/3] 任务创建失败！
    echo ========================================
    echo 错误代码: %errorlevel%
    echo.
    echo 请手动创建任务：
    echo 1. 打开 '任务计划程序' (taskschd.msc)
    echo 2. 创建基本任务
    echo 3. 设置：
    echo    - 程序: C:\Users\luzhe\.openclaw\workspace-main\skills\log-migrator\scripts\migrate_logs.bat
    echo    - 起始于: C:\Users\luzhe\.openclaw\workspace-main\skills\log-migrator\scripts
    echo    - 触发器: 每天 23:20
    echo.
)

pause
