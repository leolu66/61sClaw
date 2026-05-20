"""
RSS 新闻深度总结器 - 使用 LLM 生成中文深度总结 + 标题翻译
"""
import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

from .rss_fetcher import RSSItem, _safe_print

logger = logging.getLogger(__name__)

# 默认 API 配置（从 WhaleCloud 代理走 OpenAI 兼容端点）
DEFAULT_API_BASE = os.environ.get(
    "RSS_LLM_BASE_URL",
    "https://lab.iwhalecloud.com/gpt-proxy/v1"
)
DEFAULT_API_KEY = os.environ.get("RSS_LLM_API_KEY", "")
DEFAULT_MODEL = os.environ.get("RSS_LLM_MODEL", "Kimi-K2.5")

# 翻译+总结的 System Prompt（批量模式）
BATCH_TRANSLATE_SUMMARIZE_PROMPT = """你是专业的 AI 科技新闻翻译与编辑。下面是一批英文 AI 科技新闻的标题和内容。

对每篇新闻做两件事：
1. **title_cn**: 将英文标题翻译为准确、简洁的中文标题（保留专有名词原文）
2. **summary_cn**: 用 2-3 句话中文概括文章核心内容，突出技术创新点、关键数据和产业影响

输出格式（严格 JSON 数组，只输出 JSON，不要其他内容）：
[
  {"index": 0, "title_cn": "中文标题", "summary_cn": "中文摘要"},
  {"index": 1, "title_cn": "中文标题", "summary_cn": "中文摘要"}
]"""

# 单篇翻译+总结 Prompt（有原文时使用）
TRANSLATE_SUMMARIZE_PROMPT = """你是专业的 AI 科技新闻翻译与编辑。请处理以下英文 AI 新闻：

1. **中文标题**: 将英文标题翻译为准确、简洁的中文（保留产品名/公司名原文）
2. **中文摘要**: 用 2-3 句话概括核心内容，突出技术创新、关键数据、产业影响

输出格式（严格 2 行，不要任何前缀标记）：
中文标题：<翻译的标题>
中文摘要：<中文摘要>"""

# 纯翻译 Prompt（无原文时，只翻译标题和RSS摘要）
TRANSLATE_ONLY_PROMPT = """你是专业的 AI 科技新闻翻译。请将以下英文 AI 新闻翻译为中文：

输出格式（严格 2 行）：
中文标题：<翻译的标题>
中文摘要：<中文摘要>"""


def _get_openai_client():
    """获取 OpenAI 客户端（延迟导入）"""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("需要安装 openai 库: pip install openai")

    api_key = DEFAULT_API_KEY
    base_url = DEFAULT_API_BASE
    if not api_key:
        # 尝试从 openclaw config 读取 API 配置
        config_path = Path(os.environ.get(
            "OPENCLAW_CONFIG",
            os.path.expanduser("~/.openclaw/openclaw.json")
        ))
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                providers = config.get("models", {}).get("providers", {})
                
                # 优先用 poloapi（原生 OpenAI 兼容）
                poloapi = providers.get("poloapi", {})
                if poloapi.get("apiKey") and poloapi.get("api") == "openai-completions":
                    api_key = poloapi["apiKey"]
                    base_url = poloapi.get("baseUrl", base_url)
                
                # 备选：whalecloud 的 OpenAI 兼容端点
                if not api_key:
                    whalecloud = providers.get("whalecloud", {})
                    whalecloud_key = whalecloud.get("apiKey")
                    if whalecloud_key:
                        # whalecloud 的 OpenAI 兼容端点
                        api_key = whalecloud_key
                        base_url = "https://lab.iwhalecloud.com/gpt-proxy/v1"
            except Exception:
                pass

    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY", "")

    if not api_key:
        logger.warning("未找到 API Key，将跳过 LLM 翻译/总结")
        return None

    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=1,
    )


def _parse_translate_summarize_output(text: str) -> tuple[str, str]:
    """解析单篇翻译+总结的输出"""
    title_cn = ""
    summary_cn = ""
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("中文标题：") or line.startswith("中文标题:"):
            title_cn = line.split("：", 1)[-1].split(":", 1)[-1].strip()
        elif line.startswith("中文摘要：") or line.startswith("中文摘要:"):
            summary_cn = line.split("：", 1)[-1].split(":", 1)[-1].strip()
    return title_cn, summary_cn


