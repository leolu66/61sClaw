#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书云盘文件上传工具
支持自动分类上传
"""

import os
import sys
import io
import json
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 文件类型分类映射
FILE_CATEGORIES = {
    'src': {
        'exts': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php',
                 '.html', '.htm', '.css', '.scss', '.sass', '.less', '.jsx', '.tsx', '.vue', '.svelte',
                 '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.conf', '.cfg',
                 '.sql', '.sh', '.bash', '.zsh', '.bat', '.cmd', '.ps1', '.psm1', '.psd1',
                 '.swift', '.kt', '.kts', '.scala', '.groovy', '.dart', '.lua', '.r', '.m', '.mm'],
        'desc': '源代码文件'
    },
    'videos': {
        'exts': ['.mp4', '.avi', '.mov', '.qt', '.wmv', '.flv', '.f4v', '.mkv', '.webm', '.m4v', 
                 '.3gp', '.3g2', '.mpg', '.mpeg', '.mpe', '.mpv', '.m2v', '.ts', '.mts', '.m2ts',
                 '.vob', '.ogv', '.ogx', '.divx', '.xvid', '.rm', '.rmvb', '.asf', '.dv', '.mxf'],
        'desc': '视频文件'
    },
    'recordings': {
        'exts': ['.mp3', '.wav', '.wave', '.wma', '.aac', '.m4a', '.m4p', '.m4b', '.ogg', '.oga',
                 '.flac', '.alac', '.aiff', '.au', '.snd', '.pcm', '.raw', '.opus', '.weba',
                 '.amr', '.awb', '.gsm', '.dss', '.msv', '.dvf', '.oma', '.at3', '.aa3'],
        'desc': '录音/音频文件'
    },
    'images': {
        'exts': ['.jpg', '.jpeg', '.jpe', '.jfif', '.png', '.gif', '.bmp', '.dib', '.webp', '.svg',
                 '.svgz', '.ico', '.cur', '.tiff', '.tif', '.raw', '.arw', '.cr2', '.nef', '.orf',
                 '.raf', '.pef', '.dng', '.x3f', '.sr2', '.k25', '.heic', '.heif', '.avif', '.apng',
                 '.exr', '.hdr', '.pcx', '.tga', '.icb', '.vda', '.vst', '.ppm', '.pgm', '.pbm',
                 '.pnm', '.xpm', '.xbm', '.wbmp', '.psd', '.ai', '.eps', '.ps'],
        'desc': '图片文件'
    },
    'documents': {
        'exts': ['.doc', '.docx', '.dot', '.dotx', '.docm', '.dotm',
                 '.xls', '.xlsx', '.xlsm', '.xlsb', '.xltx', '.xltm', '.xlam',
                 '.ppt', '.pptx', '.pps', '.ppsx', '.pot', '.potx', '.pptm', '.ppsm', '.potm',
                 '.pdf', '.epub', '.mobi', '.azw', '.azw3',
                 '.txt', '.text', '.md', '.markdown', '.mdown', '.mkd', '.mkdn',
                 '.rtf', '.csv', '.tsv', '.tab',
                 '.odt', '.ods', '.odp', '.odg', '.odf', '.odb', '.odc', '.odm',
                 '.pages', '.numbers', '.key', '.keynote',
                 '.tex', '.ltx', '.latex', '.bib', '.bst',
                 '.wpd', '.wp', '.sdw', '.sgl', '.smf', '.sdc', '.sdd', '.sdp'],
        'desc': '文档文件'
    },
    'appdatas': {
        'exts': ['.db', '.sqlite', '.sqlite3', '.db3', '.s3db', '.sl3',
                 '.log', '.logs', '.trace',
                 '.cache', '.tmp', '.temp', '.swap', '.swp', '.swo',
                 '.config', '.conf', '.cfg', '.settings', '.prefs', '.properties',
                 '.env', '.envrc', '.env.local', '.env.development', '.env.production',
                 '.pid', '.lock', '.sock', '.socket',
                 '.dat', '.data', '.bin', '.idx', '.index', '.manifest', '.pak',
                 '.pak', '.vpk', '.wad', '.bsp', '.gcf', '.ncf', '.vtf', '.vmt'],
        'desc': '应用数据/配置文件'
    }
}

# 临时文件扩展名（优先级最低）
TEMP_EXTS = ['.tmp', '.temp', '.cache', '.swp', '.swo', '.bak', '.backup', '.old', '.orig', '.rej']


def get_file_category(file_path: str) -> str:
    """
    根据文件扩展名判断分类
    
    Args:
        file_path: 文件路径
        
    Returns:
        分类名称: src/videos/recordings/images/documents/appdatas/temp
    """
    ext = Path(file_path).suffix.lower()
    
    # 检查是否为临时文件
    if ext in TEMP_EXTS:
        return 'temp'
    
    # 按优先级检查分类
    for category, info in FILE_CATEGORIES.items():
        if ext in info['exts']:
            return category
    
    # 默认分类
    return 'temp'


def scan_directory(directory: str) -> Dict[str, List[str]]:
    """
    扫描目录，按分类整理文件
    
    Args:
        directory: 要扫描的目录路径
        
    Returns:
        分类到文件列表的映射
    """
    categorized = {cat: [] for cat in list(FILE_CATEGORIES.keys()) + ['temp']}
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            category = get_file_category(file_path)
            categorized[category].append(file_path)
    
    return categorized


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def print_scan_result(categorized: Dict[str, List[str]]) -> None:
    """打印扫描结果"""
    print("\n[文件扫描结果]")
    print("=" * 60)
    
    total_files = 0
    total_size = 0
    
    for category, files in categorized.items():
        if not files:
            continue
            
        cat_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
        total_files += len(files)
        total_size += cat_size
        
        cat_info = FILE_CATEGORIES.get(category, {'desc': '临时文件'})
        print(f"\n[{category}/] - {cat_info['desc']}")
        print(f"   文件数: {len(files)}, 大小: {format_size(cat_size)}")
        
        # 显示前5个文件
        for i, f in enumerate(files[:5]):
            fname = os.path.basename(f)
            fsize = format_size(os.path.getsize(f)) if os.path.exists(f) else "未知"
            print(f"   - {fname} ({fsize})")
        
        if len(files) > 5:
            print(f"   ... 还有 {len(files) - 5} 个文件")
    
    print("\n" + "=" * 60)
    print(f"总计: {total_files} 个文件, {format_size(total_size)}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python feishu_uploader.py <目录路径>")
        print("示例: python feishu_uploader.py E:\\feishudoc")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    if not os.path.isdir(directory):
        print(f"错误: 目录不存在 - {directory}")
        sys.exit(1)
    
    print(f"[正在扫描目录] {directory}")
    categorized = scan_directory(directory)
    print_scan_result(categorized)
    
    # 输出 JSON 格式的分类结果（供后续上传使用）
    result = {
        'source_dir': directory,
        'categories': {}
    }
    
    for category, files in categorized.items():
        if files:
            result['categories'][category] = [
                {
                    'path': f,
                    'name': os.path.basename(f),
                    'size': os.path.getsize(f) if os.path.exists(f) else 0
                }
                for f in files
            ]
    
    # 保存结果到临时文件
    output_file = os.path.join(os.path.dirname(__file__), 'scan_result.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n[扫描结果已保存] {output_file}")
    print("\n下一步: 使用飞书 API 上传文件到对应文件夹")


if __name__ == '__main__':
    main()
