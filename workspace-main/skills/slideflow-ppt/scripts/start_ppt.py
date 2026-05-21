"""
SlideFlow 命令行 PPT 生成工具

一键从主题生成完整 PPT。支持多种模型提供商。

用法:
    # 默认模型（从 config.json 或环境变量读取）
    python scripts/start_ppt.py --topic "人工智能在医疗领域的应用"

    # 指定模型
    python scripts/start_ppt.py --topic "AI in Healthcare" --language en
    python scripts/start_ppt.py --topic "量子计算" --template company_report

    # 指定 LLM 模型（支持 OpenAI 兼容 API）
    python scripts/start_ppt.py --topic "..." --model "deepseek-chat" ^
        --base-url "https://api.deepseek.com/v1" --api-key "sk-xxx"

    python scripts/start_ppt.py --topic "..." --model "glm-4-plus" ^
        --base-url "https://open.bigmodel.cn/api/paas/v4" --api-key "xxx"

    python scripts/start_ppt.py --topic "..." --model "qwen-plus" ^
        --base-url "https://dashscope.aliyuncs.com/compatible-mode/v1" ^
        --api-key "sk-xxx"

    # RAG 知识增强
    python scripts/start_ppt.py --topic "..." --pdf "doc1.pdf" "doc2.pdf"

    # 不联网搜索（纯 LLM 生成）
    python scripts/start_ppt.py --topic "..." --no-search
"""

import os
import sys
import io
import json
import asyncio
import argparse
from pathlib import Path

# Windows UTF-8 编码修复
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SKILL_DIR = Path(__file__).parent.parent
WORKSPACE = SKILL_DIR.parent.parent
PROJECT_DIR = (WORKSPACE / "repos" / "SlideFlow").resolve()
SLIDEFLOW_CONFIG = PROJECT_DIR / "config" / "config.json"

# 将 SlideFlow 项目目录加入 Python 搜索路径
sys.path.insert(0, str(PROJECT_DIR))


