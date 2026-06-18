"""
FunASR 语音转录脚本
支持本地音频/视频文件、URL 音频，输出带时间戳和说话人标签的结构化结果
视频文件自动用 ffmpeg 提取音轨后转录
"""
import sys
import os
import tempfile
import subprocess
import argparse
from pathlib import Path
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm", ".m4v", ".wmv"}


def extract_audio(video_path: str) -> str:
    """用 ffmpeg 从视频提取音频到临时 wav"""
    tmp = tempfile.mktemp(suffix=".wav")
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
           "-ar", "16000", "-ac", "1", tmp, "-loglevel", "error"]
    subprocess.run(cmd, check=True)
    return tmp


def main():
    parser = argparse.ArgumentParser(description="FunASR 语音/视频转文字")
    parser.add_argument("input", help="音频/视频文件路径或URL")
    parser.add_argument("--model", default="FunAudioLLM/Fun-ASR-Nano-2512",
                        choices=["iic/SenseVoiceSmall", "FunAudioLLM/Fun-ASR-Nano-2512"],
                        help="模型选择 (默认: Fun-ASR-Nano 800M)")
    parser.add_argument("--fast", action="store_true",
                        help="快速翻录 (SenseVoiceSmall 234M, 带时间戳但无标点)")
    parser.add_argument("--detailed", action="store_true",
                        help="详细翻录 (Fun-ASR-Nano 800M, 带标点高精度, 默认)")
    parser.add_argument("--no-timestamps", action="store_true", help="不显示时间戳")
    parser.add_argument("--no-speaker", action="store_true", help="不区分说话人")
    parser.add_argument("--output", "-o", help="保存到文本文件")
    args = parser.parse_args()

    # --fast / --detailed 快捷覆盖模型选择
    if args.fast:
        args.model = "iic/SenseVoiceSmall"
    elif args.detailed:
        args.model = "FunAudioLLM/Fun-ASR-Nano-2512"

    # 检测视频文件，自动提取音频
    input_path = args.input
    tmp_audio = None
    if os.path.isfile(input_path) and Path(input_path).suffix.lower() in VIDEO_EXTS:
        print(f"[INFO] 检测到视频文件，正在提取音频...")
        tmp_audio = extract_audio(input_path)
        input_path = tmp_audio
        print(f"[INFO] 音频提取完成")

    print(f"[INFO] 加载模型: {args.model}")

    vad_model = "fsmn-vad"
    spk_model = None if args.no_speaker else "cam++"

    model = AutoModel(
        model=args.model,
        vad_model=vad_model,
        spk_model=spk_model,
        device="cpu",
    )

    print(f"[INFO] 识别中: {input_path}")
    result = model.generate(input=input_path)

    # 清理临时文件
    if tmp_audio and os.path.exists(tmp_audio):
        os.unlink(tmp_audio)

    if not result or len(result) == 0:
        print("[ERROR] 识别失败，无结果")
        sys.exit(1)

    output_lines = []
    segments = result[0].get("sentence_info", [])
    if not segments:
        text = result[0].get("text", str(result))
        print(text)
        output_lines.append(text)
    else:
        for seg in segments:
            ts = ""
            if not args.no_timestamps:
                ts = f"[{seg['start']/1000:.1f}s-{seg['end']/1000:.1f}s] "
            spk = ""
            if not args.no_speaker and "spk" in seg:
                spk = f"说话人{seg['spk']}: "
            text = rich_transcription_postprocess(seg["sentence"])
            line = f"{ts}{spk}{text}"
            print(line)
            output_lines.append(line)

    if "emo" in result[0]:
        print(f"\n[情感] {result[0]['emo']}")

    if args.output:
        if args.no_speaker:
            joined = "".join(output_lines)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(joined)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines))
        print(f"[OK] 已保存: {args.output}")


if __name__ == "__main__":
    main()
