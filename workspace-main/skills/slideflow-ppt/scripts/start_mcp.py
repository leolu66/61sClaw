"""
启动 SlideFlow MCP Server

使 SlideFlow 可通过 MCP 协议被 Claude Desktop 等 Agent 调用。

用法:
    python scripts/start_mcp.py
"""

import os
import sys
import subprocess

# 获取项目根目录
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(SKILL_DIR, "..", "..", "repos", "SlideFlow")
PROJECT_DIR = os.path.abspath(PROJECT_DIR)


def main():
    if not os.path.exists(PROJECT_DIR):
        print(f"❌ SlideFlow 项目不存在: {PROJECT_DIR}")
        print("请先使用 `git clone` 下载项目到 repos/SlideFlow/")
        sys.exit(1)

    mcp_py = os.path.join(PROJECT_DIR, "mcp_server.py")
    if not os.path.exists(mcp_py):
        print(f"❌ mcp_server.py 不存在: {mcp_py}")
        sys.exit(1)

    print(f"🚀 启动 SlideFlow MCP Server...")
    print(f"📂 项目路径: {PROJECT_DIR}")
    print()
    print("将以下配置添加到 Claude Desktop 的 claude_desktop_config.json:")
    print()
    print(f'''  {{
    "mcpServers": {{
      "slideflow": {{
        "command": "{sys.executable}",
        "args": ["{mcp_py}"]
      }}
    }}
  }}''')
    print()
    print("按 Ctrl+C 停止...")
    print()

    try:
        subprocess.run(
            [sys.executable, mcp_py],
            cwd=PROJECT_DIR
        )
    except KeyboardInterrupt:
        print("\n👋 MCP Server 已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
