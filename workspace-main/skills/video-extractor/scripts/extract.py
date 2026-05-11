#!/usr/bin/env python3
"""
Video Content Extractor - extract transcript from Chinese video platforms.

Supports: 头条/Toutiao, 抖音/Douyin, 快手/Kuaishou, B站/Bilibili,
西瓜视频/Xigua, 好看视频, 小红书/Xiaohongshu, 微博/Weibo, etc.

Usage:
    python extract.py <video-url>
    python extract.py <video-url> --model tiny   # override whisper model
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Fix stdout encoding for Windows (emoji/unicode)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)


# ============================================================
# Path setup: resolve yt-dlp and ffmpeg
# ============================================================

YT_DLP = shutil.which("yt-dlp") or "D:\\anaconda3\\Scripts\\yt-dlp.exe"
FFMPEG = shutil.which("ffmpeg") or "D:\\ffmpeg-8.1.1\\bin\\ffmpeg.EXE"
ANACONDA_PYTHON = "D:\\anaconda3\\python.exe"

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


# ============================================================
# Utils
# ============================================================

def run(cmd, **kwargs):
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_video_info(url):
    """Get video metadata (title, duration) via yt-dlp."""
    cmd = [YT_DLP, "--print", "%(title)s|||%(duration)s", "--skip-download", url]
    rc, out, err = run(cmd, timeout=120)
    if rc != 0 or not out:
        raise RuntimeError(f"yt-dlp failed: {err or out}")

    parts = out.split("|||")
    title = parts[0].strip() if len(parts) > 0 else "unknown_title"
    duration = float(parts[1]) if len(parts) > 1 and parts[1] != "NA" else 0
    return title, duration


def sanitize_filename(name):
    """Remove characters invalid on Windows, then shorten if needed."""
    name = re.sub(r'[\\/:*?"<>|]', '-', name)
    name = re.sub(r'\s+', ' ', name).strip()
    # Limit to 200 chars max including extension space
    if len(name) > 190:
        name = name[:190].rstrip('-').strip()
    return name or "video_transcript"


def has_subtitles(url):
    """Check if the video has subtitle tracks."""
    cmd = [YT_DLP, "--list-subs", url]
    rc, out, err = run(cmd, timeout=60)
    if rc != 0:
        return False
    # yt-dlp prints "has no subtitles" or lists them
    return "has no subtitles" not in out.lower() and len(out.strip()) > 0


def download_subtitles(url, lang="zh-Hans,zh-Hant,zh,en"):
    """Download subtitles and return cleaned transcript text."""
    tmpdir = tempfile.mkdtemp(prefix="vxt_")
    try:
        cmd = [
            YT_DLP,
            "--write-sub", "--write-auto-sub",
            "--skip-download",
            "--sub-lang", lang,
            "-o", os.path.join(tmpdir, "%(id)s.%(ext)s"),
            url,
        ]
        rc, out, err = run(cmd, timeout=120)
        if rc != 0:
            return None

        # Find downloaded subtitle files
        sub_files = sorted(
            [f for f in Path(tmpdir).iterdir() if f.suffix.lower() in (".vtt", ".srt", ".ass")],
            key=lambda f: f.stat().st_mtime, reverse=True
        )
        if not sub_files:
            # Try again without lang filter
            cmd[4] = "--all-subs"
            run(cmd, timeout=120)
            sub_files = sorted(
                [f for f in Path(tmpdir).iterdir() if f.suffix.lower() in (".vtt", ".srt", ".ass")],
                key=lambda f: f.stat().st_mtime, reverse=True
            )
        if not sub_files:
            return None

        # Parse subtitle file into text
        with open(sub_files[0], "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()

        lines = raw.splitlines()
        text_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Skip VTT/SRT headers, timestamps, numbering
            if line in ("WEBVTT",):
                continue
            if re.match(r'^\d+$', line):
                continue
            if '-->' in line:
                continue
            if re.match(r'^(Kind|Language|align|position|size|line):', line, re.IGNORECASE):
                continue
            # Remove inline timestamps <00:00:00.000>
            line = re.sub(r'<\d{2}:\d{2}:\d{2}[.,]\d{3}>', '', line).strip()
            # Remove HTML tags
            line = re.sub(r'<[^>]+>', '', line).strip()
            if line:
                text_lines.append(line)

        # Deduplicate
        cleaned = []
        for t in text_lines:
            if cleaned and (t == cleaned[-1] or t.startswith(cleaned[-1])):
                continue
            cleaned.append(t)

        return " ".join(cleaned)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def download_audio(url):
    """Download audio to a temp file, return the file path."""
    tmpdir = tempfile.mkdtemp(prefix="vxt_audio_")
    out_template = os.path.join(tmpdir, "audio.%(ext)s")
    cmd = [
        YT_DLP,
        "-x", "--audio-format", "mp3",
        "--ffmpeg-location", FFMPEG,
        "-o", out_template,
        url,
    ]
    rc, out, err = run(cmd, timeout=300)
    if rc != 0:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"Audio download failed: {err or out}")
    
    # Find the downloaded file
    files = list(Path(tmpdir).glob("*"))
    if not files:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError("No audio file downloaded")
    return str(files[0]), tmpdir


def transcribe_audio(audio_path, model_name="small"):
    """Transcribe audio using Whisper (via Anaconda Python)."""
    script = f"""
