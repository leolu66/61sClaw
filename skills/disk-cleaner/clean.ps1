# C 盘清理助手 v1.0
param(
    [ValidateSet('clean', 'analyze', 'full')]
    [string]$Mode = 'full'
)

$ErrorActionPreference = 'SilentlyContinue'
$user = $env:USERNAME
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================"
Write-Host "  C 盘清理助手 v1.0"
Write-Host "========================================"
Write-Host ""

# Step 1: Clean temp files
if ($Mode -eq 'clean' -or $Mode -eq 'full') {
    Write-Host "[1/3] 清理临时文件..."
    Write-Host ""
    
    # User temp
    $tempPath = "C:\Users\$user\AppData\Local\Temp"
    if (Test-Path $tempPath) {
        $count = (Get-ChildItem $tempPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
        try {
            Remove-Item "$tempPath\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] 用户临时文件 (约 $count 个文件)" -ForegroundColor Green
        } catch {
            Write-Host "  [SKIP] 用户临时文件" -ForegroundColor Yellow
        }
    }
    
    # System temp
    $sysTemp = "C:\Windows\Temp"
    if (Test-Path $sysTemp) {
        try {
            Remove-Item "$sysTemp\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] 系统临时文件" -ForegroundColor Green
        } catch {
            Write-Host "  [SKIP] 系统临时文件" -ForegroundColor Yellow
        }
    }
    
    # npm cache
    try {
        $null = npm cache clean --force 2>&1
        Write-Host "  [OK] npm 缓存" -ForegroundColor Green
    } catch {
        Write-Host "  [SKIP] npm 缓存" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "  临时文件清理完成" -ForegroundColor Green
    Write-Host ""
}

# Step 2: Analyze
if ($Mode -eq 'analyze' -or $Mode -eq 'full') {
    Write-Host "[2/3] 分析 C 盘空间..."
    Write-Host ""
    
    # Disk info
    $disk = Get-Volume -DriveLetter C
    $totalGB = [math]::Round($disk.Size/1GB, 2)
    $usedGB = [math]::Round(($disk.Size - $disk.SizeRemaining)/1GB, 2)
    $freeGB = [math]::Round($disk.SizeRemaining/1GB, 2)
    $pct = [math]::Round(($disk.Size - $disk.SizeRemaining)/$disk.Size*100, 1)
    
    Write-Host "  C 盘概况:"
    Write-Host "  总容量：$totalGB GB"
    Write-Host "  已使用：$usedGB GB ($pct)"
    Write-Host "  剩余：$freeGB GB"
    Write-Host ""
    
    # Main dirs
    Write-Host "  主要目录:"
    foreach ($d in @('Windows', 'Users', 'Program Files', 'Program Files (x86)', 'ProgramData')) {
        $p = "C:\$d"
        if (Test-Path $p) {
            $s = (Get-ChildItem $p -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($s -gt 0) { Write-Host "  - $d`: $([math]::Round($s/1GB, 2)) GB" }
        }
    }
    Write-Host ""
    
    # User dirs
    Write-Host "  用户目录:"
    foreach ($d in @('AppData', 'Documents', 'Downloads', 'Desktop')) {
        $p = "C:\Users\$user\$d"
        if (Test-Path $p) {
            $s = (Get-ChildItem $p -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($s/1GB -gt 0.1) { Write-Host "  - $d`: $([math]::Round($s/1GB, 2)) GB" }
        }
    }
    Write-Host ""
    
    # Apps
    Write-Host "  应用缓存:"
    $apps = @{
        '微信' = "C:\Users\$user\Documents\WeChat Files"
        'QQ' = "C:\Users\$user\Documents\Tencent Files"
        '飞书' = "C:\Users\$user\AppData\Local\Feishu"
        '钉钉' = "C:\Users\$user\AppData\Local\DingTalk"
        'Chrome' = "C:\Users\$user\AppData\Local\Google\Chrome\User Data"
        'Edge' = "C:\Users\$user\AppData\Local\Microsoft\Edge\User Data"
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

# Step 3: Tips
if ($Mode -eq 'full') {
    Write-Host "[3/3] 清理建议:"
    Write-Host ""
    Write-Host "  高优先级 (已自动清理):" -ForegroundColor Red
    Write-Host "  - 临时文件"
    Write-Host "  - npm 缓存"
    Write-Host ""
    Write-Host "  中优先级 (手动清理):" -ForegroundColor Yellow
    Write-Host "  - 微信：设置 - 存储空间管理"
    Write-Host "  - QQ: 设置 - 文件管理"
    Write-Host "  - 浏览器：设置 - 清除浏览数据"
    Write-Host ""
    Write-Host "========================================"
    Write-Host "  完成!" -ForegroundColor Green
    Write-Host "========================================"
    Write-Host ""
    $disk = Get-Volume -DriveLetter C
    $freeGB = [math]::Round($disk.SizeRemaining/1GB, 2)
    $pct = [math]::Round(($disk.Size - $disk.SizeRemaining)/$disk.Size*100, 1)
    $c = if ($freeGB -lt 10) { "Red" } elseif ($freeGB -lt 20) { "Yellow" } else { "Green" }
    Write-Host "  当前剩余：$freeGB GB ($pct)" -ForegroundColor $c
    Write-Host ""
}
