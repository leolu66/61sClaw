"""
AI新闻智能分析器 - 批量分类 + 重要度评分 + Top N 筛选
"""
import asyncio
import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# 分类体系
CATEGORIES = [
    "基础模型",      # 大模型发布、训练技术、架构创新
    "平台与工具",    # 开发平台、IDE、API、云服务
    "Agent产品",     # AI Agent、智能体应用
    "具身智能",      # 机器人、自动驾驶、无人机
    "AI硬件",        # 芯片、眼镜、穿戴设备
    "AI+科研",       # AI for Science、药物发现
    "AI+医疗",       # 医疗AI、病历、诊断
    "AI+金融",       # 金融AI、投顾、风控
    "AI+安全",       # 网络安全、内容安全、对抗攻击
    "AI+设计/创作",  # AI设计、AI绘画、AI视频
    "投融资",        # 融资、IPO、收购
    "政策监管",      # 法规、政策、标准、伦理
    "大厂战略",      # 组织调整、战略转向、人事变动
    "行业落地",      # 垂直行业应用案例
    "开源生态",      # 开源模型、开源工具、社区
]

# 重要性评分关键词
HIGH_PRIORITY_COMPANIES = [
    "OpenAI", "Google", "谷歌", "Anthropic", "Meta", "Microsoft", "微软",
    "Apple", "苹果", "Amazon", "亚马逊", "字节跳动", "ByteDance", "腾讯",
    "百度", "阿里", "华为", "NVIDIA", "英伟达", "DeepSeek", "Tesla", "特斯拉",
    "智谱", "百川", "月之暗面", "零一", "MiniMax",
]

HIGH_PRIORITY_PEOPLE = [
    "Sam Altman", "奥特曼", "Demis Hassabis", "Dario Amodei",
    "李飞飞", "杨立昆", "Yann LeCun", "卡帕西", "Karpathy",
    "黄仁勋", "Jensen Huang", "马斯克", "Elon Musk", "扎克伯格",
    "Satya Nadella", "纳德拉", "李彦宏", "马化腾", "任正非",
    "Greg Brockman", "Ilya Sutskever",
]

HIGH_PRIORITY_KEYWORDS = [
    "发布", "推出", "发布新", "首次", "突破", "融资.*亿",
    "IPO", "上市", "收购", "重组", "开源", "Nature", "Science",
    "CVPR", "ICML", "NeurIPS", "ACL", "最佳论文", "Best Paper",
    "政策", "监管", "禁令", "法规", "标准",
    "AGI", "GPT-5", "Claude 4", "Gemini 3", "GPT-4",
    "万亿", "千亿",
]

@dataclass
class AnalyzedItem:
    title: str
    url: str
    source: str
    date: str
    categories: List[str] = field(default_factory=list)
    importance: int = 0          # 1-5
    reason: str = ""             # 重要性理由
    is_original: bool = True     # 是否去重后保留

    def __hash__(self):
        return hash(self.url)


def deduplicate_titles(items: List[dict]) -> List[dict]:
    """URL去重，同URL保留最早出现的"""
    seen = set()
    result = []
    for item in items:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            result.append(item)
    return result


def load_titles_from_file(filepath: str) -> List[dict]:
    """从 Markdown 标题列表文件加载"""
    items = []
    current_source = ""
    current_date = ""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('## '):
                # 清理来源名中的 emoji
                current_source = re.sub(r'[^\w\u4e00-\u9fff\s\-\.]', '', line[3:]).strip()
            # 匹配 - [20260520] [Title](url)
            match = re.match(r'- \[(\d{8})\] \[(.+?)\]\((.+?)\)', line)
            if match:
                current_date = match.group(1)
                title = match.group(2)
                url = match.group(3)
                items.append({
                    "title": title,
                    "url": url,
                    "source": current_source,
                    "date": current_date,
                })
    return items


def build_analysis_prompt(items: List[dict]) -> str:
    """构建批量分析 prompt（精简版）"""
    titles_text = []
    for i, item in enumerate(items):
        titles_text.append(f"{i}|[{item['title']}]|[+{item['source']}]")
    
    prompt = f"""你是AI新闻分析师。对下面 {len(items)} 条新闻标题进行分析。

分类标签（选1-3个）: {", ".join(CATEGORIES)}

重要度1-5分:
5=头部厂商重大发布/亿级融资IPO/NatureScience论文/国家政策/CEO变动
4=大厂战略/重要产品/5000万+融资/顶会论文/技术突破
3=新产品功能/千万融资/重要合作/标杆案例
2=行业动态/中小融资/观点
1=资讯汇总

输出JSON数组:
[{{"i":0,"c":["基础模型"],"s":5,"r":"理由"}},...]
(i=序号,c=categories,s=score,r=reason)

新闻列表:
{chr(10).join(titles_text)}"""
    return prompt


