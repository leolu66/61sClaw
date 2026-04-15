"""
图片裁剪工具
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


def crop_image(input_path, output_path, x, y, width, height, center=False):
    """
    裁剪图片
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        x: 起始 X 坐标
        y: 起始 Y 坐标
        width: 裁剪宽度
        height: 裁剪高度
        center: 是否居中裁剪
    
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
    
    # 构建裁剪参数
    if center:
        # 居中裁剪
        crop_arg = f"{width}x{height}+0+0"
        gravity = "center"
        success, output, error = run_magick_command([
            str(input_path),
            "-gravity", gravity,
            "-crop", crop_arg,
            "+repage",
            str(output_path)
        ])
    else:
        # 指定坐标裁剪
        crop_arg = f"{width}x{height}+{x}+{y}"
        success, output, error = run_magick_command([
            str(input_path),
            "-crop", crop_arg,
            "+repage",
            str(output_path)
        ])
    
    if success:
        print(f"✅ 裁剪成功: {input_path} -> {output_path}")
        return True
    else:
        print(f"❌ 裁剪失败: {error}")
        return False


def main():
    parser = argparse.ArgumentParser(description='图片裁剪工具')
    parser.add_argument('input', help='输入图片路径')
    parser.add_argument('output', help='输出图片路径')
    parser.add_argument('--x', type=int, default=0, help='起始 X 坐标')
    parser.add_argument('--y', type=int, default=0, help='起始 Y 坐标')
    parser.add_argument('--width', '-w', type=int, required=True, help='裁剪宽度')
    parser.add_argument('--height', '-ht', type=int, required=True, help='裁剪高度')
    parser.add_argument('--center', '-c', action='store_true', help='居中裁剪')
    
    args = parser.parse_args()
    
    success = crop_image(
        args.input, 
        args.output, 
        args.x, 
        args.y, 
        args.width, 
        args.height,
        center=args.center
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
