#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
差旅发票抓取器主脚本
根据用户行程描述，自动创建目录并从邮箱抓取发票
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 添加脚本目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from trip_parser import TripParser, TripSegment
from email_fetcher import EmailFetcher


def load_config() -> Dict:
    """加载配置文件"""
    config_path = script_dir / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 无法加载配置文件: {e}")
        print("使用默认配置")
        return {
            "base_path": "D:\\Users\\luzhe\\报销凭证",
            "imap_server": "imap.qq.com",
            "imap_port": 993,
            "search_days": 7,
            "email_subject_keywords": ["发票"],
            "auto_extract": True
        }


def get_vault_credentials() -> Optional[Dict]:
    """
    从 vault 读取邮箱凭据
    
    Returns:
        包含 email 和 password 的字典，或 None
    """
    try:
        # 尝试从 vault 读取
        # 注意：这里使用环境变量方式，实际使用时需要配置 vault
        vault_key = "qq_email"
        
        # 首先检查环境变量
        email = os.environ.get("QQ_EMAIL")
        password = os.environ.get("QQ_EMAIL_PASSWORD")
        
        if email and password:
            return {"email": email, "password": password}
        
        # 尝试从 .vault 文件读取（如果存在）
        vault_path = Path.home() / ".vault" / "credentials.json"
        if vault_path.exists():
            with open(vault_path, "r", encoding="utf-8") as f:
                vault_data = json.load(f)
                if vault_key in vault_data:
                    return vault_data[vault_key]
        
        # 尝试从工作区 vault 目录读取
        workspace_vault = Path("C:/Users/luzhe/.openclaw/workspace-main/vault/credentials.json")
        if workspace_vault.exists():
            with open(workspace_vault, "r", encoding="utf-8") as f:
                vault_data = json.load(f)
                if vault_key in vault_data:
                    return vault_data[vault_key]
        
        return None
        
    except Exception as e:
        print(f"⚠️ 读取 vault 凭据失败: {e}")
        return None


def create_trip_directories(segments: List[TripSegment], base_path: str) -> List[str]:
    """
    创建行程目录
    
    Args:
        segments: 行程段列表
        base_path: 基础路径
        
    Returns:
        创建的目录路径列表
    """
    created_dirs = []
    base = Path(base_path)
    
    for segment in segments:
        folder_name = segment.folder_name
        trip_dir = base / folder_name
        
        try:
            trip_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(trip_dir))
            print(f"📁 创建目录: {trip_dir}")
        except Exception as e:
            print(f"❌ 创建目录失败 {folder_name}: {e}")
    
    return created_dirs


def fetch_invoices_for_trips(
    segments: List[TripSegment],
    credentials: Dict,
    config: Dict
) -> Dict:
    """
    为行程抓取发票
    
    Args:
        segments: 行程段列表
        credentials: 邮箱凭据
        config: 配置
        
    Returns:
        执行结果统计
    """
    results = {
        "total_trips": len(segments),
        "emails_found": 0,
        "attachments_downloaded": 0,
        "errors": []
    }
    
    # 初始化邮件抓取器
    fetcher = EmailFetcher(
        email_address=credentials["email"],
        password=credentials["password"],
        imap_server=config.get("imap_server", "imap.qq.com"),
        imap_port=config.get("imap_port", 993)
    )
    
    # 连接邮箱
    if not fetcher.connect():
        results["errors"].append("邮箱连接失败")
        return results
    
    try:
        # 搜索发票邮件
        emails = fetcher.search_invoice_emails(
            days=config.get("search_days", 7),
            subject_keywords=config.get("email_subject_keywords", ["发票"])
        )
        
        results["emails_found"] = len(emails)
        
        if not emails:
            print("⚠️ 未找到发票邮件")
            return results
        
        # 为每个行程目录下载附件
        base_path = Path(config.get("base_path", "D:\\Users\\luzhe\\报销凭证"))
        
        for segment in segments:
            trip_dir = base_path / segment.folder_name
            
            print(f"\n📍 处理行程: {segment.departure_city} -> {segment.destination_city}")
            print(f"   目录: {trip_dir}")
            
            # 下载所有发票邮件的附件到此目录
            for email_data in emails:
                try:
                    files = fetcher.download_attachments(
                        email_data=email_data,
                        output_dir=str(trip_dir),
                        auto_extract=config.get("auto_extract", True)
                    )
                    results["attachments_downloaded"] += len(files)
                except Exception as e:
                    error_msg = f"下载附件失败 ({email_data.get('subject', 'Unknown')}): {e}"
                    print(f"   ❌ {error_msg}")
                    results["errors"].append(error_msg)
    
    finally:
        fetcher.disconnect()
    
    return results


