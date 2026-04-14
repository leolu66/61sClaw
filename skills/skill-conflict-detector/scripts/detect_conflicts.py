#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import sys
# 修复Windows控制台中文编码问题
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import re
import argparse
from pathlib import Path
from difflib import SequenceMatcher

# 技能库根目录
SKILLS_ROOT = Path(__file__).parent.parent.parent

def extract_triggers(description):
    """从技能描述中提取触发关键词"""
    triggers = []
    
    # 匹配常见触发词模式
    patterns = [
        r"触发[：:]\s*([^。\n]+)",
        r"触发(?:场景|词)[：:]\s*([^。\n]+)",
        r"当用户(?:说|询问|使用)[：:]?\s*([^。\n]+)",
        r"关键词[：:]\s*([^。\n]+)"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, description)
        for match in matches:
            # 分割多个触发词
            parts = re.split(r"[、，,；;]", match.strip())
            for part in parts:
                part = part.strip().strip("\"'“”‘’")
                if part and len(part) > 1:
                    triggers.append(part)
    
    return triggers

def scan_skills():
    """扫描所有技能，提取元数据"""
    skills = []
    
    for skill_dir in SKILLS_ROOT.iterdir():
        if not skill_dir.is_dir():
            continue
            
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
            
        try:
            content = skill_md.read_text(encoding="utf-8")
            
            # 解析frontmatter
            frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not frontmatter_match:
                continue
                
            frontmatter = frontmatter_match.group(1)
            
            # 提取name和description
            name_match = re.search(r"name:\s*(.+)", frontmatter)
            desc_match = re.search(r"description:\s*(.+)", frontmatter)
            
            if not name_match or not desc_match:
                continue
                
            name = name_match.group(1).strip()
            description = desc_match.group(1).strip()
            
            # 提取触发词
            triggers = extract_triggers(content + " " + description)
            
            skills.append({
                "name": name,
                "description": description,
                "triggers": triggers,
                "path": skill_dir
            })
            
        except Exception as e:
            print(f"读取技能 {skill_dir.name} 失败: {e}")
            continue
    
    return skills

def calculate_similarity(a, b):
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, a, b).ratio()

def detect_conflicts(skills, threshold=0.7):
    """检测冲突"""
    conflicts = {
        "high_risk": [],  # 触发词完全重复
        "medium_risk": [],  # 触发词语义相似 / 功能高度相似
        "low_risk": [],  # 功能部分相似
        "groups": []  # 相似技能分组
    }
    
    # 触发词冲突检测
    trigger_map = {}
    for skill in skills:
        for trigger in skill["triggers"]:
            trigger_lower = trigger.lower()
            if trigger_lower not in trigger_map:
                trigger_map[trigger_lower] = []
            trigger_map[trigger_lower].append({
                "skill": skill,
                "trigger": trigger
            })
    
    # 处理完全重复的触发词（排除同一个技能内部的重复）
    for trigger, entries in trigger_map.items():
        # 去重，同一个技能只保留一个
        unique_skills = list({e["skill"]["name"]: e["skill"] for e in entries}.values())
        if len(unique_skills) >= 2:
            conflicts["high_risk"].append({
                "type": "trigger_duplicate",
                "trigger": trigger,
                "skills": unique_skills,
                "risk": "high"
            })
    
    # 检测相似触发词（排除同一个技能内部的相似）
    all_triggers = list(trigger_map.keys())
    for i in range(len(all_triggers)):
        t1 = all_triggers[i]
        skills1 = list({e["skill"]["name"]: e["skill"] for e in trigger_map[t1]}.values())
        for j in range(i + 1, len(all_triggers)):
            t2 = all_triggers[j]
            sim = calculate_similarity(t1, t2)
            if sim >= threshold:
                skills2 = list({e["skill"]["name"]: e["skill"] for e in trigger_map[t2]}.values())
                # 合并去重，排除完全相同的技能
                all_skills = list({s["name"]: s for s in skills1 + skills2}.values())
                if len(all_skills) >= 2:
                    conflicts["medium_risk"].append({
                        "type": "trigger_similar",
                        "trigger1": t1,
                        "trigger2": t2,
                        "similarity": sim,
                        "skills": all_skills,
                        "risk": "medium"
                    })
    
    # 检测功能相似的技能
    for i in range(len(skills)):
        s1 = skills[i]
        desc1 = s1["description"].strip()
        # 跳过没有描述的技能
        if not desc1 or len(desc1) < 10:
            continue
            
        for j in range(i + 1, len(skills)):
            s2 = skills[j]
            desc2 = s2["description"].strip()
            # 跳过同一个技能或者没有描述的技能
            if s1["name"] == s2["name"] or not desc2 or len(desc2) < 10:
                continue
                
            sim = calculate_similarity(desc1, desc2)
            if sim >= 0.8:
                conflicts["medium_risk"].append({
                    "type": "function_similar",
                    "similarity": sim,
                    "skills": [s1, s2],
                    "risk": "medium"
                })
            elif sim >= 0.6:
                conflicts["low_risk"].append({
                    "type": "function_partial_similar",
                    "similarity": sim,
                    "skills": [s1, s2],
                    "risk": "low"
                })
    
    # 技能分组（功能相似的归为一组）
    groups = []
    used = set()
    
    for skill in skills:
        if skill["name"] in used or not skill["description"].strip() or len(skill["description"].strip()) < 10:
            continue
            
        # 找和这个技能相似度>=0.5的所有技能
        group = [skill]
        used.add(skill["name"])
        
        for other in skills:
            if other["name"] in used or not other["description"].strip() or len(other["description"].strip()) < 10:
                continue
            sim = calculate_similarity(skill["description"], other["description"])
            if sim >= 0.5:
                group.append(other)
                used.add(other["name"])
        
        if len(group) >= 2:
            groups.append({
                "skills": group,
                "avg_similarity": sum(calculate_similarity(g["description"], skill["description"]) for g in group) / len(group)
            })
    
    conflicts["groups"] = sorted(groups, key=lambda x: x["avg_similarity"], reverse=True)
    
    return conflicts

