---
name: vpn-controller
description: Control VPN application (Clash for Windows) - start VPN, stop VPN, check VPN status, disable/enable Windows proxy settings. Use when user asks to start VPN, stop VPN, turn on VPN, turn off VPN, launch Clash, quit Clash, check if VPN is running, enable proxy, or disable proxy. The VPN executable is located at "D:\Users\luzhe\AppData\Local\Programs\Clash for Windows\Clash for Windows.exe". When stopping VPN, also disable Windows proxy settings.
---

# VPN Controller

Control the Clash for Windows VPN application and manage Windows proxy settings.

## VPN Path

The VPN executable is located at:
`D:\Users\luzhe\AppData\Local\Programs\Clash for Windows\Clash for Windows.exe`

## Scripts

所有VPN控制功能通过 `vpn_control.py` 脚本实现：

```powershell
# 启动 VPN
python "C:\Users\luzhe\.openclaw\workspace-main\skills\vpn-controller\scripts\vpn_control.py" start

# 停止 VPN
python "C:\Users\luzhe\.openclaw\workspace-main\skills\vpn-controller\scripts\vpn_control.py" stop

# 检查状态
python "C:\Users\luzhe\.openclaw\workspace-main\skills\vpn-controller\scripts\vpn_control.py" status
```

### Start VPN

Launch the Clash for Windows application:

```python
import subprocess
subprocess.Popen([
    r"D:\Users\luzhe\AppData\Local\Programs\Clash for Windows\Clash for Windows.exe"
], shell=True)
```

### Stop VPN

Quit the Clash for Windows application AND disable Windows proxy settings:

```python
import subprocess

# Stop the VPN application
subprocess.run(["taskkill", "/F", "/IM", "Clash for Windows.exe"], capture_output=True)

# Disable Windows proxy
disable_proxy_command = """
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -Name 'ProxyEnable' -Value 0;
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -Name 'ProxyServer' -Value ''
"""
subprocess.run(["powershell", "-Command", disable_proxy_command], capture_output=True)

# Refresh Internet settings
refresh_command = """
$signature = '[DllImport("wininet.dll", SetLastError=true)] public static extern bool InternetSetOption(IntPtr hInternet, int dwOption, IntPtr lpBuffer, int dwBufferLength);';
$type = Add-Type -MemberDefinition $signature -Name wininet -Namespace pinvoke -PassThru;
$type::InternetSetOption(0, 39, 0, 0);
$type::InternetSetOption(0, 37, 0, 0)
"""
subprocess.run(["powershell", "-Command", refresh_command], capture_output=True)
```

### Check VPN Status

Check if Clash for Windows is running:

```python
import subprocess
result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Clash for Windows.exe"],
                       capture_output=True, text=True)
is_running = "Clash for Windows.exe" in result.stdout
```

### Disable Proxy Only

Disable Windows proxy settings without stopping VPN:

```python
import subprocess
subprocess.run([
    "powershell", "-Command",
    "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name 'ProxyEnable' -Value 0"
], capture_output=True)
```

### Enable Proxy Only

Enable Windows proxy settings:

```python
import subprocess
# Set proxy server (default Clash port is 7890)
subprocess.run([
    "powershell", "-Command",
    "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name 'ProxyServer' -Value '127.0.0.1:7890'"
], capture_output=True)

# Enable proxy
subprocess.run([
    "powershell", "-Command",
    "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name 'ProxyEnable' -Value 1"
], capture_output=True)
```

## Important Notes

- **When stopping VPN, ALWAYS disable Windows proxy settings** to restore normal internet access
- Default Clash proxy address: `127.0.0.1:7890`

## Usage Examples

- "启动 VPN" -> Start the VPN
- "停止 VPN" -> Stop the VPN and disable proxy
- "关闭 VPN" -> Stop the VPN and disable proxy
- "打开 Clash" -> Start the VPN
- "退出 Clash" -> Stop the VPN and disable proxy
- "VPN 状态" -> Check if VPN is running
- "取消代理" -> Disable Windows proxy settings
- "关闭代理" -> Disable Windows proxy settings
