# 设置日志自动归档定时任务
# 每天凌晨 2 点自动迁移超过 7 天的工作日志

$taskName = "日志自动归档"
$taskDescription = "每天凌晨 2 点自动迁移超过 7 天的工作日志到归档目录"
$scriptPath = "C:\Users\luzhe\.openclaw\workspace-main\skills\log-migrator\scripts\migrate_logs.bat"

# 检查是否已存在同名任务
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "任务 '$taskName' 已存在，正在删除旧任务..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "旧任务已删除" -ForegroundColor Green
}

# 创建任务动作
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory "C:\Users\luzhe\.openclaw\workspace-main\skills\log-migrator\scripts"

# 创建任务触发器 - 每天晚上 11:20
$trigger = New-ScheduledTaskTrigger -Daily -At "23:20"

# 创建任务设置
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 创建任务对象
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Description $taskDescription

# 注册任务
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 定时任务创建成功!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "任务名称: $taskName"
Write-Host "执行时间: 每天 02:00"
Write-Host "执行脚本: $scriptPath"
Write-Host "保留天数: 7 天"
Write-Host "归档目录: D:\openclaw\logs\daily\archive"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示: 可以在'任务计划程序'中查看和管理此任务" -ForegroundColor Yellow
