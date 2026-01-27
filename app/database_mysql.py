#!/usr/bin/env python3
"""
BioData Manager - MySQL数据库管理模块
生物信息学数据管理系统 - MySQL数据库操作

提供数据库连接、查询、执行等基础操作
"""

import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
from typing import Dict, List, Optional, Tuple, Any
import os


class DatabaseManager:
    """数据库管理器 - 使用连接池支持并发请求"""
    
    _pool = None
    _pool_lock = None
    
    def __init__(self):
        """初始化数据库连接池"""
        self.connection = None
        self.config = self._load_config()
        self._init_pool()
    
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
    
    @classmethod
    def _init_pool(cls):
        """初始化连接池（类级别，只初始化一次）"""
        if cls._pool is None:
            cls._pool_lock = cls._pool_lock or __import__('threading').Lock()
            with cls._pool_lock:
                if cls._pool is None:
                    config = {
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
                    try:
                        cls._pool = pooling.MySQLConnectionPool(
                            pool_name="biodata_pool",
                            pool_size=20,  # 连接池大小，支持20个并发连接
                            pool_reset_session=True,
                            **config
                        )
                        print("MySQL连接池初始化成功 (大小: 20)")
                    except Error as e:
                        print(f"连接池初始化失败: {e}")
                        cls._pool = None
    
    def connect(self) -> bool:
        """建立数据库连接（从连接池获取）"""
        try:
            if self._pool:
                self.connection = self._pool.get_connection()
                if self.connection and self.connection.is_connected():
                    db_info = self.connection.get_server_info()
                    print(f"从连接池获取MySQL连接 (版本 {db_info})")
                    return True
                return False
            else:
                # 连接池未初始化，回退到普通连接
                return self._connect_direct()
        except Error:
            return False
    
    def _connect_direct(self) -> bool:
        """直接建立数据库连接（无连接池）"""
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
            return False
    
    def disconnect(self):
        """关闭数据库连接（归还到连接池）"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
        self.connection = None
    
    def get_connection(self):
        """获取数据库连接并设置字符集为 UTF-8"""
        if self._pool:
            try:
                # 直接从连接池获取新连接，不使用 self.connection 缓存
                connection = self._pool.get_connection()
                # 显式设置字符集为 utf8mb4，防止会话重置后编码错误
                cursor = connection.cursor()
                cursor.execute("SET NAMES utf8mb4")
                cursor.close()
                return connection
            except Error as e:
                print(f"从连接池获取连接失败: {e}")
                return None
        
        # 回退到直接连接（仅连接池不可用时）
        if self._connect_direct():
            return self.connection
        return None
    
    def execute(self, query: str, params: Tuple = None) -> bool:
        """执行SQL语句（INSERT, UPDATE, DELETE）"""
        connection = self.get_connection()
        if connection is None:
            return False
        
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            return True
        except Error as e:
            print(f"执行SQL失败: {e}")
            connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def query_one(self, query: str, params: Tuple = None) -> Optional[Tuple]:
        """查询单条记录"""
        connection = self.get_connection()
        if connection is None:
            return None
        
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"查询失败: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def query(self, query: str, params: Tuple = None) -> List[Tuple]:
        """查询多条记录"""
        connection = self.get_connection()
        if connection is None:
            return []
        
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results
        except Error as e:
            print(f"查询失败: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """批量执行SQL语句"""
        connection = self.get_connection()
        if connection is None:
            return False
        
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.executemany(query, params_list)
            connection.commit()
            return True
        except Error as e:
            print(f"批量执行SQL失败: {e}")
            connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def create_tables(self):
        """创建所有数据表"""
        connection = self.get_connection()
        if connection is None:
            print("无法创建表：数据库未连接")
            return
        
        cursor = connection.cursor()
        
        try:
            # 1. 元数据字段配置表 (field_config)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS field_config (
                    id              INT PRIMARY KEY AUTO_INCREMENT COMMENT '字段配置ID',
                    field_seq       INT NOT NULL DEFAULT 0 COMMENT '序号',
                    field_id        VARCHAR(50) NOT NULL UNIQUE COMMENT '字段标识',
                    field_name      VARCHAR(100) NOT NULL COMMENT '字段名称',
                    field_type      ENUM('text', 'textarea', 'select', 'multi_select', 'link', 'tags') NOT NULL COMMENT '字段类型',
                    field_necessary TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否必填',
                    field_placeholder VARCHAR(10) DEFAULT '2' COMMENT '排列方式',
                    field_readonly  TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否只读',
                    field_table     ENUM('raw', 'result', 'file') NOT NULL COMMENT '所属项目类型',
                    field_options   JSON COMMENT '选项配置',
                    field_default   VARCHAR(255) DEFAULT NULL COMMENT '默认值',
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_field_table (field_table),
                    INDEX idx_field_seq (field_seq)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='元数据字段配置表'
            """)
            
            # 2. 原始数据项目表 (raw_project)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_project (
                    id                  INT PRIMARY KEY AUTO_INCREMENT COMMENT '自增ID',
                    raw_id              VARCHAR(50) NOT NULL UNIQUE COMMENT '项目编号(格式: RAW_{UUID})',
                    raw_title           VARCHAR(255) NOT NULL COMMENT '项目名称',
                    raw_type            VARCHAR(50) NOT NULL COMMENT '数据类型',
                    raw_species         VARCHAR(50) NOT NULL COMMENT '物种',
                    raw_tissue          VARCHAR(255) DEFAULT NULL COMMENT '组织来源(多选逗号分隔)',
                    raw_DOI             VARCHAR(100) DEFAULT NULL COMMENT 'DOI号',
                    raw_db_id           VARCHAR(100) DEFAULT NULL COMMENT '数据库编号',
                    raw_db_link         VARCHAR(500) DEFAULT NULL COMMENT '数据库链接',
                    raw_author          VARCHAR(500) DEFAULT NULL COMMENT '作者(多人逗号分隔)',
                    raw_article         VARCHAR(500) DEFAULT NULL COMMENT '文章标题',
                    raw_description     TEXT DEFAULT NULL COMMENT '项目描述',
                    raw_keywords        VARCHAR(500) DEFAULT NULL COMMENT '关键词(逗号分隔)',
                    raw_file_count      INT DEFAULT 0 COMMENT '关联文件数量',
                    raw_total_size      BIGINT DEFAULT 0 COMMENT '文件总大小(字节)',
                    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_raw_id (raw_id),
                    INDEX idx_raw_type (raw_type),
                    INDEX idx_raw_species (raw_species),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='原始数据项目表'
            """)
            
            # 3. 结果数据项目表 (result_project)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS result_project (
                    id                  INT PRIMARY KEY AUTO_INCREMENT COMMENT '自增ID',
                    results_id          VARCHAR(50) NOT NULL UNIQUE COMMENT '项目编号(格式: RES_{UUID})',
                    results_title       VARCHAR(255) NOT NULL COMMENT '项目名称',
                    results_type        VARCHAR(50) NOT NULL COMMENT '结果类型',
                    results_raw         VARCHAR(255) DEFAULT NULL COMMENT '关联原始数据项目编号(逗号分隔)',
                    results_description TEXT DEFAULT NULL COMMENT '项目描述',
                    results_keywords    VARCHAR(500) DEFAULT NULL COMMENT '关键词',
                    results_file_count  INT DEFAULT 0 COMMENT '关联文件数量',
                    results_total_size  BIGINT DEFAULT 0 COMMENT '文件总大小(字节)',
                    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_results_id (results_id),
                    INDEX idx_results_type (results_type),
                    INDEX idx_results_raw (results_raw),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='结果数据项目表'
            """)
            
            # 4. 文件记录表 (file_record)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_record (
                    id                  INT PRIMARY KEY AUTO_INCREMENT COMMENT '自增ID',
                    file_name           VARCHAR(255) NOT NULL COMMENT '文件名',
                    file_path           VARCHAR(500) NOT NULL COMMENT '文件相对路径(相对于/bio)',
                    file_property       VARCHAR(500) DEFAULT NULL COMMENT '文件属性(用于显示和筛选)',
                    file_size           BIGINT NOT NULL COMMENT '文件大小(字节)',
                    file_type           VARCHAR(50) DEFAULT NULL COMMENT '文件类型扩展名',
                    file_project_type   ENUM('raw', 'result') NOT NULL COMMENT '所属项目类型',
                    file_project_id     VARCHAR(50) NOT NULL COMMENT '所属项目编号',
                    file_project_ref_id VARCHAR(50) DEFAULT NULL COMMENT '关联项目编号（结果文件关联的原始数据项目）',
                    imported_at         DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '导入时间',
                    INDEX idx_project (file_project_type, file_project_id),
                    INDEX idx_file_path (file_path),
                    INDEX idx_file_property (file_property),
                    INDEX idx_file_project_ref_id (file_project_ref_id),
                    INDEX idx_imported_at (imported_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文件记录表'
            """)
            
            # 5. 下拉选项表 (select_options)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS select_options (
                    id              INT PRIMARY KEY AUTO_INCREMENT COMMENT '自增ID',
                    option_type     VARCHAR(50) NOT NULL COMMENT '选项类型(对应field_id)',
                    option_value    VARCHAR(100) NOT NULL COMMENT '选项值(value)',
                    option_label    VARCHAR(255) NOT NULL COMMENT '选项标签(label)',
                    option_seq      INT DEFAULT 0 COMMENT '排序序号',
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    UNIQUE KEY uk_type_value (option_type, option_value),
                    INDEX idx_option_type (option_type),
                    INDEX idx_option_seq (option_seq)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='下拉选项表'
            """)
            
            # 6. 缩写映射表 (abbr_mapping)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS abbr_mapping (
                    id              INT PRIMARY KEY AUTO_INCREMENT COMMENT '自增ID',
                    field_id        VARCHAR(50) NOT NULL COMMENT '字段标识符(对应field_config.field_id)',
                    full_name       VARCHAR(100) NOT NULL COMMENT '全称(选项的完整名称)',
                    abbr_name       VARCHAR(20) NOT NULL COMMENT '缩写(用于文件路径)',
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    UNIQUE KEY uk_field_full (field_id, full_name),
                    INDEX idx_field_id (field_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='缩写映射表'
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
            'file_record', 'select_options', 'abbr_mapping',
            'result_project', 'raw_project', 'field_config'
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
