import sys
import os

def main():
    """打开五子棋游戏页面"""
    # 使用相对路径，基于脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 游戏文件在技能目录下（scripts 的父目录）
    gobang_path = os.path.abspath(os.path.join(script_dir, "..", "gobang.html"))
    
    # 确保文件存在
    if not os.path.exists(gobang_path):
        print(f"错误：游戏文件不存在：{gobang_path}")
        print("请确认 gobang.html 在 skills/gobang-game/目录下")
        sys.exit(1)
    
    try:
        # 使用 explorer 打开，强制在新标签页中打开
        os.system(f'start "" "{gobang_path}"')
        print("五子棋游戏已启动!")
        print("")
        print("游戏说明:")
        print("  - 选择棋盘大小 (11x11/15x15/19x19)")
        print("  - 选择游戏模式 (双人对战/人机对战)")
        print("  - 黑棋先行，点击棋盘落子")
        print("  - 五子连珠即可获胜!")
        print("  - 人机模式：玩家赢放烟花，AI 赢机器人跳舞!")
    except Exception as e:
        print(f"启动失败：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
