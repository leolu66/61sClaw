"""
从 OpenClaw 配置中提取 WhaleCloud API Key 并写入 SlideFlow config.json
"""

import sys
import io
import json
import os
from pathlib import Path

# 强制 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"
SLIDEFLOW_CONFIG = Path(__file__).parent.parent.parent.parent / "repos" / "SlideFlow" / "config" / "config.json"


def main():
    if not OPENCLAW_CONFIG.exists():
        print("❌ OpenClaw config not found")
        return False

    cfg = json.loads(OPENCLAW_CONFIG.read_text(encoding="utf-8"))
    providers = cfg.get("models", {}).get("providers", {})
    wc = providers.get("whalecloud", {})

    api_key = wc.get("apiKey", "")
    base_url = wc.get("baseUrl", "https://lab.iwhalecloud.com/gpt-proxy/anthropic")

    if not api_key:
        print("❌ WhaleCloud API Key not found in OpenClaw config")
        return False

    # WhaleCloud 的 OpenAI 兼容端点
    openai_base_url = "https://lab.iwhalecloud.com/gpt-proxy/v1"

    slideflow_cfg = {
        "api_key": api_key,
        "base_url": openai_base_url,
        "model": "deepseek-v4-pro",
        "emb_api_key": api_key,
        "emb_base_url": openai_base_url,
        "embedding_model": "text-embedding-3-small"
    }

    SLIDEFLOW_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    SLIDEFLOW_CONFIG.write_text(
        json.dumps(slideflow_cfg, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )

    print(f"✅ SlideFlow 已配置为 WhaleCloud DeepSeek V4 Pro")
    print(f"   model:    deepseek-v4-pro")
    print(f"   base_url: {openai_base_url}")
    print(f"   config:   {SLIDEFLOW_CONFIG}")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
