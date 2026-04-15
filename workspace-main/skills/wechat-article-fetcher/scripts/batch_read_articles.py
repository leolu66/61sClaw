#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量读取微信公众号文章并保存为 Markdown
"""

import json
import sys
import os
import time

# 修复 Windows 控制台编码问题 - 仅在非测试环境
if sys.platform == 'win32' and sys.stdout.isatty():
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except:
        pass

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from read_article import WechatArticleReader, sanitize_filename


# 文章列表
ARTICLES = [
    # 究模智 - 10篇
    {"account": "究模智", "title": "重磅！OpenClaw创始人宣布加盟OpenAI！", "url": "http://mp.weixin.qq.com/s?__biz=MzAxMjYyMzcwNA==&mid=2247491483&idx=1&sn=db0548e29e3a8c615e6811bff66321cf&chksm=9bae55acacd9dcba26f9eb76cf06d33edcf0422e2ff638285f5ba8ec8d2192e821f8b88241ec#rd"},
    {"account": "究模智", "title": "突破长上下文困境：麻省理工RLM递归语言模型解读（附下载）", "url": "http://mp.weixin.qq.com/s?__biz=MzAxMjYyMzcwNA==&mid=2247491474&idx=1&sn=894cef916b8ba8c6612cb0c9ac7e7730&chksm=9bae55a5acd9dcb3352390cf262be3297ac0eb4b475315c7f2abd00c4dc70cf513ffc5fa207e#rd"},
    {"account": "究模智", "title": "OpenClaw生态深度解析：9大AI智能体互动平台全景", "url": "http://mp.weixin.qq.com/s?__biz=MzAxMjYyMzcwNA==&mid=2247491462&idx=1&sn=011d57fea2c033a818a75b539fa9b900&chksm=9bae55b1acd9dca75ccdce92102798f1c701d5054fa12d91335d9302c1990ff31f6e267f7056#rd"},
    {"account": "究模智", "title": "Anthropic 2026最新报告：智能体编程重塑软件开发的八大趋势（附下载）", "url": "http://mp.weixin.qq.com/s?__biz=MzAxMjYyMzcwNA==&mid=2247491447&idx=1&sn=2d94674999096e770b608cf3ac6ed51b&chksm=9bae5540acd9dc564c7ecfef4181b62f992033754f6daf52d725ec50a06ab6b00096db020c01#rd"},
    {"account": "究模智", "title": "黄仁勋最新访谈解读：五大方法让企业在AI时代保持优势", "url": "http://mp.weixin.qq.com/s?__biz=MzAxMjYyMzcwNA==&mid=2247491447&idx=2&sn=5ef3bc7128e47784f345c5b1afd5a795&chksm=9bae5540acd9dc56afd6c17be203adc2b1354b42ae1fad20f720c3f4581e432d0879236d78ab#rd"},
    {"account": "究模智", "title": "2026谷歌预算$1750亿+投资AI Infra！深度剖析谷歌AI全栈自研布局", "url": "http://mp.weixin.qq.com/s?__biz=MzAxMjYyMzcwNA==&mid=2247491437&idx=1&sn=ce1de531abcd1595aca6486583e43b5a&chksm=9bae555aacd9dc4cae99c2584f33a29ae8b6ebd27f1df46897d5d93c8b9972c86b447ec319c2#rd"},
    {"account": "究模智", "title": "思科AI峰会奥特曼访谈：Moltbook只是一时狂欢", "url": "http://mp.weixin.qq.com/s?__biz=MzAxMjYyMzcwNA==&mid=2247491437&idx=2&sn=25c8b4e7584264b8665c2b2b8d583559&chksm=9bae555aacd9dc4c1fb50de7694c9697b74d4d411c0472de0fe5ae123244acdb72f0093e1bbd#rd"},
    {"account": "究模智", "title": "AI 智能体生态解析：资本流向、市场格局与六大商业模式", "url": "http://mp.weixin.qq.com/s?__biz=MzAxMjYyMzcwNA==&mid=2247491414&idx=1&sn=7b38a9148c555448493c8fd216717742&chksm=9bae5561acd9dc77dc116237dc230c5f081e16991784ca87c358b71301241b495d2597667d13#rd"},
    {"account": "究模智", "title": "谷歌DeepMind发布AlphaGenome模型：人类向消灭疾病的愿景又迈进一大步", "url": "http://mp.weixin.qq.com/s?__biz=MzAxMjYyMzcwNA==&mid=2247491414&idx=2&sn=3396395b1dfdda1b9ab6f5bbb35f8bf4&chksm=9bae5561acd9dc776334aad0fdd552fa8f7f8e44ea8799f0db14468ae0d57121630af56afb2f#rd"},
    {"account": "究模智", "title": "AI 双雄对决！Anthropic推出Claude Opus 4.6、OpenAI 发布 GPT-5.3-Codex", "url": "http://mp.weixin.qq.com/s?__biz=MzAxMjYyMzcwNA==&mid=2247491403&idx=1&sn=992fbe138eb1e9cc788568f2934c678b&chksm=9bae557cacd9dc6af23e54a352fe907b8cb04e7693d53d20e546a7b3c0afcc6ee2cac2cfb748#rd"},
    
    # 新智元 - 10篇
    {"account": "新智元", "title": "春晚机器人炸翻全球，10亿人围观零翻车！老外惊掉下巴，订单暴涨卖疯", "url": "http://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652676391&idx=1&sn=f704ada772bf007db876e0a839769416&chksm=f12fd5d6c6585cc00167cca2192f621bcda5ec633dbb480084485647b5196285574cf239d034#rd"},
    {"account": "新智元", "title": "Anthropic预警成真！AI写长文网暴人类工程师，只因拒绝它改代码", "url": "http://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652676391&idx=2&sn=6c9f6f77102ff8072f0beee5d48034f2&chksm=f12fd5d6c6585cc0044ab004d94e891b20d0492b2910f26f067c0dd677d1dcb6268eef8300aa#rd"},
    {"account": "新智元", "title": "多轮Agent训练拐点！清华首创可执行数据闭环，开源超越GPT-5", "url": "http://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652676391&idx=3&sn=f9e3095d48986d201cecd7fd417bcc43&chksm=f12fd5d6c6585cc0893e320a4fe95cf0b0e908a5000f5f3bbd703f581828cd2cde13fe637f6e#rd"},
    {"account": "新智元", "title": "春晚黑科技曝光！30天造出「奶奶」脸，万元级人形机器人杀入客厅", "url": "http://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652676283&idx=1&sn=99d29f9498bfc60281fcd80de0c55fac&chksm=f12fd44ac6585d5c9b0c82565cf1646b517dd1385b0cd191bbe8d3cedbb6e34095ec3abefc55#rd"},
    {"account": "新智元", "title": "红杉重磅宣言：2026，AGI已至！", "url": "http://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652676283&idx=2&sn=ca65b9b7c42295ebb854dbcb77fe4190&chksm=f12fd44ac6585d5ca41b31ce3a6ce08e47c12434871c0a7b7c20da1930ba23ad7eeb761f1007#rd"},
    {"account": "新智元", "title": "清华打破强化学习安全性悖论，14项测试基准任务全SOTA", "url": "http://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652676283&idx=3&sn=bcd86e643835ae83c7c229adc5ef5372&chksm=f12fd44ac6585d5c2d09a0806a7cd8febaa0e932fbd217dfb202e2a24857a92a86b55daa942d#rd"},
    {"account": "新智元", "title": "万亿思考模型夺下IMO金牌，无缝接入OpenClaw！一句话手搓丐版PS", "url": "http://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652675814&idx=1&sn=064a8d334ea5a734880cfa398c0feb0e&chksm=f12fea17c6586301ce317e186d7eeaba29b355b06c94df59cf496f944e02f7f5672838fde656#rd"},
    {"account": "新智元", "title": "程序员不许写代码！OpenAI硬核实验：3人指挥AI，5个月造出百万行", "url": "http://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652675814&idx=2&sn=8d40a12b5307ffef3678b6c789a5a188&chksm=f12fea17c6586301866f7dd768c79b42c2000bb9584a707906241b503052085432a4c9202e72#rd"},
    {"account": "新智元", "title": "AI甚至开始抢土木老哥的工作了", "url": "http://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652675814&idx=3&sn=7c40c8d9d3c40418687c08744036e2a5&chksm=f12fea17c658630177a60bd09325142f072e245cccbb6c1c05e8f695dfced594b7ac81222c15#rd"},
    {"account": "新智元", "title": "具身智能奇点已至！超越π*0.6，极佳视界自我进化VLA大模型拿下世界第一", "url": "http://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652675631&idx=1&sn=9dbdf303618f530e2da4a94ed8fcfe8e&chksm=f12feadec65863c8062c09b9270403c9d312f91cc7fb57906a58f803337c41c8b43c0aac5543#rd"},
]


def main():
    output_dir = r"D:\anthropic\wechat"
    
    print(f"输出目录: {output_dir}")
    print(f"共 {len(ARTICLES)} 篇文章需要读取")
    print("=" * 60)
    
    # 统计
    success_count = 0
    failed_count = 0
    failed_articles = []
    
    with WechatArticleReader(headless=True) as reader:
        for i, article_info in enumerate(ARTICLES, 1):
            account = article_info["account"]
            title = article_info["title"]
            url = article_info["url"]
            
            print(f"\n[{i}/{len(ARTICLES)}] 正在读取: {title[:50]}...")
            
            try:
                # 读取文章
                article = reader.read_article(url, timeout=30)
                
                if 'error' in article:
                    print(f"读取失败: {article['error']}")
                    failed_count += 1
                    failed_articles.append(article_info)
                    continue
                
                # 生成文件名: 公众号_文章名.md
                safe_account = sanitize_filename(account)
                safe_title = sanitize_filename(title)
                filename = f"{safe_account}_{safe_title}.md"
                
                # 保存文章
                reader.save_article(article, output_dir, filename)
                success_count += 1
                
                # 短暂休息，避免请求过快
                time.sleep(1)
                
            except Exception as e:
                print(f"处理失败: {e}")
                failed_count += 1
                failed_articles.append(article_info)
    
    # 输出统计
    print("\n" + "=" * 60)
    print(f"成功: {success_count} 篇")
    print(f"失败: {failed_count} 篇")
    
    if failed_articles:
        print("\n失败的文章:")
        for article in failed_articles:
            print(f"  - {article['account']}: {article['title'][:50]}...")
    
    print(f"\n所有文件已保存到: {output_dir}")


if __name__ == '__main__':
    main()
