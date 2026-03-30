#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件抓取模块
从QQ邮箱通过IMAP协议抓取发票邮件
"""

import imaplib
import email
import os
import re
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import zipfile
import shutil


class EmailFetcher:
    """邮件抓取器"""
    
    def __init__(
        self,
        email_address: str,
        password: str,
        imap_server: str = "imap.qq.com",
        imap_port: int = 993
    ):
        """
        初始化邮件抓取器
        
        Args:
            email_address: 邮箱地址
            password: 邮箱密码或授权码
            imap_server: IMAP服务器地址
            imap_port: IMAP服务器端口
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.mail: Optional[imaplib.IMAP4_SSL] = None
    
    def connect(self) -> bool:
        """
        连接邮箱服务器
        
        Returns:
            是否连接成功
        """
        try:
            print(f"正在连接 {self.imap_server}:{self.imap_port}...")
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_address, self.password)
            print(f"✅ 邮箱登录成功: {self.email_address}")
            return True
        except imaplib.IMAP4.error as e:
            print(f"❌ 邮箱登录失败: {e}")
            print("提示: 请确保已开启QQ邮箱IMAP服务，并使用授权码而非密码")
            return False
        except Exception as e:
            print(f"❌ 连接邮箱失败: {e}")
            return False
    
    def disconnect(self):
        """断开邮箱连接"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                print("📴 已断开邮箱连接")
            except:
                pass
    
    def search_invoice_emails(
        self, 
        days: int = 7,
        subject_keywords: List[str] = None,
        exclude_telecom: bool = True,
        start_date: datetime = None,
        end_date: datetime = None,
        sender_whitelist: List[str] = None
    ) -> List[str]:
        """
        搜索发票邮件
        
        Args:
            days: 搜索最近几天的邮件（当 start_date 为 None 时使用）
            subject_keywords: 邮件主题关键词列表
            exclude_telecom: 是否排除通信运营商发票（移动、联通、电信）
            start_date: 行程开始日期，如果提供则搜索从该日期开始的邮件
            end_date: 行程结束日期，如果提供则只搜索到该日期为止的邮件（包含当天）
            sender_whitelist: 发件人白名单，如果提供则只接受这些发件人的邮件
            
        Returns:
            邮件数据列表
        """
        if not self.mail:
            print("❌ 未连接邮箱")
            return []
        
        if subject_keywords is None:
            subject_keywords = ["发票"]
        
        # 默认发件人白名单（可配置的差旅相关发票发件人）
        if sender_whitelist is None:
            sender_whitelist = [
                "12306@rails.com.cn",  # 铁路12306
                "didifapiao@mailgate.xiaojukeji.com",  # 滴滴出行
                "dzfp04@guangzhoumetroz.com",  # 广州地铁
                "invoice@ops.ruubypay.com",  # 如贝支付
                "invoice@info.nuonuo.com",  # 诺诺发票
            ]
        
        # 通信运营商关键词（排除这些发票）
        telecom_keywords = ["移动", "联通", "电信", "中国移动", "中国联通", "中国电信"]
        
        try:
            # 选择收件箱
            status, messages = self.mail.select("INBOX")
            if status != "OK":
                print(f"❌ 无法选择收件箱: {messages}")
                return []
            
            # 计算日期范围
            if start_date:
                # 使用行程开始日期作为搜索起点
                since_date = start_date.strftime("%d-%b-%Y")
                
                # 如果有结束日期，使用BEFORE来限制范围（BEFORE是排他的，所以要加一天）
                if end_date:
                    before_date = (end_date + timedelta(days=1)).strftime("%d-%b-%Y")
                    # 只按日期范围搜索，不在 IMAP 层面过滤主题
                    # 这样可以确保所有日期范围内的邮件都被搜索到
                    search_criteria = f'(SINCE "{since_date}" BEFORE "{before_date}")'
                    date_range_str = f"{since_date} 至 {end_date.strftime('%d-%b-%Y')}"
                    print(f"🔍 搜索行程日期范围内的邮件: {date_range_str}")
                else:
                    days = (datetime.now() - start_date).days
                    search_criteria = f'(SINCE "{since_date}")'
                    print(f"🔍 搜索从行程开始日期 {since_date} 到今天的邮件（共{days}天）...")
            else:
                # 使用默认的最近N天
                since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
                search_criteria = f'(SINCE "{since_date}")'
                print(f"🔍 搜索最近{days}天的邮件（自{since_date}起）...")
            
            # 搜索邮件
            print(f"   IMAP 搜索条件: {search_criteria}")
            status, message_ids = self.mail.search(None, search_criteria)
            
            if status != "OK":
                print(f"❌ 搜索邮件失败: {message_ids}")
                return []
            
            email_ids = message_ids[0].split()
            total_emails = len(email_ids)
            print(f"📧 找到 {total_emails} 封邮件")
            
            # IMAP 返回的邮件 ID 是升序的（ID 1 是最早的，ID N 是最新的）
            # 倒序处理，从最新的邮件开始处理
            email_ids = email_ids[::-1]  # 倒序：从最新到最旧
            print(f"   将按从新到旧的顺序处理邮件")
            
            # 筛选包含关键词的邮件
            invoice_emails = []
            skipped_telecom = 0
            skipped_sender = 0
            skipped_date_range = 0
            
            # 设置最大发票邮件数量，避免处理过多
            max_invoice_emails = 20  # 找到 20 封发票邮件后停止
            
            for idx, email_id in enumerate(email_ids):
                # 如果已经找到足够的发票邮件，停止处理
                if len(invoice_emails) >= max_invoice_emails:
                    print(f"   ⏹️  已找到 {len(invoice_emails)} 封发票邮件，停止处理")
                    break
                
                try:
                    status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # 解码邮件主题
                    subject = self._decode_subject(msg.get("Subject", ""))
                    
                    # 获取发件人
                    from_address = msg.get("From", "")
                    # 提取邮箱地址（从 "Name <email@example.com>" 格式中提取）
                    from_email = self._extract_email(from_address)
                    
                    # 确保 from_email 是字符串
                    if not isinstance(from_email, str):
                        from_email = str(from_email)
                    
                    # 检查是否为通信运营商发票（需要排除）
                    if exclude_telecom:
                        is_telecom = any(telecom in subject for telecom in telecom_keywords)
                        if is_telecom:
                            skipped_telecom += 1
                            print(f"  ⏭️  跳过通信发票: {subject}")
                            continue
                    
                    # 检查发件人是否在白名单中（如果配置了白名单）
                    if sender_whitelist:
                        is_whitelisted = any(whitelist in from_email.lower() for whitelist in sender_whitelist)
                        if not is_whitelisted:
                            # 发件人不在白名单中，检查主题是否包含关键词
                            has_keyword = any(keyword in subject for keyword in subject_keywords)
                            if not has_keyword:
                                skipped_sender += 1
                                continue  # 跳过此邮件
                    
                    # 检查主题是否包含关键词
                    for keyword in subject_keywords:
                        if keyword in subject:
                            # 获取邮件日期
                            email_date = msg.get("Date", "")
                            
                            # 调试输出
                            parsed_dt = self._parse_email_date(email_date)
                            date_str = parsed_dt.strftime('%Y-%m-%d') if parsed_dt else 'Unknown'
                            print(f"    📧 检查邮件: {subject[:40]}... | 发件人: {from_email[:30]} | 日期: {date_str}")
                            
                            # 如果指定了日期范围，进行精确过滤
                            if start_date and end_date:
                                if not self._is_date_in_range(email_date, start_date, end_date):
                                    # 邮件日期不在范围内，跳过
                                    skipped_date_range += 1
                                    print(f"       ⏭️  跳过: 日期 {date_str} 不在范围 {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
                                    continue
                            elif start_date:
                                # 只有开始日期，检查是否从开始日期之后
                                email_dt = self._parse_email_date(email_date)
                                if email_dt:
                                    start = start_date.date() if isinstance(start_date, datetime) else start_date
                                    if email_dt.date() < start:
                                        skipped_date_range += 1
                                        print(f"       ⏭️  跳过: 日期 {date_str} 早于开始日期 {start}")
                                        continue
                            
                            invoice_emails.append({
                                "id": email_id.decode(),
                                "subject": subject,
                                "from": from_address,
                                "from_email": from_email,
                                "date": email_date,
                                "message": msg
                            })
                            print(f"       ✅ 匹配成功")
                            break
                            
                except Exception as e:
                    print(f"  ⚠️ 处理邮件 {email_id} 时出错: {e}")
                    continue
            
            print(f"📋 共找到 {len(invoice_emails)} 封发票邮件")
            if skipped_telecom > 0:
                print(f"   (已排除 {skipped_telecom} 封通信运营商发票)")
            if skipped_sender > 0:
                print(f"   (已排除 {skipped_sender} 封非白名单发件人邮件)")
            if skipped_date_range > 0:
                print(f"   (已排除 {skipped_date_range} 封日期范围外的邮件)")
            return invoice_emails
            
        except Exception as e:
            print(f"❌ 搜索邮件时出错: {e}")
            return []
    
    def download_attachments(
        self,
        email_data: Dict,
        output_dir: str,
        auto_extract: bool = True
    ) -> List[str]:
        """
        下载邮件附件
        
        Args:
            email_data: 邮件数据字典
            output_dir: 输出目录
            auto_extract: 是否自动解压压缩文件
            
        Returns:
            下载的文件路径列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        downloaded_files = []
        msg = email_data.get("message")
        
        if not msg:
            return downloaded_files
        
        try:
            for part in msg.walk():
                # 跳过 multipart 容器
                if part.get_content_maintype() == "multipart":
                    continue
                
                # 检查是否有附件
                content_disposition = part.get("Content-Disposition", "")
                if "attachment" not in content_disposition:
                    continue
                
                # 获取文件名
                filename = part.get_filename()
                if not filename:
                    continue
                
                # 解码文件名
                filename = self._decode_filename(filename)
                
                # 保存文件
                file_path = output_path / filename
                
                try:
                    with open(file_path, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    print(f"  💾 已下载: {filename}")
                    downloaded_files.append(str(file_path))
                    
                    # 自动解压
                    if auto_extract and self._is_archive_file(filename):
                        self._extract_archive(file_path, output_path)
                        
                except Exception as e:
                    print(f"  ❌ 下载失败 {filename}: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ 处理附件时出错: {e}")
        
        return downloaded_files
    
    def _decode_subject(self, subject: str) -> str:
        """解码邮件主题"""
        if not subject:
            return ""
        
        try:
            decoded_parts = decode_header(subject)
            result = ""
            for part, charset in decoded_parts:
                if isinstance(part, bytes):
                    try:
                        result += part.decode(charset or "utf-8", errors="ignore")
                    except:
                        result += part.decode("utf-8", errors="ignore")
                else:
                    result += part
            return result
        except:
            return subject
    
    def _extract_email(self, from_header: str) -> str:
        """
        从邮件头中提取邮箱地址
        支持格式: "Name <email@example.com>" 或 "email@example.com"
        
        Args:
            from_header: From 邮件头
            
        Returns:
            邮箱地址
        """
        if not from_header:
            return ""
        
        try:
            # 尝试匹配 <email@example.com> 格式
            match = re.search(r'<([^>]+)>', from_header)
            if match:
                return match.group(1).lower().strip()
            
            # 如果没有尖括号，直接返回整个字符串（假设就是邮箱地址）
            return from_header.lower().strip()
        except:
            return from_header.lower().strip()
    
    def _parse_email_date(self, date_str: str) -> Optional[datetime]:
        """
        解析邮件日期字符串为 datetime 对象
        
        Args:
            date_str: 邮件日期字符串（如 "Mon, 23 Mar 2026 10:30:00 +0800"）
            
        Returns:
            datetime 对象，解析失败返回 None
        """
        if not date_str:
            return None
        
        # 清理日期字符串，移除 (CST) 等时区缩写
        cleaned_date = date_str.strip()
        # 移除括号内的时区缩写，如 (CST), (GMT) 等
        import re
        cleaned_date = re.sub(r'\s*\([A-Z]{3,4}\)\s*$', '', cleaned_date)
        
        try:
            # 使用 email.utils.parsedate_to_datetime 解析
            dt = parsedate_to_datetime(cleaned_date)
            # 转换为本地时间（去掉时区信息便于比较）
            return dt.replace(tzinfo=None)
        except Exception as e:
            # 尝试其他格式
            formats = [
                "%a, %d %b %Y %H:%M:%S %z",
                "%d %b %Y %H:%M:%S %z",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%a, %d %b %Y %H:%M:%S %z (%Z)",  # 带括号时区的格式
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(cleaned_date.strip(), fmt)
                except:
                    continue
            
            # 如果都失败，打印调试信息
            print(f"   ⚠️  日期解析失败: '{date_str}'")
            return None
    
    def _is_date_in_range(self, email_date_str: str, start_date: datetime, end_date: datetime) -> bool:
        """
        检查邮件日期是否在指定范围内
        
        Args:
            email_date_str: 邮件日期字符串
            start_date: 开始日期（包含）
            end_date: 结束日期（包含）
            
        Returns:
            是否在范围内
        """
        email_dt = self._parse_email_date(email_date_str)
        if not email_dt:
            # 如果无法解析日期，默认排除该邮件（避免包含过期发票）
            return False
        
        # 只比较日期部分
        email_date = email_dt.date()
        start = start_date.date() if isinstance(start_date, datetime) else start_date
        end = end_date.date() if isinstance(end_date, datetime) else end_date
        
        return start <= email_date <= end
    
    def _decode_filename(self, filename: str) -> str:
        """解码文件名"""
        if not filename:
            return ""
        
        try:
            decoded_parts = decode_header(filename)
            result = ""
            for part, charset in decoded_parts:
                if isinstance(part, bytes):
                    try:
                        result += part.decode(charset or "utf-8", errors="ignore")
                    except:
                        result += part.decode("utf-8", errors="ignore")
                else:
                    result += part
            return result
        except:
            return filename
    
    def _is_archive_file(self, filename: str) -> bool:
        """检查是否为压缩文件"""
        archive_extensions = [".zip", ".rar", ".7z"]
        return any(filename.lower().endswith(ext) for ext in archive_extensions)
    
    def _extract_archive(self, archive_path: Path, output_dir: Path):
        """解压压缩文件"""
        try:
            if archive_path.suffix.lower() == ".zip":
                self._extract_zip(archive_path, output_dir)
            elif archive_path.suffix.lower() == ".rar":
                self._extract_rar(archive_path, output_dir)
            elif archive_path.suffix.lower() == ".7z":
                self._extract_7z(archive_path, output_dir)
        except Exception as e:
            print(f"  ⚠️ 解压失败 {archive_path.name}: {e}")
    
    def _extract_zip(self, archive_path: Path, output_dir: Path):
        """解压ZIP文件"""
        try:
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(output_dir)
            print(f"  📂 已解压 ZIP: {archive_path.name}")
        except Exception as e:
            raise Exception(f"ZIP解压失败: {e}")
    
    def _extract_rar(self, archive_path: Path, output_dir: Path):
        """解压RAR文件"""
        try:
            # 尝试使用rarfile库
            import rarfile
            with rarfile.RarFile(archive_path, "r") as rar_ref:
                rar_ref.extractall(output_dir)
            print(f"  📂 已解压 RAR: {archive_path.name}")
        except ImportError:
            print(f"  ⚠️ 未安装 rarfile 库，无法解压 RAR: {archive_path.name}")
            print("     请运行: pip install rarfile")
        except Exception as e:
            raise Exception(f"RAR解压失败: {e}")
    
    def _extract_7z(self, archive_path: Path, output_dir: Path):
        """解压7Z文件"""
        try:
            # 尝试使用py7zr库
            import py7zr
            with py7zr.SevenZipFile(archive_path, "r") as sz_ref:
                sz_ref.extractall(output_dir)
            print(f"  📂 已解压 7Z: {archive_path.name}")
        except ImportError:
            print(f"  ⚠️ 未安装 py7zr 库，无法解压 7Z: {archive_path.name}")
            print("     请运行: pip install py7zr")
        except Exception as e:
            raise Exception(f"7Z解压失败: {e}")


def test_email_fetcher():
    """测试邮件抓取器"""
    # 注意：这只是一个示例，实际使用时需要从vault读取凭据
    print("邮件抓取模块测试")
    print("请确保已配置QQ邮箱IMAP访问权限")


if __name__ == "__main__":
    test_email_fetcher()
