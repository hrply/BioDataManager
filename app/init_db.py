#!/usr/bin/env python3
"""
BioData Manager - 数据库初始化脚本
生物信息学数据管理系统 - 数据库初始化

创建数据库表、初始化默认配置
"""

import sys
import argparse
from pathlib import Path

# 添加app目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from database_mysql import DatabaseManager


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='BioData Manager 数据库初始化')
    parser.add_argument('--force', action='store_true', 
                        help='强制重建模式：清空并重新初始化所有配置数据')
    return parser.parse_args()


def init_database(force=False):
    """初始化数据库
    
    Args:
        force: 是否强制重建模式
    """
    print("开始初始化数据库...")
    
    if force:
        print("⚠️  强制重建模式：将清空并重新初始化所有配置数据")
    else:
        print("📝 追加模式：只添加不存在的配置，已存在的配置将更新")
    
    # 连接数据库
    db = DatabaseManager()
    if not db.connect():
        print("无法连接到数据库，初始化失败")
        return False
    
    try:
        # 强制重建模式：先清空所有表
        if force:
            print("清空所有数据表...")
            db.execute("DELETE FROM files")
            db.execute("DELETE FROM results")
            db.execute("DELETE FROM raw_data")
            db.execute("TRUNCATE TABLE field_config")
            db.execute("TRUNCATE TABLE select_options")
            db.execute("TRUNCATE TABLE abbr_mapping")
            print("  已清空所有表")
        
        # 创建表
        print("创建数据表...")
        db.create_tables()
        
        # 初始化配置数据
        print("初始化 field_config...")
        init_field_config(db, force)
        
        print("初始化 select_options...")
        init_select_options(db, force)
        
        print("初始化 abbr_mapping...")
        init_abbr_mapping(db, force)
        
        mode_str = "强制重建" if force else "追加"
        print(f"数据库初始化完成! (模式: {mode_str})")
        return True
        
    except Exception as e:
        print(f"初始化失败: {e}")
        return False
    finally:
        db.disconnect()


