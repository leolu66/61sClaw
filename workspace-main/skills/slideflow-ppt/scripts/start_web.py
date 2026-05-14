"""
启动 SlideFlow Web Dashboard

用法:
    python scripts/start_web.py            # 默认端口 5001
    python scripts/start_web.py -p 8080    # 指定端口
"""

import os
import sys
import argparse
import subprocess

# 获取项目根目录
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(SKILL_DIR, "..", "..", "repos", "SlideFlow")
PROJECT_DIR = os.path.abspath(PROJECT_DIR)


def main():
    parser = argparse.ArgumentParser(description="启动 SlideFlow Web Dashboard")
    parser.add_argument("-p", "--port", type=int, default=5001, help="端口号（默认 5001）")
    args = parser.parse_args()

    if not os.path.exists(PROJECT_DIR):
        print(f"❌ SlideFlow 项目不存在: {PROJECT_DIR}")
        print("请先使用 `git clone` 下载项目到 repos/SlideFlow/")
        sys.exit(1)

    main_py = os.path.join(PROJECT_DIR, "main.py")
    if not os.path.exists(main_py):
        print(f"❌ main.py 不存在: {main_py}")
        sys.exit(1)

    print(f"🚀 启动 SlideFlow Web Dashboard...")
    print(f"📂 项目路径: {PROJECT_DIR}")
    print(f"🌐 访问地址: http://localhost:{args.port}")
    print()

    env = os.environ.copy()
    env["FLASK_PORT"] = str(args.port)

    try:
        subprocess.run(
            [sys.executable, main_py],
            cwd=PROJECT_DIR,
            env=env
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
