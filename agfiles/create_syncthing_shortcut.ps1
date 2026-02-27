$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("$env:USERPROFILE\Desktop\Syncthing.lnk")
$s.TargetPath = "E:\download\syncthing\syncthing-windows-amd64-v1.27.7\syncthing.exe"
$s.WorkingDirectory = "E:\download\syncthing\syncthing-windows-amd64-v1.27.7"
$s.Description = "Syncthing 文件同步"
$s.Save()
