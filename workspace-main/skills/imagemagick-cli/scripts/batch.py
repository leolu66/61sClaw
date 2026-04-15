"""
批量图片处理工具
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

from utils import run_magick_command, ensure_dir, get_image_files, get_config


def batch_convert(input_dir, output_dir, target_format, quality=None):
    """批量格式转换"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    ensure_dir(output_dir)
    
    image_files = get_image_files(input_dir)
    if not image_files:
        print(f"⚠️ 未找到图片文件: {input_dir}")
        return False
    
    success_count = 0
    fail_count = 0
    
    for img_path in image_files:
        output_path = output_dir / f"{img_path.stem}.{target_format}"
        
        cmd = [str(img_path)]
        if quality:
            cmd.extend(["-quality", str(quality)])
        cmd.append(str(output_path))
        
        success, _, error = run_magick_command(cmd)
        if success:
            print(f"  ✅ {img_path.name} -> {output_path.name}")
            success_count += 1
        else:
            print(f"  ❌ {img_path.name}: {error}")
            fail_count += 1
    
    print(f"\n完成: {success_count} 成功, {fail_count} 失败")
    return fail_count == 0


def batch_resize(input_dir, output_dir, width=None, height=None, percent=None):
    """批量调整尺寸"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    ensure_dir(output_dir)
    
    image_files = get_image_files(input_dir)
    if not image_files:
        print(f"⚠️ 未找到图片文件: {input_dir}")
        return False
    
    # 构建 resize 参数
    if percent:
        resize_arg = f"{percent}%"
    elif width and height:
        resize_arg = f"{width}x{height}>"
    elif width:
        resize_arg = f"{width}x"
    elif height:
        resize_arg = f"x{height}"
    else:
        print("❌ 错误: 请指定宽度、高度或百分比")
        return False
    
    success_count = 0
    fail_count = 0
    
    for img_path in image_files:
        output_path = output_dir / img_path.name
        
        success, _, error = run_magick_command([
            str(img_path),
            "-resize", resize_arg,
            str(output_path)
        ])
        
        if success:
            print(f"  ✅ {img_path.name}")
            success_count += 1
        else:
            print(f"  ❌ {img_path.name}: {error}")
            fail_count += 1
    
    print(f"\n完成: {success_count} 成功, {fail_count} 失败")
    return fail_count == 0


def batch_compress(input_dir, output_dir, quality):
    """批量压缩"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    ensure_dir(output_dir)
    
    image_files = get_image_files(input_dir)
    if not image_files:
        print(f"⚠️ 未找到图片文件: {input_dir}")
        return False
    
    success_count = 0
    total_saved = 0
    
    for img_path in image_files:
        output_path = output_dir / img_path.name
        
        input_size = img_path.stat().st_size
        
        success, _, error = run_magick_command([
            str(img_path),
            "-quality", str(quality),
            str(output_path)
        ])
        
        if success:
            output_size = output_path.stat().st_size
            saved = input_size - output_size
            total_saved += saved
            ratio = (saved / input_size * 100) if input_size > 0 else 0
            print(f"  ✅ {img_path.name} (节省 {ratio:.1f}%)")
            success_count += 1
        else:
            print(f"  ❌ {img_path.name}: {error}")
    
    print(f"\n完成: {success_count} 张图片")
    print(f"总计节省: {total_saved / 1024:.1f} KB")
    return True


def main():
    parser = argparse.ArgumentParser(description='批量图片处理工具')
    parser.add_argument('--input-dir', '-i', required=True, help='输入目录')
    parser.add_argument('--output-dir', '-o', required=True, help='输出目录')
    
    # 功能选择
    parser.add_argument('--format', '-f', help='目标格式（如 jpg/png/webp）')
    parser.add_argument('--resize', '-r', action='store_true', help='调整尺寸')
    parser.add_argument('--compress', '-c', action='store_true', help='压缩')
    
    # 参数
    parser.add_argument('--width', '-w', type=int, help='目标宽度')
    parser.add_argument('--height', '-ht', type=int, help='目标高度')
    parser.add_argument('--percent', '-p', type=int, help='缩放百分比')
    parser.add_argument('--quality', '-q', type=int, help='压缩质量 1-100')
    
    args = parser.parse_args()
    
    # 检查输入目录
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"❌ 错误: 输入目录不存在: {input_dir}")
        sys.exit(1)
    
    # 执行对应功能
    if args.format:
        print(f"🔄 批量格式转换: {args.format}")
        success = batch_convert(args.input_dir, args.output_dir, args.format, args.quality)
    elif args.resize:
        print(f"🔄 批量调整尺寸")
        success = batch_resize(args.input_dir, args.output_dir, args.width, args.height, args.percent)
    elif args.compress:
        quality = args.quality or get_config().get("default_quality", 90)
        print(f"🔄 批量压缩 (质量: {quality})")
        success = batch_compress(args.input_dir, args.output_dir, quality)
    else:
        print("❌ 错误: 请指定 --format、--resize 或 --compress")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
