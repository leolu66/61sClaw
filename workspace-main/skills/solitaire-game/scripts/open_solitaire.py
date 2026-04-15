import os
import webbrowser

def open_solitaire():
    """打开纸牌接龙游戏"""
    html_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'solitaire.html')
    html_path = os.path.abspath(html_path)
    
    # 使用 file:// 协议打开本地 HTML 文件
    url = f'file:///{html_path.replace(chr(92), "/")}'
    webbrowser.open(url)
    print(f"纸牌接龙游戏已启动: {url}")

if __name__ == '__main__':
    open_solitaire()
