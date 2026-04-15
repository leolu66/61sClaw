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


def import_from_fol(count: int = 1, content: str = None) -> List[TripSegment]:
    """
    从 FOL 系统导入行程
    
    Args:
        count: 导入最近几条申请单，默认1条
        content: FOL申请单列表文本（从FOL复制粘贴），为None时自动获取
        
    Returns:
        TripSegment 列表
    """
    print(f"\n📥 从 FOL 系统导入最近 {count} 条申请单...")
    
    applications_data = []
    
    # 如果未提供内容，尝试自动获取
    if not content:
        # 尝试调用 fol_auto_login.py 自动获取
        fol_skill_path = Path.home() / ".openclaw" / "workspace-main" / "skills" / "fol-login"
        auto_login_script = fol_skill_path / "fol_auto_login.py"
        
        if auto_login_script.exists():
            print("🔗 调用 fol_auto_login.py 自动获取申请单...")
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, str(auto_login_script)],
                    capture_output=True,
                    text=True,
                    timeout=150  # 150秒超时
                )
                
                if result.returncode == 0:
                    # 解析返回的 JSON
                    try:
                        data = json.loads(result.stdout)
                        applications_data = data.get('applications', [])
                        print(f"✅ 成功获取 {len(applications_data)} 条申请单")
                    except json.JSONDecodeError as e:
                        print(f"⚠️ 解析返回数据失败: {e}")
                else:
                    print(f"⚠️ fol_auto_login.py 执行失败: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("⏰ fol_auto_login.py 执行超时（150秒）")
            except Exception as e:
                print(f"⚠️ 调用 fol_auto_login.py 失败: {e}")
        else:
            print("⚠️ 未找到 fol_auto_login.py，尝试读取缓存文件...")
    
    # 如果自动获取失败，尝试读取缓存文件
    if not applications_data and not content:
        cache_file = script_dir / "fol_applications.json"
        if cache_file.exists():
            print(f"📁 从缓存文件读取: {cache_file}")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    applications_data = data.get('applications', [])
                    print(f"✅ 从缓存读取 {len(applications_data)} 条申请单")
            except Exception as e:
                print(f"⚠️ 读取缓存文件失败: {e}")
    
    # 如果提供了文本内容，解析它
    if content:
        importer = FOLImporter()
        applications = importer.parse_application_list(content)
        # 转换为新的数据格式
        applications_data = []
        for app in applications:
            applications_data.append({
                'form_no': app.form_no,
                'form_name': app.form_name,
                'description': app.description,
                'submit_time': app.submit_time,
                'status': app.status,
                'departure_city': None,
                'destination_city': None,
                'start_date': None,
                'end_date': None,
                'transport': None
            })
    
    # 如果仍然没有数据，使用模拟数据
    if not applications_data:
        print("⚠️ 未能获取 FOL 申请单数据，使用模拟数据...")
        applications_data = [
            {
                'form_no': '1-SQ12026001948',
                'form_name': '国内差旅申请单',
                'description': '首代工作',
                'submit_time': '2026-02-21 10:05:59',
                'status': '完成',
                'departure_city': '南京',
                'destination_city': '北京',
                'start_date': '2026-02-25',
                'end_date': '2026-03-13',
                'transport': '火车'
            },
            {
                'form_no': '1-SQ12026002686',
                'form_name': '国内差旅申请单',
                'description': '从北京到广州回驻地订票补单',
                'submit_time': '2026-03-10 16:43:29',
                'status': '完成',
                'departure_city': '北京',
                'destination_city': '广州',
                'start_date': '2026-03-13',
                'end_date': '2026-03-18',
                'transport': '飞机'
            }
        ]
    
    print(f"✅ 共 {len(applications_data)} 条申请单")
    
    # 取最近 N 条
    applications_data = applications_data[:count]
    
    segments = []
    for app_data in applications_data:
        print(f"\n📋 处理申请单: {app_data.get('form_no', '未知')}")
        print(f"   描述: {app_data.get('description', '无描述')}")
        
        # 从数据创建 TripSegment
        try:
            from datetime import datetime
            
            start_date_str = app_data.get('start_date')
            end_date_str = app_data.get('end_date')
            
            # 如果日期缺失，从提交时间推断
            if not start_date_str or not end_date_str:
                submit_time = app_data.get('submit_time', '')
                if submit_time:
                    try:
                        submit_date = datetime.strptime(submit_time.split()[0], '%Y-%m-%d')
                        from datetime import timedelta
                        start_date = (submit_date + timedelta(days=3))
                        end_date = (submit_date + timedelta(days=8))
                    except:
                        start_date = datetime.now()
                        end_date = datetime.now()
                else:
                    start_date = datetime.now()
                    end_date = datetime.now()
            else:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            departure = app_data.get('departure_city') or '南京'
            destination = app_data.get('destination_city') or '北京'
            transport = app_data.get('transport') or '火车'
            
            segment = TripSegment(
                departure_city=departure,
                destination_city=destination,
                start_date=start_date,
                end_date=end_date,
                transport_mode=transport,
                form_no=app_data.get('form_no')
            )
            
            segments.append(segment)
            print(f"   ✅ 行程: {segment.departure_city} -> {segment.destination_city}")
            print(f"      日期: {segment.start_date.strftime('%Y-%m-%d')} 至 {segment.end_date.strftime('%Y-%m-%d')}")
            
        except Exception as e:
            print(f"   ⚠️ 创建行程失败: {e}")
    
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
            "sender_whitelist": [
                "12306@rails.com.cn",  # 铁路12306
                "didifapiao@mailgate.xiaojukeji.com",  # 滴滴出行
                "dzfp04@guangzhoumetroz.com",  # 广州地铁
                "invoice@ops.ruubypay.com",  # 如贝支付
                "invoice@info.nuonuo.com",  # 诺诺发票
            ],
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
    创建行程目录并生成行程描述文件
    
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
            
            # 创建行程描述文件 trip_info.json
            create_trip_info_file(trip_dir, segment)
            
        except Exception as e:
            print(f"❌ 创建目录失败 {folder_name}: {e}")
    
    return created_dirs


def create_trip_info_file(trip_dir: Path, segment: TripSegment):
    """
    创建行程描述文件 trip_info.json
    
    Args:
        trip_dir: 行程目录路径
        segment: 行程段信息
    """
    try:
        # 计算总天数
        total_days = (segment.end_date - segment.start_date).days + 1
        
        # 构建行程信息字典
        trip_info = {
            "单号": getattr(segment, 'form_no', ''),  # FOL导入时会有此字段
            "出发日期": segment.start_date.strftime('%Y-%m-%d'),
            "结束日期": segment.end_date.strftime('%Y-%m-%d'),
            "总天数": total_days,
            "出发地": segment.departure_city,
            "出差地": segment.destination_city,
            "交通工具": segment.transport_mode or '',
            "宾馆标准": "",  # 默认空
            "宾馆天数": 0,
            "宿舍天数": total_days  # 默认住宿天数等于总天数
        }
        
        # 写入文件
        trip_info_file = trip_dir / "trip_info.json"
        with open(trip_info_file, 'w', encoding='utf-8') as f:
            json.dump(trip_info, f, ensure_ascii=False, indent=2)
            
        print(f"📝 创建行程描述文件: {trip_info_file.name}")
        
    except Exception as e:
        print(f"   ⚠️ 创建行程描述文件失败: {e}")


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
        earliest_start = None
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
        # 为每个行程单独搜索和下载发票
        base_path = Path(config.get("base_path", "D:\\Users\\luzhe\\报销凭证"))
        
        for segment in segments:
            trip_dir = base_path / segment.folder_name
            
            print(f"\n📍 处理行程: {segment.departure_city} -> {segment.destination_city}")
            print(f"   日期: {segment.start_date.strftime('%Y-%m-%d')} 至 {segment.end_date.strftime('%Y-%m-%d')}")
            print(f"   目录: {trip_dir}")
            
            # 搜索该行程的发票邮件（从出发日期开始到结束日期）
            print(f"🔍 搜索行程日期范围内的发票邮件: {segment.start_date.strftime('%Y-%m-%d')} 至 {segment.end_date.strftime('%Y-%m-%d')}...")
            emails = fetcher.search_invoice_emails(
                days=None,  # 不使用天数限制，使用 start_date 和 end_date
                subject_keywords=config.get("email_subject_keywords", ["发票"]),
                start_date=segment.start_date,
                end_date=segment.end_date,
                sender_whitelist=config.get("sender_whitelist", None)
            )
            
            results["emails_found"] += len(emails)
            
            if not emails:
                print(f"   ⚠️ 未找到该行程的发票邮件")
                continue
            
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
    - 将非PDF文件移入bak目录（保留trip_info.json）
    
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
                # 保留trip_info.json文件
                if file_path.name == "trip_info.json":
                    continue
                
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
