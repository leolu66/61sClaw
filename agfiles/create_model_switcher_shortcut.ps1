$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("$env:USERPROFILE\Desktop\Model Switcher.lnk")
$s.TargetPath = "$env:USERPROFILE\.openclaw\workspace-main\Model Switcher.bat"
$s.WorkingDirectory = "$env:USERPROFILE\.openclaw\workspace-main"
$s.Description = "Model Switcher"
$s.Save()
