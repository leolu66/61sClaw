"""
图片尺寸调整工具
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


def resize_image(input_path, output_path, width=None, height=None, exact=False, percent=None):
    """
    调整图片尺寸
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        width: 目标宽度
        height: 目标高度
        exact: 是否强制指定尺寸（可能变形）
        percent: 缩放百分比
    
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
    
    # 构建 resize 参数
    if percent:
        resize_arg = f"{percent}%"
    elif exact and width and height:
        resize_arg = f"{width}x{height}!"
    elif width and height:
        # 等比缩放，适应指定区域
        resize_arg = f"{width}x{height}>"
    elif width:
        resize_arg = f"{width}x"
    elif height:
        resize_arg = f"x{height}"
    else:
        print("❌ 错误: 请指定宽度、高度或百分比")
        return False
    
    # 执行调整
    success, output, error = run_magick_command([
        str(input_path),
        "-resize", resize_arg,
        str(output_path)
    ])
    
    if success:
        print(f"✅ 调整成功: {input_path} -> {output_path} (尺寸: {resize_arg})")
        return True
    else:
        print(f"❌ 调整失败: {error}")
        return False


def main():
    parser = argparse.ArgumentParser(description='图片尺寸调整工具')
    parser.add_argument('input', help='输入图片路径')
    parser.add_argument('output', help='输出图片路径')
    parser.add_argument('--width', '-w', type=int, help='目标宽度（像素）')
    parser.add_argument('--height', '-ht', type=int, help='目标高度（像素）')
    parser.add_argument('--exact', action='store_true', help='强制指定尺寸（可能变形）')
    parser.add_argument('--percent', '-p', type=int, help='缩放百分比（如 50 表示缩小到 50%）')
    
    args = parser.parse_args()
    
    success = resize_image(
        args.input, 
        args.output, 
        width=args.width, 
        height=args.height, 
        exact=args.exact,
        percent=args.percent
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
