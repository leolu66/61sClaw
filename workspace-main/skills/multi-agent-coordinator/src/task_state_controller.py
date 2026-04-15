#!/usr/bin/env python3
"""
任务状态控制模块 (Task State Controller)
使用 SQLite 管理多智能体协作任务的全生命周期状态

状态流转:
    pending → sent → received → running → completed/failed → closed

作者: kimi
创建时间: 2026-03-05
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"       # 待发送
    SENT = "sent"            # 已发送
    RECEIVED = "received"    # 已接收
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CLOSED = "closed"        # 已关闭


class TaskStateController:
    """
    任务状态控制器
    
    使用 SQLite 数据库管理任务状态，支持：
    - 任务创建、状态更新、查询
    - 状态历史记录
    - 任务统计和监控
    """
    
    def __init__(self, db_path: str = None):
        """
        初始化控制器
        
        Args:
            db_path: 数据库文件路径，默认使用 config 目录
        """
        if db_path is None:
            # 默认路径: workspace-main/config/task_states.db
            base_dir = Path(__file__).parent.parent.parent.parent
            db_path = base_dir / "config" / "task_states.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 主任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    sender TEXT NOT NULL,
                    receiver TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    received_at TIMESTAMP,
                    running_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    closed_at TIMESTAMP,
                    output_dir TEXT,
                    claude_workspace TEXT,
                    error_msg TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 2,
                    metadata TEXT  -- JSON 格式存储额外信息
                )
            """)
            
            # 状态历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    from_status TEXT,
                    to_status TEXT NOT NULL,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    changed_by TEXT,  -- 谁触发的状态变更
                    reason TEXT,      -- 变更原因
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_task ON task_history(task_id)
            """)
            
            conn.commit()
    
    def create_task(
        self,
        task_id: str,
        title: str,
        sender: str,
        receiver: str,
        description: str = None,
        output_dir: str = None,
        claude_workspace: str = None,
        metadata: Dict = None
    ) -> bool:
        """
        创建新任务
        
        Args:
            task_id: 任务唯一ID
            title: 任务标题
            sender: 发送者节点ID
            receiver: 接收者节点ID
            description: 任务描述
            output_dir: 输出目录
            claude_workspace: Claude Code 工作区路径
            metadata: 额外元数据
        
        Returns:
            是否创建成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tasks (
                        task_id, title, description, status,
                        sender, receiver, output_dir, claude_workspace, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    title,
                    description,
                    TaskStatus.PENDING.value,
                    sender,
                    receiver,
                    output_dir,
                    claude_workspace,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                
                # 记录初始状态
                self._record_history(task_id, None, TaskStatus.PENDING.value, "system", "任务创建")
                return True
        except sqlite3.IntegrityError:
            print(f"[错误] 任务已存在: {task_id}")
            return False
        except Exception as e:
            print(f"[错误] 创建任务失败: {e}")
            return False
    
    def update_status(
        self,
        task_id: str,
        new_status: TaskStatus,
        changed_by: str = "system",
        reason: str = None,
        error_msg: str = None
    ) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            new_status: 新状态
            changed_by: 谁触发的变更
            reason: 变更原因
            error_msg: 错误信息（失败时使用）
        
        Returns:
            是否更新成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取当前状态
                cursor.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,))
                row = cursor.fetchone()
                if not row:
                    print(f"[错误] 任务不存在: {task_id}")
                    return False
                
                old_status = row[0]
                
                # 构建更新字段
                update_fields = ["status = ?"]
                params = [new_status.value]
                
                # 根据状态设置时间戳
                timestamp_fields = {
                    TaskStatus.SENT: "sent_at",
                    TaskStatus.RECEIVED: "received_at",
                    TaskStatus.RUNNING: "running_at",
                    TaskStatus.COMPLETED: "completed_at",
                    TaskStatus.FAILED: "completed_at",
                    TaskStatus.CLOSED: "closed_at"
                }
                
                if new_status in timestamp_fields:
                    field = timestamp_fields[new_status]
                    update_fields.append(f"{field} = CURRENT_TIMESTAMP")
                
                # 错误信息
                if error_msg:
                    update_fields.append("error_msg = ?")
                    params.append(error_msg)
                
                params.append(task_id)
                
                # 执行更新
                cursor.execute(f"""
                    UPDATE tasks 
                    SET {', '.join(update_fields)}
                    WHERE task_id = ?
                """, params)
                
                conn.commit()
                
                # 记录历史
                self._record_history(task_id, old_status, new_status.value, changed_by, reason)
                
                print(f"[状态] {task_id}: {old_status} → {new_status.value}")
                return True
                
        except Exception as e:
            print(f"[错误] 更新状态失败: {e}")
            return False
    
    def _record_history(
        self,
        task_id: str,
        from_status: Optional[str],
        to_status: str,
        changed_by: str,
        reason: str
    ):
        """记录状态变更历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO task_history (task_id, from_status, to_status, changed_by, reason)
                    VALUES (?, ?, ?, ?, ?)
                """, (task_id, from_status, to_status, changed_by, reason))
                conn.commit()
        except Exception as e:
            print(f"[警告] 记录历史失败: {e}")
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务详情
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务信息字典，不存在返回 None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
                row = cursor.fetchone()
                
                if row:
                    task = dict(row)
                    if task.get('metadata'):
                        task['metadata'] = json.loads(task['metadata'])
                    return task
                return None
        except Exception as e:
            print(f"[错误] 查询任务失败: {e}")
            return None
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Dict[str, Any]]:
        """
        按状态查询任务
        
        Args:
            status: 任务状态
        
        Returns:
            任务列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM tasks 
                    WHERE status = ?
                    ORDER BY created_at DESC
                """, (status.value,))
                rows = cursor.fetchall()
                
                tasks = []
                for row in rows:
                    task = dict(row)
                    if task.get('metadata'):
                        task['metadata'] = json.loads(task['metadata'])
                    tasks.append(task)
                return tasks
        except Exception as e:
            print(f"[错误] 查询任务失败: {e}")
            return []
    
    def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取任务状态历史
        
        Args:
            task_id: 任务ID
        
        Returns:
            状态变更历史列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM task_history 
                    WHERE task_id = ?
                    ORDER BY changed_at ASC
                """, (task_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"[错误] 查询历史失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取任务统计
        
        Returns:
            各状态任务数量统计
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM tasks 
                    GROUP BY status
                """)
                rows = cursor.fetchall()
                
                stats = {status.value: 0 for status in TaskStatus}
                for row in rows:
                    stats[row[0]] = row[1]
                
                # 总数
                cursor.execute("SELECT COUNT(*) FROM tasks")
                stats['total'] = cursor.fetchone()[0]
                
                return stats
        except Exception as e:
            print(f"[错误] 统计失败: {e}")
            return {}
    
    def increment_retry(self, task_id: str) -> bool:
        """
        增加重试次数
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tasks 
                    SET retry_count = retry_count + 1
                    WHERE task_id = ?
                """, (task_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"[错误] 更新重试次数失败: {e}")
            return False
    
    def should_retry(self, task_id: str) -> bool:
        """
        判断是否应该重试
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否应该重试
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        return task['retry_count'] < task['max_retries']
    
    def list_active_tasks(self) -> List[Dict[str, Any]]:
        """
        获取活跃任务列表（未关闭的任务）
        
        Returns:
            活跃任务列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM tasks 
                    WHERE status NOT IN ('closed', 'completed', 'failed')
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                
                tasks = []
                for row in rows:
                    task = dict(row)
                    if task.get('metadata'):
                        task['metadata'] = json.loads(task['metadata'])
                    tasks.append(task)
                return tasks
        except Exception as e:
            print(f"[错误] 查询活跃任务失败: {e}")
            return []
    
    def close_task(self, task_id: str, changed_by: str = "system") -> bool:
        """
        关闭任务
        
        Args:
            task_id: 任务ID
            changed_by: 谁关闭的
        
        Returns:
            是否成功
        """
        return self.update_status(
            task_id,
            TaskStatus.CLOSED,
            changed_by,
            "任务完成，已关闭"
        )


