"""
录制系统音频并转录（B站/网页视频等）

用法:
  python capture_transcribe.py -d 420 --fast -t "标题" --terms "Claude Code,Loop Engineering"
"""
import sys
import os
import time
import argparse
import wave
import threading
import subprocess
import numpy as np
import sounddevice as sd
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

LOOPBACK_IDX = 20       # WASAPI 环回设备索引 (回退值)
SAMPLE_RATE = 16000
COUNTDOWN_SECS = 3


def find_loopback_device() -> int:
    """自动查找可用环回设备"""
    candidates = []
    try:
        devices = sd.query_devices()
        for d in devices:
            name = d.get("name", "")
            inp = d.get("max_input_channels", 0)
            idx = d["index"]
            # 优先级 1: 立体声混音 (Stereo Mix)
            if inp > 0 and "混音" in name:
                print(f"[INFO] loopback: [{idx}] {name}")
                return idx
            # 优先级 2: 扬声器环回 / speaker loopback
            if inp > 0 and ("扬声器" in name or "speaker" in name.lower()):
                candidates.append(idx)
        if candidates:
            idx = candidates[0]
            print(f"[INFO] loopback: [{idx}] {devices[idx]['name']}")
            return idx
    except Exception:
        pass
    print(f"[WARN] no loopback device found")
    return None


def countdown(secs: int):
    """倒计时，提示用户启动视频"""
    for i in range(secs, 0, -1):
        print(f"\r  >> {i} 秒后开始录制...", end="", flush=True)
        time.sleep(1)
    print("\r  >> 录制开始！")


def progress_bar(current: float, total: float, width: int = 30):
    """绘制进度条"""
    pct = min(current / total, 1.0) if total > 0 else 0
    filled = int(width * pct)
    bar = "#" * filled + "-" * (width - filled)
    elapsed = current
    remaining = total - current if total > 0 else 0
    return f"  [{bar}] {elapsed:.0f}s / {total:.0f}s  rem {remaining:.0f}s"