import sys
import whisper
model = whisper.load_model('{model_name}')
result = model.transcribe(r'{audio_path}', language='zh')
print(result['text'])
"""
    # Write script to temp file to avoid escaping issues
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(script)
        tmp_script = f.name

    try:
        rc, out, err = run([ANACONDA_PYTHON, tmp_script], timeout=600)
        if rc != 0:
            raise RuntimeError(f"Whisper transcription failed: {err}")
        return out.strip()
    finally:
        os.unlink(tmp_script)


def save_transcript(text, title, url):
    """Save transcript to output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(title)
    output_path = OUTPUT_DIR / f"{safe_name}.txt"

    # Avoid overwriting: append number if exists
    counter = 1
    while output_path.exists():
        output_path = OUTPUT_DIR / f"{safe_name}_{counter}.txt"
        counter += 1

    content = f"""视频标题: {title}
来源URL: {url}
提取时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 60}

转录内容：

{text}
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Extract transcript from Chinese video platforms")
    parser.add_argument("url", help="Video URL")
    parser.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: small)")
    args = parser.parse_args()

    url = args.url

    print(f"[1/4] Fetching video info: {url}")
    try:
        title, duration = get_video_info(url)
        print(f"      标题: {title}")
        print(f"      时长: {duration:.0f}s" if duration else "")
    except Exception as e:
        print(f"      [FAIL] 获取视频信息失败: {e}", file=sys.stderr)
        sys.exit(1)

    text = None

    # Step 2: Try subtitle download first
    print(f"[2/4] 检查字幕...")
    try:
        if has_subtitles(url):
            print(f"      发现字幕轨道，尝试下载...")
            text = download_subtitles(url)
            if text:
                print(f"      字幕提取成功 ({len(text)} 字符)")
    except Exception as e:
        print(f"      字幕下载失败: {e}")

    # Step 3: Fallback to audio + Whisper STT
    if not text:
        print(f"[3/4] 视频无字幕，下载音频进行语音识别...")
        audio_path = None
        tmp_dir = None
        try:
            audio_path, tmp_dir = download_audio(url)
            print(f"      音频下载完成 ({audio_path})")
            print(f"      使用 Whisper ({args.model}) 进行语音识别...")
            text = transcribe_audio(audio_path, args.model)
            if text:
                print(f"      语音识别完成 ({len(text)} 字符)")
        except Exception as e:
            print(f"      [FAIL] 语音识别失败: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    if not text:
        print(f"      [FAIL] 无法提取视频内容", file=sys.stderr)
        sys.exit(1)

    # Step 4: Save output
    print(f"[4/4] 保存转录结果...")
    output_path = save_transcript(text, title, url)
    print(f"      [OK] 已保存到: {output_path}")

    # Print the transcript
    print(f"\n{'=' * 60}")
    print(f"转录内容:\n")
    print(text)
    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