# 便捷函数：获取默认控制器实例
_default_controller = None

def get_controller(db_path: str = None) -> TaskStateController:
    """获取默认的任务状态控制器实例"""
    global _default_controller
    if _default_controller is None:
        _default_controller = TaskStateController(db_path)
    return _default_controller


# 测试代码
if __name__ == "__main__":
    # 创建控制器
    ctrl = TaskStateController()
    
    # 创建测试任务
    task_id = "test-task-001"
    ctrl.create_task(
        task_id=task_id,
        title="测试任务",
        sender="kimi",
        receiver="claude",
        description="这是一个测试任务",
        output_dir="D:\\projects\\output\\test",
        metadata={"priority": "high"}
    )
    
    # 更新状态
    ctrl.update_status(task_id, TaskStatus.SENT, "kimi", "发送给 Claude Code")
    ctrl.update_status(task_id, TaskStatus.RECEIVED, "claude", "Claude Code 已接收")
    ctrl.update_status(task_id, TaskStatus.RUNNING, "claude", "开始执行")
    ctrl.update_status(task_id, TaskStatus.COMPLETED, "claude", "执行完成")
    ctrl.close_task(task_id, "kimi")
    
    # 查询任务
    task = ctrl.get_task(task_id)
    print("\n任务详情:")
    print(json.dumps(task, indent=2, ensure_ascii=False, default=str))
    
    # 查询历史
    history = ctrl.get_task_history(task_id)
    print("\n状态历史:")
    for h in history:
        print(f"  {h['changed_at']}: {h['from_status']} → {h['to_status']} ({h['reason']})")
    
    # 统计
    stats = ctrl.get_statistics()
    print("\n任务统计:")
    print(json.dumps(stats, indent=2))
