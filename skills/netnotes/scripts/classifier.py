#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章分类模块 - 使用大模型API进行分类和摘要生成
"""

import os
import json
from typing import Optional


class ArticleClassifier:
    """文章分类器"""
    
    # 预定义的分类
    CATEGORIES = ["AI", "运营商", "管理", "社会生活", "技术其他", "其他"]
    
    # 分类关键词映射（用于快速判断）
    CATEGORY_KEYWORDS = {
        "AI": ["人工智能", "AI", "机器学习", "深度学习", "大模型", "GPT", "LLM", "神经网络", 
               "算法", "ChatGPT", "Claude", "OpenAI", "生成式AI", "AIGC", "多模态", "NLP", "CV"],
        "运营商": ["运营商", "电信", "移动", "联通", "5G", "通信", "网络", "基站", "宽带",
                   "携号转网", "套餐", "流量", "话费", "工信部", "通信行业", "ICT"],
        "管理": ["管理", "领导力", "团队", "OKR", "KPI", "绩效", "组织架构", "流程",
                 "项目管理", "敏捷", "Scrum", "企业文化", "人力资源", "HR", "战略", "决策"],
        "社会生活": ["社会", "生活", "文化", "教育", "医疗", "房价", "就业", "养老",
                     "消费", "旅游", "美食", "健康", "心理", "人际关系", "家庭", "婚姻"],
        "技术其他": ["编程", "开发", "代码", "架构", "数据库", "前端", "后端", "云原生",
                     "Kubernetes", "Docker", "Linux", "Python", "Java", "Go", "微服务", "DevOps"],
    }
    
    def __init__(self):
        # 尝试从环境变量获取API配置
        self.api_key = os.getenv('OPENAI_API_KEY') or os.getenv('WHALE_API_KEY')
        self.base_url = os.getenv('OPENAI_BASE_URL') or os.getenv('WHALE_BASE_URL')
        self.model = os.getenv('CLASSIFIER_MODEL', 'whalecloud/kimi-k2.5')
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """调用大模型API"""
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': self.model,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 500
            }
            
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"     LLM调用失败: {e}")
            return None
    
    def _keyword_classify(self, title: str, content: str) -> str:
        """基于关键词的快速分类"""
        text = (title + " " + content[:1000]).lower()
        
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return "其他"
    
    def _clean_text(self, text: str) -> str:
        """清理文本中的emoji等特殊字符"""
        import re
        # 移除emoji
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)

    def classify(self, title: str, content: str, summary: str = "") -> str:
        """
        对文章进行分类
        
        Returns:
            str: 分类名称
        """
        # 首先尝试关键词分类
        keyword_result = self._keyword_classify(title, content)
        
        # 如果有关键词匹配，直接使用
        if keyword_result != "其他":
            return keyword_result
        
        # 如果没有API配置，返回关键词结果
        if not self.api_key or not self.base_url:
            print("     未配置LLM API，使用关键词分类")
            return keyword_result
        
        # 使用大模型分类
        prompt = f"""请分析以下文章，从以下分类中选择一个最合适的：

可选分类：{', '.join(self.CATEGORIES)}

文章标题：{title}

文章摘要：{summary}

文章开头（前500字）：
{content[:500]}

请直接回复分类名称（只需回复一个分类名称，不要其他内容）："""
        
        result = self._call_llm(prompt)
        
        if result:
            # 验证返回的分类是否有效
            for cat in self.CATEGORIES:
                if cat in result:
                    return cat
        
        return keyword_result
    
    def generate_summary(self, title: str, content: str) -> str:
        """
        生成文章摘要（不超过100字）
        
        Returns:
            str: 文章摘要
        """
        # 如果没有API配置，使用简单摘要
        if not self.api_key or not self.base_url:
            # 提取前100字作为摘要
            text = content.replace('\n', ' ').strip()
            if len(text) > 100:
                return text[:97] + "..."
            return text
        
        prompt = f"""请为以下文章生成一个简洁的摘要，不超过100字：

文章标题：{title}

文章内容：
{content[:2000]}

请用一句话概括文章的核心内容："""
        
        result = self._call_llm(prompt)
        
        if result:
            # 限制长度并清理emoji
            result = self._clean_text(result)
            if len(result) > 100:
                result = result[:97] + "..."
            return result
        
        # 失败时返回简单摘要
        text = content.replace('\n', ' ').strip()
        text = self._clean_text(text)
        if len(text) > 100:
            return text[:97] + "..."
        return text
