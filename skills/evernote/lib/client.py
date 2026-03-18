#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印象笔记客户端 - 基于官方 SDK 实现
"""

import os
import sys
import hashlib
import time
from datetime import datetime

# 添加 SDK 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# 导入官方 SDK
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.ttypes import Note, Notebook, Tag, Resource, Data
from evernote.edam.error.ttypes import EDAMUserException, EDAMSystemException, EDAMNotFoundException

# Thrift 导入
from thrift.transport import THttpClient
from thrift.protocol import TBinaryProtocol

class EvernoteClient:
    """印象笔记客户端"""
    
    def __init__(self, auth_token=None, notestore_url=None):
        """
        初始化客户端
        
        Args:
            auth_token: Developer Token
            notestore_url: NoteStore URL
        """
        self.auth_token = auth_token or os.getenv('EVERNOTE_TOKEN')
        self.notestore_url = notestore_url or os.getenv(
            'EVERNOTE_NOTESTORE_URL', 
            'https://app.yinxiang.com/shard/s19/notestore'
        )
        
        if not self.auth_token:
            raise ValueError("需要提供 auth_token 或设置 EVERNOTE_TOKEN 环境变量")
        
        # 初始化 NoteStore 客户端
        self._init_notestore()
        
    def _init_notestore(self):
        """初始化 NoteStore 连接"""
        self.transport = THttpClient.THttpClient(self.notestore_url)
        self.transport.setCustomHeaders({
            'Authorization': f'Bearer {self.auth_token}'
        })
        self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        
        # 动态创建 NoteStore 客户端
        from evernote.edam.notestore import NoteStore
        self.note_store = NoteStore.Client(self.protocol)
        
    def test_connection(self):
        """测试连接"""
        try:
            # 尝试列出笔记本来测试连接
            self.transport.open()
            notebooks = self.note_store.listNotebooks(self.auth_token)
            self.transport.close()
            return len(notebooks) >= 0
        except Exception as e:
            print(f"[ERROR] 连接失败: {e}", file=sys.stderr)
            return False
    
    def create_note(self, title, content, notebook_guid=None, tag_names=None):
        """
        创建笔记
        
        Args:
            title: 笔记标题
            content: 笔记内容（纯文本或 HTML）
            notebook_guid: 笔记本 GUID（可选）
            tag_names: 标签名称列表（可选）
            
        Returns:
            dict: 创建的笔记信息
        """
        try:
            # 创建 Note 对象
            note = Note()
            note.title = title
            
            # 构建 ENML 内容
            if not content.startswith('<?xml'):
                content_html = self._text_to_enml(content)
            else:
                content_html = content
            
            note.content = content_html
            
            if notebook_guid:
                note.notebookGuid = notebook_guid
            
            if tag_names:
                note.tagNames = tag_names
            
            # 调用 API 创建笔记
            self.transport.open()
            created_note = self.note_store.createNote(self.auth_token, note)
            self.transport.close()
            
            return {
                'guid': created_note.guid,
                'title': created_note.title,
                'created': datetime.fromtimestamp(created_note.created / 1000).isoformat(),
                'updated': datetime.fromtimestamp(created_note.updated / 1000).isoformat(),
                'notebookGuid': created_note.notebookGuid,
                'tagNames': created_note.tagNames
            }
                
        except EDAMUserException as e:
            print(f"[ERROR] 用户错误: {e.parameter} - {e.errorCode}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"[ERROR] 创建笔记失败: {e}", file=sys.stderr)
            return None
    
    def list_notebooks(self):
        """
        列出所有笔记本
        
        Returns:
            list: 笔记本列表
        """
        try:
            self.transport.open()
            notebooks = self.note_store.listNotebooks(self.auth_token)
            self.transport.close()
            
            return [
                {
                    'guid': nb.guid,
                    'name': nb.name,
                    'defaultNotebook': nb.defaultNotebook,
                    'serviceCreated': datetime.fromtimestamp(nb.serviceCreated / 1000).isoformat() if nb.serviceCreated else None,
                    'serviceUpdated': datetime.fromtimestamp(nb.serviceUpdated / 1000).isoformat() if nb.serviceUpdated else None
                }
                for nb in notebooks
            ]
            
        except Exception as e:
            print(f"[ERROR] 列出笔记本失败: {e}", file=sys.stderr)
            return []
    
    def search_notes(self, query, max_results=10):
        """
        搜索笔记
        
        Args:
            query: 搜索关键词
            max_results: 最大返回数量
            
        Returns:
            list: 笔记列表
        """
        try:
            # 创建过滤器
            filter = NoteFilter()
            filter.words = query
            
            # 创建结果规格
            result_spec = NotesMetadataResultSpec()
            result_spec.includeTitle = True
            result_spec.includeCreated = True
            result_spec.includeUpdated = True
            result_spec.includeNotebookGuid = True
            
            # 搜索
            self.transport.open()
            result = self.note_store.findNotesMetadata(self.auth_token, filter, 0, max_results, result_spec)
            self.transport.close()
            
            if result and result.notes:
                return [
                    {
                        'guid': note.guid,
                        'title': note.title,
                        'created': datetime.fromtimestamp(note.created / 1000).isoformat() if note.created else None,
                        'updated': datetime.fromtimestamp(note.updated / 1000).isoformat() if note.updated else None,
                        'notebookGuid': note.notebookGuid
                    }
                    for note in result.notes
                ]
            else:
                return []
                
        except Exception as e:
            print(f"[ERROR] 搜索笔记失败: {e}", file=sys.stderr)
            return []
    
    def _text_to_enml(self, text):
        """
        将纯文本转换为 ENML 格式
        
        Args:
            text: 纯文本
            
        Returns:
            str: ENML 格式内容
        """
        # HTML 转义
        content_html = text.replace('&', '&amp;')
        content_html = content_html.replace('<', '&lt;')
        content_html = content_html.replace('>', '&gt;')
        content_html = content_html.replace('"', '&quot;')
        
        # 换行转 <br/>
        content_html = content_html.replace('\n', '<br/\u003e')
        
        # 构建 ENML
        enml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note><div>{content_html}</div></en-note>'''
        
        return enml.strip()

if __name__ == '__main__':
    # 测试
    client = EvernoteClient()
    if client.test_connection():
        print("[OK] 印象笔记连接成功")
        
        # 列出笔记本
        notebooks = client.list_notebooks()
        print(f"\n找到 {len(notebooks)} 个笔记本:")
        for nb in notebooks[:5]:
            print(f"  - {nb['name']}")
    else:
        print("[ERROR] 印象笔记连接失败")
