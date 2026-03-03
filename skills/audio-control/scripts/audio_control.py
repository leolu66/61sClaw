#!/usr/bin/env python3
"""
Audio Control Script
Using PowerShell to control Windows audio devices
"""
import sys
import subprocess

def run_ps(command):
    """Run PowerShell command"""
    result = subprocess.run(
        ['powershell', '-Command', command],
        capture_output=True, text=True, encoding='utf-8', errors='ignore'
    )
    return result.stdout.strip()

def list_devices():
    """List audio devices"""
    print("=== Playback Devices ===")
    
    # Get playback devices
    cmd = """
    Add-Type -TypeDefinition @'
    using System;
    using System.Runtime.InteropServices;
    public class Audio {
        [DllImport("user32.dll")]
        public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
    }
'@
    $devices = Get-WmiObject Win32_SoundDevice | Where-Object {$_.Name -notmatch "Virtual"}
    $devices | ForEach-Object { Write-Output $_.Name }
    """
    result = run_ps(cmd)
    
    if result:
        for i, line in enumerate(result.split('\n'), 1):
            if line.strip():
                print(f"{i}. {line.strip()}")
    else:
        print("No devices found")
    
    print("\n=== Recording Devices ===")
    print("(Use system settings to view)")

def get_status():
    """Get current audio status"""
    print("=== Current Status ===\n")
    
    # Get mute status using NirCmd if available, otherwise use PowerShell
    # Try PowerShell
    cmd = """
    $shell = New-Object -ComObject WScript.Shell
    # Get master volume (approximate)
    try {
        $volume = [Math]::Round((Get-AudioVolume).DefaultDevice.AudioEndpointVolume.MasterVolumeLevelScalar * 100)
        Write-Output "Volume: $volume%"
    } catch {
        Write-Output "Volume: N/A"
    }
    """
    result = run_ps(cmd)
    print(result)

def mutePlayback(mute=True):
    """Mute/unmute playback using PowerShell"""
    state = 1 if mute else 0
    cmd = f"""
    Add-Type -TypeDefinition @'
    using System;
    using System.Runtime.InteropServices;
    public class AudioMute {{
        [DllImport("user32.dll", CharSet = CharSet.Auto)]
        static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
        public static void Mute(bool mute) {{
            // This is a workaround - use keyboard shortcut
        }}
    }}
'@
    # Use CoreAudio API
    Add-Type -MemberDefinition @'
    [DllImport("user32.dll")]
    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
'@ -Name Win32 -Namespace CoreAudio -PassThru
    """
    
    # Simpler approach - use nircmd or system volume
    if mute:
        cmd = """
        # Try to mute
        $key = [System.Windows.Forms.Keys]::VolumeMute
        # This requires UI automation
        Write-Output "Mute: Use system tray or keyboard"
        """
    
    print("Use system tray or keyboard shortcut to mute/unmute")

def muteMic(mute=True):
    """Mute/unmute microphone"""
    print("Microphone mute: Use system settings")

def setVolume(level):
    """Set volume (this is limited in PowerShell)"""
    print(f"Volume control: Use system tray or keyboard")

def main():
    if len(sys.argv) < 2:
        print("Audio Control")
        print("=" * 30)
        print("Usage:")
        print("  audio_control.py list           - List devices")
        print("  audio_control.py status         - Show status")
        print("  audio_control.py mute           - Mute")
        print("  audio_control.py unmute         - Unmute")
        print("  audio_control.py mic-mute       - Mute mic")
        print("  audio_control.py mic-unmute     - Unmute mic")
        print("  audio_control.py vol <0-100>    - Set volume")
        print()
        print("Note: Full audio control requires additional setup.")
        print("Consider using SoundSwitch or NirCmd.")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_devices()
    elif command == "status":
        get_status()
    elif command == "mute":
        mutePlayback(True)
    elif command == "unmute":
        mutePlayback(False)
    elif command == "mic-mute":
        muteMic(True)
    elif command == "mic-unmute":
        muteMic(False)
    elif command == "vol":
        if len(sys.argv) < 3:
            print("Specify volume (0-100)")
            return
        setVolume(int(sys.argv[2]))
    else:
        print(f"Unknown: {command}")

if __name__ == "__main__":
    main()