async def _translate_summarize_single(
    item: RSSItem,
    client,
    model: str,
) -> RSSItem:
    """翻译+总结单篇文章"""
    has_content = item.content and len(item.content) > 100

    if has_content:
        content = item.content[:5000]
        prompt = TRANSLATE_SUMMARIZE_PROMPT
        user_msg = f"英文标题：{item.title}\n\n文章内容：\n{content}"
        max_tokens = 400
    else:
        prompt = TRANSLATE_ONLY_PROMPT
        user_msg = f"英文标题：{item.title}\n\nRSS摘要：{item.summary[:300]}"
        max_tokens = 300

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content.strip()
        title_cn, summary_cn = _parse_translate_summarize_output(text)

        if title_cn:
            item.title_cn = title_cn
        if summary_cn:
            item.deep_summary = summary_cn
            item.summary_cn = summary_cn
    except Exception as e:
        logger.warning(f"翻译+总结失败 [{item.title[:30]}]: {e}")

    return item


async def _batch_translate_summarize(
    items: List[RSSItem],
    client,
    model: str,
) -> List[RSSItem]:
    """批量翻译+总结（一次 API 调用处理多篇）"""
    # 构建批量输入
    articles = []
    for i, item in enumerate(items):
        if item.content and len(item.content) > 100:
            content = item.content[:3000]
        else:
            content = item.summary[:300]
        articles.append({
            "index": i,
            "title": item.title,
            "content": content,
        })

    articles_json = json.dumps(articles, ensure_ascii=False, indent=2)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": BATCH_TRANSLATE_SUMMARIZE_PROMPT},
                {"role": "user", "content": articles_json},
            ],
            temperature=0.3,
            max_tokens=8192,
        )
        text = response.choices[0].message.content.strip()

        # 解析 JSON 数组
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if json_match:
            results = json.loads(json_match.group())
            for r in results:
                idx = r.get("index", -1)
                if 0 <= idx < len(items):
                    if r.get("title_cn"):
                        items[idx].title_cn = r["title_cn"]
                    if r.get("summary_cn"):
                        items[idx].deep_summary = r["summary_cn"]
                        items[idx].summary_cn = r["summary_cn"]
    except Exception as e:
        logger.warning(f"批量翻译+总结失败: {e}")
        # 回退到逐篇处理
        for item in items:
            await _translate_summarize_single(item, client, model)

    return items


async def translate_and_summarize(
    items: List[RSSItem],
    model: str = DEFAULT_MODEL,
    batch: bool = True,
) -> List[RSSItem]:
    """
    翻译标题 + 生成中文深度总结

    Args:
        items: RSS 条目列表
        model: 模型名称
        batch: 是否使用批量模式（一次 API 调用处理所有）

    Returns:
        带有中文标题和总结的条目列表
    """
    client = _get_openai_client()
    if client is None:
        logger.warning("LLM 客户端不可用，跳过翻译/总结")
        for item in items:
            if not item.deep_summary:
                item.deep_summary = item.summary[:200] if item.summary else ""
        return items

    _safe_print(f"[LLM] 正在使用 {model} 翻译标题并生成深度总结...")

    if batch and len(items) > 1:
        items = await _batch_translate_summarize(items, client, model)
    else:
        sem = asyncio.Semaphore(3)
        async def process(item):
            async with sem:
                return await _translate_summarize_single(item, client, model)
        items = list(await asyncio.gather(*[process(item) for item in items]))

    cn_title_count = sum(1 for item in items if item.title_cn)
    cn_summary_count = sum(1 for item in items if item.summary_cn)
    _safe_print(f"   中文标题: {cn_title_count}/{len(items)} | 中文摘要: {cn_summary_count}/{len(items)}")

    return items


async def summarize_items(items: List[RSSItem]) -> List[RSSItem]:
    """便捷函数：翻译+总结（默认批量模式）"""
    return await translate_and_summarize(items, batch=True)