def read_slideflow_config() -> dict:
    """读取 SlideFlow 自身的 config.json"""
    if SLIDEFLOW_CONFIG.exists():
        try:
            return json.loads(SLIDEFLOW_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def write_slideflow_config(config: dict):
    """写入 SlideFlow 的 config.json，确保模型配置生效"""
    SLIDEFLOW_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    existing = read_slideflow_config()
    # 合并配置
    for k, v in config.items():
        if v is not None and v != "":
            existing[k] = v
    SLIDEFLOW_CONFIG.write_text(
        json.dumps(existing, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )
    print(f"  ⚙️  模型配置已写入: {SLIDEFLOW_CONFIG}")


async def main():
    parser = argparse.ArgumentParser(description="SlideFlow PPT 生成器")

    parser.add_argument("--topic", "-t", required=True, help="PPT 主题（必填）")
    parser.add_argument("--language", "-l", default="zh", choices=["zh", "en"],
                        help="语言（默认 zh）")
    parser.add_argument("--template", default="company_report",
                        help="视觉模板（默认 company_report）")
    parser.add_argument("--pdf", nargs="*", default=[],
                        help="参考 PDF 文件路径列表（RAG 知识增强）")
    parser.add_argument("--no-search", action="store_true",
                        help="禁用联网搜索")
    parser.add_argument("--model", "-m", default=None,
                        help="模型 ID（如 deepseek-chat, glm-4-plus, qwen-plus 等）")
    parser.add_argument("--base-url", default=None,
                        help="API 地址（如 https://api.deepseek.com/v1）")
    parser.add_argument("--api-key", default=None,
                        help="API Key")

    args = parser.parse_args()

    # ── 模型优先级：cli 参数 > 技能 config.json > 环境变量 > SlideFlow config.json ──

    # 1) 读取技能自身配置
    skill_cfg_path = SKILL_DIR / "scripts" / "config.json"
    skill_cfg = {}
    if skill_cfg_path.exists():
        try:
            skill_cfg = json.loads(skill_cfg_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 2) 确定最终模型参数
    model = args.model or skill_cfg.get("model") or os.environ.get("MODEL_ID") or ""
    base_url = args.base_url or skill_cfg.get("base_url") or os.environ.get("OPENAI_BASE_URL") or ""
    api_key = args.api_key or skill_cfg.get("api_key") or os.environ.get("OPENAI_API_KEY") or ""

    # 3) 写入 SlideFlow config.json（必须在 import 前完成，因为 SlideFlow 在导入时读取配置）
    if api_key or base_url or model:
        write_slideflow_config({
            "api_key": api_key,
            "base_url": base_url,
            "model": model
        })

    # 4) 检查依赖
    try:
        from core.ppt_graph import run_ppt_generation
    except ImportError as e:
        print(f"❌ 导入 SlideFlow 失败: {e}")
        print("请确保已安装依赖：")
        print(f"  pip install -r {PROJECT_DIR / 'requirements.txt'}")
        print(f"  playwright install chromium")
        sys.exit(1)

    if not api_key:
        print("❌ 请设置 API Key：")
        print("   1) --api-key sk-xxx")
        print("   2) 或编辑 scripts/config.json")
        print("   3) 或设置 OPENAI_API_KEY 环境变量")
        sys.exit(1)

    # 校验 PDF 路径
    pdf_paths = []
    for p in args.pdf:
        abs_p = os.path.abspath(p)
        if not os.path.exists(abs_p):
            print(f"⚠️  PDF 文件不存在: {abs_p}")
        else:
            pdf_paths.append(abs_p)

    # 显示模型信息
    model_display = model or "(SlideFlow 默认)"
    base_display = base_url or "https://api.openai.com/v1 (默认)"

    print(f"\n{'='*60}")
    print(f"🎯 主题:     {args.topic}")
    print(f"🤖 模型:     {model_display}")
    print(f"🔗 API 地址: {base_display}")
    print(f"🌐 联网搜索: {'是' if not args.no_search else '否'}")
    print(f"📄 参考文档: {len(pdf_paths)} 个")
    print(f"📋 模板:     {args.template}")
    print(f"{'='*60}\n")

    # 创建输出目录
    task_id = args.topic.replace(" ", "_").replace("/", "_")
    output_dir = PROJECT_DIR / "output" / task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建队列来接收日志
    class PrinterQueue:
        def put(self, msg):
            if isinstance(msg, dict):
                if msg.get("type") == "log":
                    content = msg.get("content", "")
                    print(f"  📝 {content}")
                elif msg.get("type") == "ppt_init":
                    total = msg.get("total", 0)
                    pages = msg.get("pages", [])
                    print(f"\n  📄 计划生成 {total} 页:")
                    for p in pages:
                        icon = {"cover": "📘", "toc": "📋", "chapter": "📂",
                                "content": "📄", "end": "🎯"}.get(p["type"], "📄")
                        print(f"    {icon} [{p['type']}] {p['title']}")
                elif msg.get("type") == "complete":
                    result = msg.get("result", {})
                    print(f"\n  ✅ PPT 生成完成!")
                    print(f"     PPTX: {result.get('pptx_path', 'N/A')}")
                    print(f"     PDF:  {result.get('pdf_path', 'N/A')}")
                elif msg.get("type") == "error":
                    print(f"\n  ❌ 错误: {msg.get('content', '')}")
                elif msg.get("type") == "hd_image":
                    print(f"  🖼️  图片: {msg.get('url', '')[:80]}...")
            else:
                msg_str = str(msg)
                if msg_str not in ("STOP_SIGNAL",):
                    print(f"  {msg_str}")

        def get(self, *args, **kwargs):
            return ""

    log_queue = PrinterQueue()

    try:
        from core.ppt_graph import run_ppt_generation

        result = await run_ppt_generation(
            topic=args.topic,
            template_name=args.template,
            language=args.language,
            log_queue=log_queue,
            pdf_paths=pdf_paths,
            enable_search=not args.no_search,
            task_id=task_id
        )

        if result:
            pptx = result.get("pptx_path", "")
            pdf = result.get("pdf_path", "")
            print(f"\n{'='*60}")
            print(f"✅ 生成完成!")
            if pptx:
                print(f"  PPTX: {pptx}")
            if pdf:
                print(f"  PDF:  {pdf}")
            print(f"{'='*60}")

    except KeyboardInterrupt:
        print("\n\n⏹️  已取消")
    except Exception as e:
        import traceback
        print(f"\n❌ 生成失败: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
