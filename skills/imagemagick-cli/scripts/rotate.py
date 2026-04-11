"""
图片旋转工具
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


def rotate_image(input_path, output_path, angle, background='white'):
    """
    旋转图片
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        angle: 旋转角度（正数为顺时针）
        background: 背景颜色
    
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
    
    # 执行旋转
    success, output, error = run_magick_command([
        str(input_path),
        "-background", background,
        "-rotate", str(angle),
        str(output_path)
    ])
    
    if success:
        print(f"✅ 旋转成功: {input_path} -> {output_path} (角度: {angle}°)")
        return True
    else:
        print(f"❌ 旋转失败: {error}")
        return False


def main():
    parser = argparse.ArgumentParser(description='图片旋转工具')
    parser.add_argument('input', help='输入图片路径')
    parser.add_argument('output', help='输出图片路径')
    parser.add_argument('--angle', '-a', type=float, required=True, help='旋转角度（正数为顺时针）')
    parser.add_argument('--background', '-b', default='white', help='背景颜色（默认 white）')
    
    args = parser.parse_args()
    
    success = rotate_image(args.input, args.output, args.angle, args.background)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
