"""
字段提取器 - 支持 XPath / CSS / Regex / JSON 多种提取方式
"""
import re
import json
import logging
from typing import Any, Optional, List, Union
from urllib.parse import urljoin, urlparse
from datetime import datetime
from dateutil import parser as date_parser
from lxml import html, etree
import cssselect

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """提取异常"""
    pass


class FieldExtractor:
    """
    字段提取器
    
    支持多种选择器类型：
    - xpath: XPath 表达式
    - css: CSS 选择器
    - regex: 正则表达式（在 HTML 文本上匹配）
    - jsonpath: JSONPath（用于 API 返回）
    - constant: 常量值
    """
    
    def __init__(self, field_config: dict):
        """
        初始化提取器
        
        Args:
            field_config: 字段配置字典，包含:
                - type: 选择器类型 (xpath/css/regex/jsonpath/constant)
                - value: 选择器表达式或常量值
                - required: 是否必填 (默认 False)
                - default: 默认值
                - transform: 转换器名称
                - multiple: 是否提取多个值 (默认 False)
        """
        self.config = field_config
        self.selector_type = field_config.get("type", "xpath")
        self.selector_value = field_config.get("value")
        self.required = field_config.get("required", False)
        self.default = field_config.get("default")
        self.transform_name = field_config.get("transform")
        self.multiple = field_config.get("multiple", False)
        
        # 预编译正则表达式
        if self.selector_type == "regex" and self.selector_value:
            try:
                self._regex_pattern = re.compile(self.selector_value, re.DOTALL)
            except re.error as e:
                raise ExtractionError(f"正则表达式编译失败: {e}")
    
    def extract(self, content: Union[str, html.HtmlElement, dict], 
                base_url: str = "") -> Any:
        """
        执行提取
        
        Args:
            content: HTML 字符串、Element 对象或 JSON 字典
            base_url: 基础 URL（用于相对路径转换）
            
        Returns:
            提取的值，失败时返回 default 或 None
        """
        try:
            # 标准化输入
            if isinstance(content, str):
                if self.selector_type == "jsonpath":
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        raise ExtractionError("内容不是有效的 JSON")
                else:
                    content = html.fromstring(content)
            
            # 执行选择
            raw_value = self._select(content)
            
            # 空值处理
            if raw_value is None or (isinstance(raw_value, list) and not raw_value):
                if self.required:
                    raise ExtractionError(f"必填字段未找到: {self.selector_value}")
                return self.default
            
            # 转换处理
            result = self._transform(raw_value, base_url)
            
            # 如果 multiple=False，但提取到列表，取第一个
            if not self.multiple and isinstance(result, list):
                result = result[0] if result else self.default
            
            return result
            
        except ExtractionError:
            raise
        except Exception as e:
            logger.warning(f"提取失败: {e}")
            if self.required:
                raise ExtractionError(f"提取必填字段失败: {e}")
            return self.default
    
    def _select(self, content: Union[html.HtmlElement, dict]) -> Any:
        """
        根据选择器类型执行选择
        """
        selectors = {
            "xpath": self._select_xpath,
            "css": self._select_css,
            "regex": self._select_regex,
            "jsonpath": self._select_jsonpath,
            "constant": self._select_constant,
        }
        
        selector_func = selectors.get(self.selector_type)
        if not selector_func:
            raise ExtractionError(f"未知的选择器类型: {self.selector_type}")
        
        return selector_func(content)
    
    def _select_xpath(self, tree: html.HtmlElement) -> Any:
        """XPath 选择"""
        try:
            result = tree.xpath(self.selector_value)
            return self._normalize_result(result)
        except etree.XPathError as e:
            raise ExtractionError(f"XPath 表达式错误: {e}")
    
    def _select_css(self, tree: html.HtmlElement) -> Any:
        """CSS 选择器"""
        try:
            result = tree.cssselect(self.selector_value)
            return self._normalize_result(result)
        except cssselect.SelectorError as e:
            raise ExtractionError(f"CSS 选择器错误: {e}")
    
    def _select_regex(self, content: Union[str, html.HtmlElement]) -> Any:
        """正则表达式匹配"""
        if isinstance(content, html.HtmlElement):
            text = html.tostring(content, encoding="unicode", method="text")
        else:
            text = str(content)
        
        matches = self._regex_pattern.findall(text)
        if not matches:
            return None
        
        # 如果有捕获组，返回捕获组内容
        if isinstance(matches[0], tuple):
            return [m[0] if m else None for m in matches]
        return matches
    
    def _select_jsonpath(self, data: dict) -> Any:
        """
        简化的 JSONPath 实现
        支持: $.key, $.key.nested, $.array[*].key, $.array[0].key
        """
        path = self.selector_value
        if path.startswith("$."):
            path = path[2:]
        
        keys = path.split(".")
        result = data
        
        for key in keys:
            # 处理数组索引，如 items[0] 或 items[*]
            if "[" in key and key.endswith("]"):
                key_name, index_str = key[:-1].split("[", 1)
                result = result.get(key_name) if isinstance(result, dict) else None
                
                if not isinstance(result, list):
                    return None
                
                if index_str == "*":
                    # 返回所有元素
                    return result
                else:
                    try:
                        idx = int(index_str)
                        result = result[idx] if 0 <= idx < len(result) else None
                    except (ValueError, IndexError):
                        return None
            else:
                result = result.get(key) if isinstance(result, dict) else None
            
            if result is None:
                return None
        
        return result
    
    def _select_constant(self, _: Any) -> Any:
        """返回常量值"""
        return self.selector_value
    
    def _normalize_result(self, result: Any) -> Any:
        """标准化选择结果"""
        if result is None:
            return None
        
        if isinstance(result, list):
            # 提取元素文本或属性值
            normalized = []
            for item in result:
                if isinstance(item, str):
                    normalized.append(item.strip())
                elif hasattr(item, "text_content"):
                    normalized.append(item.text_content().strip())
                elif hasattr(item, "get"):  # 属性值
                    normalized.append(item)
                else:
                    normalized.append(str(item).strip())
            return normalized
        
        # 单个元素
        if isinstance(result, str):
            return result.strip()
        elif hasattr(result, "text_content"):
            return result.text_content().strip()
        return str(result).strip()
    
    def _transform(self, value: Any, base_url: str) -> Any:
        """
        应用转换器
        """
        if not self.transform_name:
            return value
        
        # 获取转换器函数
        transformer = TRANSFORMERS.get(self.transform_name)
        if not transformer:
            logger.warning(f"未知的转换器: {self.transform_name}")
            return value
        
        # 应用转换
        try:
            if isinstance(value, list):
                return [transformer(v, base_url) for v in value]
            return transformer(value, base_url)
        except Exception as e:
            logger.warning(f"转换失败 ({self.transform_name}): {e}")
            return value