def record_audio(duration: int, output_path: str, dev_idx):
    """录制系统音频（WASAPI Loopback）"""
    if dev_idx is None:
        print("[ERROR] 未找到环回录音设备")
        print("[TIP] 请检查 Realtek 声卡驱动是否安装了立体声混音")
        sys.exit(1)
    countdown(COUNTDOWN_SECS)

    if duration > 0:
        print(f"  [REC] {duration}s")
        recording = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                           channels=1, device=dev_idx, dtype='int16')
        start = time.time()
        done = threading.Event()

        def progress_loop():
            while not done.is_set():
                elapsed = time.time() - start
                if elapsed >= duration:
                    break
                print(f"\r{progress_bar(elapsed, duration)}", end="", flush=True)
                time.sleep(0.5)

        t = threading.Thread(target=progress_loop, daemon=True)
        t.start()
        sd.wait()
        elapsed = time.time() - start
        done.set()
        print(f"\r{progress_bar(elapsed, elapsed)}  [OK] done")
    else:
        print(f"  [REC] recording (Enter to stop)...")
        chunks = []
        def callback(indata, frames, time_info, status):
            chunks.append(indata.copy())
        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                                device=dev_idx, dtype='int16',
                                callback=callback)
        stream.start()
        input()
        stream.stop()
        stream.close()
        recording = np.concatenate(chunks)
        dur = len(recording) / SAMPLE_RATE
        print(f"  [STOP] recorded {dur:.1f}s")

    with wave.open(output_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(recording.tobytes())


def apply_corrections(text: str, terms: list) -> str:
    """简单的术语纠正"""
    corrections = {
        "close code": "Claude Code",
        "cloth code": "Claude Code",
        "cloud code": "Claude Code",
        "look engineering": "Loop Engineering",
        "loop engineer": "Loop Engineering",
        "look engineer": "Loop Engineering",
        "os money": "O'Shaughnessy",
        "osmaney": "O'Shaughnessy",
        "aus money": "O'Shaughnessy",
        "adios money": "O'Shaughnessy",
        "borrows": "Boris",
        "overbating": "overbaking",
        "ralph": "Ralph",
        "gofree": "GoFree",
    }
    result = text
    for wrong, correct in corrections.items():
        result = result.replace(wrong, correct)
    return result


def main():
    parser = argparse.ArgumentParser(description="录制系统音频 -> FunASR 转录")
    parser.add_argument("--duration", "-d", type=int, default=60,
                        help="录制时长(秒), 0=手动停止 (默认60)")
    parser.add_argument("--fast", action="store_true",
                        help="快速翻录 (SenseVoiceSmall, 无标点)")
    parser.add_argument("--detailed", action="store_true",
                        help="详细翻录 (Fun-ASR-Nano, 带标点, 默认)")
    parser.add_argument("--title", "-t", default="",
                        help="视频标题")
    parser.add_argument("--terms", default="",
                        help="专有名词,逗号分隔 (如: 'Claude Code,Loop Engineering')")
    parser.add_argument("--output", "-o", help="保存转录文本")
    parser.add_argument("--no-timestamps", action="store_true")
    parser.add_argument("--no-speaker", action="store_true")
    parser.add_argument("--window", action="store_true",
                        help="在新终端窗口运行录制 (显示倒计时和进度条)")
    args = parser.parse_args()

    # 如果是 --window 模式，在新终端窗口启动录制进程
    if args.window:
        cmd_args = []
        for arg in sys.argv[1:]:
            if arg != "--window":
                # 用 PowerShell 单引号包裹含空格/特殊字符的参数
                special = " |&;(){}[]$`',\\"
                if any(c in arg for c in special):
                    escaped = arg.replace("'", "''")
                    cmd_args.append(f"'{escaped}'")
                else:
                    cmd_args.append(arg)
        script_path = os.path.abspath(__file__)
        ws_path = os.path.abspath(os.path.join(os.path.dirname(script_path), "..", "..", ".."))
        cmd = f'cd "{ws_path}"; python "{script_path}" {" ".join(cmd_args)}; Write-Host "[DONE] 转录完成，按任意键关闭窗口" -Foreground Green; $null = [Console]::ReadKey()'
        subprocess.Popen(["powershell", "-NoExit", "-Command", cmd],
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        print("[OK] 录制终端已启动 (新窗口)")
        print(f"[TIP] 窗口将在录制/转录完成后暂停，查看结果后关闭即可")
        return

    # 模型选择
    if args.fast:
        model_id = "iic/SenseVoiceSmall"
        mode_label = "fast"
    elif args.detailed:
        model_id = "FunAudioLLM/Fun-ASR-Nano-2512"
        mode_label = "detailed"
    else:
        model_id = "FunAudioLLM/Fun-ASR-Nano-2512"
        mode_label = "detailed (default)"

    # 专有名词列表
    terms = [t.strip() for t in args.terms.split(",") if t.strip()]

    # 打印视频信息
    print("=" * 55)
    if args.title:
        print(f"  [TITLE] {args.title}")
    if terms:
        print(f"  [TERMS] {', '.join(terms)}")
    print(f"  [MODE] {mode_label} | {model_id.split('/')[-1]}")
    print(f"  [DURATION] {'manual' if args.duration == 0 else f'{args.duration}s'}")
    print("=" * 55)

    # 1. 录制系统音频
    dev_idx = find_loopback_device()
    tmp = os.path.join(os.environ.get("TEMP", "/tmp"), f"capture_{int(time.time())}.wav")
    record_audio(args.duration, tmp, dev_idx)

    # 2. 转录
    print(f"\n[ASR] loading model: {model_id}")
    vad_model = "fsmn-vad"
    spk_model = None if args.no_speaker else "cam++"

    model = AutoModel(model=model_id, vad_model=vad_model,
                      spk_model=spk_model, device="cpu")

    print(f"[ASR] transcribing...")
    start = time.time()
    result = model.generate(input=tmp)
    elapsed = time.time() - start

    try:
        os.unlink(tmp)
    except Exception:
        pass

    if not result or len(result) == 0:
        print("[ERROR] transcription failed")
        sys.exit(1)

    # 输出结果
    print(f"\n{'=' * 55}")
    if args.title:
        print(f"[TITLE] {args.title}")
    if terms:
        print(f"[TERMS] {', '.join(terms)}")
    print(f"{'=' * 55}\n")

    output_lines = []
    segments = result[0].get("sentence_info", [])
    if not segments:
        text = result[0].get("text", str(result))
        text = apply_corrections(text, terms)
        print(text)
        output_lines.append(text)
    else:
        for seg in segments:
            ts = ""
            if not args.no_timestamps:
                ts = f"[{seg['start']/1000:.1f}s-{seg['end']/1000:.1f}s] "
            spk = ""
            if not args.no_speaker and "spk" in seg:
                spk = f"SPK{seg['spk']}: "
            text = rich_transcription_postprocess(seg["sentence"])
            text = apply_corrections(text, terms)
            line = f"{ts}{spk}{text}"
            print(line)
            output_lines.append(line)

    print(f"\n{'-' * 55}")
    print(f"transcribe: {elapsed:.1f}s")

    if args.output:
        header = []
        if args.title:
            header.append(f"# {args.title}")
        if terms:
            header.append(f"# terms: {', '.join(terms)}")
        if header:
            header.append("")
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(header + output_lines))
        print(f"[SAVED] {args.output}")


if __name__ == "__main__":
    main()
