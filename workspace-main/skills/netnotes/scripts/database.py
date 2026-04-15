#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块 - SQLite文章管理（支持标签功能）
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
        
        # 文章表
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
        
        # 标签表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 文章-标签关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS article_tags (
                article_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (article_id, tag_id),
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON articles(category)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tag_name ON tags(name)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_article(self, url: str, title: str, category: str, summary: str, file_path: str, tags: List[str] = None) -> int:
        """
        添加文章记录
        
        Args:
            tags: 标签列表，如 ["OpenClaw", "AI", "教程"]
        
        Returns:
            int: 文章ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 插入或更新文章
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
            
            # 处理标签
            if tags:
                # 先删除旧标签关联
                cursor.execute('DELETE FROM article_tags WHERE article_id = ?', (article_id,))
                
                # 添加新标签
                for tag_name in tags:
                    tag_name = tag_name.strip()
                    if not tag_name:
                        continue
                    
                    # 插入标签（如果不存在）
                    cursor.execute('''
                        INSERT OR IGNORE INTO tags (name) VALUES (?)
                    ''', (tag_name,))
                    
                    # 获取标签ID
                    cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
                    tag_id = cursor.fetchone()[0]
                    
                    # 建立关联
                    cursor.execute('''
                        INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)
                    ''', (article_id, tag_id))
            
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
            article = {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
            article['tags'] = self.get_article_tags(row[0])
            return article
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
            article = {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
            article['tags'] = self.get_article_tags(row[0])
            return article
        return None
    
    def get_article_tags(self, article_id: int) -> List[str]:
        """获取文章的标签列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.name FROM tags t
            JOIN article_tags at ON t.id = at.tag_id
            WHERE at.article_id = ?
            ORDER BY t.name
        ''', (article_id,))
        
        tags = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tags
    
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
        
        articles = []
        for row in rows:
            article = {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
            article['tags'] = self.get_article_tags(row[0])
            articles.append(article)
        
        return articles
    
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
        
        articles = []
        for row in rows:
            article = {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
            article['tags'] = self.get_article_tags(row[0])
            articles.append(article)
        
        return articles
    
    def search_by_tag(self, tag_name: str, limit: int = 50) -> List[Dict]:
        """按标签搜索文章"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.id, a.url, a.title, a.category, a.summary, a.file_path, a.created_at
            FROM articles a
            JOIN article_tags at ON a.id = at.article_id
            JOIN tags t ON at.tag_id = t.id
            WHERE t.name = ?
            ORDER BY a.created_at DESC
            LIMIT ?
        ''', (tag_name, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        articles = []
        for row in rows:
            article = {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
            article['tags'] = self.get_article_tags(row[0])
            articles.append(article)
        
        return articles
    
    def advanced_search(self, keyword: str = None, tag: str = None, category: str = None,
                        date_from: str = None, date_to: str = None, limit: int = 50) -> List[Dict]:
        """
        高级组合查询
        
        Args:
            keyword: 关键词（搜索标题和摘要）
            tag: 标签名
            category: 分类
            date_from: 开始日期 (YYYY-MM-DD)
            date_to: 结束日期 (YYYY-MM-DD)
            limit: 限制数量
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 构建查询
        conditions = []
        params = []
        
        # 基础查询
        if tag:
            # 需要关联标签表
            base_query = '''
                SELECT DISTINCT a.id, a.url, a.title, a.category, a.summary, a.file_path, a.created_at
                FROM articles a
                JOIN article_tags at ON a.id = at.article_id
                JOIN tags t ON at.tag_id = t.id
            '''
            conditions.append('t.name = ?')
            params.append(tag)
        else:
            base_query = '''
                SELECT a.id, a.url, a.title, a.category, a.summary, a.file_path, a.created_at
                FROM articles a
                WHERE 1=1
            '''
        
        # 添加关键词条件
        if keyword:
            conditions.append('(a.title LIKE ? OR a.summary LIKE ?)')
            search_pattern = f'%{keyword}%'
            params.extend([search_pattern, search_pattern])
        
        # 添加分类条件
        if category:
            conditions.append('a.category = ?')
            params.append(category)
        
        # 添加日期条件
        if date_from:
            conditions.append('a.created_at >= ?')
            params.append(f'{date_from} 00:00:00')
        
        if date_to:
            conditions.append('a.created_at <= ?')
            params.append(f'{date_to} 23:59:59')
        
        # 组装SQL
        sql = base_query
        if conditions:
            sql += ' AND ' + ' AND '.join(conditions)
        sql += ' ORDER BY a.created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        articles = []
        for row in rows:
            article = {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
            article['tags'] = self.get_article_tags(row[0])
            articles.append(article)
        
        return articles
        for row in rows:
            article = {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'file_path': row[5],
                'created_at': row[6]
            }
            article['tags'] = self.get_article_tags(row[0])
            articles.append(article)
        
        return articles
    
    def get_all_tags(self) -> List[Dict]:
        """获取所有标签及其使用次数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.name, COUNT(at.article_id) as count
            FROM tags t
            LEFT JOIN article_tags at ON t.id = at.tag_id
            GROUP BY t.id
            ORDER BY count DESC, t.name
        ''')
        
        tags = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        conn.close()
        return tags
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总文章数
        cursor.execute('SELECT COUNT(*) FROM articles')
        total = cursor.fetchone()[0]
        
        # 总标签数
        cursor.execute('SELECT COUNT(*) FROM tags')
        tag_count = cursor.fetchone()[0]
        
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
            'tag_count': tag_count,
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
    
    def add_tags_to_article(self, article_id: int, tags: List[str]):
        """为文章添加标签"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for tag_name in tags:
                tag_name = tag_name.strip()
                if not tag_name:
                    continue
                
                # 插入标签（如果不存在）
                cursor.execute('''
                    INSERT OR IGNORE INTO tags (name) VALUES (?)
                ''', (tag_name,))
                
                # 获取标签ID
                cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
                tag_id = cursor.fetchone()[0]
                
                # 建立关联
                cursor.execute('''
                    INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)
                ''', (article_id, tag_id))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def remove_tag_from_article(self, article_id: int, tag_name: str):
        """从文章中移除标签"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM article_tags 
            WHERE article_id = ? AND tag_id = (SELECT id FROM tags WHERE name = ?)
        ''', (article_id, tag_name))
        
        conn.commit()
        conn.close()
