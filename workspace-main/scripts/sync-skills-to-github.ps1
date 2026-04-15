# 同步各Agent技能到GitHub仓库
# 将各workspace的技能合并到workspace-main/skills用于GitHub提交

param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# 定义Agent工作区
$agents = @(
    @{ Name = "main"; Path = "C:\Users\luzhe\.openclaw\workspace-main"; SkillsDir = "skills" },
    @{ Name = "entertainment"; Path = "C:\Users\luzhe\.openclaw\workspace-entertainment"; SkillsDir = "skills" }
)

$githubSkillsDir = "C:\Users\luzhe\.openclaw\workspace-main\skills"
$conflicts = @()
$synced = @()
$skipped = @()

Write-Host "=== Skills Sync to GitHub ===" -ForegroundColor Cyan
Write-Host ""

foreach ($agent in $agents) {
    $agentSkillsPath = Join-Path $agent.Path $agent.SkillsDir
    
    if (-not (Test-Path $agentSkillsPath)) {
        Write-Host "[$($agent.Name)] No skills directory found, skipping..." -ForegroundColor Gray
        continue
    }
    
    Write-Host "[$($agent.Name)] Scanning skills..." -ForegroundColor Yellow
    
    $skills = Get-ChildItem -Path $agentSkillsPath -Directory -ErrorAction SilentlyContinue
    
    foreach ($skill in $skills) {
        $skillName = $skill.Name
        $sourcePath = $skill.FullName
        $targetPath = Join-Path $githubSkillsDir $skillName
        
        # 检查是否已存在（来自其他Agent）
        if (Test-Path $targetPath) {
            # 检查是否来自同一Agent（已同步过）
            $existingAgent = "unknown"
            $sourceFile = Join-Path $targetPath ".skill-source"
            if (Test-Path $sourceFile) {
                $existingAgent = Get-Content $sourceFile -Raw
            }
            
            if ($existingAgent -eq $agent.Name) {
                Write-Host "  [SKIP] $skillName (already from $($agent.Name))" -ForegroundColor Gray
                $skipped += @{ Skill = $skillName; Agent = $agent.Name }
            } else {
                # 来自不同Agent，冲突！
                Write-Host "  [CONFLICT] $skillName exists from '$existingAgent', current from '$($agent.Name)'" -ForegroundColor Red
                $conflicts += @{ 
                    Skill = $skillName
                    ExistingAgent = $existingAgent
                    NewAgent = $agent.Name
                }
            }
        } else {
            # 新技能，复制
            if ($DryRun) {
                Write-Host "  [ADD] $skillName (would add from $($agent.Name))" -ForegroundColor Blue
            } else {
                Copy-Item -Recurse -Force $sourcePath $targetPath
                $agent.Name | Out-File (Join-Path $targetPath ".skill-source") -Encoding UTF8
                Write-Host "  [ADD] $skillName (from $($agent.Name))" -ForegroundColor Green
            }
            $synced += @{ Skill = $skillName; Agent = $agent.Name; Action = "add" }
        }
    }
}

Write-Host ""
Write-Host "=== Sync Summary ===" -ForegroundColor Cyan
Write-Host "Synced: $($synced.Count)" -ForegroundColor Green
Write-Host "Skipped: $($skipped.Count)" -ForegroundColor Gray
Write-Host "Conflicts: $($conflicts.Count)" -ForegroundColor $(if ($conflicts.Count -gt 0) { "Red" } else { "Green" })

# 报告冲突
if ($conflicts.Count -gt 0) {
    Write-Host ""
    Write-Host "!!! CONFLICTS DETECTED - Manual resolution required !!!" -ForegroundColor Red -BackgroundColor Black
    Write-Host ""
    foreach ($conflict in $conflicts) {
        Write-Host "Skill: $($conflict.Skill)" -ForegroundColor Yellow
        Write-Host "  Existing from: $($conflict.ExistingAgent)" -ForegroundColor Gray
        Write-Host "  New from:      $($conflict.NewAgent)" -ForegroundColor Gray
        Write-Host ""
    }
}

# 返回结果
@{
    Synced = $synced
    Skipped = $skipped
    Conflicts = $conflicts
    HasConflicts = $conflicts.Count -gt 0
}
