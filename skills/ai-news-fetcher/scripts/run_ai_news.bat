@echo off
chcp 65001 >nul
echo ========================================
echo AI新闻日报定时任务
echo 启动时间: %date% %time%
echo ========================================
echo.

cd /d "C:\Users\luzhe\.claude\skills\ai-news-fetcher\scripts"

python generate_report.py

echo.
echo ========================================
echo 任务完成时间: %date% %time%
echo ========================================
