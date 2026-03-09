#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BaseExtractor - 基础提取器
支持CSS Selector和XPath提取
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False


class BaseExtractor(ABC):
    """提取器基类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.selectors = config.get('selectors', {})
        self.base_url = config.get('site', {}).get('base_url', '')
    
    @abstractmethod
    def extract(self, html: str) -> List[Dict]:
        """提取数据，子类必须实现"""
        pass
    
    def _transform_field(self, value: str, transform: str) -> str:
        """字段后处理"""
        if transform == "absolute_url":
            return urljoin(self.base_url, value)
        return value
    
    def _truncate(self, text: str, max_length: int) -> str:
        """截断文本"""
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text


class GenericExtractor(BaseExtractor):
    """通用提取器 - 使用CSS Selector"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        if not BS4_AVAILABLE:
            raise ImportError("需要安装 beautifulsoup4: pip install beautifulsoup4")
    
    def extract(self, html: str) -> List[Dict]:
        """使用CSS Selector提取数据"""
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # 获取容器
        container_css = self.selectors.get('container', {}).get('css')
        item_selector = self.selectors.get('item', 'div')
        
        if container_css:
            containers = soup.select(container_css)
        else:
            containers = [soup]
        
        # 遍历容器提取数据
        for container in containers:
            items = container.select(item_selector) if item_selector else [container]
            
            for item in items:
                article = self._extract_item(item)
                if article.get('title'):  # 至少要有标题
                    articles.append(article)
        
        return articles
    
    def _extract_item(self, item) -> Dict:
        """提取单条新闻"""
        article = {}
        fields_config = self.selectors.get('fields', {})
        
        for field_name, field_config in fields_config.items():
            try:
                value = self._extract_field(item, field_config)
                article[field_name] = value
            except Exception as e:
                # 使用默认值或空字符串
                article[field_name] = field_config.get('default', '')
        
        return article
    
    def _extract_field(self, item, field_config: Dict) -> str:
        """提取单个字段"""
        primary = field_config.get('primary', {})
        fallback = field_config.get('fallback', {})
        
        # 尝试主选择器
        value = self._extract_with_selector(item, primary)
        
        # 如果失败且有备选选择器，尝试备选
        if not value and fallback:
            value = self._extract_with_xpath(str(item), fallback)
        
        # 后处理
        if value:
            transform = field_config.get('transform')
            if transform:
                value = self._transform_field(value, transform)
            
            # 应用正则提取
            regex = primary.get('regex') or fallback.get('regex')
            if regex and value:
                import re
                match = re.search(regex, value)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
            
            max_length = primary.get('max_length') or fallback.get('max_length')
            if max_length:
                value = self._truncate(value, max_length)
        
        return value or ''
    
    def _extract_with_selector(self, item, selector_config: Dict) -> Optional[str]:
        """使用CSS Selector提取"""
        selector = selector_config.get('selector')
        attribute = selector_config.get('attribute', 'text')
        
        if not selector:
            return None
        
        elem = item.select_one(selector)
        if not elem:
            return None
        
        if attribute == 'text':
            return elem.get_text(strip=True)
        elif attribute == 'href':
            return elem.get('href', '')
        elif attribute == 'src':
            return elem.get('src', '')
        else:
            return elem.get(attribute, '')
    
    def _extract_with_xpath(self, html: str, selector_config: Dict) -> Optional[str]:
        """使用XPath提取（备选）"""
        if not LXML_AVAILABLE:
            return None
        
        xpath = selector_config.get('selector')
        if not xpath:
            return None
        
        try:
            tree = etree.HTML(html)
            results = tree.xpath(xpath)
            if results:
                return str(results[0]).strip()
        except Exception as e:
            pass
        
        return None


class XPathExtractor(BaseExtractor):
    """XPath提取器 - 当CSS Selector不适用时使用"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        if not LXML_AVAILABLE:
            raise ImportError("需要安装 lxml: pip install lxml")
    
    def extract(self, html: str) -> List[Dict]:
        """使用XPath提取数据"""
        tree = etree.HTML(html)
        articles = []
        
        container_xpath = self.selectors.get('container', {}).get('xpath')
        item_xpath = self.selectors.get('item', '//div')
        
        if container_xpath:
            containers = tree.xpath(container_xpath)
        else:
            containers = [tree]
        
        for container in containers:
            items = container.xpath(item_xpath) if item_xpath else [container]
            
            for item in items:
                article = self._extract_item(item)
                if article.get('title'):
                    articles.append(article)
        
        return articles
    
    def _extract_item(self, item) -> Dict:
        """提取单条新闻"""
        article = {}
        fields_config = self.selectors.get('fields', {})
        
        for field_name, field_config in fields_config.items():
            try:
                xpath_config = field_config.get('fallback') or field_config.get('primary')
                if xpath_config:
                    value = self._extract_with_xpath(item, xpath_config)
                    article[field_name] = value or ''
            except Exception as e:
                article[field_name] = ''
        
        return article
    
    def _extract_with_xpath(self, item, selector_config: Dict) -> Optional[str]:
        """使用XPath提取"""
        xpath = selector_config.get('selector')
        if not xpath:
            return None
        
        try:
            results = item.xpath(xpath)
            if results:
                return str(results[0]).strip()
        except Exception as e:
            pass
        
        return None


if __name__ == "__main__":
    # 测试提取器
    from config_loader import ConfigLoader
    
    loader = ConfigLoader("../site-configs")
    configs = loader.load_all()
    
    # 测试量子位配置
    qbitai_config = loader.get('qbitai')
    if qbitai_config:
        print(f"\n测试站点: {qbitai_config['site']['name']}")
        extractor = GenericExtractor(qbitai_config)
        print(f"提取器类型: {type(extractor).__name__}")
        print(f"容器选择器: {qbitai_config['selectors']['container']['css']}")
        print(f"字段: {list(qbitai_config['selectors']['fields'].keys())}")
