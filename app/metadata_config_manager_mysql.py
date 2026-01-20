#!/usr/bin/env python3
"""
BioData Manager - MySQL元数据配置管理模块
生物信息学数据管理系统 - 元数据配置管理

提供元数据字段配置的增删改查功能
"""

from typing import Dict, List, Optional, Tuple
import json
from database_mysql import DatabaseManager


class MetadataConfigManager:
    """元数据配置管理器"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """初始化"""
        self.db_manager = db_manager
    
    def set_db_manager(self, db_manager: DatabaseManager):
        """设置数据库管理器"""
        self.db_manager = db_manager
    
    def get_all_configs(self) -> List[Dict]:
        """获取所有配置（按排序顺序）"""
        if not self.db_manager:
            return []
        
        try:
            results = self.db_manager.query("""
                SELECT id, field_id, field_name, field_type, field_table, 
                       field_necessary, field_options, field_seq, field_default, field_placeholder,
                       field_readonly, created_at, updated_at
                FROM field_config
                ORDER BY field_table ASC, field_seq ASC, id ASC
            """)
            
            configs = []
            for row in results:
                config = {
                    'id': row[0],
                    'field_id': row[1],
                    'field_name': row[2],
                    'field_type': row[3],
                    'field_table': row[4],
                    'field_necessary': bool(row[5]),
                    'field_options': row[6],
                    'field_seq': row[7],
                    'field_default': row[8],
                    'field_placeholder': row[9],
                    'field_readonly': bool(row[10]) if row[10] is not None else False,
                    'created_at': str(row[11]) if row[11] else None,
                    'updated_at': str(row[12]) if row[12] else None
                }
                
                # 解析 field_options JSON
                if config['field_options']:
                    try:
                        config['field_options'] = json.loads(config['field_options'])
                    except (json.JSONDecodeError, TypeError):
                        config['field_options'] = []
                else:
                    config['field_options'] = []
                
                # 添加 options_count 字段
                config['options_count'] = len(config['field_options'])
                
                configs.append(config)
            
            return configs
        except Exception as e:
            print(f"获取元数据配置失败: {e}")
            return []
    
    def get_config_by_field_id(self, field_id: str) -> Optional[Dict]:
        """根据字段标识符获取配置"""
        if not self.db_manager:
            return None
        
        try:
            row = self.db_manager.query_one("""
                SELECT id, field_id, field_name, field_type, field_table, 
                       field_necessary, field_options, field_seq, field_default, field_placeholder,
                       field_readonly
                FROM field_config WHERE field_id = %s
            """, (field_id,))
            
            if row:
                config = {
                    'id': row[0],
                    'field_id': row[1],
                    'field_name': row[2],
                    'field_type': row[3],
                    'field_table': row[4],
                    'field_necessary': bool(row[5]),
                    'field_options': row[6],
                    'field_seq': row[7],
                    'field_default': row[8],
                    'field_placeholder': row[9],
                    'field_readonly': bool(row[10]) if row[10] is not None else False
                }
                
                # 解析 field_options JSON
                if config['field_options']:
                    try:
                        config['field_options'] = json.loads(config['field_options'])
                    except (json.JSONDecodeError, TypeError):
                        config['field_options'] = []
                else:
                    config['field_options'] = []
                
                return config
            return None
        except Exception as e:
            print(f"获取字段配置失败: {e}")
            return None
    
    def get_configs_by_table(self, field_table: str) -> List[Dict]:
        """根据表类型获取配置"""
        if not self.db_manager:
            return []
        
        try:
            results = self.db_manager.query("""
                SELECT id, field_id, field_name, field_type, field_table, 
                       field_necessary, field_options, field_seq, field_default, field_placeholder,
                       field_readonly
                FROM field_config
                WHERE field_table = %s
                ORDER BY field_seq ASC, id ASC
            """, (field_table,))
            
            configs = []
            for row in results:
                config = {
                    'id': row[0],
                    'field_id': row[1],
                    'field_name': row[2],
                    'field_type': row[3],
                    'field_table': row[4],
                    'field_necessary': bool(row[5]),
                    'field_options': row[6],
                    'field_seq': row[7],
                    'field_default': row[8],
                    'field_placeholder': row[9],
                    'field_readonly': bool(row[10]) if row[10] is not None else False
                }
                
                # 解析 field_options JSON
                if config['field_options']:
                    try:
                        config['field_options'] = json.loads(config['field_options'])
                    except (json.JSONDecodeError, TypeError):
                        config['field_options'] = []
                else:
                    config['field_options'] = []
                
                # 添加 options_count 字段
                config['options_count'] = len(config['field_options'])
                
                configs.append(config)
            
            return configs
        except Exception as e:
            print(f"获取表类型配置失败: {e}")
            return []
    
    def get_config_by_id(self, config_id: int) -> Optional[Dict]:
        """根据ID获取配置"""
        if not self.db_manager:
            return None
        
        try:
            row = self.db_manager.query_one("""
                SELECT id, field_id, field_name, field_type, field_table, 
                       field_necessary, field_options, field_seq, field_default, field_placeholder,
                       field_readonly
                FROM field_config WHERE id = %s
            """, (config_id,))
            
            if row:
                config = {
                    'id': row[0],
                    'field_id': row[1],
                    'field_name': row[2],
                    'field_type': row[3],
                    'field_table': row[4],
                    'field_necessary': bool(row[5]),
                    'field_options': row[6],
                    'field_seq': row[7],
                    'field_default': row[8],
                    'field_placeholder': row[9],
                    'field_readonly': bool(row[10]) if row[10] is not None else False
                }
                
                # 解析 field_options JSON
                if config['field_options']:
                    try:
                        config['field_options'] = json.loads(config['field_options'])
                    except (json.JSONDecodeError, TypeError):
                        config['field_options'] = []
                else:
                    config['field_options'] = []
                
                return config
            return None
        except Exception as e:
            print(f"获取配置失败: {e}")
            return None
    
    def add_config(self, data: Dict) -> Dict:
        """添加配置"""
        if not self.db_manager:
            return {'success': False, 'message': '数据库未连接'}
        
        try:
            # 处理 field_options
            field_options = data.get('field_options', [])
            if isinstance(field_options, list):
                field_options = json.dumps(field_options, ensure_ascii=False)
            
            self.db_manager.execute("""
                INSERT INTO field_config 
                (field_id, field_name, field_type, field_table, field_necessary, 
                 field_options, field_seq, field_default, field_placeholder, field_readonly)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('field_id', ''),
                data.get('field_name', ''),
                data.get('field_type', 'text'),
                data.get('field_table', 'raw'),
                data.get('field_necessary', False),
                field_options,
                data.get('field_seq', 0),
                data.get('field_default'),
                data.get('field_placeholder'),
                data.get('field_readonly', False)
            ))
            
            # 获取插入的ID
            config_id = self.db_manager.query_one("SELECT LAST_INSERT_ID()")[0]
            
            return {
                'id': config_id,
                'field_id': data.get('field_id', ''),
                'field_name': data.get('field_name', ''),
                'field_type': data.get('field_type', 'text'),
                'field_table': data.get('field_table', 'raw'),
                'field_necessary': data.get('field_necessary', False),
                'field_options': data.get('field_options', []),
                'field_seq': data.get('field_seq', 0),
                'field_default': data.get('field_default'),
                'field_placeholder': data.get('field_placeholder'),
                'field_readonly': data.get('field_readonly', False)
            }
        except Exception as e:
            print(f"添加配置失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def update_config(self, data: Dict) -> bool:
        """更新配置"""
        if not self.db_manager:
            return False
        
        config_id = data.get('id')
        if not config_id:
            return False
        
        try:
            # 获取原始配置，保留 field_table 不变
            original_config = self.get_config_by_id(config_id)
            if not original_config:
                return False
            
            # 处理 field_options
            field_options = data.get('field_options', [])
            if isinstance(field_options, list):
                field_options = json.dumps(field_options, ensure_ascii=False)
            
            # field_table 不应该被前端传入的值修改，使用数据库中的原始值
            self.db_manager.execute("""
                UPDATE field_config 
                SET field_name = %s, field_type = %s, 
                    field_necessary = %s, field_options = %s,
                    field_seq = %s, field_default = %s, field_placeholder = %s,
                    field_readonly = %s
                WHERE id = %s
            """, (
                data.get('field_name', ''),
                data.get('field_type', 'text'),
                data.get('field_necessary', False),
                field_options,
                data.get('field_seq', 0),
                data.get('field_default'),
                data.get('field_placeholder'),
                data.get('field_readonly', False),
                config_id
            ))
            
            return True
        except Exception as e:
            print(f"更新配置失败: {e}")
            return False
    
    def delete_config(self, config_id: int) -> bool:
        """删除配置"""
        if not self.db_manager:
            return False
        
        try:
            self.db_manager.execute(
                "DELETE FROM field_config WHERE id = %s",
                (config_id,)
            )
            return True
        except Exception as e:
            print(f"删除配置失败: {e}")
            return False
    
    def save_order(self, configs: List[Dict]) -> bool:
        """保存排序顺序"""
        if not self.db_manager or not configs:
            return False
        
        try:
            for config in configs:
                self.db_manager.execute(
                    "UPDATE field_config SET field_seq = %s WHERE id = %s",
                    (config.get('field_seq', 0), config.get('id'))
                )
            return True
        except Exception as e:
            print(f"保存排序失败: {e}")
            return False
    
    def get_field_options(self, field_id: str) -> List[Dict]:
        """获取字段选项"""
        config = self.get_config_by_field_id(field_id)
        if config and config['field_options']:
            return config['field_options']
        return []
    
    def get_required_fields(self) -> List[str]:
        """获取必填字段标识符列表"""
        configs = self.get_all_configs()
        return [c['field_id'] for c in configs if c['field_necessary']]
    
    def get_select_options(self, option_type: str) -> List[Dict]:
        """获取下拉选项"""
        if not self.db_manager:
            return []
        
        try:
            results = self.db_manager.query("""
                SELECT option_value, option_label, option_seq
                FROM select_options
                WHERE option_type = %s
                ORDER BY option_seq ASC
            """, (option_type,))
            
            return [
                {'value': row[0], 'label': row[1], 'seq': row[2]}
                for row in results
            ]
        except Exception as e:
            print(f"获取选项失败: {e}")
            return []
    
    def get_abbr_mapping(self, field_id: str, full_name: str) -> Optional[str]:
        """获取缩写"""
        if not self.db_manager:
            return None
        
        try:
            row = self.db_manager.query_one(
                "SELECT abbr_name FROM abbr_mapping WHERE field_id = %s AND full_name = %s",
                (field_id, full_name)
            )
            return row[0] if row else None
        except Exception as e:
            print(f"获取缩写失败: {e}")
            return None
    
    def validate_data(self, data: Dict, field_table: str) -> Tuple[bool, List[str]]:
        """验证数据"""
        errors = []
        configs = self.get_configs_by_table(field_table)
        
        for config in configs:
            field_id = config['field_id']
            field_necessary = config['field_necessary']
            field_type = config['field_type']
            value = data.get(field_id, '')
            
            # 检查必填
            if field_necessary and not value:
                errors.append(f"{config['field_name']} 为必填字段")
                continue
            
            # 对于 select/multi_select 类型，验证选项有效性
            if field_type in ('select', 'multi_select') and value:
                options = self.get_select_options(field_id)
                option_values = [opt['value'] for opt in options]
                
                if field_type == 'multi_select' and isinstance(value, str):
                    # 多选用逗号分隔
                    values = [v.strip() for v in value.split(',') if v.strip()]
                elif field_type == 'multi_select' and isinstance(value, list):
                    values = value
                else:
                    values = [value]
                
                for v in values:
                    if v not in option_values:
                        errors.append(f"{config['field_name']} 包含无效选项: {v}")
        
        return len(errors) == 0, errors
    
    def get_field_config_columns(self) -> List[Dict]:
        """获取 field_config 表的列信息（用于前端动态生成列标题）
        
        返回第 2-8 列的列名和 comment，用于元数据配置页面的表格列标题
        列顺序: id, field_seq, field_id, field_name, field_type, 
                field_necessary, field_placeholder, field_readonly, field_table
        """
        if not self.db_manager:
            return []
        
        try:
            results = self.db_manager.query("""
                SELECT 
                    ORDINAL_POSITION as col_order,
                    COLUMN_NAME as col_name,
                    COLUMN_COMMENT as col_comment,
                    DATA_TYPE as data_type,
                    IS_NULLABLE as is_nullable,
                    COLUMN_DEFAULT as col_default
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'field_config'
                ORDER BY ORDINAL_POSITION ASC
            """)
            
            # 只返回第 2-8 列（field_seq 到 field_readonly）
            # 索引: 0=id, 1=field_seq, 2=field_id, 3=field_name, 4=field_type,
            #       5=field_necessary, 6=field_placeholder, 7=field_readonly, 8=field_table
            columns = []
            for row in results:
                col_order = row[0]
                if 2 <= col_order <= 8:  # 第 2-8 列
                    columns.append({
                        'order': col_order,
                        'name': row[1],
                        'comment': row[2],
                        'type': row[3],
                        'nullable': row[4] == 'YES',
                        'default': row[5]
                    })
            
            return columns
        except Exception as e:
            print(f"获取列信息失败: {e}")
            return []


if __name__ == '__main__':
    from database_mysql import DatabaseManager
    
    db = DatabaseManager()
    if db.connect():
        manager = MetadataConfigManager(db)
        
        # 测试获取配置
        configs = manager.get_all_configs()
        print(f"共有 {len(configs)} 个字段配置:")
        for config in configs:
            print(f"  - {config['field_name']} ({config['field_id']}): {config['field_type']} [{config['field_table']}]")
        
        db.disconnect()
    else:
        print("数据库连接失败")