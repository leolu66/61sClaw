---
name: disk-cleaner
description: C 盘空间清理和分析工具。自动清理临时文件，分析占用空间大的应用，提供清理建议。当用户说"清理 C 盘"、"分析 C 盘空间"、"C 盘满了"、"释放空间"时触发。
version: 1.0
---

# C 盘清理助手

自动清理临时文件，分析占用空间大的应用，提供清理建议。

## 触发指令

- "清理 C 盘"
- "分析 C 盘空间"
- "C 盘满了"
- "释放空间"
- "C 盘优化"

## 工作流程

### 第一步：自动清理临时文件（安全，可自动执行）

```powershell
# 1. 清理用户临时文件
Remove-Item "C:\Users\$env:USERNAME\AppData\Local\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

# 2. 清理系统临时文件
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

# 3. 清理 npm 缓存
npm cache clean --force 2>$null

# 4. 清理回收站
Clear-RecycleBin -Force -ErrorAction SilentlyContinue

# 5. 清理 Windows 更新缓存
Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
Start-Service wuauserv -ErrorAction SilentlyContinue
```

**预计释放：** 2-10 GB

---

### 第二步：分析 C 盘空间占用

#### 1. 检查整体使用情况

```powershell
$disk = Get-Volume -DriveLetter C | Select-Object Size, SizeRemaining
$usedGB = [math]::Round(($disk.Size - $disk.SizeRemaining)/1GB, 2)
$totalGB = [math]::Round($disk.Size/1GB, 2)
$usagePercent = [math]::Round(($disk.Size - $disk.SizeRemaining)/$disk.Size*100, 1)

Write-Host "C 盘总容量：$totalGB GB"
Write-Host "已使用：$usedGB GB ($usagePercent%)"
Write-Host "剩余：$([math]::Round($disk.SizeRemaining/1GB, 2)) GB"
```

#### 2. 分析主要目录占用

```powershell
$dirs = @('Windows', 'Users', 'Program Files', 'Program Files (x86)', 'ProgramData')
foreach ($d in $dirs) {
    $path = "C:\$d"
    if (Test-Path $path) {
        $size = (Get-ChildItem -Path $path -Recurse -Force -ErrorAction SilentlyContinue | 
                 Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
        [PSCustomObject]@{
            Directory = $d
            SizeGB = [math]::Round($size/1GB, 2)
        }
    }
} | Sort-Object SizeGB -Descending
```

#### 3. 分析用户目录占用

```powershell
$user = $env:USERNAME
$paths = @{
    'AppData' = "C:\Users\$user\AppData"
    'Documents' = "C:\Users\$user\Documents"
    'Downloads' = "C:\Users\$user\Downloads"
    'Desktop' = "C:\Users\$user\Desktop"
    'Pictures' = "C:\Users\$user\Pictures"
    'Videos' = "C:\Users\$user\Videos"
}

foreach ($p in $paths.Keys) {
    $path = $paths[$p]
    if (Test-Path $path) {
        $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | 
                 Measure-Object -Property Length -Sum).Sum
        Write-Host "$p`: $([math]::Round($size/1GB, 2)) GB"
    }
}
```

#### 4. 分析常见应用缓存

```powershell
$apps = @{
    '微信' = "C:\Users\$user\Documents\WeChat Files"
    'QQ' = "C:\Users\$user\Documents\Tencent Files"
    '飞书' = "C:\Users\$user\AppData\Local\Feishu"
    '钉钉' = "C:\Users\$user\AppData\Local\DingTalk"
    'Chrome' = "C:\Users\$user\AppData\Local\Google\Chrome"
    'Edge' = "C:\Users\$user\AppData\Local\Microsoft\Edge"
    'Firefox' = "C:\Users\$user\AppData\Roaming\Mozilla\Firefox"
    'npm' = "C:\Users\$user\AppData\Local\npm-cache"
    'pip' = "C:\Users\$user\AppData\Local\pip\Cache"
    '印象笔记' = "C:\Users\$user\Documents\WizNote"
    'WPS 云盘' = "C:\Users\$user\Documents\WPS Cloud Files"
    'Visual Studio' = "C:\Users\$user\AppData\Local\Microsoft\VisualStudio"
    'Node.js' = "C:\Users\$user\AppData\Roaming\npm"
    'Python' = "C:\Users\$user\AppData\Local\pip"
    'Docker' = "C:\Users\$user\AppData\Local\Docker"
    'Git' = "C:\Users\$user\AppData\Local\Git"
}

