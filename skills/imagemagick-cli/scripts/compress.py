"""
图片压缩工具
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

from utils import run_magick_command, ensure_dir, get_config


def compress_image(input_path, output_path, quality=None):
    """
    压缩图片
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        quality: 压缩质量（1-100）
    
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
    
    # 获取默认质量
    if quality is None:
        config = get_config()
        quality = config.get("default_quality", 90)
    
    # 执行压缩
    success, output, error = run_magick_command([
        str(input_path),
        "-quality", str(quality),
        str(output_path)
    ])
    
    if success:
        # 计算压缩率
        input_size = input_path.stat().st_size
        output_size = output_path.stat().st_size
        ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0
        
        print(f"✅ 压缩成功: {input_path} -> {output_path}")
        print(f"   原大小: {input_size / 1024:.1f} KB")
        print(f"   新大小: {output_size / 1024:.1f} KB")
        print(f"   压缩率: {ratio:.1f}%")
        return True
    else:
        print(f"❌ 压缩失败: {error}")
        return False


def main():
    parser = argparse.ArgumentParser(description='图片压缩工具')
    parser.add_argument('input', help='输入图片路径')
    parser.add_argument('output', help='输出图片路径')
    parser.add_argument('--quality', '-q', type=int, help='压缩质量 1-100（默认 90）')
    
    args = parser.parse_args()
    
    success = compress_image(args.input, args.output, quality=args.quality)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