def _get_llm_client():
    """获取 LLM 客户端"""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("需要安装 openai")

    config_path = Path(os.environ.get(
        "OPENCLAW_CONFIG", os.path.expanduser("~/.openclaw/openclaw.json")
    ))
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = "https://api.openai.com/v1"

    if config_path.exists() and not api_key:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            providers = config.get("models", {}).get("providers", {})
            # 优先 whalecloud（更快更稳定）
            whale = providers.get("whalecloud", {})
            if whale.get("apiKey"):
                api_key = whale["apiKey"]
                base_url = "https://lab.iwhalecloud.com/gpt-proxy/v1"
            if not api_key:
                poloapi = providers.get("poloapi", {})
                if poloapi.get("apiKey"):
                    api_key = poloapi["apiKey"]
                    base_url = poloapi.get("baseUrl", base_url)
        except Exception:
            pass

    if not api_key:
        raise RuntimeError("未找到 API Key")

    return AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=180.0)


async def analyze_titles(items: List[dict], batch_size: int = 300) -> List[dict]:
    """批量分析标题：分类 + 评分"""
    client = _get_llm_client()
    
    all_results = []
    # 分批处理
    for batch_start in range(0, len(items), batch_size):
        batch = items[batch_start:batch_start + batch_size]
        prompt = build_analysis_prompt(batch)
        
        print(f"  分析批次 {batch_start//batch_size + 1}: {len(batch)} 条...", end=" ", flush=True)
        
        try:
            response = await client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[
                    {"role": "system", "content": "你是一个专业的AI新闻分析师。请严格按照JSON格式输出。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=16384,
            )
            text = response.choices[0].message.content.strip()
            
            # 解析 JSON (兼容精简格式 i/c/s/r 和完整格式)
            json_match = re.search(r"\[.*\]", text, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
                for r in results:
                    idx = r.get("i", r.get("index", -1))
                    if 0 <= idx < len(batch):
                        batch[idx]["categories"] = r.get("c", r.get("categories", []))
                        batch[idx]["importance"] = int(r.get("s", r.get("importance", 2)))
                        batch[idx]["reason"] = r.get("r", r.get("reason", ""))
                all_results.extend(batch)
                print(f"✅")
            else:
                print(f"❌ JSON解析失败")
                all_results.extend(batch)
        except Exception as e:
            print(f"❌ {e}")
            all_results.extend(batch)
    
    return all_results


def generate_report(items: List[dict], output_path: str):
    """生成分析报告"""
    # 按重要度排序
    items.sort(key=lambda x: x.get("importance", 0), reverse=True)
    total = len(items)
    
    top10_count = max(1, int(total * 0.1))
    top20_count = max(1, int(total * 0.2))
    
    top10 = items[:top10_count]
    top20 = items[:top20_count]
    
    # 统计分类分布
    from collections import Counter
    cat_counter = Counter()
    for item in items:
        for cat in item.get("categories", []):
            cat_counter[cat] += 1
    
    imp_counter = Counter()
    for item in items:
        imp_counter[item.get("importance", 0)] += 1
    
    lines = []
    lines.append(f"# 📊 AI 新闻智能分析报告")
    lines.append(f"")
    lines.append(f"> 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> 覆盖范围: 2026/04/26 - 2026/05/20")
    lines.append(f"> 分析条数: {total} 条（已去重）")
    lines.append(f"")
    
    # 分类分布
    lines.append(f"## 📂 分类分布")
    lines.append(f"")
    lines.append(f"| 分类 | 数量 |")
    lines.append(f"|------|------|")
    for cat, count in cat_counter.most_common():
        lines.append(f"| {cat} | {count} |")
    lines.append(f"")
    
    # 重要度分布
    lines.append(f"## ⭐ 重要度分布")
    lines.append(f"")
    lines.append(f"| 重要度 | 数量 | 占比 |")
    lines.append(f"|--------|------|------|")
    for level in [5, 4, 3, 2, 1]:
        count = imp_counter.get(level, 0)
        lines.append(f"| {'⭐'*level} ({level}分) | {count} | {count/total*100:.1f}% |")
    lines.append(f"")
    
    # Top 10% 最重要新闻
    lines.append(f"## 🔥 Top 10% 最重要新闻 ({top10_count}条)")
    lines.append(f"")
    for i, item in enumerate(top10, 1):
        title = item.get("title", "")
        url = item.get("url", "")
        source = item.get("source", "")
        date = item.get("date", "")[:4] + "/" + item.get("date", "")[4:6] + "/" + item.get("date", "")[6:]
        cats = " · ".join(item.get("categories", []))
        imp = "⭐" * item.get("importance", 1)
        reason = item.get("reason", "")
        lines.append(f"### {i}. [{title}]({url})")
        lines.append(f"")
        lines.append(f"| 属性 | 值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 重要度 | {imp} ({item.get('importance', 0)}分) |")
        lines.append(f"| 分类 | {cats} |")
        lines.append(f"| 来源 | {source} |")
        lines.append(f"| 日期 | {date} |")
        if reason:
            lines.append(f"| 评分理由 | {reason} |")
        lines.append(f"")
        lines.append(f"> {item.get('reason', '')}")
        lines.append(f"")
    
    # Top 20% 新闻（表格简版）
    lines.append(f"## 📋 Top 20% 重要新闻 ({top20_count}条)")
    lines.append(f"")
    lines.append(f"| # | 重要度 | 标题 | 来源 | 分类 |")
    lines.append(f"|---|--------|------|------|------|")
    for i, item in enumerate(top20, 1):
        title = item.get("title", "")[:60]
        url = item.get("url", "")
        source = item.get("source", "")
        cats = " · ".join(item.get("categories", [])[:2])
        imp = "⭐" * item.get("importance", 1)
        lines.append(f"| {i} | {imp} | [{title}]({url}) | {source} | {cats} |")
    lines.append(f"")
    
    # 按分类汇总 Top
    lines.append(f"## 🏷️ 各分类 Top 新闻")
    lines.append(f"")
    for cat, _ in cat_counter.most_common():
        cat_items = [item for item in items if cat in item.get("categories", [])]
        cat_items.sort(key=lambda x: x.get("importance", 0), reverse=True)
        top3 = cat_items[:3]
        lines.append(f"### {cat} (共{len(cat_items)}条)")
        lines.append(f"")
        for item in top3:
            title = item.get("title", "")[:80]
            url = item.get("url", "")
            lines.append(f"- **[{title}]({url})** ⭐{item.get('importance', 0)}")
        lines.append(f"")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return top10, top20


async def main():
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    base_dir = Path(__file__).parent
    title_file = base_dir / "output" / "title_list_20260426_20260520.md"
    
    print("=" * 60)
    print("  AI 新闻智能分析器")
    print("=" * 60)
    print()
    
    # 1. 加载标题
    print("📖 加载标题...")
    raw_items = load_titles_from_file(str(title_file))
    print(f"   原始标题: {len(raw_items)} 条")
    
    # 2. 去重
    items = deduplicate_titles(raw_items)
    print(f"   去重后: {len(items)} 条")
    print()
    
    # 3. LLM 分析
    print("🤖 批量分析分类与重要度评分...")
    items = await analyze_titles(items, batch_size=100)
    print()
    
    # 4. 生成报告
    print("📊 生成报告...")
    report_path = base_dir / "output" / "analysis_report.md"
    top10, top20 = generate_report(items, str(report_path))
    
    # 同时输出简洁版 Top 10
    brief_path = base_dir / "output" / "top10_brief.md"
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(f"# 🔥 Top 10% 最重要 AI 新闻\n\n")
        for i, item in enumerate(top10, 1):
            imp = "⭐" * item.get("importance", 1)
            cats = " · ".join(item.get("categories", []))
            f.write(f"## {i}. [{item['title']}]({item['url']})\n\n")
            f.write(f"> {imp} | {cats} | {item.get('source','')} | {item.get('reason','')}\n\n")
    
    print(f"   ✅ 完整报告: {report_path}")
    print(f"   ✅ 简洁版: {brief_path}")
    print()
    print(f"   Top 10%: {len(top10)} 条 (4-5分)")
    print(f"   Top 20%: {len(top20)} 条 (3-5分)")
    print()

if __name__ == "__main__":
    asyncio.run(main())
