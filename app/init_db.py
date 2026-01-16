#!/usr/bin/env python3
"""
BioData Manager - 数据库初始化脚本
生物信息学数据管理系统 - 数据库初始化

创建数据库表、初始化默认配置
"""

import json
import sys
from pathlib import Path

# 添加app目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from database_mysql import DatabaseManager
from metadata_config_manager_mysql import MetadataConfigManager


def init_database():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    # 连接数据库
    db = DatabaseManager()
    if not db.connect():
        print("无法连接到数据库，初始化失败")
        return False
    
    try:
        # 创建表
        print("创建数据表...")
        db.create_tables()
        
        # 初始化元数据配置
        print("初始化元数据配置...")
        config_manager = MetadataConfigManager(db)
        init_metadata_config(config_manager)
        
        print("数据库初始化完成!")
        return True
        
    except Exception as e:
        print(f"初始化失败: {e}")
        return False
    finally:
        db.disconnect()


def init_metadata_config(config_manager):
    """初始化元数据配置"""
    # 默认字段配置
    default_configs = [
        {
            'field_name': 'data_type',
            'label': '数据类型',
            'field_type': 'multi_select',
            'options': json.dumps([
                {'value': 'rnaseq', 'label': '转录组 (RNA-Seq)'},
                {'value': 'singlecell', 'label': '单细胞转录组 (Single-cell)'},
                {'value': 'spatial', 'label': '空间转录组 (Spatial)'},
                {'value': 'proteomics', 'label': '蛋白组 (Proteomics)'},
                {'value': 'phosphoproteomics', 'label': '磷酸化组 (Phosphoproteomics)'},
                {'value': 'mass_cytometry', 'label': '质谱流式 (CyTOF)'},
                {'value': 'multiomics', 'label': '多组学 (Multi-omics)'},
                {'value': 'other', 'label': '其他 (Other)'}
            ]),
            'required': True,
            'sort_order': 1
        },
        {
            'field_name': 'organism',
            'label': '物种',
            'field_type': 'multi_select',
            'options': json.dumps([
                {'value': 'Homo sapiens', 'label': '人类 (Homo sapiens)'},
                {'value': 'Mus musculus', 'label': '小鼠 (Mus musculus)'},
                {'value': 'Rattus norvegicus', 'label': '大鼠 (Rattus norvegicus)'},
                {'value': 'Danio rerio', 'label': '斑马鱼 (Danio rerio)'},
                {'value': 'Drosophila melanogaster', 'label': '果蝇 (Drosophila melanogaster)'},
                {'value': 'Caenorhabditis elegans', 'label': '秀丽隐杆线虫 (C. elegans)'},
                {'value': 'Arabidopsis thaliana', 'label': '拟南芥 (Arabidopsis thaliana)'},
                {'value': 'Saccharomyces cerevisiae', 'label': '酿酒酵母 (S. cerevisiae)'},
                {'value': 'Escherichia coli', 'label': '大肠杆菌 (E. coli)'},
                {'value': 'other', 'label': '其他'}
            ], ensure_ascii=False),
            'required': True,
            'sort_order': 2
        },
        {
            'field_name': 'tissue_type',
            'label': '样本类型',
            'field_type': 'select',
            'options': json.dumps([
                {'value': 'whole_blood', 'label': '全血'},
                {'value': 'pbmc', 'label': '外周血单个核细胞 (PBMC)'},
                {'value': 'tumor', 'label': '肿瘤组织'},
                {'value': 'normal_tissue', 'label': '正常组织'},
                {'value': 'cell_line', 'label': '细胞系'},
                {'value': 'primary_cells', 'label': '原代细胞'},
                {'value': 'tissue_lysate', 'label': '组织裂解物'},
                {'value': 'other', 'label': '其他'}
            ], ensure_ascii=False),
            'required': False,
            'sort_order': 3
        },
        {
            'field_name': 'disease',
            'label': '疾病背景',
            'field_type': 'text',
            'options': json.dumps([]),
            'required': False,
            'sort_order': 4
        },
        {
            'field_name': 'doi',
            'label': 'DOI',
            'field_type': 'text',
            'options': json.dumps([]),
            'required': False,
            'sort_order': 5
        },
        {
            'field_name': 'db_id',
            'label': '数据库编号',
            'field_type': 'text',
            'options': json.dumps([]),
            'required': False,
            'sort_order': 6
        },
        {
            'field_name': 'authors',
            'label': '作者',
            'field_type': 'text',
            'options': json.dumps([]),
            'required': False,
            'sort_order': 7
        },
        {
            'field_name': 'journal',
            'label': '期刊',
            'field_type': 'text',
            'options': json.dumps([]),
            'required': False,
            'sort_order': 8
        },
        {
            'field_name': 'tags',
            'label': '标签',
            'field_type': 'multi_select',
            'options': json.dumps([
                {'value': 'public', 'label': '公开数据'},
                {'value': 'controlled', 'label': '受控访问'},
                {'value': 'raw', 'label': '原始数据'},
                {'value': 'processed', 'label': '处理后数据'},
                {'value': 'quality_control', 'label': '质量控制'},
                {'value': 'replicate', 'label': '生物学重复'},
                {'value': 'time_series', 'label': '时间序列'},
                {'value': 'treatment', 'label': '处理组'},
                {'value': 'control', 'label': '对照组'}
            ], ensure_ascii=False),
            'required': False,
            'sort_order': 9
        },
        {
            'field_name': 'description',
            'label': '描述',
            'field_type': 'textarea',
            'options': json.dumps([]),
            'required': False,
            'sort_order': 10
        }
    ]
    
    for config in default_configs:
        try:
            existing = config_manager.get_config_by_field(config['field_name'])
            if not existing:
                config_manager.add_config(config)
                print(f"  添加字段: {config['label']} ({config['field_name']})")
            else:
                print(f"  字段已存在: {config['label']} ({config['field_name']})")
        except Exception as e:
            print(f"  添加字段失败: {config['field_name']} - {e}")


if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
