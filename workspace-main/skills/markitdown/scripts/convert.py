#!/usr/bin/env python3
"""MarkItDown 文件转换脚本
将各种格式文档转换为 Markdown。

用法:
    python convert.py <文件路径> [-o <输出文件>] [--keep-urls] [--no-strip-links]
"""

import argparse
import sys
from pathlib import Path

from markitdown import MarkItDown


def main():
    parser = argparse.ArgumentParser(
        description="将文件转换为 Markdown（基于 Microsoft MarkItDown）"
    )
    parser.add_argument("input", type=str, help="输入文件路径或 URL")
    parser.add_argument(
        "-o", "--output", type=str, default=None, help="输出 Markdown 文件路径"
    )
    parser.add_argument(
        "--keep-urls",
        action="store_true",
        default=True,
        help="保留文档中的 URL 链接（默认启用）",
    )
    parser.add_argument(
        "--no-strip-links",
        action="store_true",
        default=False,
        help="不清理链接格式（调试用）",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists() and not args.input.startswith(("http:", "https:")):
        print(f"错误: 文件不存在 - {args.input}")
        sys.exit(1)

    print(f"正在转换: {args.input} ...")
    md = MarkItDown()
    try:
        result = md.convert(args.input)
        text = result.text_content

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(text, encoding="utf-8")
            print(f"已保存到: {output_path.resolve()} ({len(text)} 字符)")
        else:
            print(text)

    except Exception as e:
        print(f"转换失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
