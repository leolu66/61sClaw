@echo off
chcp 65001 > nul
cd /d "%~dp0"
python audio_control.py %*
