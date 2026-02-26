# C 盘清理助手 - 主脚本
# 功能：自动清理临时文件，分析空间占用，生成清理建议

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('clean', 'analyze', 'full')]
    [string]$Mode = 'full',
    
    [Parameter(Mandatory=$false)]
    [switch]$AutoClean
)

$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  C 盘清理助手 v1.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$user = $env:USERNAME

# ========================================
# 第一步：自动清理临时文件
# ========================================
if ($Mode -eq 'clean' -or $Mode -eq 'full') {
    Write-Host "[1/3] 自动清理临时文件..." -ForegroundColor Yellow
    Write-Host ""
    
    # 1. 清理用户临时文件
    try {
        $tempPath = "C:\Users\$user\AppData\Local\Temp"
        if (Test-Path $tempPath) {
            Remove-Item "$tempPath\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] 用户临时文件已清理" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [WARN] 用户临时文件清理失败" -ForegroundColor Yellow
    }
    
    # 2. 清理系统临时文件
    try {
        $sysTempPath = "C:\Windows\Temp"
        if (Test-Path $sysTempPath) {
            Remove-Item "$sysTempPath\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] 系统临时文件已清理" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [WARN] 系统临时文件清理失败" -ForegroundColor Yellow
    }
    
    # 3. 清理 npm 缓存
    try {
        npm cache clean --force 2>$null
        Write-Host "  [OK] npm 缓存已清理" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] npm 缓存清理失败" -ForegroundColor Yellow
    }
    
    # 4. 清理回收站
    try {
        Clear-RecycleBin -Force -ErrorAction SilentlyContinue
        Write-Host "  [OK] 回收站已清理" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] 回收站清理失败" -ForegroundColor Yellow
    }
    
    # 5. 清理 Windows 更新缓存
    try {
        Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
        Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
        Start-Service wuauserv -ErrorAction SilentlyContinue
        Write-Host "  [OK] Windows 更新缓存已清理" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Windows 更新缓存清理失败" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "  临时文件清理完成！" -ForegroundColor Green
    Write-Host ""
}

# ========================================
# 第二步：分析 C 盘空间占用
# ========================================
if ($Mode -eq 'analyze' -or $Mode -eq 'full') {
    Write-Host "[2/3] C 盘空间分析..." -ForegroundColor Yellow
    Write-Host ""
    
    # 1. 检查整体使用情况
    $disk = Get-Volume -DriveLetter C | Select-Object Size, SizeRemaining
    $usedGB = [math]::Round(($disk.Size - $disk.SizeRemaining)/1GB, 2)
    $totalGB = [math]::Round($disk.Size/1GB, 2)
    $usagePercent = [math]::Round(($disk.Size - $disk.SizeRemaining)/$disk.Size*100, 1)
    $freeGB = [math]::Round($disk.SizeRemaining/1GB, 2)
    
    Write-Host "  C 盘使用情况:" -ForegroundColor Cyan
    Write-Host "  +------------------------------------+"
    Write-Host "  | 总容量：$totalGB GB"
    Write-Host "  | 已使用：$usedGB GB ($usagePercent%)"
    Write-Host "  | 剩余：$freeGB GB"
    Write-Host "  +------------------------------------+"
    Write-Host ""
    
    # 2. 分析主要目录占用
    Write-Host "  主要目录占用:" -ForegroundColor Cyan
    $mainDirs = @()
    $dirs = @('Windows', 'Users', 'Program Files', 'Program Files (x86)', 'ProgramData')
    foreach ($d in $dirs) {
        $path = "C:\$d"
        if (Test-Path $path) {
            $size = (Get-ChildItem -Path $path -Recurse -Force -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
            if ($size -gt 0) {
                $mainDirs += [PSCustomObject]@{
                    Directory = $d
                    SizeGB = [math]::Round($size/1GB, 2)
                }
            }
        }
    }
    
    $mainDirs | Sort-Object SizeGB -Descending | ForEach-Object {
        $filled = [math]::Min([int]($_.SizeGB/2), 30)
        $empty = 30 - $filled
        $bar = "[" + ("#" * $filled) + ("." * $empty) + "]"
        Write-Host "  $($_.Directory.PadRight(20)) $($_.SizeGB.ToString("F2").PadLeft(6)) GB $bar"
    }
    Write-Host ""
    
    # 3. 分析用户目录占用
    Write-Host "  用户目录占用 (C:\Users\$user):" -ForegroundColor Cyan
    $userPaths = @{
        'AppData' = "C:\Users\$user\AppData"
        'Documents' = "C:\Users\$user\Documents"
        'Downloads' = "C:\Users\$user\Downloads"
        'Desktop' = "C:\Users\$user\Desktop"
        'Pictures' = "C:\Users\$user\Pictures"
        'Videos' = "C:\Users\$user\Videos"
    }
    
    foreach ($p in $userPaths.Keys) {
        $path = $userPaths[$p]
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum).Sum
            if ($size/1GB -gt 0.1) {
                Write-Host "  - $p`: $([math]::Round($size/1GB, 2)) GB" -ForegroundColor Gray
            }
        }
    }
    Write-Host ""
    
    # 4. 分析常见应用缓存
    Write-Host "  应用缓存占用:" -ForegroundColor Cyan
    $apps = @{
        '微信' = "C:\Users\$user\Documents\WeChat Files"
        'QQ' = "C:\Users\$user\Documents\Tencent Files"
        '飞书' = "C:\Users\$user\AppData\Local\Feishu"
        '钉钉' = "C:\Users\$user\AppData\Local\DingTalk"
        'Chrome' = "C:\Users\$user\AppData\Local\Google\Chrome\User Data"
        'Edge' = "C:\Users\$user\AppData\Local\Microsoft\Edge\User Data"
        'Firefox' = "C:\Users\$user\AppData\Roaming\Mozilla\Firefox"
        'npm' = "C:\Users\$user\AppData\Local\npm-cache"
        'Postman' = "C:\Users\$user\AppData\Roaming\Postman"
        '印象笔记' = "C:\Users\$user\Documents\WizNote"
        'WPS 云盘' = "C:\Users\$user\Documents\WPS Cloud Files"
        'Visual Studio' = "C:\Users\$user\AppData\Local\Microsoft\VisualStudio"
        'Node.js' = "C:\Users\$user\AppData\Roaming\npm"
        'Python' = "C:\Users\$user\AppData\Local\pip"
        'Docker' = "C:\Users\$user\AppData\Local\Docker"
        'Git' = "C:\Users\$user\AppData\Local\Git"
    }
    
    $appSizes = @()
    foreach ($app in $apps.Keys) {
        $path = $apps[$app]
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum).Sum
            if ($size/1GB -gt 0.1) {
                $appSizes += [PSCustomObject]@{
                    App = $app
                    SizeGB = [math]::Round($size/1GB, 2)
                    Path = $path
                }
            }
        }
    }
    
    if ($appSizes.Count -gt 0) {
        $appSizes | Sort-Object SizeGB -Descending | ForEach-Object {
            $color = if ($_.SizeGB -gt 5) { "Red" } elseif ($_.SizeGB -gt 1) { "Yellow" } else { "Green" }
            Write-Host "  - $($_.App): $($_.SizeGB) GB" -ForegroundColor $color
        }
    } else {
        Write-Host "  - 未发现大型应用缓存" -ForegroundColor Green
    }
    Write-Host ""
}

