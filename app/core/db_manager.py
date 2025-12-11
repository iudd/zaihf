#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器 - 统一所有数据库操作
唯一入口，避免锁竞争和数据不一致
"""

import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from app.core.config import settings

class DBManager:
    """数据库管理器 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.db_path = settings.DB_PATH
        self._db_lock = threading.Lock()  # 数据库操作锁
        self._init_database()
        self._initialized = True
        logger.info("✅ 数据库管理器初始化完成")
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self._db_lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # 账号表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    data_dir TEXT UNIQUE,  -- 存放浏览器数据的文件夹名
                    token TEXT,
                    token_source TEXT DEFAULT 'manual',  -- 'browser' or 'manual'
                    created_at TEXT,
                    expires_at TEXT,
                    discord_username TEXT,
                    discord_password TEXT,
                    is_active INTEGER DEFAULT 1,
                    total_calls INTEGER DEFAULT 0,
                    last_used_at TEXT,
                    last_refresh_at TEXT
                )
            ''')
            
            # 日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    account_name TEXT,
                    model TEXT,
                    status TEXT,
                    duration INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ 数据库表结构初始化完成")
    
    def _get_conn(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    # ==================== 账号操作 ====================
    
    def get_all_accounts(self, active_only=False):
        """获取所有账号"""
        with self._db_lock:
            conn = self._get_conn()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute("SELECT * FROM accounts WHERE is_active = 1 ORDER BY id ASC")
            else:
                cursor.execute("SELECT * FROM accounts ORDER BY id ASC")
            
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rows
    
    def get_account_by_id(self, account_id):
        """根据ID获取账号"""
        with self._db_lock:
            conn = self._get_conn()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
    
    def create_account(self, name, token, data_dir, token_source='browser', discord_username=''):
        """创建账号"""
        with self._db_lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            created_at = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(hours=3)).isoformat()
            
            try:
                cursor.execute('''
                    INSERT INTO accounts 
                    (name, token, data_dir, token_source, created_at, expires_at, discord_username, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                ''', (name, token, data_dir, token_source, created_at, expires_at, discord_username))
                
                account_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                logger.success(f"创建账号成功: {name} (ID: {account_id})")
                return account_id
                
            except sqlite3.IntegrityError as e:
                logger.error(f"创建账号失败: {e}")
                conn.close()
                return None
    
    def update_token(self, account_id, token):
        """更新账号Token"""
        with self._db_lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            expires_at = (datetime.now() + timedelta(hours=3)).isoformat()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                UPDATE accounts 
                SET token = ?, expires_at = ?, last_refresh_at = ?, is_active = 1 
                WHERE id = ?
            ''', (token, expires_at, now, account_id))
            
            conn.commit()
            conn.close()
            logger.info(f"更新Token成功: ID {account_id}")
    
    def update_stats(self, account_id):
        """更新账号统计"""
        with self._db_lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            cursor.execute('''
                UPDATE accounts 
                SET total_calls = total_calls + 1, last_used_at = ? 
                WHERE id = ?
            ''', (now, account_id))
            
            conn.commit()
            conn.close()
    
    def disable_account(self, account_id):
        """禁用账号"""
        with self._db_lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("UPDATE accounts SET is_active = 0 WHERE id = ?", (account_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"禁用账号: ID {account_id}")
    
    def delete_account(self, account_id):
        """删除账号"""
        with self._db_lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"删除账号: ID {account_id}")
    
    def toggle_account(self, account_id):
        """切换账号状态"""
        with self._db_lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("SELECT is_active FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            
            if row:
                new_status = 0 if row[0] else 1
                cursor.execute("UPDATE accounts SET is_active = ? WHERE id = ?", (new_status, account_id))
                conn.commit()
                
                status_text = "启用" if new_status else "禁用"
                logger.info(f"{status_text}账号: ID {account_id}")
            
            conn.close()
    
    # ==================== 日志操作 ====================
    
    def add_log(self, account_name, model, status, duration, message=None):
        """添加日志"""
        with self._db_lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO logs (timestamp, account_name, model, status, duration)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), account_name, model, status, duration))
            
            conn.commit()
            conn.close()
    
    def get_recent_logs(self, limit=20):
        """获取最近日志"""
        with self._db_lock:
            conn = self._get_conn()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
            
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rows
    
    def clear_logs(self):
        """清空日志"""
        with self._db_lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM logs")
            conn.commit()
            conn.close()
            logger.info("日志已清空")

# 全局实例
db_manager = DBManager()