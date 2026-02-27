# C Disk Cleaner v1.2 - 安全版
# 原则：临时文件自动清理，重要数据只分析不删除

param(
    [ValidateSet('analyze', 'clean-temp', 'full')]
    [string]$Mode = 'analyze',
    
    [Parameter(Mandatory=$false)]
    [switch]$CleanTemp
)

$ErrorActionPreference = 'SilentlyContinue'
$user = $env:USERNAME

Write-Host "========================================"
Write-Host "  C Disk Cleaner v1.2 (安全版)"
Write-Host "========================================"
Write-Host ""

# ========================================
# Step 1: Clean temp files ONLY (safe to auto-clean)
# ========================================
if ($Mode -eq 'clean-temp' -or $Mode -eq 'full' -or $CleanTemp) {
    Write-Host "[Step 1] 清理临时文件 (安全)..." -ForegroundColor Green
    Write-Host ""
    
    # User temp - skip locked files
    $tempPath = "C:\Users\$user\AppData\Local\Temp"
    if (Test-Path $tempPath) {
        $deletedCount = 0
        $skippedCount = 0
        
        Get-ChildItem $tempPath -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                Remove-Item $_.FullName -Force -ErrorAction Stop
                $deletedCount++
            } catch {
                $skippedCount++
            }
        }
        
        # Try to delete empty directories
        Get-ChildItem $tempPath -Recurse -Directory -ErrorAction SilentlyContinue | 
            Sort-Object FullName -Descending | 
            Remove-Item -Force -ErrorAction SilentlyContinue
        
        Write-Host "  [OK] 用户临时文件：$deletedCount 个文件已删除" -ForegroundColor Green
        if ($skippedCount -gt 0) {
            Write-Host "      跳过 $skippedCount 个锁定文件 (重启后会自动删除)" -ForegroundColor Yellow
        }
    }
    
    # System temp
    $sysTemp = "C:\Windows\Temp"
    if (Test-Path $sysTemp) {
        $deletedCount = 0
        try {
            Get-ChildItem $sysTemp -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
                Remove-Item $_.FullName -Force -ErrorAction Stop
                $deletedCount++
            }
            Write-Host "  [OK] 系统临时文件：$deletedCount 个文件已删除" -ForegroundColor Green
        } catch {
            Write-Host "  [OK] 系统临时文件：部分已删除" -ForegroundColor Green
        }
    }
    
    # npm cache
    try {
        $null = npm cache clean --force 2>&1
        Write-Host "  [OK] npm 缓存已清理" -ForegroundColor Green
    } catch {
        Write-Host "  [SKIP] npm 缓存" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "  临时文件清理完成！" -ForegroundColor Green
    Write-Host ""
}

