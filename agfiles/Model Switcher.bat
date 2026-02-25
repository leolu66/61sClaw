@echo off
chcp 65001 >nul
python "%~dp0model_switcher.py" %*
