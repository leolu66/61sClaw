# C Disk Cleaner - Simple Version
param(
    [ValidateSet('clean', 'analyze', 'full')]
    [string]$Mode = 'full'
)

$ErrorActionPreference = 'SilentlyContinue'
$user = $env:USERNAME

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  C Disk Cleaner v1.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean temp files
if ($Mode -eq 'clean' -or $Mode -eq 'full') {
    Write-Host "[Step 1] Cleaning temporary files..." -ForegroundColor Yellow
    
    $tempPaths = @(
        "C:\Users\$user\AppData\Local\Temp",
        "C:\Windows\Temp",
        "C:\Windows\SoftwareDistribution\Download"
    )
    
    foreach ($path in $tempPaths) {
        if (Test-Path $path) {
            try {
                Remove-Item "$path\*" -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "  [OK] Cleaned: $path" -ForegroundColor Green
            } catch {
                Write-Host "  [SKIP] $path" -ForegroundColor Gray
            }
        }
    }
    
    # Clean npm cache
    try { npm cache clean --force 2>$null; Write-Host "  [OK] npm cache cleaned" -ForegroundColor Green } catch {}
    
    # Clean Recycle Bin
    try { Clear-RecycleBin -Force -ErrorAction SilentlyContinue; Write-Host "  [OK] Recycle Bin cleaned" -ForegroundColor Green } catch {}
    
    Write-Host ""
}

# Step 2: Analyze disk usage
if ($Mode -eq 'analyze' -or $Mode -eq 'full') {
    Write-Host "[Step 2] Analyzing disk usage..." -ForegroundColor Yellow
    Write-Host ""
    
    # Disk overview
    $disk = Get-Volume -DriveLetter C
    $totalGB = [math]::Round($disk.Size/1GB, 2)
    $usedGB = [math]::Round(($disk.Size - $disk.SizeRemaining)/1GB, 2)
    $freeGB = [math]::Round($disk.SizeRemaining/1GB, 2)
    $percent = [math]::Round(($disk.Size - $disk.SizeRemaining)/$disk.Size*100, 1)
    
    Write-Host "  Disk Overview:" -ForegroundColor Cyan
    Write-Host "  Total: $totalGB GB"
    Write-Host "  Used: $usedGB GB ($percent%)"
    Write-Host "  Free: $freeGB GB"
    Write-Host ""
    
    # Main directories
    Write-Host "  Top Directories:" -ForegroundColor Cyan
    foreach ($dir in @('Windows', 'Users', 'Program Files', 'Program Files (x86)', 'ProgramData')) {
        $path = "C:\$dir"
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($size -gt 0) {
                $gb = [math]::Round($size/1GB, 2)
                Write-Host "  - $dir`: $gb GB"
            }
        }
    }
    Write-Host ""
    
    # User directories
    Write-Host "  User Directories ($user):" -ForegroundColor Cyan
    foreach ($dir in @('AppData', 'Documents', 'Downloads', 'Desktop', 'Pictures', 'Videos')) {
        $path = "C:\Users\$user\$dir"
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($size/1GB -gt 0.1) {
                Write-Host "  - $dir`: $([math]::Round($size/1GB, 2)) GB"
            }
        }
    }
    Write-Host ""
    
    # Application caches
    Write-Host "  Application Caches:" -ForegroundColor Cyan
    $apps = @{
        'WeChat' = "C:\Users\$user\Documents\WeChat Files"
        'QQ' = "C:\Users\$user\Documents\Tencent Files"
        'Feishu' = "C:\Users\$user\AppData\Local\Feishu"
        'DingTalk' = "C:\Users\$user\AppData\Local\DingTalk"
        'Chrome' = "C:\Users\$user\AppData\Local\Google\Chrome\User Data"
        'Edge' = "C:\Users\$user\AppData\Local\Microsoft\Edge\User Data"
        'npm' = "C:\Users\$user\AppData\Local\npm-cache"
        'Evernote' = "C:\Users\$user\Documents\WizNote"
        'WPS Cloud' = "C:\Users\$user\Documents\WPS Cloud Files"
    }
    
    $found = $false
    foreach ($app in $apps.Keys) {
        $path = $apps[$app]
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($size/1GB -gt 0.1) {
                $gb = [math]::Round($size/1GB, 2)
                $color = if ($gb -gt 5) { "Red" } elseif ($gb -gt 1) { "Yellow" } else { "Green" }
                Write-Host "  - $app`: $gb GB" -ForegroundColor $color
                $found = $true
            }
        }
    }
    if (-not $found) { Write-Host "  - No large caches found" -ForegroundColor Green }
    Write-Host ""
}

# Step 3: Recommendations
if ($Mode -eq 'full') {
    Write-Host "[Step 3] Recommendations:" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "  [HIGH] Safe to clean:" -ForegroundColor Red
    Write-Host "  - Temp files: Done"
    Write-Host "  - Recycle Bin: Done"
    Write-Host ""
    
    Write-Host "  [MEDIUM] Review and clean:" -ForegroundColor Yellow
    Write-Host "  - WeChat: Settings -> Storage Management"
    Write-Host "  - QQ: Settings -> File Management"
    Write-Host "  - Browser: Settings -> Privacy -> Clear browsing data"
    Write-Host ""
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Current Status: $freeGB GB free ($percent% used)" -ForegroundColor $(if ($freeGB -lt 10) { "Red" } elseif ($freeGB -lt 20) { "Yellow" } else { "Green" })
    Write-Host ""
}
