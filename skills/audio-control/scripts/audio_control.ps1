# Audio Device Control using PowerShell
# Run with: powershell -ExecutionPolicy Bypass -File audio_control.ps1

param(
    [string]$Action = "status",
    [int]$Index = 0
)

# Import module
Import-Module AudioDeviceCmdlets -ErrorAction SilentlyContinue

function Get-AudioStatus {
    $device = Get-AudioDevice -Playback | Where-Object { $_.Default -eq $true } | Select-Object -First 1
    $vol = [Math]::Round($device.Device.AudioEndpointVolume.MasterVolumeLevelScalar * 100)
    $muted = $device.Device.AudioEndpointVolume.Mute
    
    Write-Host "=== Audio Status ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Playback:" $device.Name
    Write-Host "Volume: $vol%" -ForegroundColor $(if($vol -gt 50){'Green'}else{'Yellow'})
    Write-Host "Muted:" $muted -ForegroundColor $(if($muted){'Red'}else{'Green'})
    
    $mic = Get-AudioDevice -Recording | Where-Object { $_.Default -eq $true } | Select-Object -First 1
    $micMuted = $mic.Device.AudioEndpointVolume.Mute
    Write-Host ""
    Write-Host "Microphone:" $mic.Name
    Write-Host "Muted:" $micMuted -ForegroundColor $(if($micMuted){'Red'}else{'Green'})
}

function Set-PlaybackMute {
    param([bool]$Mute)
    if ($Mute) {
        Set-AudioDevice -PlaybackMute $true
    } else {
        Set-AudioDevice -PlaybackMute $false
    }
    Write-Host "Playback $(if($Mute){'muted'}else{'unmuted'})" -ForegroundColor Green
}

function Set-MicMute {
    param([bool]$Mute)
    if ($Mute) {
        Set-AudioDevice -RecordingMute $true
    } else {
        Set-AudioDevice -RecordingMute $false
    }
    Write-Host "Microphone $(if($Mute){'muted'}else{'unmuted'})" -ForegroundColor Green
}

function Switch-PlaybackDevice {
    param([int]$Index)
    $devices = Get-AudioDevice -Playback
    if ($Index -lt 1 -or $Index -gt $devices.Count) {
        Write-Host "Invalid device index. Use 'list' to see available devices." -ForegroundColor Red
        return
    }
    Set-AudioDevice -Index $Index
    $targetDevice = $devices[$Index - 1]
    Write-Host "Switched to: $($targetDevice.Name)" -ForegroundColor Green
}

function Switch-RecordingDevice {
    param([int]$Index)
    $devices = Get-AudioDevice -Recording
    if ($Index -lt 1 -or $Index -gt $devices.Count) {
        Write-Host "Invalid device index. Use 'list' to see available devices." -ForegroundColor Red
        return
    }
    # Recording devices are indexed after playback devices in the full list
    # We need to adjust the index
    Set-AudioDevice -Index $Index
    $targetDevice = $devices[$Index - 1]
    Write-Host "Switched to: $($targetDevice.Name)" -ForegroundColor Green
}

function List-Devices {
    Write-Host "=== Audio Devices ===" -ForegroundColor Cyan
    Write-Host ""
    
    $playback = Get-AudioDevice -Playback
    Write-Host "Playback Devices:" -ForegroundColor Yellow
    $i = 1
    foreach($dev in $playback) {
        $default = if($dev.Default){" [Default]"}else{""}
        Write-Host "  $i. $($dev.Name)$default"
        $i++
    }
    
    Write-Host ""
    $recording = Get-AudioDevice -Recording
    Write-Host "Recording Devices:" -ForegroundColor Yellow
    $i = 1
    foreach($dev in $recording) {
        $default = if($dev.Default){" [Default]"}else{""}
        Write-Host "  $i. $($dev.Name)$default"
        $i++
    }
}

# Main
switch($Action.ToLower()) {
    "status" { Get-AudioStatus }
    "list" { List-Devices }
    "mute" { Set-PlaybackMute -Mute $true }
    "unmute" { Set-PlaybackMute -Mute $false }
    "mic-mute" { Set-MicMute -Mute $true }
    "mic-unmute" { Set-MicMute -Mute $false }
    "switch" { 
        if ($Index -eq 0) {
            Write-Host "Please specify device index. Example: switch 1" -ForegroundColor Yellow
        } else {
            Switch-PlaybackDevice -Index $Index 
        }
    }
    "switch-mic" {
        if ($Index -eq 0) {
            Write-Host "Please specify device index. Example: switch-mic 1" -ForegroundColor Yellow
        } else {
            Switch-RecordingDevice -Index $Index
        }
    }
    default {
        if ($Action -match "^\d+$") {
            Switch-PlaybackDevice -Index $Action
        } else {
            Write-Host "Usage: .\audio_control.ps1 [status|list|mute|unmute|mic-mute|mic-unmute|switch|switch-mic] [index]"
        }
    }
}
