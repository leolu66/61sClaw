"""
Token 计算器 - 计算文本的 token 数量
支持多种编码器：cl100k_base (GPT-4/3.5), p50k_base (GPT-3), 等
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


def get_tokenizer(encoding_name='cl100k_base'):
    """获取 tokenizer"""
    try:
        import tiktoken
        return tiktoken.get_encoding(encoding_name)
    except ImportError:
        print("❌ 错误: 未安装 tiktoken，请先运行: pip install tiktoken")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: 无法加载编码器 '{encoding_name}': {e}")
        sys.exit(1)


def count_tokens(text, encoding_name='cl100k_base'):
    """
    计算文本的 token 数量
    
    Args:
        text: 输入文本
        encoding_name: 编码器名称
    
    Returns:
        int: token 数量
    """
    tokenizer = get_tokenizer(encoding_name)
    tokens = tokenizer.encode(text)
    return len(tokens)


def count_tokens_from_file(file_path, encoding_name='cl100k_base'):
    """从文件计算 token 数量"""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ 错误: 文件不存在: {file_path}")
        return None
    
    try:
        text = file_path.read_text(encoding='utf-8')
        return count_tokens(text, encoding_name)
    except Exception as e:
        print(f"❌ 错误: 无法读取文件: {e}")
        return None


def show_tokens(text, encoding_name='cl100k_base', max_display=20):
    """显示 token 详情"""
    tokenizer = get_tokenizer(encoding_name)
    tokens = tokenizer.encode(text)
    
    print(f"\n📊 Token 统计结果")
    print(f"{'='*40}")
    print(f"编码器: {encoding_name}")
    print(f"总 Token 数: {len(tokens)}")
    print(f"字符数: {len(text)}")
    print(f"平均每个 Token 字符数: {len(text)/len(tokens):.1f}" if tokens else "N/A")
    
    if max_display > 0 and len(tokens) > 0:
        print(f"\n前 {min(max_display, len(tokens))} 个 Token:")
        for i, token in enumerate(tokens[:max_display]):
            try:
                decoded = tokenizer.decode([token])
                print(f"  [{i+1:3d}] {token:6d} -> '{decoded}'")
            except:
                print(f"  [{i+1:3d}] {token:6d} -> <无法解码>")
        
        if len(tokens) > max_display:
            print(f"  ... 还有 {len(tokens) - max_display} 个 token")
    
    print(f"{'='*40}")
    return len(tokens)


def list_encodings():
    """列出可用的编码器"""
    try:
        import tiktoken
        print("\n📋 可用的编码器:")
        print(f"{'='*40}")
        encodings = [
            ('cl100k_base', 'GPT-4, GPT-3.5-turbo, text-embedding-ada-002'),
            ('p50k_base', 'GPT-3 (text-davinci-003, text-davinci-002)'),
            ('p50k_edit', 'GPT-3 编辑模型'),
            ('r50k_base', 'GPT-3 (text-davinci-001)'),
            ('gpt2', 'GPT-2'),
        ]
        for name, desc in encodings:
            print(f"  {name:15s} - {desc}")
        print(f"{'='*40}")
    except ImportError:
        print("❌ 错误: 未安装 tiktoken")


def main():
    parser = argparse.ArgumentParser(
        description='Token 计算器 - 计算文本的 token 数量',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python count_tokens.py -t "Hello World"
  python count_tokens.py -f document.txt
  python count_tokens.py -f document.txt -e cl100k_base --detail
  echo "Hello" | python count_tokens.py --stdin
        """
    )
    
    parser.add_argument('-t', '--text', help='直接输入文本')
    parser.add_argument('-f', '--file', help='从文件读取文本')
    parser.add_argument('--stdin', action='store_true', help='从标准输入读取')
    parser.add_argument('-e', '--encoding', default='cl100k_base', 
                        help='编码器名称 (默认: cl100k_base)')
    parser.add_argument('--detail', '-d', action='store_true', 
                        help='显示详细的 token 分解')
    parser.add_argument('--list', '-l', action='store_true', 
                        help='列出可用的编码器')
    
    args = parser.parse_args()
    
    # 列出编码器
    if args.list:
        list_encodings()
        sys.exit(0)
    
    # 获取输入文本
    text = None
    if args.text:
        text = args.text
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ 错误: 文件不存在: {file_path}")
            sys.exit(1)
        text = file_path.read_text(encoding='utf-8')
    elif args.stdin:
        text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)
    
    # 计算并显示结果
    if args.detail:
        count = show_tokens(text, args.encoding)
    else:
        count = count_tokens(text, args.encoding)
        print(f"Token 数量: {count}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
