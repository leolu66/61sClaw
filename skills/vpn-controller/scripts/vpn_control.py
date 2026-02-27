#!/usr/bin/env python3
"""
VPN Controller for Clash for Windows
"""
import subprocess
import sys
import os

VPN_PATH = r"D:\Users\luzhe\AppData\Local\Programs\Clash for Windows\Clash for Windows.exe"
VPN_EXE_NAME = "Clash for Windows.exe"

def is_vpn_running():
    """Check if VPN is currently running."""
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {VPN_EXE_NAME}"],
        capture_output=True, text=True, encoding='utf-8', errors='ignore'
    )
    return VPN_EXE_NAME in result.stdout

def disable_proxy():
    """Disable Windows proxy settings."""
    try:
        # Disable proxy by setting ProxyEnable to 0
        subprocess.run([
            "powershell", "-Command",
            "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name 'ProxyEnable' -Value 0"
        ], capture_output=True, check=True)

        # Clear proxy server
        subprocess.run([
            "powershell", "-Command",
            "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name 'ProxyServer' -Value ''"
        ], capture_output=True, check=True)

        # Refresh Internet settings
        subprocess.run([
            "powershell", "-Command",
            "$signature = '[DllImport(\"wininet.dll\", SetLastError=true)] public static extern bool InternetSetOption(IntPtr hInternet, int dwOption, IntPtr lpBuffer, int dwBufferLength);'; $type = Add-Type -MemberDefinition $signature -Name wininet -Namespace pinvoke -PassThru; $type::InternetSetOption(0, 39, 0, 0); $type::InternetSetOption(0, 37, 0, 0)"
        ], capture_output=True)

        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not disable proxy: {e}")
        return False

def enable_proxy(server="127.0.0.1:7890"):
    """Enable Windows proxy settings."""
    try:
        # Set proxy server
        subprocess.run([
            "powershell", "-Command",
            f"Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name 'ProxyServer' -Value '{server}'"
        ], capture_output=True, check=True)

        # Enable proxy
        subprocess.run([
            "powershell", "-Command",
            "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name 'ProxyEnable' -Value 1"
        ], capture_output=True, check=True)

        # Refresh Internet settings
        subprocess.run([
            "powershell", "-Command",
            "$signature = '[DllImport(\"wininet.dll\", SetLastError=true)] public static extern bool InternetSetOption(IntPtr hInternet, int dwOption, IntPtr lpBuffer, int dwBufferLength);'; $type = Add-Type -MemberDefinition $signature -Name wininet -Namespace pinvoke -PassThru; $type::InternetSetOption(0, 39, 0, 0); $type::InternetSetOption(0, 37, 0, 0)"
        ], capture_output=True)

        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not enable proxy: {e}")
        return False

def start_vpn():
    """Start the VPN application."""
    if is_vpn_running():
        print("VPN is already running.")
        return True

    if not os.path.exists(VPN_PATH):
        print(f"Error: VPN executable not found at {VPN_PATH}")
        return False

    try:
        subprocess.Popen([VPN_PATH], shell=True)
        print("VPN started successfully.")
        return True
    except Exception as e:
        print(f"Error starting VPN: {e}")
        return False

def stop_vpn():
    """Stop the VPN application and disable proxy."""
    if not is_vpn_running():
        print("VPN is not running.")
        # Still try to disable proxy in case it was left enabled
        disable_proxy()
        print("Proxy settings disabled.")
        return True

    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", VPN_EXE_NAME],
            capture_output=True, check=True
        )
        print("VPN stopped successfully.")

        # Disable proxy after stopping VPN
        if disable_proxy():
            print("Proxy settings disabled.")
        else:
            print("Warning: Could not disable proxy settings.")

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error stopping VPN: {e}")
        return False

def status():
    """Show VPN status."""
    if is_vpn_running():
        print("VPN is running.")
    else:
        print("VPN is not running.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python vpn_control.py [start|stop|status]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        success = start_vpn()
    elif command == "stop":
        success = stop_vpn()
    elif command == "status":
        status()
        success = True
    elif command == "disable-proxy":
        success = disable_proxy()
        print("Proxy disabled." if success else "Failed to disable proxy.")
    elif command == "enable-proxy":
        server = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1:7890"
        success = enable_proxy(server)
        print(f"Proxy enabled ({server})." if success else "Failed to enable proxy.")
    else:
        print(f"Unknown command: {command}")
        print("Usage: python vpn_control.py [start|stop|status|disable-proxy|enable-proxy]")
        success = False

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