foreach ($app in $apps.Keys) {
    $path = $apps[$app]
    if (Test-Path $path) {
        $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | 
                 Measure-Object -Property Length -Sum).Sum
        if ($size/1GB -gt 0.1) {
            Write-Host "$app`: $([math]::Round($size/1GB, 2)) GB"
        }
    }
}
```

---

### 第三步：生成清理建议

根据分析结果，生成清理建议：

#### 高优先级（可安全清理）

| 应用 | 缓存大小 | 清理方法 |
|------|---------|---------|
| 临时文件 | 自动清理 | 已完成 |
| npm 缓存 | >0.5GB | `npm cache clean --force` |
| Chrome 缓存 | >1GB | Chrome 设置 → 清除浏览数据 |
| Edge 缓存 | >1GB | Edge 设置 → 清除浏览数据 |

#### 中优先级（需要确认）

| 应用 | 缓存大小 | 清理方法 |
|------|---------|---------|
| 微信 | >5GB | 微信 → 设置 → 存储空间管理 → 清理 |
| QQ | >5GB | QQ → 设置 → 文件管理 → 更改文件保存位置 |
| 飞书 | >1GB | 飞书 → 设置 → 高级 → 清理缓存 |
| 钉钉 | >1GB | 钉钉 → 设置 → 存储管理 → 清理 |
| 印象笔记 | >1GB | 印象笔记 → 工具 → 选项 → 高级 → 更改缓存位置 |
| WPS 云盘 | >1GB | WPS → 设置 → 高级 → 文件缓存位置 |
| Chrome | >1GB | Chrome → 设置 → 隐私和安全 → 清除浏览数据 |
| Edge | >1GB | Edge → 设置 → 隐私 → 清除浏览数据 |
| Visual Studio | >2GB | VS → 工具 → 选项 → 环境 → 导入和导出 → 重置 |
| Docker | >1GB | Docker Desktop → Settings → Resources → Clean up |
| Git | >1GB | 运行 `git gc --aggressive` |

#### 低优先级（迁移建议）

| 目录 | 大小 | 建议 |
|------|------|------|
| Documents | >20GB | 迁移到 D 盘 |
| Downloads | >10GB | 定期清理 |
| Videos | >10GB | 迁移到 D 盘 |

---

## 清理命令参考

### 微信缓存清理

```powershell
# 清理微信临时缓存（安全）
Remove-Item "C:\Users\$user\Documents\WeChat Files\*\FileStorage\Cache\*" -Recurse -Force

# 清理微信临时文件
Remove-Item "C:\Users\$user\Documents\WeChat Files\*\FileStorage\Temp\*" -Recurse -Force
```

### 浏览器缓存清理

```powershell
# Chrome
Remove-Item "C:\Users\$user\AppData\Local\Google\Chrome\User Data\Default\Cache\*" -Recurse -Force

# Edge
Remove-Item "C:\Users\$user\AppData\Local\Microsoft\Edge\User Data\Default\Cache\*" -Recurse -Force
```

### 应用缓存清理

```powershell
# 飞书
Remove-Item "C:\Users\$user\AppData\Local\Feishu\*\Cache\*" -Recurse -Force

# 钉钉
Remove-Item "C:\Users\$user\AppData\Local\DingTalk\*\Cache\*" -Recurse -Force

# npm
npm cache clean --force
```

---

## 使用示例

### 示例 1：快速清理

```
用户：清理 C 盘
助手：
✅ 第一步：自动清理临时文件
   - 用户临时文件：清理完成
   - 系统临时文件：清理完成
   - npm 缓存：清理完成
   - 回收站：清理完成
   预计释放：5.2 GB

📊 第二步：C 盘空间分析
   - 总容量：200 GB
   - 已使用：176 GB (88%)
   - 剩余：24 GB

📁 主要占用目录：
   1. Users: 76.5 GB
   2. Windows: 61.5 GB
   3. Program Files: 21.2 GB

💡 清理建议：
   🔴 微信缓存：17.9 GB - 可在微信设置中清理
   🟡 Chrome 缓存：1.6 GB - 可在浏览器设置中清理
   🟢 飞书缓存：1.5 GB - 可在飞书设置中清理

需要我帮你执行哪个清理操作？
```

### 示例 2：详细分析

```
用户：分析 C 盘空间
助手：
📊 C 盘使用情况：
   总容量：200 GB
   已使用：167 GB (83.7%)
   剩余：33 GB

📁 目录占用分析：
   C:\Users: 48.4 GB
   ├─ AppData: 26.5 GB
   ├─ Documents: 22.9 GB
   └─ 其他：8.0 GB

📱 应用缓存：
   微信：17.9 GB
   Chrome: 1.6 GB
   飞书：1.5 GB
   钉钉：0.02 GB

💡 优化建议：
   1. 清理微信缓存（可释放~15GB）
   2. 迁移 Documents 到 D 盘（可释放~20GB）
   3. 清理浏览器缓存（可释放~2GB）
```

---

## 注意事项

1. **自动清理安全** - 第一步临时文件清理是安全的，可以自动执行
2. **应用缓存谨慎** - 微信/QQ 等应用缓存清理前建议备份重要文件
3. **迁移数据** - Documents/Videos 等目录迁移需要创建符号链接
4. **定期清理** - 建议每月执行一次完整清理

---

## 扩展功能

### 迁移 Documents 目录

```powershell
# 1. 复制到 D 盘
robocopy "C:\Users\$user\Documents" "D:\Documents" /MIR

# 2. 创建符号链接
Remove-Item "C:\Users\$user\Documents" -Recurse -Force
mklink /J "C:\Users\$user\Documents" "D:\Documents"
```

### 监控空间变化

```powershell
# 清理前后对比
$before = (Get-Volume -DriveLetter C).SizeRemaining
# ... 执行清理 ...
$after = (Get-Volume -DriveLetter C).SizeRemaining
$freed = [math]::Round(($after - $before)/1GB, 2)
Write-Host "释放空间：$freed GB"
```

---

## 版本历史

- v1.0 - 2026-02-26 - 初始版本
  - 自动清理临时文件
  - 分析主要目录占用
  - 分析常见应用缓存
  - 生成清理建议
