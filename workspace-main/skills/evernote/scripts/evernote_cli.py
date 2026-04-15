#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印象笔记技能主脚本
支持：创建笔记、更新笔记、删除笔记、搜索笔记、查看笔记本、管理标签
"""

import sys
import os
import json
import argparse

# 添加 lib 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from client import EvernoteClient

def create_note(title, content, notebook=None, tags=None):
    """创建笔记"""
    try:
        client = EvernoteClient()
        
        # 获取笔记本 GUID
        notebook_guid = None
        if notebook:
            notebooks = client.list_notebooks()
            for nb in notebooks:
                if nb['name'] == notebook:
                    notebook_guid = nb['guid']
                    break
        
        note = client.create_note(title, content, notebook_guid, tags)
        
        if note:
            result = {
                'success': True,
                'action': 'create_note',
                'note': note
            }
            print(json.dumps(result, ensure_ascii=False))
            return True
        else:
            raise Exception("创建笔记失败")
        
    except Exception as e:
        result = {
            'success': False,
            'action': 'create_note',
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        return False

def update_note(guid, title=None, content=None, notebook=None):
    """更新笔记"""
    try:
        client = EvernoteClient()
        
        # 获取笔记本 GUID
        notebook_guid = None
        if notebook:
            notebooks = client.list_notebooks()
            for nb in notebooks:
                if nb['name'] == notebook:
                    notebook_guid = nb['guid']
                    break
        
        note = client.update_note(guid, title, content, notebook_guid)
        
        if note:
            result = {
                'success': True,
                'action': 'update_note',
                'note': note
            }
            print(json.dumps(result, ensure_ascii=False))
            return True
        else:
            raise Exception("更新笔记失败")
        
    except Exception as e:
        result = {
            'success': False,
            'action': 'update_note',
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        return False

def delete_note(guid):
    """删除笔记"""
    try:
        client = EvernoteClient()
        success = client.delete_note(guid)
        
        result = {
            'success': success,
            'action': 'delete_note',
            'guid': guid
        }
        print(json.dumps(result, ensure_ascii=False))
        return success
        
    except Exception as e:
        result = {
            'success': False,
            'action': 'delete_note',
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        return False

def get_note(guid):
    """获取笔记详情"""
    try:
        client = EvernoteClient()
        note = client.get_note(guid)
        
        if note:
            result = {
                'success': True,
                'action': 'get_note',
                'note': note
            }
            print(json.dumps(result, ensure_ascii=False))
            return True
        else:
            raise Exception("笔记不存在")
        
    except Exception as e:
        result = {
            'success': False,
            'action': 'get_note',
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        return False

def list_notebooks():
    """列出笔记本"""
    try:
        client = EvernoteClient()
        notebooks = client.list_notebooks()
        
        result = {
            'success': True,
            'action': 'list_notebooks',
            'count': len(notebooks),
            'notebooks': notebooks
        }
        print(json.dumps(result, ensure_ascii=False))
        return True
        
    except Exception as e:
        result = {
            'success': False,
            'action': 'list_notebooks',
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        return False

def search_notes(query, max_results=10):
    """搜索笔记"""
    try:
        client = EvernoteClient()
        notes = client.search_notes(query, max_results)
        
        result = {
            'success': True,
            'action': 'search_notes',
            'query': query,
            'count': len(notes),
            'notes': notes
        }
        print(json.dumps(result, ensure_ascii=False))
        return True
        
    except Exception as e:
        result = {
            'success': False,
            'action': 'search_notes',
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        return False

def list_tags():
    """列出标签"""
    try:
        client = EvernoteClient()
        tags = client.list_tags()
        
        result = {
            'success': True,
            'action': 'list_tags',
            'count': len(tags),
            'tags': tags
        }
        print(json.dumps(result, ensure_ascii=False))
        return True
        
    except Exception as e:
        result = {
            'success': False,
            'action': 'list_tags',
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        return False

def create_tag(name):
    """创建标签"""
    try:
        client = EvernoteClient()
        tag = client.create_tag(name)
        
        if tag:
            result = {
                'success': True,
                'action': 'create_tag',
                'tag': tag
            }
            print(json.dumps(result, ensure_ascii=False))
            return True
        else:
            raise Exception("创建标签失败")
        
    except Exception as e:
        result = {
            'success': False,
            'action': 'create_tag',
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        return False

def test_connection():
    """测试连接"""
    try:
        client = EvernoteClient()
        if client.test_connection():
            result = {
                'success': True,
                'action': 'test_connection',
                'message': '印象笔记连接成功'
            }
            print(json.dumps(result, ensure_ascii=False))
            return True
        else:
            raise Exception("连接失败")
            
    except Exception as e:
        result = {
            'success': False,
            'action': 'test_connection',
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        return False

def main():
    parser = argparse.ArgumentParser(description='印象笔记技能')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建笔记
    create_parser = subparsers.add_parser('create', help='创建笔记')
    create_parser.add_argument('title', help='笔记标题')
    create_parser.add_argument('content', help='笔记内容')
    create_parser.add_argument('--notebook', '-n', help='笔记本名称')
    create_parser.add_argument('--tags', '-t', help='标签（逗号分隔）')
    
    # 更新笔记
    update_parser = subparsers.add_parser('update', help='更新笔记')
    update_parser.add_argument('guid', help='笔记GUID')
    update_parser.add_argument('--title', help='新标题')
    update_parser.add_argument('--content', help='新内容')
    update_parser.add_argument('--notebook', help='新笔记本')
    
    # 删除笔记
    delete_parser = subparsers.add_parser('delete', help='删除笔记')
    delete_parser.add_argument('guid', help='笔记GUID')
    
    # 获取笔记
    get_parser = subparsers.add_parser('get', help='获取笔记详情')
    get_parser.add_argument('guid', help='笔记GUID')
    
    # 列出笔记本
    subparsers.add_parser('notebooks', help='列出笔记本')
    
    # 搜索笔记
    search_parser = subparsers.add_parser('search', help='搜索笔记')
    search_parser.add_argument('query', help='搜索关键词')
    search_parser.add_argument('--max', '-m', type=int, default=10, help='最大结果数')
    
    # 列出标签
    subparsers.add_parser('tags', help='列出标签')
    
    # 创建标签
    tag_parser = subparsers.add_parser('create-tag', help='创建标签')
    tag_parser.add_argument('name', help='标签名称')
    
    # 测试连接
    subparsers.add_parser('test', help='测试连接')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        tags = args.tags.split(',') if args.tags else None
        return create_note(args.title, args.content, args.notebook, tags)
    
    elif args.command == 'update':
        return update_note(args.guid, args.title, args.content, args.notebook)
    
    elif args.command == 'delete':
        return delete_note(args.guid)
    
    elif args.command == 'get':
        return get_note(args.guid)
    
    elif args.command == 'notebooks':
        return list_notebooks()
    
    elif args.command == 'search':
        return search_notes(args.query, args.max)
    
    elif args.command == 'tags':
        return list_tags()
    
    elif args.command == 'create-tag':
        return create_tag(args.name)
    
    elif args.command == 'test':
        return test_connection()
    
    else:
        parser.print_help()
        return False

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