def print_summary(segments: List[TripSegment], results: Dict):
    """打印执行摘要"""
    print("\n" + "=" * 50)
    print("📊 执行摘要")
    print("=" * 50)
    
    print(f"\n🗓️  行程数量: {results['total_trips']}")
    for i, segment in enumerate(segments, 1):
        print(f"   {i}. {segment.departure_city} -> {segment.destination_city}")
        print(f"      {segment.start_date.strftime('%Y-%m-%d')} 至 {segment.end_date.strftime('%Y-%m-%d')}")
        print(f"      目录: {segment.folder_name}")
    
    print(f"\n📧 找到邮件: {results['emails_found']} 封")
    print(f"💾 下载附件: {results['attachments_downloaded']} 个")
    
    if results["errors"]:
        print(f"\n⚠️  错误 ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"   - {error}")
    else:
        print("\n✅ 执行完成，无错误")
    
    print("=" * 50)


def main():
    """主函数"""
    print("🚀 差旅发票抓取器")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print(f"  python {sys.argv[0]} \"行程描述\"")
        print("\n示例:")
        print(f'  python {sys.argv[0]} "2月8日到3月16日，南京到北京，高铁"')
        print(f'  python {sys.argv[0]} "3月1日-3月5日上海出差，3月10日-3月15日深圳出差，都是飞机"')
        sys.exit(1)
    
    # 获取行程描述
    trip_description = " ".join(sys.argv[1:])
    print(f"\n📝 行程描述: {trip_description}")
    
    # 加载配置
    config = load_config()
    
    # 解析行程
    print("\n🔍 解析行程...")
    parser = TripParser()
    segments = parser.parse(trip_description)
    
    if not segments:
        print("❌ 无法解析行程，请检查输入格式")
        print("\n支持的格式:")
        print('  - "2月8日到3月16日，南京到北京，高铁"')
        print('  - "3月1日-3月5日上海出差，3月10日-3月15日深圳出差，都是飞机"')
        print('  - "2025-02-08到2025-03-16，南京到北京"')
        sys.exit(1)
    
    print(f"✅ 解析到 {len(segments)} 段行程")
    
    # 创建目录
    print("\n📁 创建行程目录...")
    created_dirs = create_trip_directories(segments, config["base_path"])
    print(f"✅ 已创建 {len(created_dirs)} 个目录")
    
    # 获取邮箱凭据
    print("\n🔐 读取邮箱凭据...")
    credentials = get_vault_credentials()
    
    if not credentials:
        print("❌ 未找到邮箱凭据")
        print("\n请配置以下环境变量:")
        print("  QQ_EMAIL=你的邮箱地址")
        print("  QQ_EMAIL_PASSWORD=你的邮箱授权码")
        print("\n或在 vault 中配置 qq_email 凭据")
        sys.exit(1)
    
    print(f"✅ 已读取邮箱凭据: {credentials['email']}")
    
    # 抓取发票
    print("\n📧 开始抓取发票...")
    results = fetch_invoices_for_trips(segments, credentials, config)
    
    # 打印摘要
    print_summary(segments, results)


if __name__ == "__main__":
    main()
