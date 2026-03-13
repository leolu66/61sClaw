#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块 - SQLite文章管理
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime


class ArticleDatabase:
    """文章数据库管理"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT,
                file_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON articles(category)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_article(self, url: str, title: str, category: str, summary: str, file_path: str) -> int:
        """
        添加文章记录
        
        Returns:
            int: 文章ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO articles (url, title, category, summary, file_path, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title=excluded.title,
                    category=excluded.category,
                    summary=excluded.summary,
                    file_path=excluded.file_path,
                    updated_at=excluded.updated_at
            ''', (url, title, category, summary, file_path, datetime.now().isoformat()))
            
            article_id = cursor.lastrowid
            conn.commit()
            return article_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_article_by_url(self, url: str) -> Optional[Dict]:
        """根据URL获取文章"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, url, title, category, summary, file_path, created_at
            FROM articles WHERE url = ?
        ''', (url,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
        return None
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """根据ID获取文章"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, url, title, category, summary, file_path, created_at
            FROM articles WHERE id = ?
        ''', (article_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
        return None
    
    def list_articles(self, category: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """列出文章"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT id, url, title, category, summary, file_path, created_at
                FROM articles WHERE category = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT id, url, title, category, summary, file_path, created_at
                FROM articles
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
            for row in rows
        ]
    
    def search_articles(self, keyword: str, limit: int = 50) -> List[Dict]:
        """搜索文章"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_pattern = f'%{keyword}%'
        
        cursor.execute('''
            SELECT id, url, title, category, summary, file_path, created_at
            FROM articles
            WHERE title LIKE ? OR summary LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (search_pattern, search_pattern, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
            for row in rows
        ]
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总文章数
        cursor.execute('SELECT COUNT(*) FROM articles')
        total = cursor.fetchone()[0]
        
        # 各分类数量
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM articles
            GROUP BY category
            ORDER BY count DESC
        ''')
        
        categories = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        return {
            'total': total,
            'categories': categories
        }
    
    def delete_article(self, article_id: int) -> bool:
        """删除文章记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM articles WHERE id = ?', (article_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
