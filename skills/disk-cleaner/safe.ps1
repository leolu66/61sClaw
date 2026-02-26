# C Disk Cleaner v1.2 - SAFE Version
# Principle: Auto-clean temp files ONLY, analyze and report for important data

param(
    [ValidateSet('analyze', 'clean-temp', 'full')]
    [string]$Mode = 'analyze'
)

$ErrorActionPreference = 'SilentlyContinue'
$user = $env:USERNAME

Write-Host "========================================"
Write-Host "  C Disk Cleaner v1.2 (SAFE)"
Write-Host "========================================"
Write-Host ""

# Step 1: Clean temp files ONLY
if ($Mode -eq 'clean-temp' -or $Mode -eq 'full') {
    Write-Host "[Step 1] Cleaning temp files (SAFE)..." -ForegroundColor Green
    Write-Host ""
    
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
        
        Write-Host "  [OK] User temp: $deletedCount files deleted" -ForegroundColor Green
        if ($skippedCount -gt 0) {
            Write-Host "      Skipped $skippedCount locked files" -ForegroundColor Yellow
        }
    }
    
    $sysTemp = "C:\Windows\Temp"
    if (Test-Path $sysTemp) {
        $deletedCount = 0
        Get-ChildItem $sysTemp -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                Remove-Item $_.FullName -Force -ErrorAction Stop
                $deletedCount++
            } catch {}
        }
        Write-Host "  [OK] System temp: $deletedCount files deleted" -ForegroundColor Green
    }
    
    try { $null = npm cache clean --force 2>&1; Write-Host "  [OK] npm cache cleaned" -ForegroundColor Green } catch {}
    
    Write-Host ""
    Write-Host "  Temp cleanup complete!" -ForegroundColor Green
    Write-Host ""
}

# Step 2: Analyze (NEVER auto-delete)
if ($Mode -eq 'analyze' -or $Mode -eq 'clean-temp' -or $Mode -eq 'full') {
    Write-Host "[Step 2] Analyzing disk..." -ForegroundColor Cyan
    Write-Host ""
    
    $disk = Get-Volume -DriveLetter C
    $totalGB = [math]::Round($disk.Size/1GB, 2)
    $usedGB = [math]::Round(($disk.Size - $disk.SizeRemaining)/1GB, 2)
    $freeGB = [math]::Round($disk.SizeRemaining/1GB, 2)
    $pct = [math]::Round(($disk.Size - $disk.SizeRemaining)/$disk.Size*100, 1)
    
    Write-Host "  C Disk:"
    Write-Host "  Total: $totalGB GB"
    Write-Host "  Used: $usedGB GB ($pct)"
    Write-Host "  Free: $freeGB GB"
    Write-Host ""
    
    Write-Host "  Top Directories:"
    foreach ($d in @('Windows', 'Users', 'Program Files', 'Program Files (x86)', 'ProgramData')) {
        $p = "C:\$d"
        if (Test-Path $p) {
            $s = (Get-ChildItem $p -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($s -gt 0) { Write-Host "  - $d`: $([math]::Round($s/1GB, 2)) GB" }
        }
    }
    Write-Host ""
    
    Write-Host "  User Directories:"
    foreach ($d in @('AppData', 'Documents', 'Downloads', 'Desktop')) {
        $p = "C:\Users\$user\$d"
        if (Test-Path $p) {
            $s = (Get-ChildItem $p -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($s/1GB -gt 0.1) { Write-Host "  - $d`: $([math]::Round($s/1GB, 2)) GB" }
        }
    }
    Write-Host ""
    
    Write-Host "  App Caches (manual clean only):" -ForegroundColor Yellow
    $apps = @{
        'WeChat' = "C:\Users\$user\Documents\WeChat Files"
        'QQ' = "C:\Users\$user\Documents\Tencent Files"
        'Feishu' = "C:\Users\$user\AppData\Local\Feishu"
        'Chrome' = "C:\Users\$user\AppData\Local\Google\Chrome\User Data"
        'Edge' = "C:\Users\$user\AppData\Local\Microsoft\Edge\User Data"
        'Firefox' = "C:\Users\$user\AppData\Roaming\Mozilla\Firefox"
        'Evernote' = "C:\Users\$user\Documents\WizNote"
        'WPS' = "C:\Users\$user\Documents\WPS Cloud Files"
    }
    
    foreach ($app in $apps.Keys) {
        $path = $apps[$app]
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($size/1GB -gt 0.1) {
                $gb = [math]::Round($size/1GB, 2)
                $c = if ($gb -gt 5) { "Red" } elseif ($gb -gt 1) { "Yellow" } else { "Green" }
                Write-Host "  - $app`: $gb GB" -ForegroundColor $c
            }
        }
    }
    Write-Host ""
}

# Step 3: Recommendations
if ($Mode -eq 'analyze' -or $Mode -eq 'clean-temp' -or $Mode -eq 'full') {
    Write-Host "[Step 3] Recommendations:" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "  [SAFE] Auto-clean:" -ForegroundColor Green
    Write-Host "  - Temp files, npm cache"
    Write-Host "  Command: .\run.ps1 -Mode clean-temp"
    Write-Host ""
    
    Write-Host "  [MANUAL] Review and clean yourself:" -ForegroundColor Yellow
    Write-Host "  - WeChat: Settings -> Storage"
    Write-Host "  - QQ: Settings -> File Management"
    Write-Host "  - Browsers: Settings -> Privacy"
    Write-Host ""
    
    Write-Host "  [IMPORTANT] Documents folder:" -ForegroundColor Red
    $docsPath = "C:\Users\$user\Documents"
    if (Test-Path $docsPath) {
        Write-Host "  DO NOT auto-delete! Manual review only."
        Get-ChildItem $docsPath -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
            $s = (Get-ChildItem $_.FullName -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($s/1GB -gt 0.5) {
                Write-Host "  - $($_.Name): $([math]::Round($s/1GB, 2)) GB" -ForegroundColor $(if ($s/1GB -gt 5) { "Red" } else { "Yellow" })
            }
        }
    }
    Write-Host ""
    
    Write-Host "========================================"
    Write-Host "  Analysis Complete!" -ForegroundColor Green
    Write-Host "========================================"
    
    $disk = Get-Volume -DriveLetter C
    $freeGB = [math]::Round($disk.SizeRemaining/1GB, 2)
    $pct = [math]::Round(($disk.Size - $disk.SizeRemaining)/$disk.Size*100, 1)
    Write-Host "  Status: $freeGB GB free ($pct used)" -ForegroundColor $(if ($freeGB -lt 10) { "Red" } elseif ($freeGB -lt 20) { "Yellow" } else { "Green" })
    Write-Host ""
}
