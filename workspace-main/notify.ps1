param([string]$Title = 'OpenClaw', [string]$Message = 'Need your attention')

Add-Type -AssemblyName System.Windows.Forms
$balloon = New-Object System.Windows.Forms.NotifyIcon
$balloon.Icon = [System.Drawing.SystemIcons]::Information
$balloon.BalloonTipTitle = $Title
$balloon.BalloonTipText = $Message
$balloon.BalloonTipIcon = 'Info'
$balloon.Visible = $true
$balloon.ShowBalloonTip(8000)
Start-Sleep -Seconds 9
$balloon.Dispose()
