"""
ImageMagick CLI 工具公共函数
"""
import json
import subprocess
import sys
from pathlib import Path

# 修复 Windows 控制台编码（仅在直接运行时）
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass


def get_config():
    """读取配置文件"""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "imagemagick_path": "D:\\Program Files\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe",
        "default_quality": 90,
        "default_format": "jpg"
    }


def get_magick_path():
    """获取 ImageMagick 可执行文件路径"""
    config = get_config()
    magick_path = config.get("imagemagick_path", "magick")
    
    # 检查文件是否存在
    if not Path(magick_path).exists():
        # 尝试使用命令名（如果在 PATH 中）
        return "magick"
    return magick_path


def run_magick_command(args):
    """
    执行 ImageMagick 命令
    
    Args:
        args: 命令参数列表
    
    Returns:
        (success: bool, output: str, error: str)
    """
    magick_path = get_magick_path()
    cmd = [magick_path] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0:
            return True, result.stdout, ""
        else:
            return False, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def ensure_dir(path):
    """确保目录存在，不存在则创建"""
    Path(path).mkdir(parents=True, exist_ok=True)


def is_image_file(filepath):
    """检查文件是否为图片"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.ico'}
    return Path(filepath).suffix.lower() in image_extensions


def get_image_files(directory):
    """获取目录中的所有图片文件"""
    directory = Path(directory)
    if not directory.exists():
        return []
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    files = []
    for ext in image_extensions:
        files.extend(directory.glob(f"*{ext}"))
        files.extend(directory.glob(f"*{ext.upper()}"))
    
    return sorted(set(files))