def generate_report(conflicts, skills, only_conflicts=False):
    """生成Markdown格式的报告"""
    report = []
    report.append("# 技能冲突检测报告")
    report.append(f"📅 检测时间: {os.popen('date +"%Y-%m-%d %H:%M:%S"').read().strip()}")
    report.append(f"🔍 扫描技能总数: {len(skills)}")
    report.append(f"⚠️  高风险冲突: {len(conflicts['high_risk'])}")
    report.append(f"⚠️  中风险冲突: {len(conflicts['medium_risk'])}")
    report.append(f"⚠️  低风险冲突: {len(conflicts['low_risk'])}")
    report.append(f"📦 相似技能分组: {len(conflicts['groups'])}")
    report.append("")
    
    # 高风险冲突
    if conflicts["high_risk"]:
        report.append("## 🔴 高风险冲突（触发词完全重复）")
        report.append("")
        for idx, conflict in enumerate(conflicts["high_risk"], 1):
            report.append(f"### 冲突组 {idx}: 触发词「{conflict['trigger']}」")
            report.append("")
            report.append("| 技能名称 | 功能描述 |")
            report.append("|----------|----------|")
            for skill in conflict["skills"]:
                report.append(f"| {skill['name']} | {skill['description'][:50]}... |")
            report.append("")
            report.append("💡 优化建议：调整触发词，明确区分使用场景，避免用户触发时产生歧义")
            report.append("")
    
    # 中风险冲突
    if conflicts["medium_risk"]:
        report.append("## 🟡 中风险冲突（触发词相似 / 功能高度重叠）")
        report.append("")
        for idx, conflict in enumerate(conflicts["medium_risk"], 1):
            if conflict["type"] == "trigger_similar":
                report.append(f"### 冲突组 {idx}: 触发词相似")
                report.append(f"- 触发词1: `{conflict['trigger1']}`")
                report.append(f"- 触发词2: `{conflict['trigger2']}`")
                report.append(f"- 相似度: {conflict['similarity']:.2f}")
            else:
                report.append(f"### 冲突组 {idx}: 功能高度相似")
                report.append(f"- 功能相似度: {conflict['similarity']:.2f}")
            
            report.append("")
            report.append("| 技能名称 | 功能描述 |")
            report.append("|----------|----------|")
            for skill in conflict["skills"]:
                report.append(f"| {skill['name']} | {skill['description'][:80]}... |")
            report.append("")
            report.append("💡 优化建议：根据功能定位调整触发词，或合并重复功能的技能")
            report.append("")
    
    # 低风险冲突
    if conflicts["low_risk"] and not only_conflicts:
        report.append("## 🟢 低风险冲突（功能部分相似）")
        report.append("")
        for idx, conflict in enumerate(conflicts["low_risk"], 1):
            report.append(f"### 冲突组 {idx}: 功能部分相似")
            report.append(f"- 功能相似度: {conflict['similarity']:.2f}")
            report.append("")
            report.append("| 技能名称 | 功能描述 |")
            report.append("|----------|----------|")
            for skill in conflict["skills"]:
                report.append(f"| {skill['name']} | {skill['description'][:80]}... |")
            report.append("")
            report.append("💡 建议：确认功能定位是否有重叠，可根据需要调整触发词区分")
            report.append("")
    
    # 相似技能分组
    if conflicts["groups"] and not only_conflicts:
        report.append("## 📦 相似技能分组")
        report.append("")
        for idx, group in enumerate(conflicts["groups"], 1):
            report.append(f"### 分组 {idx} (平均相似度: {group['avg_similarity']:.2f})")
            report.append("")
            report.append("| 技能名称 | 功能描述 |")
            report.append("|----------|----------|")
            for skill in group["skills"]:
                report.append(f"| {skill['name']} | {skill['description'][:80]}... |")
            report.append("")
    
    # 全部技能列表
    if not only_conflicts:
        report.append("## 📋 全部技能列表")
        report.append("")
        report.append("| 技能名称 | 触发词数量 | 功能描述 |")
        report.append("|----------|------------|----------|")
        for skill in sorted(skills, key=lambda x: x["name"]):
            report.append(f"| {skill['name']} | {len(skill['triggers'])} | {skill['description'][:80]}... |")
        report.append("")
    
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="技能冲突检测工具")
    parser.add_argument("--output", "-o", help="输出报告文件路径")
    parser.add_argument("--threshold", "-t", type=float, default=0.7, help="相似度阈值（默认0.7）")
    parser.add_argument("--only-conflicts", action="store_true", help="只输出冲突部分，不展示全部技能")
    args = parser.parse_args()
    
    print("🔍 正在扫描技能库...")
    skills = scan_skills()
    print(f"✅ 共扫描到 {len(skills)} 个技能")
    
    print("🔍 正在检测冲突...")
    conflicts = detect_conflicts(skills, args.threshold)
    
    print("📝 正在生成报告...")
    report = generate_report(conflicts, skills, args.only_conflicts)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"✅ 报告已保存到: {output_path}")
    else:
        print("\n" + report)

if __name__ == "__main__":
    main()
