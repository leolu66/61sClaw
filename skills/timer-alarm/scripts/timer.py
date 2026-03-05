#!/usr/bin/env python3
"""
定时器与闹钟管理工具

支持：
- 倒计时（如15分钟）
- 指定时间闹钟（如18:00）
- 重复闹钟（如每天上午10点）
- TTS语音播报
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 技能目录
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
CONFIG_FILE = SKILL_DIR / "config.json"
ALARMS_FILE = DATA_DIR / "alarms.json"


def load_config():
    """加载配置文件"""
    default_config = {
        "tts_enabled": True,
        "tts_voice": "default",
        "alarm_sound": "default",
        "snooze_minutes": 5
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                default_config.update(config)
        except Exception as e:
            print(f"[WARNING] 读取配置文件失败: {e}")
    
    return default_config


def load_alarms():
    """加载所有闹钟"""
    if not ALARMS_FILE.exists():
        return []
    
    try:
        with open(ALARMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取闹钟数据失败: {e}")
        return []


def save_alarms(alarms):
    """保存闹钟数据"""
    DATA_DIR.mkdir(exist_ok=True)
    try:
        with open(ALARMS_FILE, "w", encoding="utf-8") as f:
            json.dump(alarms, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] 保存闹钟数据失败: {e}")


def generate_alarm_id():
    """生成唯一闹钟ID"""
    return f"alarm_{int(time.time() * 1000)}"


def parse_time(time_str):
    """解析时间字符串"""
    formats = [
        "%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    return None


def speak_message(message):
    """使用TTS播放消息"""
    config = load_config()
    
    if not config.get("tts_enabled", True):
        return
    
    # Windows 使用 PowerShell TTS
    if sys.platform == "win32":
        try:
            import subprocess
            ps_script = f'''
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Speak("{message}")
'''
            subprocess.run(["powershell", "-Command", ps_script], 
                         capture_output=True, timeout=30)
            print(f"[TTS] {message}")
        except Exception as e:
            print(f"[WARNING] TTS播放失败: {e}")
    else:
        # macOS/Linux 使用 say 或 espeak
        try:
            import subprocess
            if sys.platform == "darwin":
                subprocess.run(["say", message], capture_output=True, timeout=30)
            else:
                subprocess.run(["espeak", message], capture_output=True, timeout=30)
            print(f"[TTS] {message}")
        except Exception as e:
            print(f"[WARNING] TTS播放失败: {e}")


def play_alarm(message):
    """播放闹钟提醒"""
    print("\n" + "=" * 50)
    print("[ALARM] 闹钟响了！")
    print(f"[MESSAGE] {message}")
    print("=" * 50 + "\n")
    
    # 播放TTS
    speak_message(message)
    
    # 播放提示音（如果配置）
    config = load_config()
    if config.get("alarm_sound") and config["alarm_sound"] != "default":
        try:
            import subprocess
            # Windows 播放提示音
            if sys.platform == "win32":
                subprocess.run(["powershell", "-c", "[Console]::Beep(1000, 500)"])
        except Exception:
            pass


def set_countdown(minutes, message="闹钟响了！"):
    """设置倒计时"""
    alarm_id = generate_alarm_id()
    target_time = datetime.now() + timedelta(minutes=minutes)
    
    alarm = {
        "id": alarm_id,
        "type": "countdown",
        "minutes": minutes,
        "target_time": target_time.isoformat(),
        "message": message,
        "created_at": datetime.now().isoformat(),
        "enabled": True
    }
    
    alarms = load_alarms()
    alarms.append(alarm)
    save_alarms(alarms)
    
    print(f"[OK] 倒计时闹钟已设置")
    print(f"   ID: {alarm_id}")
    print(f"   时间: {minutes} 分钟后 ({target_time.strftime('%H:%M:%S')})")
    print(f"   提示: {message}")
    
    return alarm_id


def set_alarm(time_str, message="闹钟响了！", repeat=None):
    """设置指定时间闹钟"""
    target_time = parse_time(time_str)
    
    if not target_time:
        print(f"[ERROR] 无法解析时间: {time_str}")
        print("   支持的格式: HH:MM, YYYY-MM-DD HH:MM")
        return None
    
    # 如果时间是今天且已过，设置为明天
    now = datetime.now()
    if target_time.date() == now.date() and target_time < now:
        target_time += timedelta(days=1)
        print(f"[INFO] 时间已过，已自动设置为明天 {target_time.strftime('%H:%M')}")
    
    alarm_id = generate_alarm_id()
    
    alarm = {
        "id": alarm_id,
        "type": "alarm",
        "time": time_str,
        "target_time": target_time.isoformat(),
        "message": message,
        "repeat": repeat,
        "created_at": datetime.now().isoformat(),
        "enabled": True
    }
    
    alarms = load_alarms()
    alarms.append(alarm)
    save_alarms(alarms)
    
    repeat_str = f" (重复: {repeat})" if repeat else ""
    print(f"[OK] 闹钟已设置")
    print(f"   ID: {alarm_id}")
    print(f"   时间: {target_time.strftime('%Y-%m-%d %H:%M')}{repeat_str}")
    print(f"   提示: {message}")
    
    return alarm_id


def list_alarms():
    """列出所有闹钟"""
    alarms = load_alarms()
    
    if not alarms:
        print("[INFO] 没有设置任何闹钟")
        return
    
    print("\n" + "-" * 70)
    print(f"{'ID':<20} {'类型':<10} {'时间':<20} {'重复':<10} {'状态':<6}")
    print("-" * 70)
    
    for alarm in alarms:
        alarm_id = alarm["id"][:18] + ".." if len(alarm["id"]) > 20 else alarm["id"]
        alarm_type = alarm.get("type", "alarm")
        target = alarm.get("target_time", "unknown")
        try:
            dt = datetime.fromisoformat(target)
            target_str = dt.strftime("%m-%d %H:%M")
        except:
            target_str = target[:16]
        
        repeat = alarm.get("repeat", "-") or "-"
        status = "启用" if alarm.get("enabled", True) else "禁用"
        
        print(f"{alarm_id:<20} {alarm_type:<10} {target_str:<20} {repeat:<10} {status:<6}")
    
    print("-" * 70)
    print(f"共 {len(alarms)} 个闹钟\n")


def cancel_alarm(alarm_id):
    """取消指定闹钟"""
    alarms = load_alarms()
    
    for alarm in alarms:
        if alarm["id"] == alarm_id:
            alarms.remove(alarm)
            save_alarms(alarms)
            print(f"[OK] 闹钟已取消: {alarm_id}")
            return True
    
    print(f"[ERROR] 未找到闹钟: {alarm_id}")
    return False


def cancel_all_alarms():
    """取消所有闹钟"""
    alarms = load_alarms()
    count = len(alarms)
    
    if count == 0:
        print("[INFO] 没有需要取消的闹钟")
        return
    
    save_alarms([])
    print(f"[OK] 已取消所有闹钟 (共 {count} 个)")


def check_and_trigger_alarms():
    """检查并触发到期的闹钟"""
    alarms = load_alarms()
    now = datetime.now()
    triggered = []
    
    for alarm in alarms:
        if not alarm.get("enabled", True):
            continue
        
        try:
            target_time = datetime.fromisoformat(alarm["target_time"])
            if target_time <= now:
                triggered.append(alarm)
        except:
            continue
    
    for alarm in triggered:
        play_alarm(alarm["message"])
        
        # 处理重复闹钟
        if alarm.get("repeat"):
            # 计算下次触发时间
            target_time = datetime.fromisoformat(alarm["target_time"])
            
            if alarm["repeat"] == "daily":
                next_time = target_time + timedelta(days=1)
            elif alarm["repeat"] == "weekdays":
                # 周一到周五
                next_time = target_time + timedelta(days=1)
                while next_time.weekday() >= 5:  # 5=周六, 6=周日
                    next_time += timedelta(days=1)
            else:
                # 其他重复规则暂不处理
                alarm["enabled"] = False
                continue
            
            alarm["target_time"] = next_time.isoformat()
            print(f"[INFO] 重复闹钟已更新到: {next_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            # 非重复闹钟，禁用
            alarm["enabled"] = False
    
    if triggered:
        save_alarms(alarms)
    
    return len(triggered)


def run_daemon():
    """运行后台守护进程，持续检查闹钟"""
    print("[INFO] 闹钟守护进程已启动 (按 Ctrl+C 停止)")
    
    try:
        while True:
            count = check_and_trigger_alarms()
            if count > 0:
                print(f"[INFO] 触发了 {count} 个闹钟")
            time.sleep(10)  # 每10秒检查一次
    except KeyboardInterrupt:
        print("\n[INFO] 闹钟守护进程已停止")


def main():
    parser = argparse.ArgumentParser(description="定时器与闹钟管理工具")
    parser.add_argument("-c", "--countdown", type=int, help="设置倒计时（分钟）")
    parser.add_argument("-t", "--time", type=str, help="设置指定时间（如 18:00）")
    parser.add_argument("-m", "--message", type=str, default="闹钟响了！", help="提醒消息")
    parser.add_argument("-r", "--repeat", type=str, help="重复规则（daily/weekdays）")
    parser.add_argument("-l", "--list", action="store_true", help="列出所有闹钟")
    parser.add_argument("--cancel", type=str, help="取消指定ID的闹钟")
    parser.add_argument("--cancel-all", action="store_true", help="取消所有闹钟")
    parser.add_argument("--daemon", action="store_true", help="运行后台守护进程")
    parser.add_argument("--check", action="store_true", help="检查并触发到期闹钟")
    
    args = parser.parse_args()
    
    if args.countdown:
        set_countdown(args.countdown, args.message)
    elif args.time:
        set_alarm(args.time, args.message, args.repeat)
    elif args.list:
        list_alarms()
    elif args.cancel:
        cancel_alarm(args.cancel)
    elif args.cancel_all:
        cancel_all_alarms()
    elif args.daemon:
        run_daemon()
    elif args.check:
        check_and_trigger_alarms()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
