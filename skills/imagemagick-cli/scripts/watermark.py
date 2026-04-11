"""
图片水印工具
"""
import argparse
import sys
from pathlib import Path

# 修复 Windows 控制台编码
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from utils import run_magick_command, ensure_dir


def add_text_watermark(input_path, output_path, text, position='southeast', 
                       fontsize=24, color='rgba(255,255,255,0.5)', font=None):
    """
    添加文字水印
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        text: 水印文字
        position: 位置 (northwest/north/northeast/west/center/east/southwest/south/southeast)
        fontsize: 字体大小
        color: 字体颜色
        font: 字体名称（可选）
    
    Returns:
        bool: 是否成功
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # 检查输入文件是否存在
    if not input_path.exists():
        print(f"❌ 错误: 输入文件不存在: {input_path}")
        return False
    
    # 确保输出目录存在
    ensure_dir(output_path.parent)
    
    # 构建命令
    cmd = [str(input_path)]
    
    # 字体设置
    if font:
        cmd.extend(["-font", font])
    
    # 添加文字水印
    cmd.extend([
        "-gravity", position,
        "-pointsize", str(fontsize),
        "-fill", color,
        "-annotate", "+10+10", text,
        str(output_path)
    ])
    
    # 执行
    success, output, error = run_magick_command(cmd)
    
    if success:
        print(f"✅ 水印添加成功: {input_path} -> {output_path}")
        print(f"   文字: {text}, 位置: {position}")
        return True
    else:
        print(f"❌ 水印添加失败: {error}")
        return False


def add_image_watermark(input_path, output_path, watermark_path, position='southeast', 
                        opacity=50, size=None):
    """
    添加图片水印
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        watermark_path: 水印图片路径
        position: 位置
        opacity: 透明度 0-100
        size: 水印尺寸（如 100x100）
    
    Returns:
        bool: 是否成功
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    watermark_path = Path(watermark_path)
    
    # 检查文件是否存在
    if not input_path.exists():
        print(f"❌ 错误: 输入文件不存在: {input_path}")
        return False
    if not watermark_path.exists():
        print(f"❌ 错误: 水印文件不存在: {watermark_path}")
        return False
    
    # 确保输出目录存在
    ensure_dir(output_path.parent)
    
    # 调整水印尺寸（如果需要）
    watermark_arg = str(watermark_path)
    if size:
        watermark_arg = f"{watermark_arg} -resize {size}"
    
    # 使用 composite 命令
    success, output, error = run_magick_command([
        "composite",
        "-gravity", position,
        "-dissolve", f"{opacity}%",
        watermark_arg,
        str(input_path),
        str(output_path)
    ])
    
    if success:
        print(f"✅ 图片水印添加成功: {input_path} -> {output_path}")
        return True
    else:
        print(f"❌ 图片水印添加失败: {error}")
        return False


def main():
    parser = argparse.ArgumentParser(description='图片水印工具')
    parser.add_argument('input', help='输入图片路径')
    parser.add_argument('output', help='输出图片路径')
    parser.add_argument('--text', '-t', help='水印文字')
    parser.add_argument('--watermark-image', '-wi', help='水印图片路径')
    parser.add_argument('--position', '-p', default='southeast',
                        choices=['northwest', 'north', 'northeast', 'west', 'center', 
                                'east', 'southwest', 'south', 'southeast'],
                        help='水印位置（默认 southeast）')
    parser.add_argument('--fontsize', '-fs', type=int, default=24, help='字体大小（默认 24）')
    parser.add_argument('--color', '-c', default='rgba(255,255,255,0.5)', help='字体颜色')
    parser.add_argument('--font', '-f', help='字体名称')
    parser.add_argument('--opacity', '-o', type=int, default=50, help='图片水印透明度 0-100')
    
    args = parser.parse_args()
    
    if args.watermark_image:
        success = add_image_watermark(
            args.input, args.output, args.watermark_image,
            position=args.position, opacity=args.opacity
        )
    elif args.text:
        success = add_text_watermark(
            args.input, args.output, args.text,
            position=args.position, fontsize=args.fontsize, 
            color=args.color, font=args.font
        )
    else:
        print("❌ 错误: 请指定 --text 或 --watermark-image")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