# ==================== 转换器 ====================

def _absolute_url(value: str, base_url: str) -> str:
    """相对 URL 转绝对 URL"""
    if not value:
        return value
    if value.startswith(("http://", "https://", "//")):
        return value
    return urljoin(base_url, value)


def _join_text(value: Union[str, List[str]], base_url: str = "") -> str:
    """合并多段文本"""
    if isinstance(value, list):
        return " ".join(str(v).strip() for v in value if v).strip()
    return str(value).strip()


def _strip_html(value: str, base_url: str = "") -> str:
    """去除 HTML 标签"""
    if not value:
        return value
    try:
        tree = html.fromstring(value)
        return tree.text_content().strip()
    except:
        return re.sub(r"<[^\>]+>", "", value).strip()


def _parse_datetime(value: str, base_url: str = "") -> Optional[datetime]:
    """解析日期时间"""
    if not value:
        return None
    try:
        # 尝试多种格式
        return date_parser.parse(value)
    except:
        return None


def _timestamp_to_iso(value: Union[str, int], base_url: str = "") -> Optional[str]:
    """时间戳转 ISO 格式"""
    try:
        ts = int(value)
        # 判断是秒还是毫秒
        if ts > 1e10:
            ts = ts / 1000
        return datetime.fromtimestamp(ts).isoformat()
    except:
        return None


def _extract_number(value: str, base_url: str = "") -> Optional[int]:
    """提取数字"""
    if not value:
        return None
    numbers = re.findall(r"\d+", str(value))
    return int(numbers[0]) if numbers else None


def _clean_whitespace(value: str, base_url: str = "") -> str:
    """清理空白字符"""
    if not value:
        return value
    return re.sub(r"\s+", " ", str(value)).strip()


def _truncate(value: str, max_length: int = 200) -> str:
    """截断文本"""
    if not value or len(value) <= max_length:
        return value
    return value[:max_length].rsplit(" ", 1)[0] + "..."


def _add_year_to_date(value: str, base_url: str = "") -> str:
    """将 MM-DD 格式转换为 YYYY-MM-DD"""
    if not value:
        return value
    from datetime import datetime
    try:
        # 格式如 "03-08"
        value = value.strip()
        if len(value) == 5 and value[2] == '-':
            current_year = datetime.now().year
            return f"{current_year}-{value}"
        return value
    except:
        return value


# 转换器注册表
TRANSFORMERS = {
    "absolute_url": _absolute_url,
    "join_text": _join_text,
    "strip_html": _strip_html,
    "parse_datetime": _parse_datetime,
    "timestamp_to_iso": _timestamp_to_iso,
    "extract_number": _extract_number,
    "clean_whitespace": _clean_whitespace,
    "truncate": _truncate,
    "add_year_to_date": _add_year_to_date,
}


def register_transformer(name: str, func):
    """注册自定义转换器"""
    TRANSFORMERS[name] = func


# ==================== 便捷函数 ====================

def extract_field(html_content: str, field_config: dict, base_url: str = "") -> Any:
    """快捷提取单个字段"""
    extractor = FieldExtractor(field_config)
    return extractor.extract(html_content, base_url)


def extract_fields(html_content: str, field_configs: dict, base_url: str = "") -> dict:
    """快捷提取多个字段"""
    results = {}
    for field_name, config in field_configs.items():
        try:
            extractor = FieldExtractor(config)
            results[field_name] = extractor.extract(html_content, base_url)
        except ExtractionError as e:
            logger.warning(f"提取字段 {field_name} 失败: {e}")
            results[field_name] = config.get("default")
    return results
