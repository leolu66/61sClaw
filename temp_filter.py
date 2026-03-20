# -*- coding: utf-8 -*-
import json

# 读取发票汇总
with open(r'D:\Users\luzhe\报销凭证\南京-北京-0225-0311\invoice_summary.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 筛选差旅相关发票（火车票 + 打车票）
travel_invoices = []
for inv in data['invoices']:
    if inv['invoice_type'] in ['train', 'taxi']:
        travel_invoices.append(inv)
        print(f"{inv['invoice_type']}: {inv['amount']} | {inv['source_file']}")

total = sum(i['amount'] for i in travel_invoices)
print(f'\n共 {len(travel_invoices)} 张，合计 {total:.2f} 元')
