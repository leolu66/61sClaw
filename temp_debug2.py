# -*- coding: utf-8 -*-
import sys
import os
import re
sys.path.insert(0, r'C:\Users\luzhe\.openclaw\workspace-main\skills\travel-invoice-fetcher\scripts')
from pdf_invoice_parser import PDFInvoiceParser

parser = PDFInvoiceParser()
fpath = r'D:\Users\luzhe\报销凭证\南京-北京-0225-0311\260316_28.43_上海久柏易游信息科技有限公司.pdf'
info = parser.parse(fpath)

result = f'Amount: {info.amount}\n'
result += f'InvoiceNo: {info.invoice_number}\n'
result += f'Raw length: {len(info.raw_text)}\n'

# 检查是否有发票号码关键词
text = info.raw_text
if text:
    # 用Unicode码点检查
    has_inv = '发票号码' in text or '\u53d1\u7968\u53f7\u7801' in text
    result += f'Has keyword: {has_inv}\n'
    
    # 尝试查找
    match = re.search(r'发票号码[：:]\s*(\d+)', text)
    result += f'Pattern match: {match}\n'
else:
    result += 'No raw text\n'

with open(r'D:\Users\luzhe\报销凭证\南京-北京-0225-0311\debug_result.txt', 'w', encoding='utf-8') as f:
    f.write(result)
print(result)
