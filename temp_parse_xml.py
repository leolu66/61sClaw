# -*- coding: utf-8 -*-
import os
import glob
import xml.etree.ElementTree as ET
import json

base = r'D:\Users\luzhe\报销凭证\南京-北京-0225-0311'
xml_files = glob.glob(os.path.join(base, '*.xml'))

results = []

for f in xml_files:
    fname = os.path.basename(f)
    print(f'=== {fname} ===')
    try:
        tree = ET.parse(f)
        root = tree.getroot()
        
        # 发票号码
        inv_num = root.find('.//InvoiceNumber')
        inv_num_val = inv_num.text if inv_num is not None else None
        
        # 开票日期
        issue_time = root.find('.//IssueTime')
        issue_time_val = issue_time.text if issue_time is not None else None
        
        # 金额
        total = root.find('.//TotalTax-includedAmount')
        total_val = float(total.text) if total is not None and total.text else 0.0
        
        # 购买方
        buyer = root.find('.//BuyerName')
        buyer_val = buyer.text if buyer is not None else None
        
        # 销售方
        seller = root.find('.//SellerName')
        seller_val = seller.text if seller is not None else None
        
        # 商品名称
        item = root.find('.//ItemName')
        item_val = item.text if item is not None else None
        
        # 识别发票类型
        invoice_type = 'unknown'
        if item_val:
            if '铁路' in item_val or '火车' in item_val or '高铁' in item_val:
                invoice_type = 'train'
            elif '航空' in item_val or '机票' in item_val or '航班' in item_val:
                invoice_type = 'flight'
            elif '出租车' in item_val or '网约车' in item_val or '滴滴' in item_val or '打车' in item_val:
                invoice_type = 'taxi'
            elif '电信' in item_val or '通信' in item_val or '联通' in item_val or '移动' in item_val or '电信' in item_val:
                invoice_type = 'telecom'
            elif '住宿' in item_val or '酒店' in item_val:
                invoice_type = 'hotel'
        
        result = {
            'filename': fname,
            'invoice_number': inv_num_val,
            'issue_date': issue_time_val,
            'amount': total_val,
            'buyer': buyer_val,
            'seller': seller_val,
            'item': item_val,
            'type': invoice_type
        }
        results.append(result)
        
        print(f'Invoice Number: {inv_num_val}')
        print(f'Issue Date: {issue_time_val}')
        print(f'Amount: {total_val}')
        print(f'Buyer: {buyer_val}')
        print(f'Seller: {seller_val}')
        print(f'Item: {item_val}')
        print(f'Type: {invoice_type}')
        
    except Exception as e:
        print(f'Parse Error: {e}')
    print()

# Summary
print('\n=== SUMMARY ===')
print(f'Total XML files: {len(xml_files)}')
total_amount = sum(r['amount'] for r in results)
print(f'Total Amount: {total_amount}')

# Type summary
type_counts = {}
for r in results:
    t = r['type']
    type_counts[t] = type_counts.get(t, 0) + 1
print(f'Type counts: {type_counts}')
