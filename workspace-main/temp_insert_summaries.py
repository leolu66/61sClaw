import re

path = r'C:\Users\luzhe\.openclaw\workspace-main\agfiles\transcript_ppRvzPXGpEw.md'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define summaries for each chapter
summaries = {
    '00:00 硅谷新风尚：烧Token成为衡量AI原生的新指标': '> 硅谷掀起Token-maxxing风潮，每天烧多少token成了新的攀比指标。Meta内部排行榜曝光：8.5万名员工一个月烧了60万亿token，价值约9亿美元。',
    '01:26 Token-maxxing之辩：用得越多就越好吗？': '> 支持派（Writer/Uber）认为不全力拥抱AI就会被淘汰，反对派（HubSpot/Jellyfish）认为结果比消耗量更重要。但共识正在形成：不充分利用AI的公司会被超越。创业者面临token成本焦虑，SaaS成本结构被彻底改写。',
    '05:38 拆解Token账单：大模型公司到底怎么算钱？': '> 深度拆解token定价：Input/Cached/Output三种价格约为1:0.1:6。一个反直觉的悖论——越贵的模型反而总成本可能越低，因为强模型一次做对，弱模型反复重试。云厂商在模型价格上加收封装费和基础设施溢价。',
    '12:32 中国模型登顶token调用排行榜：如何做到超高性价比？': '> 中国开源模型凭借极致性价比杀入全球市场，中美模型价差可达50-70倍。MiniMax M2.5 vs Claude Opus 4.6：性能差距不到1%，价格仅为1/17。背后原因：深度MoE技术、补贴生态、云厂商高利润率。',
    '16:33 OpenRouter：从NFT到AI的\u201c货架之王\u201d': '> OpenRouter创始人从OpenSea转型，做统一API入口抽成5%，估值13亿美元。OpenClaw爆发成为催化剂。但数据只能代表创业公司和独立开发者，不是全行业全景图。',
    '19:31 Metronome：谁在给token\u201c装电表\u201d？': '> Metronome解决AI计费难题：把\u201c发生了什么\u201d和\u201c该怎么收费\u201d拆成四层架构。客户包括OpenAI/NVIDIA/Anthropic。100人团队被Stripe收购，说明\u201c算账\u201d本身就是一个大生意。',
    '22:31 Token套利：当\u201c中间商\u201d开始赚差价': '> Token套利：用便宜模型执行，贵模型把关。智能路由器自动判断任务复杂度并分配模型，用户感知不到切换。Anthropic已内置Advisor模式，但跨模型调度空间远未穷尽。',
    '29:22 中国token出海：结构性的产业机会？': '> \u201c电力不出境，但电的价值出去了\u201d。伦敦程序员调用贵州GPU，token完成跨境结算。中国特高压+光伏板 vs 美国配电瓶颈。MiniMax海外收入超七成，token需求天花板远未到来。',
}

# Step 1: For each chapter title that is inline (not at start of line),
# insert a newline before it so it becomes its own line
# We process from end to start to preserve positions
positions = []
for m in re.finditer(r'## (\d{2}:\d{2} .+)', content):
    pos = m.start()
    # Check if this is already at the start of a line
    if pos > 0 and content[pos-1] != '\n':
        positions.append(pos)

# Process from end to maintain positions
for pos in reversed(positions):
    content = content[:pos] + '\n' + content[pos:]

# Step 2: Now find all chapter headings (they should all be at line start now)
# and insert summaries after them
lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    new_lines.append(lines[i])
    # Check if this line is a chapter title
    m = re.match(r'^## (\d{2}:\d{2} .+)$', lines[i])
    if m:
        title = m.group(1)
        if title in summaries:
            new_lines.append(summaries[title])
    i += 1

new_content = '\n'.join(new_lines)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done!')

# Verify: count how many summaries were inserted
summary_count = new_content.count('\n> ')
print(f'Total summaries inserted: {summary_count}')
