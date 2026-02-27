@echo off
chcp 65001 >nul
title =E5=88=9B=90=85=E5=A1=A8=E7=9B=BB=E5=A4=8D=E7=A8=BE=E4=BB=BB=E5=8A=A1=E5=9C=B0=EF=BC=8C=EF=BC=8C

echo.
echo ========================================
echo   =E5=88=9B=90=85=E5=A1=A8=E7=9B=BB=E5=A4=8D=E7=A8=BE=E4=BB=BB=E5=8A=A1=E5=9C=B0=EF=BC=8C=EF=BC=8C
echo ========================================
echo.
echo =E6=AD=A3=E5=9C=A8=E4=BB=A5=E7=AE=A1=E7=90=86=E6=9D=83=E8=BF=90=E8=A1=8C=E8=A1=90...
echo.

cd /d "%~dp0"

:: =E4=BD=BF=E7=94=A8 PowerShell =E7=9A=84 -File =E5=8F=82=E6=95=B0=E8=A1=90=E8=84=A7=E7=90=86=E7=9B=BB
powershell -ExecutionPolicy Bypass -File create_task.py

echo.
if %errorlevel% equ 0 (
    echo ========================================
    echo   =E5=AE=9A=E6=97=B6=E4=BB=BB=E5=8A=A1=E5=9C=B0=E5=88=9B=E6=88=90=EF=BC=81=E5=AE=8C=EF=BC=81
    echo ========================================
    echo.
    echo =E6=8C=89=E4=BB=BB=E6=84=8F=E4=BB=BB=E6=89=93=E5=88=A5=EF=BC=8C=E5=AF=83=EF=BC=8C=E6=89=93=E5=88=A1=E8=A7=92=E7=A8=8B...
    pause >nul
    start taskschd.msc
) else (
    echo ========================================
    echo   =E5=AE=9A=E6=97=B6=E4=BB=BB=E5=8A=A1=E5=9C=B0=E5=88=9B=E6=88=90=E5=A4=B1=E8=B4=A5=EF=BC=81
    echo ========================================
    echo.
    echo =E9=94=99=E8=AF=AF=E7=A0=81=E7=A0=81: %errorlevel%
    echo.
    echo =E8=AF=B7=E6=89=8B=E5=8A=A8=E5=88=A5=E5=88=9B=E6=89=93=EF=BC=8C=E5=8F=82=E8=80=83=E7=94=A8=E8=AE=BE=E9=A1=8B=E5=AE=9A=E5=9C=B0.md
    echo.
    pause
)
