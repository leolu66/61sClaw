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
        subject_keywords: List[str] = None
    ) -> List[str]:
        """
        搜索发票邮件
        
        Args:
            days: 搜索最近几天的邮件
            subject_keywords: 邮件主题关键词列表
            
        Returns:
            邮件ID列表
        """
        if not self.mail:
            print("❌ 未连接邮箱")
            return []
        
        if subject_keywords is None:
            subject_keywords = ["发票"]
        
        try:
            # 选择收件箱
            status, messages = self.mail.select("INBOX")
            if status != "OK":
                print(f"❌ 无法选择收件箱: {messages}")
                return []
            
            # 计算日期范围
            since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
            
            print(f"🔍 搜索最近{days}天的邮件（自{since_date}起）...")
            
            # 搜索邮件
            # 使用SINCE搜索最近日期的邮件
            search_criteria = f'(SINCE "{since_date}")'
            status, message_ids = self.mail.search(None, search_criteria)
            
            if status != "OK":
                print(f"❌ 搜索邮件失败: {message_ids}")
                return []
            
            email_ids = message_ids[0].split()
            print(f"📧 找到 {len(email_ids)} 封邮件")
            
            # 筛选包含关键词的邮件
            invoice_emails = []
            for email_id in email_ids:
                try:
                    status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # 解码邮件主题
                    subject = self._decode_subject(msg.get("Subject", ""))
                    
                    # 检查主题是否包含关键词
                    for keyword in subject_keywords:
                        if keyword in subject:
                            invoice_emails.append({
                                "id": email_id.decode(),
                                "subject": subject,
                                "from": msg.get("From", ""),
                                "date": msg.get("Date", ""),
                                "message": msg
                            })
                            print(f"  ✉️ 找到发票邮件: {subject}")
                            break
                            
                except Exception as e:
                    print(f"  ⚠️ 处理邮件 {email_id} 时出错: {e}")
                    continue
            
            print(f"📋 共找到 {len(invoice_emails)} 封发票邮件")
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