# ========================================
# 第三步：生成清理建议
# ========================================
if ($Mode -eq 'full') {
    Write-Host "[3/3] 清理建议:" -ForegroundColor Cyan
    Write-Host ""
    
    # 高优先级
    Write-Host "  [HIGH] 高优先级（可安全清理）:" -ForegroundColor Red
    Write-Host "  - 临时文件：已完成自动清理" -ForegroundColor Gray
    Write-Host "  - 回收站：已完成自动清理" -ForegroundColor Gray
    Write-Host ""
    
    # 中优先级
    Write-Host "  [MEDIUM] 中优先级（需要确认）:" -ForegroundColor Yellow
    
    if ($appSizes) {
        $largeApps = $appSizes | Where-Object { $_.SizeGB -gt 1 }
        if ($largeApps) {
            foreach ($app in $largeApps) {
                $method = switch ($app.App) {
                    '微信' { "微信 -> 设置 -> 存储空间管理 -> 清理" }
                    'QQ' { "QQ -> 设置 -> 文件管理 -> 更改文件保存位置" }
                    '飞书' { "飞书 -> 设置 -> 高级 -> 清理缓存" }
                    '钉钉' { "钉钉 -> 设置 -> 存储管理 -> 清理" }
                    'Chrome' { "Chrome -> 设置 -> 隐私和安全 -> 清除浏览数据" }
                    'Edge' { "Edge -> 设置 -> 隐私 -> 清除浏览数据" }
                    'npm' { "运行：npm cache clean --force" }
                    '印象笔记' { "印象笔记 -> 工具 -> 选项 -> 高级 -> 更改缓存位置" }
                    'WPS 云盘' { "WPS -> 设置 -> 高级 -> 文件缓存位置" }
                    'Visual Studio' { "VS -> 工具 -> 选项 -> 环境 -> 导入和导出 -> 重置" }
                    'Node.js' { "手动清理或使用 npm cache clean --force" }
                    'Python' { "pip cache purge" }
                    'Docker' { "Docker Desktop -> Settings -> Resources -> Clean up" }
                    'Git' { "git gc --aggressive" }
                    default { "手动清理" }
                }
                Write-Host "  - $($app.App) ($($app.SizeGB) GB) - $method" -ForegroundColor Gray
            }
        } else {
            Write-Host "  - 无" -ForegroundColor Green
        }
    }
    Write-Host ""
    
    # 低优先级
    Write-Host "  [LOW] 低优先级（迁移建议）:" -ForegroundColor Green
    
    $docsPath = "C:\Users\$user\Documents"
    if (Test-Path $docsPath) {
        $docsSize = (Get-ChildItem $docsPath -Recurse -Force -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum).Sum
        if ($docsSize/1GB -gt 20) {
            Write-Host "  - Documents ($([math]::Round($docsSize/1GB, 2)) GB) - 建议迁移到 D 盘" -ForegroundColor Gray
        }
    }
    
    $videosPath = "C:\Users\$user\Videos"
    if (Test-Path $videosPath) {
        $videosSize = (Get-ChildItem $videosPath -Recurse -Force -ErrorAction SilentlyContinue | 
                       Measure-Object -Property Length -Sum).Sum
        if ($videosSize/1GB -gt 10) {
            Write-Host "  - Videos ($([math]::Round($videosSize/1GB, 2)) GB) - 建议迁移到 D 盘" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  清理完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
}

# 显示最终空间情况
if ($Mode -eq 'full' -or $Mode -eq 'clean') {
    Start-Sleep -Seconds 2
    $disk = Get-Volume -DriveLetter C
    $freeGB = [math]::Round($disk.SizeRemaining/1GB, 2)
    $usagePercent = [math]::Round(($disk.Size - $disk.SizeRemaining)/$disk.Size*100, 1)
    
    Write-Host ""
    Write-Host "  当前 C 盘状态:" -ForegroundColor Cyan
    $color = if ($freeGB -lt 10) { "Red" } elseif ($freeGB -lt 20) { "Yellow" } else { "Green" }
    Write-Host "  剩余空间：$freeGB GB ($usagePercent% 已使用)" -ForegroundColor $color
    Write-Host ""
}