def init_field_config(db, force=False):
    """初始化 field_config 表
    
    Args:
        db: 数据库连接
        force: 是否强制重建模式
    """
    import json

    # 原始数据字段配置 (field_id, field_name, field_type, field_table, field_necessary, field_seq, field_options, field_placeholder, field_readonly)
    raw_fields = [
        ('raw_id', '项目编号', 'text', 'raw', 1, 0, None, '2', 0),
        ('raw_title', '项目名称', 'text', 'raw', 1, 1, None, '2', 0),
        ('raw_type', '数据类型', 'select', 'raw', 1, 2, json.dumps([
            {"value": "mRNAseq", "label": "转录组"},
            {"value": "Long-Read RNAseq", "label": "长读转录组"},
            {"value": "lncRNAseq", "label": "lncRNAseq"},
            {"value": "miRNAseq", "label": "miRNAseq"},
            {"value": "sRNAseq", "label": "小RNA转录组"},
            {"value": "epitRNAseq", "label": "表观转录组"},
            {"value": "scRNAseq", "label": "单细胞转录组"},
            {"value": "LR-scRNAseq", "label": "长读单细胞转录组"},
            {"value": "蛋白组", "label": "蛋白组"},
            {"value": "磷酸化组", "label": "磷酸化组"},
            {"value": "泛素化组", "label": "泛素化组"},
            {"value": "乙酰化组", "label": "乙酰化组"},
            {"value": "SUMO PTMome", "label": "SUMO PTMome"},
            {"value": "甲基化组", "label": "甲基化组"},
            {"value": "糖基化组", "label": "糖基化组"},
            {"value": "棕榈酰化组", "label": "棕榈酰化组"},
            {"value": "代谢组", "label": "代谢组"},
            {"value": "脂质组学", "label": "脂质组学"},
            {"value": "免疫组学", "label": "免疫组学"},
            {"value": "CyTOF", "label": "质谱流式"},
            {"value": "空间多组学", "label": "空间多组学"},
        ]), '2', 0),
        ('raw_species', '物种', 'select', 'raw', 1, 3, json.dumps([
            {"value": "Homo sapiens", "label": "人"},
            {"value": "Mus musculus", "label": "小鼠"},
            {"value": "Rattus norvegicus", "label": "大鼠"},
            {"value": "Others", "label": "其他"},
        ]), '2', 0),
        ('raw_tissue', '组织来源', 'select', 'raw', 0, 4, json.dumps([
            {"value": "Not Specific", "label": "Not Specific (非单一组织)"},
            {"value": "Adipose tissue", "label": "Adipose tissue (脂肪组织)"},
            {"value": "Adrenal gland", "label": "Adrenal gland (肾上腺)"},
            {"value": "Amygdala", "label": "Amygdala (杏仁核)"},
            {"value": "Basal ganglia", "label": "Basal ganglia (基底神经节)"},
            {"value": "Blood vessel", "label": "Blood vessel (血管)"},
            {"value": "Bone marrow", "label": "Bone marrow (骨髓)"},
            {"value": "Breast", "label": "Breast (乳房)"},
            {"value": "Cerebellum", "label": "Cerebellum (小脑)"},
            {"value": "Cerebral cortex", "label": "Cerebral cortex (大脑皮层)"},
            {"value": "Cervix", "label": "Cervix (子宫颈)"},
            {"value": "Choroid plexus", "label": "Choroid plexus (脉络丛)"},
            {"value": "Colon", "label": "Colon (结肠)"},
            {"value": "Duodenum", "label": "Duodenum (十二指肠)"},
            {"value": "Endometrium", "label": "Endometrium (子宫内膜)"},
            {"value": "Epididymis", "label": "Epididymis (附睾)"},
            {"value": "Esophagus", "label": "Esophagus (食管)"},
            {"value": "Fallopian tube", "label": "Fallopian tube (输卵管)"},
            {"value": "Gallbladder", "label": "Gallbladder (胆囊)"},
            {"value": "Heart muscle", "label": "Heart muscle (心肌)"},
            {"value": "Hippocampal formation", "label": "Hippocampal formation (海马结构)"},
            {"value": "Hypothalamus", "label": "Hypothalamus (下丘脑)"},
            {"value": "Kidney", "label": "Kidney (肾脏)"},
            {"value": "Liver", "label": "Liver (肝脏)"},
            {"value": "Lung", "label": "Lung (肺)"},
            {"value": "Lymph node", "label": "Lymph node (淋巴结)"},
            {"value": "Midbrain", "label": "Midbrain (中脑)"},
            {"value": "Ovary", "label": "Ovary (卵巢)"},
            {"value": "Pancreas", "label": "Pancreas (胰腺)"},
            {"value": "Parathyroid gland", "label": "Parathyroid gland (甲状旁腺)"},
            {"value": "Pituitary gland", "label": "Pituitary gland (垂体)"},
            {"value": "Placenta", "label": "Placenta (胎盘)"},
            {"value": "Prostate", "label": "Prostate (前列腺)"},
            {"value": "Rectum", "label": "Rectum (直肠)"},
            {"value": "Retina", "label": "Retina (视网膜)"},
            {"value": "Salivary gland", "label": "Salivary gland (唾液腺)"},
            {"value": "Seminal vesicle", "label": "Seminal vesicle (精囊)"},
            {"value": "Skeletal muscle", "label": "Skeletal muscle (骨骼肌)"},
            {"value": "Skin", "label": "Skin (皮肤)"},
            {"value": "Small intestine", "label": "Small intestine (小肠)"},
            {"value": "Smooth muscle", "label": "Smooth muscle (平滑肌)"},
            {"value": "Spinal cord", "label": "Spinal cord (脊髓)"},
            {"value": "Spleen", "label": "Spleen (脾脏)"},
            {"value": "Stomach", "label": "Stomach (胃)"},
            {"value": "Testis", "label": "Testis (睾丸)"},
            {"value": "Thymus", "label": "Thymus (胸腺)"},
            {"value": "Thyroid gland", "label": "Thyroid gland (甲状腺)"},
            {"value": "Tongue", "label": "Tongue (舌头)"},
            {"value": "Tonsil", "label": "Tonsil (扁桃体)"},
            {"value": "Urinary bladder", "label": "Urinary bladder (膀胱)"},
            {"value": "Vagina", "label": "Vagina (阴道)"},
        ]), '2', 0),
        ('raw_DOI', 'DOI', 'link', 'raw', 0, 5, None, '2', 0),
        ('raw_db_id', '数据库编号', 'text', 'raw', 0, 6, None, '2', 0),
        ('raw_db_link', '数据库链接', 'link', 'raw', 0, 7, None, '2', 0),
        ('raw_author', '作者', 'text', 'raw', 0, 8, None, '2', 0),
        ('raw_article', '文章标题', 'text', 'raw', 0, 9, None, '2', 0),
        ('raw_description', '描述', 'textarea', 'raw', 0, 10, None, '1', 0),
        ('raw_keywords', '关键词', 'tags', 'raw', 0, 11, None, '1', 0),
        ('raw_file_count', '文件数量', 'text', 'raw', 0, 12, None, '2', 1),
        ('raw_total_size', '文件总大小', 'text', 'raw', 0, 13, None, '2', 1),
    ]
    
    # 结果数据字段配置
    result_fields = [
        ('results_id', '项目编号', 'text', 'result', 1, 0, None, '2', 0),
        ('results_title', '项目名称', 'text', 'result', 1, 1, None, '2', 0),
        ('results_type', '结果类型', 'select', 'result', 1, 2, json.dumps([
            {"value": "DEA", "label": "差异分析 (DEA)"},
            {"value": "Marker", "label": "Marker基因"},
            {"value": "Enrichment", "label": "富集分析"},
            {"value": "PPI", "label": "蛋白互作 (PPI)"},
            {"value": "Network", "label": "网络分析"},
            {"value": "Clustering", "label": "聚类分析"},
            {"value": "Dimension", "label": "降维分析"},
            {"value": "Trajectory", "label": "轨迹分析"},
        ]), '2', 0),
        ('results_raw', '关联原始项目', 'tags', 'result', 0, 3, None, '1', 0),
        ('results_description', '描述', 'textarea', 'result', 0, 4, None, '1', 0),
        ('results_keywords', '关键词', 'tags', 'result', 0, 5, None, '1', 0),
        ('results_file_count', '文件数量', 'text', 'result', 0, 6, None, '2', 1),
        ('results_total_size', '文件总大小', 'text', 'result', 0, 7, None, '2', 1),
    ]
    
    # 文件管理字段配置
    file_fields = [
        ('file_name', '文件名', 'text', 'file', 1, 0, None, '2', 0),
        ('file_path', '文件路径', 'text', 'file', 1, 1, None, '2', 0),
        ('file_property', '文件属性', 'text', 'file', 0, 2, None, '2', 0),
        ('file_size', '文件大小', 'text', 'file', 0, 3, None, '2', 0),
        ('file_type', '文件类型', 'text', 'file', 0, 4, None, '2', 0),
        ('file_project_type', '项目类型', 'text', 'file', 1, 5, None, '2', 0),
        ('file_project_id', '项目编号', 'text', 'file', 1, 6, None, '2', 0),
        ('file_MD5', 'MD5哈希值', 'text', 'file', 0, 7, None, '2', 0),
        ('file_SHA256', 'SHA256哈希值', 'text', 'file', 0, 8, None, '2', 0),
        ('imported_at', '导入时间', 'text', 'file', 0, 9, None, '2', 0),
    ]
    
    all_fields = raw_fields + result_fields + file_fields
    
    # 强制重建模式：先清空表
    if force:
        print("  清空 field_config 表...")
        db.execute("TRUNCATE TABLE field_config")
    
    for field in all_fields:
        field_id = field[0]
        existing = db.query_one(
            "SELECT id FROM field_config WHERE field_id = %s",
            (field_id,)
        )
        if not existing:
            db.execute(
                """INSERT INTO field_config 
                   (field_id, field_name, field_type, field_table, field_necessary, field_seq, field_options, field_placeholder, field_readonly) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                field
            )
            print(f"  添加字段: {field[1]} ({field_id})")


def init_select_options(db, force=False):
    """初始化 select_options 表
    
    Args:
        db: 数据库连接
        force: 是否强制重建模式
    """
    # 强制重建模式：先清空表
    if force:
        print("  清空 select_options 表...")
        db.execute("TRUNCATE TABLE select_options")
    
    # 数据类型选项
    raw_type_options = [
        ('mRNAseq', '转录组', 1),
        ('Long-Read RNAseq', '长读转录组', 2),
        ('lncRNAseq', 'lncRNAseq', 3),
        ('miRNAseq', 'miRNAseq', 4),
        ('sRNAseq', '小RNA转录组', 5),
        ('epitRNAseq', '表观转录组', 6),
        ('scRNAseq', '单细胞转录组', 7),
        ('LR-scRNAseq', '长读单细胞转录组', 8),
        ('蛋白组', '蛋白组', 9),
        ('磷酸化组', '磷酸化组', 10),
        ('泛素化组', '泛素化组', 11),
        ('乙酰化组', '乙酰化组', 12),
        ('SUMO PTMome', 'SUMO PTMome', 13),
        ('甲基化组', '甲基化组', 14),
        ('糖基化组', '糖基化组', 15),
        ('棕榈酰化组', '棕榈酰化组', 16),
        ('代谢组', '代谢组', 17),
        ('脂质组学', '脂质组学', 18),
        ('免疫组学', '免疫组学', 19),
        ('CyTOF', '质谱流式', 20),
        ('空间多组学', '空间多组学', 21),
    ]
    
    # 物种选项
    raw_species_options = [
        ('Homo sapiens', '人', 1),
        ('Mus musculus', '小鼠', 2),
        ('Rattus norvegicus', '大鼠', 3),
        ('Others', '其他', 4),
    ]
    
    # 组织来源选项
    raw_tissue_options = [
        ('Not Specific', 'Not Specific (非单一组织)', 0),
        ('Adipose tissue', 'Adipose tissue (脂肪组织)', 1),
        ('Adrenal gland', 'Adrenal gland (肾上腺)', 2),
        ('Amygdala', 'Amygdala (杏仁核)', 3),
        ('Basal ganglia', 'Basal ganglia (基底神经节)', 4),
        ('Blood vessel', 'Blood vessel (血管)', 5),
        ('Bone marrow', 'Bone marrow (骨髓)', 6),
        ('Breast', 'Breast (乳房)', 7),
        ('Cerebellum', 'Cerebellum (小脑)', 8),
        ('Cerebral cortex', 'Cerebral cortex (大脑皮层)', 9),
        ('Cervix', 'Cervix (子宫颈)', 10),
        ('Choroid plexus', 'Choroid plexus (脉络丛)', 11),
        ('Colon', 'Colon (结肠)', 12),
        ('Duodenum', 'Duodenum (十二指肠)', 13),
        ('Endometrium', 'Endometrium (子宫内膜)', 14),
        ('Epididymis', 'Epididymis (附睾)', 15),
        ('Esophagus', 'Esophagus (食管)', 16),
        ('Fallopian tube', 'Fallopian tube (输卵管)', 17),
        ('Gallbladder', 'Gallbladder (胆囊)', 18),
        ('Heart muscle', 'Heart muscle (心肌)', 19),
        ('Hippocampal formation', 'Hippocampal formation (海马结构)', 20),
        ('Hypothalamus', 'Hypothalamus (下丘脑)', 21),
        ('Kidney', 'Kidney (肾脏)', 22),
        ('Liver', 'Liver (肝脏)', 23),
        ('Lung', 'Lung (肺)', 24),
        ('Lymph node', 'Lymph node (淋巴结)', 25),
        ('Midbrain', 'Midbrain (中脑)', 26),
        ('Ovary', 'Ovary (卵巢)', 27),
        ('Pancreas', 'Pancreas (胰腺)', 28),
        ('Parathyroid gland', 'Parathyroid gland (甲状旁腺)', 29),
        ('Pituitary gland', 'Pituitary gland (垂体)', 30),
        ('Placenta', 'Placenta (胎盘)', 31),
        ('Prostate', 'Prostate (前列腺)', 32),
        ('Rectum', 'Rectum (直肠)', 33),
        ('Retina', 'Retina (视网膜)', 34),
        ('Salivary gland', 'Salivary gland (唾液腺)', 35),
        ('Seminal vesicle', 'Seminal vesicle (精囊)', 36),
        ('Skeletal muscle', 'Skeletal muscle (骨骼肌)', 37),
        ('Skin', 'Skin (皮肤)', 38),
        ('Small intestine', 'Small intestine (小肠)', 39),
        ('Smooth muscle', 'Smooth muscle (平滑肌)', 40),
        ('Spinal cord', 'Spinal cord (脊髓)', 41),
        ('Spleen', 'Spleen (脾脏)', 42),
        ('Stomach', 'Stomach (胃)', 43),
        ('Testis', 'Testis (睾丸)', 44),
        ('Thymus', 'Thymus (胸腺)', 45),
        ('Thyroid gland', 'Thyroid gland (甲状腺)', 46),
        ('Tongue', 'Tongue (舌头)', 47),
        ('Tonsil', 'Tonsil (扁桃体)', 48),
        ('Urinary bladder', 'Urinary bladder (膀胱)', 49),
        ('Vagina', 'Vagina (阴道)', 50),
        ('Peripheral blood mononuclear cell', '外周单个核细胞 (PMBC)', 51),
    ]
    
    all_options = [
        ('raw_type', raw_type_options),
        ('raw_species', raw_species_options),
        ('raw_tissue', raw_tissue_options),
    ]

    # ==================== 结果数据类型选项 ====================
    # 重要：results_type 必须有对应的 select_options 数据
    # 否则 get_abbr() 和 _build_file_property() 无法正确工作
    # 路径生成需要使用 abbr_mapping 表中的缩写
    results_type_options = [
        ('DEA', '差异分析 (DEA)', 1),
        ('Marker', 'Marker基因', 2),
        ('Enrichment', '富集分析', 3),
        ('PPI', '蛋白互作 (PPI)', 4),
        ('Network', '网络分析', 5),
        ('Clustering', '聚类分析', 6),
        ('Dimension', '降维分析', 7),
        ('Trajectory', '轨迹分析', 8),
    ]
    all_options.append(('results_type', results_type_options))
    
    for option_type, options in all_options:
        for opt in options:
            # opt 是 (option_value, option_label, option_seq) 三元组
            existing = db.query_one(
                "SELECT id FROM select_options WHERE option_type = %s AND option_value = %s",
                (option_type, opt[0])
            )
            if not existing:
                db.execute(
                    "INSERT INTO select_options (option_type, option_value, option_label, option_seq) VALUES (%s, %s, %s, %s)",
                    (option_type, opt[0], opt[1], opt[2])
                )
                print(f"  添加选项: {option_type} -> {opt[1]}")
            else:
                print(f"  选项已存在: {option_type} -> {opt[1]}")


def init_abbr_mapping(db, force=False):
    """初始化 abbr_mapping 表
    
    Args:
        db: 数据库连接
        force: 是否强制重建模式
    """
    # 强制重建模式：先清空表
    if force:
        print("  清空 abbr_mapping 表...")
        db.execute("TRUNCATE TABLE abbr_mapping")
    
    # 数据类型缩写
    raw_type_abbrs = [
        ('mRNAseq', 'mRseq'),
        ('Long-Read RNAseq', 'LRseq'),
        ('lncRNAseq', 'lncseq'),
        ('miRNAseq', 'miseq'),
        ('sRNAseq', 'srseq'),
        ('epitRNAseq', 'epitseq'),
        ('scRNAseq', 'scseq'),
        ('LR-scRNAseq', 'LR_sc'),
        ('蛋白组', 'pro'),
        ('磷酸化组', 'pho'),
        ('泛素化组', 'ubi'),
        ('乙酰化组', 'acety'),
        ('SUMO PTMome', 'sumo'),
        ('甲基化组', 'meth'),
        ('糖基化组', 'glyco'),
        ('棕榈酰化组', 'pal'),
        ('代谢组', 'metab'),
        ('脂质组学', 'lipo'),
        ('免疫组学', 'immuno'),
        ('CyTOF', 'cytof'),
        ('空间多组学', 'spatial'),
        ('QTL', 'qtl'),
    ]
    
    # 物种缩写
    raw_species_abbrs = [
        ('Homo sapiens', 'Hs'),
        ('Mus musculus', 'Mu'),
        ('Rattus norvegicus', 'Ra'),
        ('Others', 'Ot'),
    ]
    
    # 组织来源缩写
    raw_tissue_abbrs = [
        ('Not Specific', 'Ns'),
        ('Adipose tissue', 'At'),
        ('Adrenal gland', 'Ag'),
        ('Amygdala', 'Am'),
        ('Basal ganglia', 'Bg'),
        ('Blood vessel', 'Bv'),
        ('Bone marrow', 'Bm'),
        ('Breast', 'Br'),
        ('Cerebellum', 'Ce'),
        ('Cerebral cortex', 'Cc'),
        ('Cervix', 'Cer'),
        ('Choroid plexus', 'Cp'),
        ('Colon', 'Co'),
        ('Duodenum', 'Du'),
        ('Endometrium', 'En'),
        ('Epididymis', 'Ep'),
        ('Esophagus', 'Es'),
        ('Fallopian tube', 'Fa'),
        ('Gallbladder', 'Ga'),
        ('Heart muscle', 'Hm'),
        ('Hippocampal formation', 'Hf'),
        ('Hypothalamus', 'Hy'),
        ('Kidney', 'Ki'),
        ('Liver', 'Li'),
        ('Lung', 'Lu'),
        ('Lymph node', 'Ln'),
        ('Midbrain', 'Mi'),
        ('Ovary', 'Ov'),
        ('Pancreas', 'Pa'),
        ('Parathyroid gland', 'Pg'),
        ('Pituitary gland', 'Pig'),
        ('Placenta', 'Pl'),
        ('Prostate', 'Pr'),
        ('Rectum', 'Re'),
        ('Retina', 'Ret'),
        ('Salivary gland', 'Sg'),
        ('Seminal vesicle', 'Sv'),
        ('Skeletal muscle', 'Sm'),
        ('Skin', 'Sk'),
        ('Small intestine', 'Si'),
        ('Smooth muscle', 'Sm'),
        ('Spinal cord', 'Sc'),
        ('Spleen', 'Sp'),
        ('Stomach', 'St'),
        ('Testis', 'Te'),
        ('Thymus', 'Th'),
        ('Thyroid gland', 'Tg'),
        ('Tongue', 'To'),
        ('Tonsil', 'Ton'),
        ('Urinary bladder', 'Ub'),
        ('Vagina', 'Va'),
        ('Peripheral blood mononuclear cell', 'pbmc'),
    ]
    
    all_abbrs = [
        ('raw_type', raw_type_abbrs),
        ('raw_species', raw_species_abbrs),
        ('raw_tissue', raw_tissue_abbrs),
    ]

    # ==================== 结果类型缩写 ====================
    # 重要：results_type 必须有对应的 abbr_mapping 数据
    # 否则 _build_result_project_path() 和 _build_file_property() 无法正确生成路径
    # 路径生成规则：/bio/results/{分析类型缩写}/{项目ID}[/{关联项目ID}]
    results_type_abbrs = [
        ('DEA', 'DEA'),
        ('Marker', 'MKR'),
        ('Enrichment', 'ENR'),
        ('PPI', 'PPI'),
        ('Network', 'NET'),
        ('Clustering', 'CLU'),
        ('Dimension', 'DIM'),
        ('Trajectory', 'TRA'),
    ]
    all_abbrs.append(('results_type', results_type_abbrs))
    
    for field_id, abbrs in all_abbrs:
        for abbr in abbrs:
            existing = db.query_one(
                "SELECT id FROM abbr_mapping WHERE field_id = %s AND full_name = %s",
                (field_id, abbr[0])
            )
            if not existing:
                db.execute(
                    "INSERT INTO abbr_mapping (field_id, full_name, abbr_name) VALUES (%s, %s, %s)",
                    (field_id,) + abbr
                )
                print(f"  添加缩写: {field_id} -> {abbr[0]} ({abbr[1]})")
            else:
                print(f"  缩写已存在: {field_id} -> {abbr[0]}")


if __name__ == '__main__':
    args = parse_args()
    success = init_database(force=args.force)
    sys.exit(0 if success else 1)