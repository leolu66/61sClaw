# -*- coding: utf-8 -*-
"""
PDF发票解析模块
功能：从PDF提取文本，分析发票类型，提取报销关键字段
依赖：pdf-extract 技能（调用提取文本）+ 正则解析
"""

import os
import re
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class InvoiceInfo:
    """发票信息"""
    filename: str
    invoice_type: str  # train/flight/taxi/hotel/telecom/other
    amount: float
    date: str
    from_location: str
    to_location: str
    transport_no: str  # 车次/航班号/车牌号
    seller: str
    buyer: str
    invoice_number: str = ''  # 发票号码
    raw_text: str = ''
    
    def to_dict(self) -> dict:
        return asdict(self)


class PDFInvoiceParser:
    """PDF发票解析器"""
    
    # 发票类型关键词
    TYPE_KEYWORDS = {
        'train': ['火车票', '铁路', '高铁', '动车', 'G\\d+', 'D\\d+', 'K\\d+', 'T\\d+', 'Z\\d+', '北京', '上海', '南京'],
        'flight': ['机票', '航空', '航班', '登机牌', 'MU\\d+', 'CZ\\d+', 'HU\\d+', 'CA\\d+'],
        'taxi': ['滴滴', 'DIDI', '出租车', '打车', '网约车', '行程单', '车费'],
        'hotel': ['酒店', '住宿', '宾馆', '民宿'],
        'telecom': ['电信', '联通', '移动', '通信', '话费'],
    }
    
    def __init__(self, pdf_extract_script: str = None):
        """
        初始化
        
        Args:
            pdf_extract_script: pdf-extract 技能的 extract.py 路径
        """
        if pdf_extract_script is None:
            # 默认路径: pdf-extract 技能在 skills 目录的平级位置
            self.pdf_extract_script = str(Path(__file__).parent.parent.parent / "pdf-extract" / "scripts" / "extract.py")
        else:
            self.pdf_extract_script = pdf_extract_script
        
        # 确保路径存在
        if not os.path.exists(self.pdf_extract_script):
            # 备选方案：直接使用 pdfplumber
            self.pdf_extract_script = None
    
    def extract_text(self, pdf_path: str) -> str:
        """
        调用 pdf-extract 技能提取文本
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        # 方式1: 使用 pdf-extract 脚本
        if self.pdf_extract_script and os.path.exists(self.pdf_extract_script):
            try:
                result = subprocess.run(
                    ['python', self.pdf_extract_script, pdf_path],
                    capture_output=True, text=True, timeout=30,
                    encoding='utf-8', errors='replace'
                )
                if result.returncode == 0:
                    return result.stdout
                else:
                    print(f"PDF提取失败: {result.stderr}")
            except Exception as e:
                print(f"PDF提取异常: {e}")
        
        # 方式2: 直接使用 pdfplumber（备选）
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() or ''
            return text
        except Exception as e:
            print(f"pdfplumber提取失败: {e}")
            return ""
    
    def detect_invoice_type(self, text: str, filename: str = '') -> str:
        """
        检测发票类型
        
        Args:
            text: PDF文本内容
            filename: 文件名（用于判断行程单）
            
        Returns:
            发票类型: train/flight/taxi/hotel/telecom/other
        """
        # 优先检查文件名是否含"行程单"
        if '行程单' in filename:
            return 'trip'
        
        text_lower = text.lower()
        
        # 按优先级检测
        if any(k in text for k in ['滴滴', 'DIDI', '行程单', '车费']):
            return 'taxi'
        
        if any(k in text for k in ['火车票', '铁路', '高铁', '动车']):
            return 'train'
        
        if any(k in text for k in ['机票', '航空', '航班', '登机牌']):
            return 'flight'
        
        if any(k in text for k in ['酒店', '住宿', '宾馆']):
            return 'hotel'
        
        if any(k in text for k in ['电信', '联通', '移动', '通信', '话费']):
            return 'telecom'
        
        return 'other'
    
    def extract_amount_from_filename(self, filename: str) -> float:
        """
        从文件名提取金额
        格式如: 260315_34.00_公司名.pdf
        
        Args:
            filename: 文件名
            
        Returns:
            金额，如果提取失败返回0
        """
        import re
        # 匹配金额：34.00, 28.43 等
        match = re.search(r'_(\d+\.\d{2})_', filename)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        return 0
    
    def parse_taxi_invoice(self, text: str) -> Dict:
        """
        解析滴滴/出租车发票
        
        滴滴行程单格式:
        出发时间: 2026-02-25 19:54
        起点: xxx
        终点: xxx
        金额: xxx元
        """
        result = {
            'amount': 0.0,
            'date': '',
            'from_location': '',
            'to_location': '',
            'transport_no': '',
            'seller': '',
            'buyer': '',
            'invoice_number': ''  # 新增发票号字段
        }
        
        # 发票号码 - 支持多种格式
        invoice_match = re.search(r'发票号码[：:]\s*(\d+)', text)
        if not invoice_match:
            # 备选：查找20位数字（发票号码通常是20位）
            invoice_match = re.search(r'(\d{20})', text)
        if invoice_match:
            result['invoice_number'] = invoice_match.group(1)
        
        # 金额
        amount_match = re.search(r'合计[:：]?\s*(\d+\.?\d*)\s*元?', text)
        if not amount_match:
            amount_match = re.search(r'(\d+\.?\d*)\s*元', text)
        if amount_match:
            result['amount'] = float(amount_match.group(1))
        
        # 日期时间
        date_match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日?\s*(\d{1,2})?:?(\d{1,2})?', text)
        if date_match:
            result['date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
        
        # 起点终点（滴滴格式）
        from_match = re.search(r'出发[地地]?:?\s*(.+?)(?:$|出发|到达|终点)', text)
        to_match = re.search(r'到达[地地]?:?\s*(.+?)(?:$|备注|支付)', text)
        
        if from_match:
            result['from_location'] = from_match.group(1).strip()
        if to_match:
            result['to_location'] = to_match.group(1).strip()
        
        # 尝试其他格式
        if not result['from_location']:
            # 行程详情格式
            from_match = re.search(r'[\u4e00-\u9fa5]+\s*-?\s*[\u4e00-\u9fa5]+.*?(\d{1,2}:\d{2}).*?→.*?([\u4e00-\u9fa5]+)', text)
        
        return result
    
    def parse_train_ticket(self, text: str) -> Dict:
        """
        解析火车票
        
        格式:
        出发站: 南京南
        到达站: 北京南
        日期: 2026-02-25
        车次: G12
        金额: xxx元
        """
        result = {
            'amount': 0.0,
            'date': '',
            'from_location': '',
            'to_location': '',
            'transport_no': '',
            'seller': '',
            'buyer': '',
            'invoice_number': ''  # 发票号码
        }
        
        # 发票号码 - 支持多种格式
        invoice_match = re.search(r'发票号码[：:]\s*(\d+)', text)
        if not invoice_match:
            # 备选：查找20位数字（发票号码通常是20位）
            invoice_match = re.search(r'(\d{20})', text)
        if invoice_match:
            result['invoice_number'] = invoice_match.group(1)
        
        # 金额 - 优先查找"￥"符号后的数字（火车票格式）
        amount_match = re.search(r'[￥¥]\s*(\d+\.?\d*)', text)
        if not amount_match:
            # 查找"人民币"后面的数字
            amount_match = re.search(r'人民币[:：]?\s*(\d+\.?\d*)', text)
        if not amount_match:
            # 查找"总额"或"合计"后面的数字
            amount_match = re.search(r'(?:总额|合计|价税合计)[:：]?\s*(\d+\.?\d*)', text)
        if not amount_match:
            # 查找单独的金额模式（带小数点）
            amount_match = re.search(r'\s(\d{2,3}\.\d{2})\s', text)
        
        if amount_match:
            try:
                val = float(amount_match.group(1))
                # 合理金额范围判断
                if 1 < val < 2000:
                    result['amount'] = val
            except:
                pass
        
        # 日期
        date_match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日?', text)
        if not date_match:
            # 尝试其他格式
            date_match = re.search(r'(\d{2})[月](\d{1,2})[日]?', text)
        if date_match:
            if len(date_match.groups()) == 3:
                result['date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
            else:
                result['date'] = f"2026-{date_match.group(1).zfill(2)}-{date_match.group(2).zfill(2)}"
        
        # 车次
        train_match = re.search(r'([GDCZTK]\d+)', text)
        if not train_match:
            train_match = re.search(r'G\d+|D\d+|K\d+', text)
        if train_match:
            result['transport_no'] = train_match.group(1)
        
        # 出发/到达站 - 查找"站"字
        stations = re.findall(r'([\u4e00-\u9fa5]+站|[A-Za-z]+nan|[A-Za-z]+bei)', text, re.IGNORECASE)
        if len(stations) >= 2:
            # 清理站名
            from_station = stations[0].replace('站', '')
            to_station = stations[1].replace('站', '')
            result['from_location'] = from_station
            result['to_location'] = to_station
        
        return result
    
    def parse_other_invoice(self, text: str) -> Dict:
        """
        解析其他发票（增值税普通发票等）
        """
        result = {
            'amount': 0.0,
            'date': '',
            'from_location': '',
            'to_location': '',
            'transport_no': '',
            'seller': '',
            'buyer': '',
            'invoice_number': ''  # 发票号码
        }
        
        # 发票号码 - 支持多种格式
        invoice_match = re.search(r'发票号码[：:]\s*(\d+)', text)
        if not invoice_match:
            # 备选：查找20位数字（发票号码通常是20位）
            invoice_match = re.search(r'(\d{20})', text)
        if invoice_match:
            result['invoice_number'] = invoice_match.group(1)
        
        # 金额 - 价税合计
        amount_match = re.search(r'价税合计[:：]?\s*(\d+\.?\d*)', text)
        if not amount_match:
            amount_match = re.search(r'[:：]\s*(\d+\.?\d*)\s*元', text)
        if amount_match:
            result['amount'] = float(amount_match.group(1))
        
        # 日期
        date_match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日?', text)
        if date_match:
            result['date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
        
        # 销售方
        seller_match = re.search(r'销售方[:：]?\s*([^\s,，,]{4,30})', text)
        if seller_match:
            result['seller'] = seller_match.group(1).strip()
        
        # 购买方
        buyer_match = re.search(r'购买方[:：]?\s*([^\s,，,]{2,30})', text)
        if buyer_match:
            result['buyer'] = buyer_match.group(1).strip()
        
        return result
    
    def parse(self, pdf_path: str) -> InvoiceInfo:
        """
        解析PDF发票
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            InvoiceInfo 对象
        """
        filename = os.path.basename(pdf_path)
        
        # 1. 先判断是否行程单（文件名包含"行程单"）
        is_trip = '行程单' in filename
        
        # 2. 提取文本
        text = self.extract_text(pdf_path)
        if not text:
            # 如果没有文本，但文件名有金额信息，仍然可以处理
            text = ''
        
        # 3. 检测类型（传入filename用于判断行程单）
        invoice_type = self.detect_invoice_type(text, filename)
        
        # 4. 根据类型解析字段
        if invoice_type == 'taxi':
            fields = self.parse_taxi_invoice(text)
        elif invoice_type == 'train':
            fields = self.parse_train_ticket(text)
        else:
            fields = self.parse_other_invoice(text)
        
        # 5. 行程单特殊处理：金额=0，从文件名提取金额作为参考
        if is_trip:
            invoice_type = 'trip'
            # 从文件名提取金额
            file_amount = self.extract_amount_from_filename(filename)
            fields['amount'] = 0  # 行程单金额记为0
            # 将PDF提取的金额作为备注
            if fields.get('amount', 0) > 0:
                fields['remark'] = f"行程单，参考金额: {fields['amount']}元"
            else:
                fields['remark'] = f"行程单，文件名金额: {file_amount}元"
        else:
            # 发票：如果PDF金额为0，尝试从文件名提取
            if fields.get('amount', 0) == 0:
                file_amount = self.extract_amount_from_filename(filename)
                if file_amount > 0:
                    fields['amount'] = file_amount
        
        return InvoiceInfo(
            filename=filename,
            invoice_type=invoice_type,
            amount=fields['amount'],
            date=fields['date'],
            from_location=fields['from_location'],
            to_location=fields['to_location'],
            transport_no=fields['transport_no'],
            seller=fields['seller'],
            buyer=fields['buyer'],
            invoice_number=fields.get('invoice_number', ''),
            raw_text=text[:500]  # 保存部分原文用于调试
        )


def parse_directory(pdf_dir: str) -> List[InvoiceInfo]:
    """
    解析目录下所有PDF发票
    
    Args:
        pdf_dir: 目录路径
        
    Returns:
        发票信息列表
    """
    parser = PDFInvoiceParser()
    
    pdf_files = list(Path(pdf_dir).glob('*.pdf'))
    
    results = []
    for pdf_file in pdf_files:
        try:
            info = parser.parse(str(pdf_file))
            results.append(info)
        except Exception as e:
            print(f"解析失败 {pdf_file.name}: {e}")
    
    return results


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python pdf_invoice_parser.py <pdf文件或目录>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    if os.path.isdir(target):
        # 解析目录
        results = parse_directory(target)
        print(f"\n解析到 {len(results)} 个PDF发票:")
        for r in results:
            print(f"  - {r.filename}: {r.invoice_type} | {r.amount}元 | {r.date}")
        
        # 按类型汇总
        type_sum = {}
        for r in results:
            t = r.invoice_type
            type_sum[t] = type_sum.get(t, 0) + r.amount
        print(f"\n类型汇总: {type_sum}")
        
    else:
        # 解析单个文件
        parser = PDFInvoiceParser()
        info = parser.parse(target)
        print(f"文件名: {info.filename}")
        print(f"类型: {info.invoice_type}")
        print(f"金额: {info.amount}")
        print(f"日期: {info.date}")
        print(f"出发: {info.from_location}")
        print(f"到达: {info.to_location}")
        print(f"车次/车牌: {info.transport_no}")
        print(f"销售方: {info.seller}")
        print(f"购买方: {info.buyer}")
