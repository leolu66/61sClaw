# 设置AI新闻定时任务
# 每天12:30运行

$taskName = "AI新闻日报获取"
$taskDescription = "每天12:30自动获取AI新闻并生成日报"
$scriptPath = Join-Path $PSScriptRoot "run_ai_news.bat"

# 检查是否已存在同名任务
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "任务 '$taskName' 已存在，正在删除旧任务..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "旧任务已删除" -ForegroundColor Green
}

# 创建任务动作
$action = New-ScheduledTaskAction -Execute $scriptPath

# 创建任务触发器 - 每天12:30
$trigger = New-ScheduledTaskTrigger -Daily -At "12:30"

# 创建任务设置
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 创建任务对象
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Description $taskDescription

# 注册任务
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "定时任务创建成功!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "任务名称: $taskName"
Write-Host "执行时间: 每天 12:30"
Write-Host "执行脚本: $scriptPath"
Write-Host "输出目录: D:\anthropic\AI新闻\"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n提示: 可以在'任务计划程序'中查看和管理此任务" -ForegroundColor Yellow
