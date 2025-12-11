#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多账号管理器
负责管理多个账号的隔离存储、数据目录、Discord信息等
"""

import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from loguru import logger
from app.core.config import settings

class AccountManager:
    """多账号管理器"""
    
    def __init__(self):
        self.base_data_dir = settings.USER_DATA_DIR
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.base_data_dir):
            os.makedirs(self.base_data_dir)
            logger.info(f"创建数据目录: {self.base_data_dir}")
    
    def get_all_accounts(self):
        """获取所有账号列表"""
        conn = sqlite3.connect(settings.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, token, token_source, created_at, expires_at, 
                   discord_username, data_dir, is_active
            FROM accounts 
            ORDER BY created_at DESC
        """)
        
        accounts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return accounts
    
    def get_account_count(self):
        """获取账号数量"""
        accounts = self.get_all_accounts()
        total = len(accounts)
        active = len([acc for acc in accounts if acc['is_active']])
        browser = len([acc for acc in accounts if acc['token_source'] == 'browser'])
        
        return {
            'total': total,
            'active': active,
            'inactive': total - active,
            'browser': browser,
            'manual': total - browser
        }
    
    def create_account_data_dir(self, account_name, account_id=None):
        """创建账号独立的数据目录
        
        目录结构：
        zai_user_data/
        ├── account_001_20251211_143022/  # 账号1+创建日期
        ├── account_002_20251211_143500/  # 账号2+创建日期
        └── account_003_20251211_144000/  # 账号3+创建日期
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if account_id:
            dir_name = f"account_{account_id:03d}_{timestamp}"
        else:
            # 获取下一个账号ID
            accounts = self.get_all_accounts()
            next_id = max([acc['id'] for acc in accounts], default=0) + 1
            dir_name = f"account_{next_id:03d}_{timestamp}"
        
        account_dir = os.path.join(self.base_data_dir, dir_name)
        
        if not os.path.exists(account_dir):
            os.makedirs(account_dir)
            logger.success(f"创建账号数据目录: {dir_name}")
        
        return account_dir
    
    def create_account(self, name, token, token_source='browser', discord_username=None, discord_password=None):
        """创建新账号"""
        try:
            # 创建独立数据目录
            data_dir = self.create_account_data_dir(name)
            
            # 保存到数据库
            conn = sqlite3.connect(settings.DB_PATH)
            cursor = conn.cursor()
            
            created_at = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(hours=3)).isoformat()
            
            cursor.execute("""
                INSERT INTO accounts 
                (name, token, token_source, created_at, expires_at, discord_username, discord_password, data_dir, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (name, token, token_source, created_at, expires_at, discord_username, discord_password, data_dir))
            
            account_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.success(f"创建账号成功: {name} (ID: {account_id})")
            logger.info(f"数据目录: {data_dir}")
            
            return {
                'id': account_id,
                'name': name,
                'data_dir': data_dir,
                'token_source': token_source
            }
            
        except Exception as e:
            logger.error(f"创建账号失败: {e}")
            return None
    
    def get_account_data_dir(self, account_id):
        """获取账号的数据目录"""
        conn = sqlite3.connect(settings.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT data_dir FROM accounts WHERE id = ?", (account_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return result[0]
        else:
            # 返回默认目录
            return self.base_data_dir
    
    def update_account_token(self, account_id, new_token, new_expires_at=None):
        """更新账号Token"""
        if not new_expires_at:
            new_expires_at = (datetime.now() + timedelta(hours=3)).isoformat()
        
        conn = sqlite3.connect(settings.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE accounts 
            SET token = ?, expires_at = ?, last_refresh_at = ?
            WHERE id = ?
        """, (new_token, new_expires_at, datetime.now().isoformat(), account_id))
        
        conn.commit()
        conn.close()
        
        logger.success(f"更新账号Token成功: ID {account_id}")
    
    def delete_account(self, account_id):
        """删除账号"""
        try:
            # 获取数据目录
            conn = sqlite3.connect(settings.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT data_dir, name FROM accounts WHERE id = ?", (account_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False
            
            data_dir, name = result
            
            # 删除数据库记录
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            conn.commit()
            conn.close()
            
            # 删除数据目录（可选）
            if data_dir and os.path.exists(data_dir):
                import shutil
                shutil.rmtree(data_dir)
                logger.info(f"删除账号数据目录: {data_dir}")
            
            logger.success(f"删除账号成功: {name} (ID: {account_id})")
            return True
            
        except Exception as e:
            logger.error(f"删除账号失败: {e}")
            return False
    
    def get_account_info(self, account_id):
        """获取账号详细信息"""
        conn = sqlite3.connect(settings.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, token, token_source, created_at, expires_at, 
                   discord_username, data_dir, is_active, total_calls, last_used_at
            FROM accounts 
            WHERE id = ?
        """, (account_id,))
        
        account = cursor.fetchone()
        conn.close()
        
        if account:
            return dict(account)
        return None
    
    def display_account_menu(self):
        """显示账号选择菜单（命令行）"""
        accounts = self.get_all_accounts()
        stats = self.get_account_count()
        
        print("\n" + "="*60)
        print("Zai-2API 账号管理")
        print("="*60)
        print(f"📊 账号统计：总共 {stats['total']} 个 | 活跃 {stats['active']} 个 | 浏览器来源 {stats['browser']} 个")
        print("="*60)
        
        if accounts:
            print("\n现有账号列表：")
            print("-" * 60)
            print(f"{'ID':<4} {'名称':<20} {'来源':<8} {'状态':<6} {'过期时间':<20}")
            print("-" * 60)
            
            for acc in accounts:
                source = "浏览器" if acc['token_source'] == 'browser' else "手动"
                status = "✅启用" if acc['is_active'] else "⏸️禁用"
                
                if acc['expires_at']:
                    expires = acc['expires_at'][:16]  # 取到分钟
                else:
                    expires = "未知"
                
                name = acc['name'][:18] + ".." if len(acc['name']) > 20 else acc['name']
                
                print(f"{acc['id']:<4} {name:<20} {source:<8} {status:<6} {expires:<20}")
        else:
            print("\nℹ️ 暂无账号，请先创建账号")
        
        print("\n" + "="*60)
        print("操作选项：")
        print("  0. 创建新账号（浏览器登录）")
        
        if accounts:
            for acc in accounts:
                print(f"  {acc['id']}. 使用账号: {acc['name']}")
        
        print("  99. 返回主菜单")
        print("="*60)
        
        return accounts

# 全局实例
account_manager = AccountManager()
