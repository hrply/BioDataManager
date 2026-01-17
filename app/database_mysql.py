#!/usr/bin/env python3
"""
BioData Manager - MySQL数据库管理模块
生物信息学数据管理系统 - MySQL数据库操作

提供数据库连接、查询、执行等基础操作
"""

import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Optional, Tuple, Any
import os


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.connection = None
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载数据库配置"""
        return {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'port': int(os.environ.get('MYSQL_PORT', 3306)),
            'user': os.environ.get('MYSQL_USER', 'biodata'),
            'password': os.environ.get('MYSQL_PASSWORD', 'biodata123'),
            'database': os.environ.get('MYSQL_DATABASE', 'biodata'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': False,
            'connection_timeout': 30
        }
    
    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            if self.connection and self.connection.is_connected():
                return True
            
            self.connection = mysql.connector.connect(**self.config)
            
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                print(f"已连接到MySQL数据库 (版本 {db_info})")
                return True
            
            return False
        except Error:
            # 连接失败时静默处理（由调用方决定是否显示错误）
            return False
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
            print("数据库连接已关闭")
    
    def get_connection(self):
        """获取数据库连接"""
        if self.connection and self.connection.is_connected():
            try:
                # 测试连接是否仍然有效
                self.connection.ping(reconnect=True, attempts=3, delay=1)
                return self.connection
            except Error:
                # 连接已断开，尝试重连
                self.connection = None
        
        # 尝试连接
        if self.connect():
            return self.connection
        # 连接失败，返回None（由调用方处理）
        return None
    
    def execute(self, query: str, params: Tuple = None) -> bool:
        """执行SQL语句（INSERT, UPDATE, DELETE）"""
        connection = self.get_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor()
        
        try:
            cursor.execute(query, params)
            connection.commit()
            return True
        except Error as e:
            print(f"执行SQL失败: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
    
    def query_one(self, query: str, params: Tuple = None) -> Optional[Tuple]:
        """查询单条记录"""
        connection = self.get_connection()
        if connection is None:
            return None
        
        cursor = connection.cursor()
        
        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"查询失败: {e}")
            return None
        finally:
            cursor.close()
    
    def query(self, query: str, params: Tuple = None) -> List[Tuple]:
        """查询多条记录"""
        connection = self.get_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor()
        
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results
        except Error as e:
            print(f"查询失败: {e}")
            return []
        finally:
            cursor.close()
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """批量执行SQL语句"""
        connection = self.get_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor()
        
        try:
            cursor.executemany(query, params_list)
            connection.commit()
            return True
        except Error as e:
            print(f"批量执行SQL失败: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
    
    def create_tables(self):
        """创建所有数据表"""
        connection = self.get_connection()
        if connection is None:
            print("无法创建表：数据库未连接")
            return
        
        cursor = connection.cursor()
        
        try:
            # 创建项目表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(500) NOT NULL,
                    doi VARCHAR(255),
                    db_id VARCHAR(100),
                    db_link VARCHAR(500),
                    data_type VARCHAR(100),
                    organism VARCHAR(100),
                    tissue_type VARCHAR(100),
                    disease VARCHAR(255),
                    authors VARCHAR(500),
                    journal VARCHAR(255),
                    description TEXT,
                    tags JSON,
                    created_date DATETIME,
                    path VARCHAR(500),
                    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建文件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    project_id VARCHAR(50),
                    file_name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500),
                    file_type VARCHAR(100),
                    file_size BIGINT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_project_id (project_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建生物结果项目表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bioresult_projects (
                    id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(500) NOT NULL,
                    description TEXT,
                    data_type VARCHAR(100),
                    analysis_type VARCHAR(100),
                    software VARCHAR(255),
                    parameters TEXT,
                    authors VARCHAR(500),
                    created_date DATETIME,
                    path VARCHAR(500)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建处理文件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    project_id VARCHAR(50),
                    file_name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500),
                    file_type VARCHAR(100),
                    file_size BIGINT,
                    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_project_id (project_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建元数据配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata_config (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    field_name VARCHAR(100) NOT NULL UNIQUE,
                    label VARCHAR(100) NOT NULL,
                    field_type VARCHAR(50) NOT NULL DEFAULT 'text',
                    options JSON,
                    required BOOLEAN DEFAULT FALSE,
                    sort_order INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建标签表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tag_name VARCHAR(100) NOT NULL UNIQUE,
                    project_id VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建项目ID序列表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_id_sequence (
                    id VARCHAR(50) PRIMARY KEY,
                    counter INT DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建生物结果项目ID序列表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bioresult_id_sequence (
                    id VARCHAR(50) PRIMARY KEY,
                    counter INT DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            connection.commit()
            print("所有数据表创建成功")
            
        except Error as e:
            print(f"创建数据表失败: {e}")
            connection.rollback()
        finally:
            cursor.close()
    
    def drop_tables(self):
        """删除所有数据表（慎用）"""
        connection = self.get_connection()
        cursor = connection.cursor()
        
        tables = [
            'files', 'processed_files', 'bioresult_projects',
            'tags', 'metadata_config', 'project_id_sequence',
            'bioresult_id_sequence', 'projects'
        ]
        
        try:
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            connection.commit()
            print("所有数据表已删除")
        except Error as e:
            print(f"删除数据表失败: {e}")
            connection.rollback()
        finally:
            cursor.close()
    
    def check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        result = self.query_one(
            "SHOW TABLES LIKE %s",
            (table_name,)
        )
        return result is not None
    
    def get_table_schema(self, table_name: str) -> List[Dict]:
        """获取表结构"""
        return self.query(f"DESCRIBE {table_name}")
    
    def truncate_table(self, table_name: str) -> bool:
        """清空表数据"""
        return self.execute(f"TRUNCATE TABLE {table_name}")


if __name__ == '__main__':
    # 测试数据库连接
    db = DatabaseManager()
    
    if db.connect():
        print("数据库连接测试成功")
        
        # 创建表
        db.create_tables()
        
        # 检查表
        tables = db.query("SHOW TABLES")
        print("当前数据库中的表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        db.disconnect()
    else:
        print("数据库连接失败")
