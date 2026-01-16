#!/usr/bin/env python3
"""
BioData Manager - 字段名称常量
生物信息学数据管理系统 - 字段定义

定义所有元数据字段名称和默认值
"""

# 项目字段
class ProjectFields:
    """项目字段常量"""
    
    # 基础字段
    ID = "id"
    TITLE = "title"
    DESCRIPTION = "description"
    
    # 标识字段
    DOI = "doi"
    DB_ID = "db_id"
    DB_LINK = "db_link"
    
    # 分类字段
    DATA_TYPE = "data_type"
    ORGANISM = "organism"
    TISSUE_TYPE = "tissue_type"
    DISEASE = "disease"
    
    # 作者信息
    AUTHORS = "authors"
    JOURNAL = "journal"
    
    # 标签
    TAGS = "tags"
    
    # 时间字段
    CREATED_DATE = "created_date"
    INDEXED_AT = "indexed_at"
    
    # 路径
    PATH = "path"


# 数据类型
DATA_TYPES = [
    ("rnaseq", "转录组 (RNA-Seq)"),
    ("singlecell", "单细胞转录组"),
    ("spatial", "空间转录组"),
    ("proteomics", "蛋白组"),
    ("phosphoproteomics", "磷酸化组"),
    ("mass_cytometry", "质谱流式 (CyTOF)"),
    ("multiomics", "多组学"),
    ("other", "其他")
]

# 物种
SPECIES = [
    ("Homo sapiens", "人类"),
    ("Mus musculus", "小鼠"),
    ("Rattus norvegicus", "大鼠"),
    ("Danio rerio", "斑马鱼"),
    ("Drosophila melanogaster", "果蝇"),
    ("Caenorhabditis elegans", "秀丽隐杆线虫"),
    ("Arabidopsis thaliana", "拟南芥"),
    ("Saccharomyces cerevisiae", "酿酒酵母"),
    ("Escherichia coli", "大肠杆菌"),
    ("other", "其他")
]

# 样本类型
TISSUE_TYPES = [
    ("whole_blood", "全血"),
    ("pbmc", "外周血单个核细胞 (PBMC)"),
    ("tumor", "肿瘤组织"),
    ("normal_tissue", "正常组织"),
    ("cell_line", "细胞系"),
    ("primary_cells", "原代细胞"),
    ("tissue_lysate", "组织裂解物"),
    ("other", "其他")
]

# 分析类型
ANALYSIS_TYPES = [
    ("differential", "差异表达分析"),
    ("enrichment", "富集分析"),
    ("pathway", "通路分析"),
    ("clustering", "聚类分析"),
    ("network", "网络分析"),
    ("other", "其他分析")
]

# 标签
TAGS = [
    ("public", "公开数据"),
    ("controlled", "受控访问"),
    ("raw", "原始数据"),
    ("processed", "处理后数据"),
    ("quality_control", "质量控制"),
    ("replicate", "生物学重复"),
    ("time_series", "时间序列"),
    ("treatment", "处理组"),
    ("control", "对照组")
]

# 文件类型
FILE_TYPES = {
    '.fastq': 'raw Sequencing Data',
    '.sam': 'Alignment File',
    '.bam': 'Alignment File',
    '.fq': 'raw Sequencing Data',
    '.h5ad': 'Single-cell Data',
    '.mtx': 'Matrix File',
    '.raw': 'Mass Spectrometry Data',
    '.mzml': 'Mass Spectrometry Data',
    '.wiff': 'Mass Spectrometry Data',
    '.fcs': 'Flow Cytometry Data',
    '.csv': 'Table/Report',
    '.tsv': 'Table/Report',
    '.txt': 'Text File',
    '.h5': 'HDF5 Data',
    '.pdf': 'Document',
    '.png': 'Image',
    '.jpg': 'Image',
    '.zip': 'Archive',
    '.gz': 'Compressed Data'
}

# 默认项目字段配置
DEFAULT_METADATA_CONFIG = [
    {
        'field_name': 'data_type',
        'label': '数据类型',
        'field_type': 'multi_select',
        'options': DATA_TYPES,
        'required': True,
        'sort_order': 1
    },
    {
        'field_name': 'organism',
        'label': '物种',
        'field_type': 'multi_select',
        'options': SPECIES,
        'required': True,
        'sort_order': 2
    },
    {
        'field_name': 'tissue_type',
        'label': '样本类型',
        'field_type': 'select',
        'options': TISSUE_TYPES,
        'required': False,
        'sort_order': 3
    },
    {
        'field_name': 'disease',
        'label': '疾病背景',
        'field_type': 'text',
        'options': [],
        'required': False,
        'sort_order': 4
    },
    {
        'field_name': 'doi',
        'label': 'DOI',
        'field_type': 'text',
        'options': [],
        'required': False,
        'sort_order': 5
    },
    {
        'field_name': 'db_id',
        'label': '数据库编号',
        'field_type': 'text',
        'options': [],
        'required': False,
        'sort_order': 6
    },
    {
        'field_name': 'authors',
        'label': '作者',
        'field_type': 'text',
        'options': [],
        'required': False,
        'sort_order': 7
    },
    {
        'field_name': 'journal',
        'label': '期刊',
        'field_type': 'text',
        'options': [],
        'required': False,
        'sort_order': 8
    },
    {
        'field_name': 'tags',
        'label': '标签',
        'field_type': 'multi_select',
        'options': TAGS,
        'required': False,
        'sort_order': 9
    },
    {
        'field_name': 'description',
        'label': '描述',
        'field_type': 'textarea',
        'options': [],
        'required': False,
        'sort_order': 10
    }
]
