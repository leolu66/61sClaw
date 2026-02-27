@echo off
chcp 65001 >nul
echo.
echo ================================================================================
echo   Model Switcher - 交互式模型选择器
echo ================================================================================
echo.
python "%~dp0scripts\model_selector.py" %*
echo.
pause
