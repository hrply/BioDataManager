#!/usr/bin/env python3
"""
BioData Manager - MySQL元数据配置管理模块
生物信息学数据管理系统 - 元数据配置管理

提供元数据字段配置的增删改查功能
"""

from typing import Dict, List, Optional, Tuple
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
                SELECT id, field_name, label, field_type, options, required, sort_order, field_table, data_type, created_at, updated_at
                FROM metadata_config
                ORDER BY sort_order ASC, id ASC
            """)
            
            configs = []
            for row in results:
                config = {
                    'id': row[0],
                    'field_name': row[1],
                    'label': row[2],
                    'field_type': row[3],
                    'options': row[4],
                    'required': bool(row[5]),
                    'sort_order': row[6],
                    'field_table': row[7],
                    'data_type': row[8],
                    'created_at': str(row[9]) if row[9] else None,
                    'updated_at': str(row[10]) if row[10] else None
                }
                
                # 解析options JSON
                if config['options']:
                    import json
                    try:
                        config['options'] = json.loads(config['options'])
                    except (json.JSONDecodeError, TypeError):
                        config['options'] = []
                else:
                    config['options'] = []
                
                configs.append(config)
            
            return configs
        except Exception as e:
            print(f"获取元数据配置失败: {e}")
            return []
    
    def get_config_by_field(self, field_name: str) -> Optional[Dict]:
        """根据字段名获取配置"""
        if not self.db_manager:
            return None
        
        try:
            row = self.db_manager.query_one("""
                SELECT id, field_name, label, field_type, options, required, sort_order, field_table, data_type
                FROM metadata_config WHERE field_name = %s
            """, (field_name,))
            
            if row:
                return {
                    'id': row[0],
                    'field_name': row[1],
                    'label': row[2],
                    'field_type': row[3],
                    'options': row[4],
                    'required': bool(row[5]),
                    'sort_order': row[6],
                    'field_table': row[7],
                    'data_type': row[8]
                }
            return None
        except Exception as e:
            print(f"获取字段配置失败: {e}")
            return None
    
    def get_configs_by_table(self, field_table: str, data_type: str = None) -> List[Dict]:
        """根据表类型获取配置"""
        if not self.db_manager:
            return []
        
        try:
            if data_type:
                results = self.db_manager.query("""
                    SELECT id, field_name, label, field_type, options, required, sort_order, field_table, data_type
                    FROM metadata_config
                    WHERE field_table = %s AND (data_type = %s OR data_type IS NULL OR data_type = '')
                    ORDER BY sort_order ASC, id ASC
                """, (field_table, data_type))
            else:
                results = self.db_manager.query("""
                    SELECT id, field_name, label, field_type, options, required, sort_order, field_table, data_type
                    FROM metadata_config
                    WHERE field_table = %s
                    ORDER BY sort_order ASC, id ASC
                """, (field_table,))
            
            configs = []
            for row in results:
                config = {
                    'id': row[0],
                    'field_name': row[1],
                    'label': row[2],
                    'field_type': row[3],
                    'options': row[4],
                    'required': bool(row[5]),
                    'sort_order': row[6],
                    'field_table': row[7],
                    'data_type': row[8]
                }
                
                # 解析options JSON
                if config['options']:
                    import json
                    try:
                        config['options'] = json.loads(config['options'])
                    except (json.JSONDecodeError, TypeError):
                        config['options'] = []
                else:
                    config['options'] = []
                
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
                SELECT id, field_name, label, field_type, options, required, sort_order
                FROM metadata_config WHERE id = %s
            """, (config_id,))
            
            if row:
                return {
                    'id': row[0],
                    'field_name': row[1],
                    'label': row[2],
                    'field_type': row[3],
                    'options': row[4],
                    'required': bool(row[5]),
                    'sort_order': row[6]
                }
            return None
        except Exception as e:
            print(f"获取配置失败: {e}")
            return None
    
    def add_config(self, data: Dict) -> Dict:
        """添加配置"""
        if not self.db_manager:
            return {'success': False, 'message': '数据库未连接'}
        
        try:
            # 处理options
            options = data.get('options', [])
            if isinstance(options, list):
                import json
                options = json.dumps(options, ensure_ascii=False)
            
            self.db_manager.execute("""
                INSERT INTO metadata_config (field_name, label, field_type, options, required, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data.get('field_name', ''),
                data.get('label', ''),
                data.get('field_type', 'text'),
                options,
                data.get('required', False),
                data.get('sort_order', 0)
            ))
            
            # 获取插入的ID
            config_id = self.db_manager.query_one("SELECT LAST_INSERT_ID()")[0]
            
            return {
                'id': config_id,
                'field_name': data.get('field_name', ''),
                'label': data.get('label', ''),
                'field_type': data.get('field_type', 'text'),
                'options': data.get('options', []),
                'required': data.get('required', False),
                'sort_order': data.get('sort_order', 0)
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
            # 处理options
            options = data.get('options', [])
            if isinstance(options, list):
                import json
                options = json.dumps(options, ensure_ascii=False)
            
            self.db_manager.execute("""
                UPDATE metadata_config 
                SET field_name = %s, label = %s, field_type = %s, 
                    options = %s, required = %s, sort_order = %s
                WHERE id = %s
            """, (
                data.get('field_name', ''),
                data.get('label', ''),
                data.get('field_type', 'text'),
                options,
                data.get('required', False),
                data.get('sort_order', 0),
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
                "DELETE FROM metadata_config WHERE id = %s",
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
                    "UPDATE metadata_config SET sort_order = %s WHERE id = %s",
                    (config.get('sort_order', 0), config.get('id'))
                )
            return True
        except Exception as e:
            print(f"保存排序失败: {e}")
            return False
    
    def get_field_options(self, field_name: str) -> List[Dict]:
        """获取字段选项"""
        config = self.get_config_by_field(field_name)
        if config and config['options']:
            return config['options']
        return []
    
    def get_required_fields(self) -> List[str]:
        """获取必填字段列表"""
        configs = self.get_all_configs()
        return [c['field_name'] for c in configs if c['required']]
    
    def validate_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """验证数据"""
        errors = []
        configs = self.get_all_configs()
        
        for config in configs:
            field_name = config['field_name']
            required = config['required']
            value = data.get(field_name, '')
            
            # 检查必填
            if required and not value:
                errors.append(f"{config['label']} 为必填字段")
                continue
            
            # 检查选项有效性（如果有options）
            if config['options'] and value:
                options = config['options']
                option_values = [opt.get('value', opt) for opt in options]
                
                if isinstance(value, list):
                    for v in value:
                        if v not in option_values:
                            errors.append(f"{config['label']} 包含无效选项: {v}")
                else:
                    if value not in option_values:
                        errors.append(f"{config['label']} 包含无效选项: {value}")
        
        return len(errors) == 0, errors


if __name__ == '__main__':
    from database_mysql import DatabaseManager
    
    db = DatabaseManager()
    if db.connect():
        manager = MetadataConfigManager(db)
        
        # 测试获取配置
        configs = manager.get_all_configs()
        print(f"共有 {len(configs)} 个字段配置:")
        for config in configs:
            print(f"  - {config['label']} ({config['field_name']}): {config['field_type']}")
        
        db.disconnect()
    else:
        print("数据库连接失败")