# ========================================
# Step 2: Analyze disk usage (NEVER auto-delete)
# ========================================
if ($Mode -eq 'analyze' -or $Mode -eq 'clean-temp' -or $Mode -eq 'full') {
    Write-Host "[Step 2] 分析 C 盘空间..." -ForegroundColor Cyan
    Write-Host ""
    
    $disk = Get-Volume -DriveLetter C
    $totalGB = [math]::Round($disk.Size/1GB, 2)
    $usedGB = [math]::Round(($disk.Size - $disk.SizeRemaining)/1GB, 2)
    $freeGB = [math]::Round($disk.SizeRemaining/1GB, 2)
    $pct = [math]::Round(($disk.Size - $disk.SizeRemaining)/$disk.Size*100, 1)
    
    Write-Host "  C 盘概况:" -ForegroundColor White
    Write-Host "  总容量：$totalGB GB"
    Write-Host "  已使用：$usedGB GB ($pct)"
    Write-Host "  剩余：$freeGB GB"
    Write-Host ""
    
    # Main directories
    Write-Host "  主要目录:" -ForegroundColor White
    foreach ($d in @('Windows', 'Users', 'Program Files', 'Program Files (x86)', 'ProgramData')) {
        $p = "C:\$d"
        if (Test-Path $p) {
            $s = (Get-ChildItem $p -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($s -gt 0) { Write-Host "  - $d`: $([math]::Round($s/1GB, 2)) GB" }
        }
    }
    Write-Host ""
    
    # User directories
    Write-Host "  用户目录:" -ForegroundColor White
    foreach ($d in @('AppData', 'Documents', 'Downloads', 'Desktop', 'Pictures', 'Videos')) {
        $p = "C:\Users\$user\$d"
        if (Test-Path $p) {
            $s = (Get-ChildItem $p -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($s/1GB -gt 0.1) { 
                $gb = [math]::Round($s/1GB, 2)
                $color = if ($gb -gt 20) { "Red" } elseif ($gb -gt 10) { "Yellow" } else { "Green" }
                Write-Host "  - $d`: $gb GB" -ForegroundColor $color
            }
        }
    }
    Write-Host ""
    
    # Application caches - ANALYSIS ONLY, NO AUTO-DELETE
    Write-Host "  应用缓存 (需要手动清理):" -ForegroundColor Yellow
    $apps = @{
        '微信' = "C:\Users\$user\Documents\WeChat Files"
        'QQ' = "C:\Users\$user\Documents\Tencent Files"
        '飞书' = "C:\Users\$user\AppData\Local\Feishu"
        '钉钉' = "C:\Users\$user\AppData\Local\DingTalk"
        'Chrome' = "C:\Users\$user\AppData\Local\Google\Chrome\User Data"
        'Edge' = "C:\Users\$user\AppData\Local\Microsoft\Edge\User Data"
        'Firefox' = "C:\Users\$user\AppData\Roaming\Mozilla\Firefox"
        '印象笔记' = "C:\Users\$user\Documents\WizNote"
        'WPS 云盘' = "C:\Users\$user\Documents\WPS Cloud Files"
        'npm' = "C:\Users\$user\AppData\Local\npm-cache"
    }
    
    $found = $false
    foreach ($app in $apps.Keys) {
        $path = $apps[$app]
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($size/1GB -gt 0.1) {
                $gb = [math]::Round($size/1GB, 2)
                $c = if ($gb -gt 5) { "Red" } elseif ($gb -gt 1) { "Yellow" } else { "Green" }
                Write-Host "  - $app`: $gb GB" -ForegroundColor $c
                $found = $true
            }
        }
    }
    if (-not $found) { Write-Host "  - 无大型缓存" -ForegroundColor Green }
    Write-Host ""
}

# ========================================
# Step 3: Recommendations (SAFE recommendations only)
# ========================================
if ($Mode -eq 'analyze' -or $Mode -eq 'clean-temp' -or $Mode -eq 'full') {
    Write-Host "[Step 3] 清理建议:" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "  [安全] 可自动清理:" -ForegroundColor Green
    Write-Host "  - 临时文件 (AppData\Local\Temp)"
    Write-Host "  - 系统临时 (Windows\Temp)"
    Write-Host "  - npm 缓存"
    Write-Host ""
    Write-Host "  运行：.\run.ps1 -Mode clean-temp"
    Write-Host ""
    
    Write-Host "  [注意] 需要手动清理 (已运行分析，不自动删除):" -ForegroundColor Yellow
    Write-Host "  - 微信：设置 -> 存储空间管理 -> 清理"
    Write-Host "  - QQ: 设置 -> 文件管理 -> 更改文件保存位置"
    Write-Host "  - 浏览器：设置 -> 隐私和安全 -> 清除浏览数据"
    Write-Host "  - 印象笔记：工具 -> 选项 -> 高级 -> 更改缓存位置"
    Write-Host "  - WPS: 设置 -> 高级 -> 文件缓存位置"
    Write-Host ""
    
    Write-Host "  [重要] Documents 目录文件:" -ForegroundColor Red
    $docsPath = "C:\Users\$user\Documents"
    if (Test-Path $docsPath) {
        Write-Host "  此目录包含重要文档，不建议自动清理！" -ForegroundColor Red
        Write-Host "  建议：" -ForegroundColor Yellow
        Write-Host "  1. 手动检查大文件" -ForegroundColor Gray
        Write-Host "  2. 迁移到 D 盘（创建符号链接）" -ForegroundColor Gray
        Write-Host "  3. 使用云存储同步后删除本地" -ForegroundColor Gray
        
        # Show subdirectories > 0.5GB
        Write-Host ""
        Write-Host "  子目录占用:" -ForegroundColor White
        Get-ChildItem $docsPath -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
            $s = (Get-ChildItem $_.FullName -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($s/1GB -gt 0.5) {
                Write-Host "  - $($_.Name): $([math]::Round($s/1GB, 2)) GB" -ForegroundColor $(if ($s/1GB -gt 5) { "Red" } else { "Yellow" })
            }
        }
    }
    Write-Host ""
    
    Write-Host "========================================"
    Write-Host "  分析完成！" -ForegroundColor Green
    Write-Host "========================================"
    Write-Host ""
    Write-Host "  下一步操作:" -ForegroundColor Cyan
    Write-Host "  1. 清理临时文件：.\run.ps1 -Mode clean-temp"
    Write-Host "  2. 重新分析：.\run.ps1 -Mode analyze"
    Write-Host ""
    
    $disk = Get-Volume -DriveLetter C
    $freeGB = [math]::Round($disk.SizeRemaining/1GB, 2)
    $pct = [math]::Round(($disk.Size - $disk.SizeRemaining)/$disk.Size*100, 1)
    $c = if ($freeGB -lt 10) { "Red" } elseif ($freeGB -lt 20) { "Yellow" } else { "Green" }
    Write-Host "  当前状态：$freeGB GB 可用 ($pct 已用)" -ForegroundColor $c
    Write-Host ""
}
