# -*- coding: utf-8 -*-
"""
发票归集模块
功能：扫描目录，解析XML和PDF发票，排重，输出统一格式
依赖：pdf_invoice_parser.py（PDF解析）
"""

import os
import re
import json
import glob
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

# 导入PDF解析模块
from pdf_invoice_parser import PDFInvoiceParser


@dataclass
class Invoice:
    """统一发票格式"""
    invoice_id: str          # 发票代码/号码（唯一标识）
    invoice_number: str      # 发票号码
    invoice_type: str        # 类型: train/flight/taxi/hotel/telecom/other
    amount: float            # 金额
    date: str                # 日期 YYYY-MM-DD
    from_location: str       # 出发地
    to_location: str        # 目的地
    transport_no: str        # 车次/航班/车牌
    seller: str              # 销售方
    buyer: str               # 购买方
    item_name: str           # 商品名称
    source_file: str        # 原始文件名
    source_format: str       # 来源格式: xml/pdf
    raw_text: str = ''       # 原始文本（调试用）
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_dedup_key(self) -> str:
        """排重键：发票号+金额"""
        return f"{self.invoice_number}|{self.amount}"


class InvoiceAggregator:
    """发票归集器"""
    
    def __init__(self, base_dir: str):
        """
        初始化
        
        Args:
            base_dir: 发票目录路径
        """
        self.base_dir = Path(base_dir)
        self.invoices: List[Invoice] = []
        self.duplicates: List[Dict] = []  # 重复发票记录
        
    def parse_xml_invoice(self, xml_path: str) -> Optional[Invoice]:
        """
        解析XML发票
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            Invoice 对象
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            filename = os.path.basename(xml_path)
            
            # 发票号码
            inv_num_el = root.find('.//InvoiceNumber')
            invoice_number = inv_num_el.text if inv_num_el is not None else ''
            
            # 金额
            total_el = root.find('.//TotalTax-includedAmount')
            amount = float(total_el.text) if total_el is not None and total_el.text else 0.0
            
            # 开票日期
            issue_time_el = root.find('.//IssueTime')
            date = issue_time_el.text if issue_time_el is not None else ''
            
            # 销售方
            seller_el = root.find('.//SellerName')
            seller = seller_el.text if seller_el is not None else ''
            
            # 购买方
            buyer_el = root.find('.//BuyerName')
            buyer = buyer_el.text if buyer_el is not None else ''
            
            # 商品名称
            item_el = root.find('.//ItemName')
            item_name = item_el.text if item_el is not None else ''
            
            # 识别类型
            invoice_type = self._detect_type(item_name, '', '')
            
            # 发票代码（用于排重）
            invoice_id = invoice_number
            
            return Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_number,
                invoice_type=invoice_type,
                amount=amount,
                date=date,
                from_location='',
                to_location='',
                transport_no='',
                seller=seller,
                buyer=buyer,
                item_name=item_name,
                source_file=filename,
                source_format='xml'
            )
            
        except Exception as e:
            print(f"XML解析失败 {xml_path}: {e}")
            return None
    
    def parse_pdf_invoice(self, pdf_path: str) -> Optional[Invoice]:
        """
        解析PDF发票
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            Invoice 对象
        """
        try:
            parser = PDFInvoiceParser()
            info = parser.parse(pdf_path)
            
            filename = os.path.basename(pdf_path)
            
            # 发票ID：优先使用解析出的发票号，否则用文件名
            invoice_id = info.invoice_number if info.invoice_number else filename.replace('.pdf', '')
            invoice_no = info.invoice_number if info.invoice_number else ''
            
            return Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_no,
                invoice_type=info.invoice_type,
                amount=info.amount,
                date=info.date,
                from_location=info.from_location,
                to_location=info.to_location,
                transport_no=info.transport_no,
                seller=info.seller,
                buyer=info.buyer,
                item_name=info.invoice_type,
                source_file=filename,
                source_format='pdf',
                raw_text=info.raw_text
            )
            
        except Exception as e:
            print(f"PDF解析失败 {pdf_path}: {e}")
            return None
    
    def _detect_type(self, item_name: str, text: str, filename: str) -> str:
        """检测发票类型"""
        combined = f"{item_name} {text} {filename}".lower()
        
        if any(k in combined for k in ['火车', '铁路', '高铁', '动车', 'g12', 'g\d']):
            return 'train'
        if any(k in combined for k in ['航空', '机票', '航班', 'mu', 'cz', 'hu']):
            return 'flight'
        if any(k in combined for k in ['滴滴', 'didi', '出租车', '打车', '网约车', '行程单']):
            return 'taxi'
        if any(k in combined for k in ['酒店', '住宿', '宾馆']):
            return 'hotel'
        if any(k in combined for k in ['电信', '联通', '移动', '通信', '话费']):
            return 'telecom'
        
        return 'other'
    
    def scan_directory(self) -> List[Invoice]:
        """
        扫描目录，解析所有发票
        
        Returns:
            发票列表（未排重）
        """
        self.invoices = []
        
        # 1. 解析XML文件
        xml_files = list(self.base_dir.glob('*.xml'))
        print(f"发现 {len(xml_files)} 个XML文件")
        
        for xml_file in xml_files:
            invoice = self.parse_xml_invoice(str(xml_file))
            if invoice:
                self.invoices.append(invoice)
                print(f"  XML: {invoice.invoice_number} | {invoice.amount} | {invoice.item_name}")
        
        # 2. 解析PDF文件
        pdf_files = list(self.base_dir.glob('*.pdf'))
        print(f"发现 {len(pdf_files)} 个PDF文件")
        
        for pdf_file in pdf_files:
            invoice = self.parse_pdf_invoice(str(pdf_file))
            if invoice:
                self.invoices.append(invoice)
                print(f"  PDF: {invoice.source_file} | {invoice.invoice_type} | {invoice.amount}")
        
        return self.invoices
    
    def deduplicate(self) -> List[Invoice]:
        """
        排重：根据发票号+金额
        
        Returns:
            排重后的发票列表
        """
        seen = {}
        unique_invoices = []
        self.duplicates = []
        
        for inv in self.invoices:
            key = inv.to_dedup_key()
            
            if key in seen:
                # 记录重复
                self.duplicates.append({
                    'original': seen[key].source_file,
                    'duplicate': inv.source_file,
                    'invoice_number': inv.invoice_number,
                    'amount': inv.amount
                })
                print(f"  重复: {inv.source_file} (与 {seen[key].source_file} 相同)")
            else:
                seen[key] = inv
                unique_invoices.append(inv)
        
        self.invoices = unique_invoices
        return unique_invoices
    
    def get_summary(self) -> Dict:
        """
        获取汇总统计
        
        Returns:
            统计字典
        """
        total = sum(inv.amount for inv in self.invoices)
        
        # 按类型汇总
        type_sum = {}
        type_count = {}
        for inv in self.invoices:
            t = inv.invoice_type
            type_sum[t] = type_sum.get(t, 0) + inv.amount
            type_count[t] = type_count.get(t, 0) + 1
        
        return {
            'total_count': len(self.invoices),
            'total_amount': total,
            'type_summary': type_sum,
            'type_count': type_count,
            'duplicate_count': len(self.duplicates)
        }
    
    def export_json(self, output_path: str = None) -> str:
        """
        导出为JSON
        
        Args:
            output_path: 输出路径（可选，默认目录下的 invoice_summary.json）
            
        Returns:
            输出文件路径
        """
        if output_path is None:
            output_path = self.base_dir / 'invoice_summary.json'
        
        data = {
            'summary': self.get_summary(),
            'invoices': [inv.to_dict() for inv in self.invoices],
            'duplicates': self.duplicates,
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    def process(self) -> List[Invoice]:
        """
        完整处理流程：扫描 → 解析 → 排重
        
        Returns:
            排重后的发票列表
        """
        print(f"\n{'='*50}")
        print(f"开始处理: {self.base_dir}")
        print(f"{'='*50}")
        
        # 1. 扫描解析
        print("\n[1/3] 扫描解析发票...")
        self.scan_directory()
        
        # 2. 排重
        print("\n[2/3] 排重...")
        self.deduplicate()
        
        # 3. 汇总
        print("\n[3/3] 汇总统计...")
        summary = self.get_summary()
        
        print(f"\n{'='*50}")
        print("处理完成!")
        print(f"{'='*50}")
        print(f"发票总数: {summary['total_count']}")
        print(f"总金额: {summary['total_amount']:.2f} 元")
        print(f"重复发票: {summary['duplicate_count']}")
        print("\n类型明细:")
        for t, amount in summary['type_summary'].items():
            count = summary['type_count'][t]
            print(f"  {t}: {count}张 | {amount:.2f}元")
        
        # 导出JSON
        output_path = self.export_json()
        print(f"\n已导出: {output_path}")
        
        return self.invoices


def aggregate_directory(directory: str) -> List[Invoice]:
    """
    便捷函数：处理目录
    
    Args:
        directory: 目录路径
        
    Returns:
        发票列表
    """
    aggregator = InvoiceAggregator(directory)
    return aggregator.process()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python invoice_aggregator.py <发票目录>")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    if not os.path.isdir(directory):
        print(f"目录不存在: {directory}")
        sys.exit(1)
    
    aggregate_directory(directory)
