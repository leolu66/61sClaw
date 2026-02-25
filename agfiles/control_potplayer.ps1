param(
    [string]$Action = "next"
)

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class PotPlayer {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    public const uint WM_KeyDown = 0x0100;
}
"@

$proc = Get-Process PotPlayerMini64 -ErrorAction SilentlyContinue
if ($proc -and $proc.MainWindowHandle) {
    $hwnd = $proc.MainWindowHandle
    [void][PotPlayer]::SetForegroundWindow($hwnd)
    Start-Sleep -Milliseconds 100
    
    switch ($Action) {
        "next"   { 
            [void][PotPlayer]::PostMessage($hwnd, [PotPlayer]::WM_KeyDown, [IntPtr]0x22, [IntPtr]0)
        }
        "prev"   { 
            [void][PotPlayer]::PostMessage($hwnd, [PotPlayer]::WM_KeyDown, [IntPtr]0x21, [IntPtr]0)
        }
        "pause"  { 
            [void][PotPlayer]::PostMessage($hwnd, [PotPlayer]::WM_KeyDown, [IntPtr]0x20, [IntPtr]0)
        }
        "stop"   { 
            [void][PotPlayer]::PostMessage($hwnd, [PotPlayer]::WM_KeyDown, [IntPtr]0x1B, [IntPtr]0)
        }
    }
    Write-Host "Sent $action to PotPlayer (hwnd: $hwnd)"
} else {
    Write-Host "PotPlayer not found"
}
