#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新站点配置引导工具
交互式引导用户完成新闻站点配置
"""

import re
from pathlib import Path


def guide_new_site():
    """引导用户配置新站点"""
    
    print("=" * 60)
    print("  AI新闻获取器 - 新站点配置引导")
    print("=" * 60)
    print()
    
    config = {}
    
    # 步骤1: 基础信息
    print("【步骤1/6】基础站点信息")
    print("-" * 40)
    
    site_name = input("请输入站点名称（中文）: ").strip()
    site_key = input("请输入配置文件名（英文，如 qbitai）: ").strip()
    base_url = input("请输入站点首页URL: ").strip()
    
    use_playwright = input("是否需要动态渲染（Playwright）? [y/N]: ").strip().lower() == 'y'
    
    config['site'] = {
        'name': site_name,
        'base_url': base_url,
        'enabled': True
    }
    
    config['fetch'] = {
        'method': 'playwright' if use_playwright else 'requests',
        'encoding': 'utf-8'
    }
    
    print()
    
    # 步骤2: 新闻列表定位
    print("【步骤2/6】新闻列表定位")
    print("-" * 40)
    print("请在浏览器中打开目标页面，右键点击新闻列表区域")
    print("选择'检查' -> 右键元素 -> Copy -> Copy selector")
    print()
    
    container_css = input("新闻列表容器 CSS Selector: ").strip()
    container_xpath = input("新闻列表容器 XPath（可选，按Enter跳过）: ").strip()
    item_selector = input("单条新闻结构（相对于容器）: ").strip()
    
    config['selectors'] = {
        'container': {
            'css': container_css
        },
        'item': item_selector
    }
    
    if container_xpath:
        config['selectors']['container']['xpath'] = container_xpath
    
    print()
    
    # 步骤3: 字段定位
    print("【步骤3/6】字段定位")
    print("-" * 40)
    print("对于每条新闻，提供各字段的选择器")
    print()
    
    fields = {}
    
    # 标题（必填）
    print("--- 标题（必填）---")
    title_selector = input("  CSS Selector: ").strip()
    title_example = input("  示例值: ").strip()
    fields['title'] = {
        'primary': {
            'selector': title_selector,
            'attribute': 'text'
        },
        'example': title_example
    }
    
    # 链接（必填）
    print("\n--- 链接（必填）---")
    link_selector = input("  CSS Selector: ").strip()
    link_attr = input("  属性（href/src）: ").strip() or 'href'
    link_example = input("  示例值: ").strip()
    fields['link'] = {
        'primary': {
            'selector': link_selector,
            'attribute': link_attr
        },
        'transform': 'absolute_url',
        'example': link_example
    }
    
    # 摘要（可选）
    print("\n--- 摘要（可选，按Enter跳过）---")
    summary_selector = input("  CSS Selector: ").strip()
    if summary_selector:
        summary_example = input("  示例值: ").strip()
        fields['summary'] = {
            'primary': {
                'selector': summary_selector,
                'attribute': 'text',
                'max_length': 200
            },
            'example': summary_example
        }
    
    # 时间（可选）
    print("\n--- 时间（可选，按Enter跳过）---")
    time_selector = input("  CSS Selector: ").strip()
    if time_selector:
        time_example = input("  示例值: ").strip()
        fields['time'] = {
            'primary': {
                'selector': time_selector,
                'attribute': 'text'
            },
            'example': time_example
        }
    
    config['selectors']['fields'] = fields
    print()
    
    # 步骤4: 反爬检测
    print("【步骤4/6】反爬措施检测")
    print("-" * 40)
    
    has_anti_crawl = input("是否检测到反爬措施? [y/N]: ").strip().lower() == 'y'
    
    if has_anti_crawl:
        anti_type = input("  反爬类型（滑块验证/验证码/频率限制）: ").strip()
        trigger = input("  触发条件: ").strip()
        cooldown = input("  建议冷却时间（分钟）: ").strip() or '60'
        
        config['anti_crawl'] = {
            'detected': True,
            'type': anti_type,
            'trigger_condition': trigger,
            'status': 'degraded',
            'mitigation': {
                'enabled': True,
                'cooldown_minutes': int(cooldown),
                'manual_intervention': True
            }
        }
        
        # 自动降低抓取频率
        config['fetch']['strategy'] = {
            'requests_per_minute': 5,
            'delay_between_requests': 12,
            'max_retries': 2
        }
    else:
        config['anti_crawl'] = {
            'detected': False,
            'status': 'normal'
        }
        config['fetch']['strategy'] = {
            'requests_per_minute': 10,
            'delay_between_requests': 6,
            'max_retries': 3
        }
    
    print()
    
    # 步骤5: 生成配置
    print("【步骤5/6】生成配置文件")
    print("-" * 40)
    
    config['extractor'] = 'default'
    config['filters'] = {
        'min_title_length': 10
    }
    
    # 生成YAML
    yaml_content = generate_yaml(config)
    
    print("\n配置预览:")
    print("-" * 40)
    print(yaml_content)
    print("-" * 40)
    
    # 保存
    save = input("\n是否保存配置? [Y/n]: ").strip().lower() != 'n'
    
    if save:
        config_dir = Path("site-configs")
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / f"{site_key}.yaml"
        config_file.write_text(yaml_content, encoding='utf-8')
        
        print(f"\n✅ 配置已保存: {config_file}")
        
        # 步骤6: 测试
        print("\n【步骤6/6】测试配置")
        print("-" * 40)
        print("请运行以下命令测试配置:")
        print(f"  python fetch_ai_news.py --source {site_key} --limit 3")
        
    else:
        print("\n❌ 配置未保存")
    
    print("\n" + "=" * 60)


def generate_yaml(config: dict) -> str:
    """生成YAML配置内容"""
    lines = []
    
    # Site
    lines.append("site:")
    lines.append(f"  name: \"{config['site']['name']}\"")
    lines.append(f"  base_url: \"{config['site']['base_url']}\"")
    lines.append(f"  enabled: {str(config['site']['enabled']).lower()}")
    lines.append("")
    
    # Fetch
    lines.append("fetch:")
    lines.append(f"  method: \"{config['fetch']['method']}\"")
    lines.append(f"  encoding: \"{config['fetch']['encoding']}\"")
    
    if 'strategy' in config['fetch']:
        lines.append("  strategy:")
        for key, value in config['fetch']['strategy'].items():
            lines.append(f"    {key}: {value}")
    lines.append("")
    
    # Selectors
    lines.append("selectors:")
    lines.append("  container:")
    lines.append(f"    css: \"{config['selectors']['container']['css']}\"")
    if 'xpath' in config['selectors']['container']:
        lines.append(f"    xpath: \"{config['selectors']['container']['xpath']}\"")
    lines.append(f"  item: \"{config['selectors']['item']}\"")
    lines.append("  fields:")
    
    for field_name, field_config in config['selectors']['fields'].items():
        lines.append(f"    {field_name}:")
        lines.append("      primary:")
        lines.append(f"        selector: \"{field_config['primary']['selector']}\"")
        lines.append(f"        attribute: \"{field_config['primary']['attribute']}\"")
        if 'max_length' in field_config['primary']:
            lines.append(f"        max_length: {field_config['primary']['max_length']}")
        if 'example' in field_config:
            lines.append(f"      example: \"{field_config['example']}\"")
        if 'transform' in field_config:
            lines.append(f"      transform: \"{field_config['transform']}\"")
    lines.append("")
    
    # Anti-crawl
    lines.append("anti_crawl:")
    lines.append(f"  detected: {str(config['anti_crawl']['detected']).lower()}")
    if config['anti_crawl']['detected']:
        lines.append(f"  type: \"{config['anti_crawl']['type']}\"")
        lines.append(f"  trigger_condition: \"{config['anti_crawl']['trigger_condition']}\"")
        lines.append(f"  status: \"{config['anti_crawl']['status']}\"")
        lines.append("  mitigation:")
        lines.append(f"    enabled: {str(config['anti_crawl']['mitigation']['enabled']).lower()}")
        lines.append(f"    cooldown_minutes: {config['anti_crawl']['mitigation']['cooldown_minutes']}")
        lines.append(f"    manual_intervention: {str(config['anti_crawl']['mitigation']['manual_intervention']).lower()}")
    lines.append("")
    
    # Filters
    lines.append("filters:")
    for key, value in config['filters'].items():
        lines.append(f"  {key}: {value}")
    lines.append("")
    
    # Extractor
    lines.append(f"extractor: \"{config['extractor']}\"")
    
    return "\n".join(lines)


if __name__ == "__main__":
    guide_new_site()
