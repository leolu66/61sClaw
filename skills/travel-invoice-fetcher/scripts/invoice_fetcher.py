#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
差旅发票抓取器主脚本
根据用户行程描述，自动创建目录并从邮箱抓取发票
"""

import json
import os
import sys
import io
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加脚本目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from trip_parser import TripParser, TripSegment
from email_fetcher import EmailFetcher
from fol_importer import FOLImporter, FOLApplication


def import_from_fol(count: int = 1) -> List[TripSegment]:
    """
    从 FOL 系统导入行程
    
    Args:
        count: 导入最近几条申请单，默认1条
        
    Returns:
        TripSegment 列表
    """
    print(f"\n📥 从 FOL 系统导入最近 {count} 条申请单...")
    
    # 调用 fol-login 技能获取申请单列表
    fol_skill_path = Path.home() / ".openclaw" / "workspace-main" / "skills" / "fol-login"
    login_script = fol_skill_path / "login.py"
    
    if not login_script.exists():
        print("❌ 未找到 fol-login 技能，请确保已安装")
        return []
    
    # 使用浏览器自动化获取申请单列表（简化版：读取本地缓存或手动输入）
    print("⚠️ 请手动复制 FOL 系统中'我的申请单'列表内容")
    print("操作步骤：")
    print("  1. 登录 FOL 系统: https://fol.iwhalecloud.com/")
    print("  2. 进入 费用申请 -> 我的申请单")
    print("  3. 复制表格中的申请单信息")
    print("  4. 粘贴到下方（输入 END 结束）：")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        except EOFError:
            break
    
    content = "\n".join(lines)
    
    if not content.strip():
        print("⚠️ 未输入任何内容")
        return []
    
    # 解析申请单
    importer = FOLImporter()
    applications = importer.parse_application_list(content)
    
    print(f"✅ 解析到 {len(applications)} 条申请单")
    
    # 取最近 N 条
    applications = applications[:count]
    
    segments = []
    for app in applications:
        print(f"\n📋 处理申请单: {app.form_no}")
        print(f"   描述: {app.description}")
        
        # 询问是否查看详情
        print(f"   请输入该申请单的行程详情（从详情页复制出发日期、结束日期、出发地、出差地、交通工具，或输入 SKIP 跳过）：")
        detail_lines = []
        while True:
            try:
                line = input()
                if line.strip() in ["SKIP", "END"]:
                    break
                detail_lines.append(line)
            except EOFError:
                break
        
        detail_text = "\n".join(detail_lines)
        
        if detail_text.strip() and detail_text.strip() != "SKIP":
            # 解析详情
            detail_info = importer.parse_application_detail(detail_text)
            segment = importer.to_trip_segment(app, detail_info)
        else:
            # 从描述推断
            segment = importer.to_trip_segment(app)
        
        if segment:
            segments.append(segment)
            print(f"   ✅ 行程: {segment.departure_city} -> {segment.destination_city}")
        else:
            print(f"   ⚠️ 无法转换为行程")
    
    return segments


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
    读取邮箱凭据
    
    Returns:
        包含 email 和 password 的字典，或 None
    """
    try:
        # 首先检查 IMAP_QQ_AUTH_CODE 环境变量（推荐方式）
        auth_code = os.environ.get("IMAP_QQ_AUTH_CODE")
        if auth_code:
            # 默认使用 QQ 邮箱
            return {"email": "lu.zhen9@qq.com", "password": auth_code}
        
        # 检查用户级环境变量（永久设置）
        import subprocess
        try:
            result = subprocess.run(
                ['powershell', '-Command', '[Environment]::GetEnvironmentVariable(\"IMAP_QQ_AUTH_CODE\", \"User\")'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return {"email": "lu.zhen9@qq.com", "password": result.stdout.strip()}
        except:
            pass
        
        # 尝试从工作区 vault 目录读取
        vault_key = "qq_email"
        workspace_vault = Path.home() / ".openclaw" / "vault" / "credentials.json"
        if workspace_vault.exists():
            with open(workspace_vault, "r", encoding="utf-8") as f:
                vault_data = json.load(f)
                cred_data = vault_data.get('credentials', {}).get(vault_key)
                if cred_data:
                    # 从 vault 结构中提取字段
                    fields = {}
                    for field in cred_data.get('fields', []):
                        key = field.get('key')
                        value = field.get('value', '')
                        fields[key] = value
                    
                    email = fields.get('email', 'lu.zhen9@qq.com')
                    password = fields.get('password')
                    if password:
                        return {"email": email, "password": password}
        
        return None
        
    except Exception as e:
        print(f"⚠️ 读取凭据失败: {e}")
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
    
    # 计算搜索天数：从最早的行程开始日期到今天的天数
    if segments:
        earliest_start = min(segment.start_date for segment in segments)
        today = datetime.now()
        search_days = (today - earliest_start).days + 7  # 加7天缓冲期
        search_days = max(search_days, config.get("search_days", 7))  # 至少使用配置的默认天数
        print(f"🔍 搜索范围: 自 {earliest_start.strftime('%Y-%m-%d')} 起，共 {search_days} 天")
    else:
        search_days = config.get("search_days", 7)
    
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
            days=search_days,
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
            
            # 整理文件：将非PDF文件移入bak子目录
            organize_files(trip_dir)
    
    finally:
        fetcher.disconnect()
    
    return results


def organize_files(trip_dir: Path):
    """
    整理行程目录下的文件
    - 创建bak子目录
    - 将非PDF文件移入bak目录
    
    Args:
        trip_dir: 行程目录路径
    """
    try:
        # 创建bak子目录
        bak_dir = trip_dir / "bak"
        bak_dir.mkdir(exist_ok=True)
        
        # 遍历目录下的所有文件
        moved_count = 0
        for file_path in trip_dir.iterdir():
            if file_path.is_file():
                # 检查是否为PDF文件
                if file_path.suffix.lower() != ".pdf":
                    # 移动非PDF文件到bak目录
                    target_path = bak_dir / file_path.name
                    # 如果目标文件已存在，添加数字后缀
                    counter = 1
                    original_target = target_path
                    while target_path.exists():
                        stem = original_target.stem
                        suffix = original_target.suffix
                        target_path = bak_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    file_path.rename(target_path)
                    moved_count += 1
                    print(f"   📦 已移动: {file_path.name} -> bak/")
        
        if moved_count > 0:
            print(f"   ✅ 已整理 {moved_count} 个非PDF文件到 bak/ 目录")
        else:
            print(f"   ℹ️  无需整理，所有文件都是PDF格式")
            
    except Exception as e:
        print(f"   ⚠️ 整理文件时出错: {e}")


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
        print(f"  python {sys.argv[0]} --fol [数量]        # 从FOL导入行程，默认1条")
        print(f"  python {sys.argv[0]} --fol-import 3       # 从FOL导入最近3条")
        print("\n示例:")
        print(f'  python {sys.argv[0]} "2月8日到3月16日，南京到北京，高铁"')
        print(f'  python {sys.argv[0]} "3月1日-3月5日上海出差，3月10日-3月15日深圳出差，都是飞机"')
        print(f'  python {sys.argv[0]} --fol                # 导入FOL最近1条')
        print(f'  python {sys.argv[0]} --fol 3              # 导入FOL最近3条')
        sys.exit(1)
    
    # 加载配置
    config = load_config()
    
    # 解析命令行参数
    arg1 = sys.argv[1].lower()
    segments = []
    
    if arg1 in ['--fol', '--fol-import', 'fol', 'fol-import']:
        # 从 FOL 导入
        count = 1
        if len(sys.argv) >= 3:
            try:
                count = int(sys.argv[2])
            except ValueError:
                print(f"⚠️ 无效的数量参数: {sys.argv[2]}，使用默认值 1")
        
        segments = import_from_fol(count)
        
        if not segments:
            print("❌ 未能从 FOL 导入任何行程")
            sys.exit(1)
    else:
        # 正常行程描述解析
        trip_description = " ".join(sys.argv[1:])
        print(f"\n📝 行程描述: {trip_description}")
        
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
