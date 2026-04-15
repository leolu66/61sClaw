@echo off
chcp 65001 > nul
echo ========================================
echo 多智能体协调器 - 启动工具
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set NODE_TYPE=%1

if "%NODE_TYPE%"=="" (
  echo 用法: start-scanner.bat [master^|worker]
  echo.
  echo 示例:
  echo   start-scanner.bat master    启动主节点扫描器
  echo   start-scanner.bat worker    启动子节点扫描器
  exit /b 1
)

if "%NODE_TYPE%"=="master" (
  echo [INFO] 正在启动主节点扫描器...
  node "%SCRIPT_DIR%..\..\skills\multi-agent-coordinator\coordinator-cli.js" start
  echo [OK] 主节点扫描器已启动
  echo.
  echo 查看状态: node coordinator-cli.js status
  echo 停止扫描: node coordinator-cli.js stop
) else if "%NODE_TYPE%"=="worker" (
  echo [INFO] 正在启动子节点扫描器...
  node "%SCRIPT_DIR%..\..\skills\multi-agent-coordinator\coordinator-cli.js" start
  echo [OK] 子节点扫描器已启动
  echo.
  echo 查看状态: node coordinator-cli.js status
  echo 停止扫描: node coordinator-cli.js stop
) else (
  echo [ERROR] 未知的节点类型: %NODE_TYPE%
  echo 用法: start-scanner.bat [master^|worker]
  exit /b 1
)

echo ========================================
