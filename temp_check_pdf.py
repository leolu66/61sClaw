# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, r'C:\Users\luzhe\.openclaw\workspace-main\skills\travel-invoice-fetcher\scripts')
from pdf_invoice_parser import PDFInvoiceParser

parser = PDFInvoiceParser()

base = r'D:\Users\luzhe\报销凭证\南京-北京-0225-0311'

# 扫描所有PDF发票（排除行程单）
pdf_files = [f for f in os.listdir(base) if f.endswith('.pdf') and '行程单' not in f]

for fname in sorted(pdf_files):
    fpath = os.path.join(base, fname)
    info = parser.parse(fpath)
    
    print(f'File: {fname}')
    print(f'  Amount: {info.amount}')
    print(f'  InvoiceNo: {info.invoice_number}')
    print()
