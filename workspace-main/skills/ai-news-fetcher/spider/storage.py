"""
数据存储模块 - 支持 JSON/CSV/Markdown 多种格式
"""
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .engine import NewsItem

logger = logging.getLogger(__name__)


class BaseStorage:
    """存储基类"""
    
    def __init__(self, output_path: Path):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def save(self, items: List[NewsItem]):
        """保存数据（子类实现）"""
        raise NotImplementedError


class JSONStorage(BaseStorage):
    """JSON 格式存储"""
    
    def __init__(self, output_path: Path, indent: int = 2):
        super().__init__(output_path)
        self.indent = indent
    
    def save(self, items: List[NewsItem]):
        """保存为 JSON"""
        data = [item.to_dict() for item in items]
        
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=self.indent)
        
        logger.info(f"已保存 {len(items)} 条数据到 JSON: {self.output_path}")


class JSONLinesStorage(BaseStorage):
    """JSON Lines 格式存储（每行一个 JSON 对象）"""
    
    def save(self, items: List[NewsItem]):
        """保存为 JSONL"""
        with open(self.output_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
        
        logger.info(f"已保存 {len(items)} 条数据到 JSONL: {self.output_path}")


class CSVStorage(BaseStorage):
    """CSV 格式存储"""
    
    def __init__(self, output_path: Path, fields: List[str] = None):
        super().__init__(output_path)
        self.fields = fields or ["title", "author", "publish_time", "url", "source", "summary"]
    
    def save(self, items: List[NewsItem]):
        """保存为 CSV"""
        with open(self.output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.fields)
            writer.writeheader()
            
            for item in items:
                row = {field: item.to_dict().get(field, "") for field in self.fields}
                writer.writerow(row)
        
        logger.info(f"已保存 {len(items)} 条数据到 CSV: {self.output_path}")


class MarkdownStorage(BaseStorage):
    """Markdown 格式存储（适合人工阅读）"""
    
    def save(self, items: List[NewsItem]):
        """保存为 Markdown"""
        lines = [
            "# 新闻采集结果",
            f"",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"总条目数: {len(items)}",
            f"",
            "---",
            f"",
        ]
        
        for i, item in enumerate(items, 1):
            lines.extend([
                f"## {i}. {item.title}",
                f"",
                f"**来源**: {item.source}  ",
                f"**作者**: {item.author or '未知'}  ",
                f"**发布时间**: {item.publish_time.strftime('%Y-%m-%d %H:%M') if item.publish_time else '未知'}  ",
                f"**链接**: [{item.url}]({item.url})",
                f"",
                f"**摘要**:",
                f"> {item.summary or '(无摘要)'}",
                f"",
                "---",
                f"",
            ])
        
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        logger.info(f"已保存 {len(items)} 条数据到 Markdown: {self.output_path}")


class StorageFactory:
    """存储工厂"""
    
    FORMATS = {
        "json": JSONStorage,
        "jsonl": JSONLinesStorage,
        "csv": CSVStorage,
        "md": MarkdownStorage,
        "markdown": MarkdownStorage,
    }
    
    @classmethod
    def create(cls, format_type: str, output_path: str, **kwargs) -> BaseStorage:
        """
        创建存储实例
        
        Args:
            format_type: 格式类型 (json/csv/md/...)
            output_path: 输出路径
            **kwargs: 额外参数
            
        Returns:
            存储实例
        """
        storage_class = cls.FORMATS.get(format_type.lower())
        if not storage_class:
            raise ValueError(f"不支持的格式: {format_type}")
        
        return storage_class(Path(output_path), **kwargs)
    
    @classmethod
    def get_extension(cls, format_type: str) -> str:
        """获取文件扩展名"""
        extensions = {
            "json": "json",
            "jsonl": "jsonl",
            "csv": "csv",
            "md": "md",
            "markdown": "md",
        }
        return extensions.get(format_type.lower(), "txt")


def auto_save(items: List[NewsItem], output_dir: str = "output", prefix: str = "news") -> Dict[str, Path]:
    """
    自动保存为多种格式
    
    Returns:
        格式 -> 路径 的字典
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {}
    
    for fmt in ["json", "csv", "md"]:
        filename = f"{prefix}_{timestamp}.{StorageFactory.get_extension(fmt)}"
        filepath = output_dir / filename
        
        storage = StorageFactory.create(fmt, filepath)
        storage.save(items)
        results[fmt] = filepath
    
    return results
