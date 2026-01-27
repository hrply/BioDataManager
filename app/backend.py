#!/usr/bin/env python3
"""
BioData Manager - 后端业务逻辑
生物信息学数据管理系统 - 数据管理核心模块

提供项目管理、文件操作、数据导入等核心功能
"""

import json
import os
import re
import shutil
import random
import string
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from database_mysql import DatabaseManager
from metadata_config_manager_mysql import MetadataConfigManager


def _format_datetime(value, fmt='%Y-%m-%d %H:%M:%S') -> str:
    """安全格式化时间字段"""
    if not value or value == 0:
        return ''
    if isinstance(value, str):
        return value[:19] if len(value) >= 19 else value
    if hasattr(value, 'strftime'):
        return value.strftime(fmt)
    return ''


class BioDataManager:
    """生物数据管理器"""
    
    # 数据类型映射
    DATA_TYPE_MAPPING = {
        'fastq': 'mRNAseq',
        'sam': 'mRNAseq',
        'bam': 'mRNAseq',
        'fq': 'mRNAseq',
        'h5ad': 'scRNAseq',
        'mtx': 'scRNAseq',
        'raw': '蛋白组',
        'mzml': '蛋白组',
        'wiff': '蛋白组',
        'fcs': '免疫组学',
        'csv': '其他',
        'tsv': '其他',
        'txt': '其他',
        'h5': '其他',
    }
    
    # 文件类型映射
    FILE_TYPE_MAPPING = {
        '.fastq': 'FASTQ',
        '.sam': 'SAM',
        '.bam': 'BAM',
        '.fq': 'FASTQ',
        '.h5ad': 'H5AD',
        '.mtx': 'MTX',
        '.raw': 'RAW',
        '.mzml': 'MZML',
        '.wiff': 'WIFF',
        '.fcs': 'FCS',
        '.csv': 'CSV',
        '.tsv': 'TSV',
        '.txt': 'TXT',
        '.h5': 'H5',
        '.pdf': 'PDF',
        '.png': 'PNG',
        '.jpg': 'JPG',
        '.jpeg': 'JPEG',
        '.zip': 'ZIP',
        '.gz': 'GZ',
    }
    
    # 数据库编号模式
    DB_PATTERNS = [
        (r'GS[Ee]\d+', 'GEO', 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc='),
        (r'GS[Mm]\d+', 'GEO', 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc='),
        (r'PRJNA\d+', 'BioProject', 'https://www.ncbi.nlm.nih.gov/bioproject/'),
        (r'ERR\d+', 'ENA', 'https://www.ebi.ac.uk/ena/browser/view/'),
        (r'SRR\d+', 'ENA', 'https://www.ebi.ac.uk/ena/browser/view/'),
        (r'MTAB_\d+', 'ArrayExpress', 'https://www.ebi.ac.uk/arrayexpress/experiments/'),
        (r'PXD\d+', 'ProteomeXchange', 'https://www.proteomecentral.com/protexchange/'),
    ]
    
    def __init__(self, db_manager: DatabaseManager, config_manager: MetadataConfigManager):
        self.db_manager = db_manager
        self.config_manager = config_manager

        # 路径配置（数据库设计规范要求）
        self.raw_data_dir = Path("/bio/rawdata")
        self.results_dir = Path("/bio/results")
        self.downloads_dir = Path("/bio/downloads")
    
    def generate_project_id(self, project_type: str) -> str:
        """生成项目编号（数据库设计规范：格式: {TYPE}_{8位UUID}）"""
        chars = string.ascii_letters + string.digits
        uuid_8 = ''.join(random.choice(chars) for _ in range(8))
        return f"{project_type}_{uuid_8}"
    
    def get_abbr(self, field_id: str, full_name: str) -> str:
        """获取缩写
        
        优先从缩写映射表获取，如果没有则取全称的前3个字符
        如果全称少于3个字符，则用下划线填充到3位
        如果是纯中文且找不到映射，则尝试从 label 映射获取，否则使用全拼首字母
        """
        if not full_name:
            return 'UNK'
        
        # 检查是否包含中文字符
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in full_name)
        
        try:
            # 尝试从缩写映射表获取
            abbr = self.config_manager.get_abbr_mapping(field_id, full_name)
            if abbr:
                return abbr
            
            # 如果是中文且没找到映射，尝试用 label 查找
            if has_chinese:
                abbr = self._get_abbr_by_label(field_id, full_name)
                if abbr:
                    return abbr
        except Exception:
            # 如果表不存在或查询失败，使用默认逻辑
            pass
        
        # 默认：取前3个字符（保留英文和数字）
        abbr = ''.join(c for c in full_name[:3] if c.isalnum())
        if len(abbr) < 3:
            abbr = abbr.ljust(3, '_')
        # 如果还是空（纯中文），使用拼音首字母或全称
        if not abbr:
            if has_chinese:
                # 中文值：尝试获取 label 并取首字母，如果没有则使用原值
                label = self._get_option_label(field_id, full_name)
                if label and label != full_name:
                    abbr = ''.join(c for c in label[:3] if c.isalnum())
                    if len(abbr) < 3:
                        abbr = abbr.ljust(3, '_')
                if not abbr:
                    # 使用安全的字符（将中文转换为拼音首字母或下划线）
                    abbr = ''.join(c if c.isalnum() else '_' for c in full_name[:6])
                    abbr = abbr[:3].ljust(3, '_') if len(abbr) >= 3 else abbr.ljust(3, '_')
            else:
                abbr = full_name[:3]
                if len(abbr) < 3:
                    abbr = abbr.ljust(3, '_')
        return abbr
    
    def _get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        ext = Path(filename).suffix.lower()
        return self.FILE_TYPE_MAPPING.get(ext, Path(filename).suffix[1:] if Path(filename).suffix else 'unknown')
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024 # type: ignore
        return f"{size_bytes:.1f} TB"
    
    def _validate_comma_separated(self, value: str, field_name: str = '字段', allow_chinese: bool = False) -> str:
        """验证并规范化逗号分隔的字段值
        
        1. 自动转换中文逗号（，）、全角逗号（／）、全角问号（？）为英文逗号（,）
        2. 只允许：大写字母(A-Z)、小写字母(a-z)、数字(0-9)、下划线(_)、英文逗号(,)
        3. 如果 allow_chinese=True，则额外允许中文字符
        4. 如果包含其他字符，抛出异常
        """
        if not value:
            return value
        
        # 步骤1：自动转换各种全角字符为英文逗号
        normalized = value.replace('，', ',').replace('／', ',').replace('？', ',').replace('?', ',')
        
        # 步骤2：验证剩余字符是否合法
        parts = normalized.split(',')
        invalid_chars = set()
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # 检查每个字符是否合法
            for char in part:
                if char.isupper() or char.islower() or char.isdigit() or char == '_' or char == ' ' or char == '-' or char == '.':
                    continue  # 允许的字符（字母、数字、下划线、空格、连字符、点）
                if allow_chinese and '\u4e00' <= char <= '\u9fff':
                    continue  # 允许中文字符
                invalid_chars.add(char)
        
        if invalid_chars:
            invalid_list = ', '.join(sorted(set(invalid_chars)))
            raise ValueError(f"{field_name} 包含无效字符 [{invalid_list}]，只允许字母、数字、下划线和英文逗号")
        
        return normalized
    
    def _value_to_label(self, field_id: str, value: str) -> str:
        """将字段值转换为显示标签（value → label 转换）
        
        用于前端显示：将存储的 value 转换为对应的中文 label
        例如: 'Long-Read RNAseq' -> '长读转录组'
        """
        if not value:
            return value
        
        try:
            options = self.config_manager.get_field_options(field_id)
            if not options:
                return value
            
            # 构建 value → label 映射
            value_to_label = {}
            for opt in options:
                if isinstance(opt, dict) and 'value' in opt and 'label' in opt:
                    value_to_label[str(opt['value'])] = str(opt['label'])
            
            # 多值转换（逗号分隔）
            parts = value.split(',')
            labels = []
            for part in parts:
                part = part.strip()
                if part in value_to_label:
                    labels.append(value_to_label[part])
                else:
                    labels.append(part)
            
            return ','.join(labels)
        except Exception:
            return value
    
    def _convert_select_values_to_labels(self, project: Dict, table: str = 'raw') -> Dict:
        """将项目中的 select 类型字段值转换为 label 显示"""
        if not project:
            return project
        
        try:
            # 获取所有字段配置
            all_configs = self.config_manager.get_all_configs()
            
            # 筛选指定表的 select 类型字段
            select_fields = {}
            for config in all_configs:
                if config.get('field_table') == table and config.get('field_type') == 'select':
                    select_fields[config['field_id']] = True
            
            # 转换 select 字段
            for field_id in select_fields:
                if field_id in project and project[field_id]:
                    project[field_id] = self._value_to_label(field_id, project[field_id])
            
        except Exception as e:
            print(f"转换字段标签失败: {e}")
        
        return project
    
    def _row_to_dict(self, row, table_name: str) -> Optional[Dict]:
        """将数据库查询结果行转换为字典（动态获取列名）
        
        使用 DESCRIBE 获取表结构，避免硬编码列索引
        """
        if not row:
            return None
        
        try:
            connection = self.db_manager.get_connection()
            if connection is None:
                return None
            cursor = connection.cursor()
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [desc[0] for desc in cursor.fetchall()]
            cursor.close()
            connection.close()
            return dict(zip(columns, row))
        except Exception as e:
            print(f"转换行为字典失败: {e}")
            return None
    
    # ==================== 原始数据项目管理 ====================
    
    def _build_raw_project_path(self, raw_type: str, species: str, tissue: str, raw_id: str) -> Path:
        """构建原始数据项目路径（三级结构）
        
        路径格式: {raw_data_dir}/{数据类型}/{物种}/{样本来源}/{项目ID}/
        如果样本来源为空，则: {raw_data_dir}/{数据类型}/{物种}/{项目ID}/
        """
        # 获取缩写
        raw_type_abbr = self.get_abbr('raw_type', raw_type) if raw_type else 'UNK'
        species_abbr = self.get_abbr('raw_species', species) if species else 'UNK'
        tissue_abbr = self.get_abbr('raw_tissue', tissue) if tissue else ''
        
        # 构建路径
        if tissue_abbr:
            # 三级结构：{类型}/{物种}/{组织}/{项目ID}/
            project_path = self.raw_data_dir / raw_type_abbr / species_abbr / tissue_abbr / raw_id
        else:
            # 二级结构：{类型}/{物种}/{项目ID}/
            project_path = self.raw_data_dir / raw_type_abbr / species_abbr / raw_id
        
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path
    
    def create_raw_project(self, data: Dict) -> Dict:
        """创建原始数据项目"""
        raw_id = self.generate_project_id('RAW')
        
        # 获取字段值
        raw_type = self._validate_comma_separated(data.get('raw_type', ''), '数据类型 (raw_type)', allow_chinese=True)
        species = self._validate_comma_separated(data.get('raw_species', ''), '物种 (raw_species)', allow_chinese=True)
        
        # 处理多选字段
        raw_tissue_input = data.get('raw_tissue', '')
        if isinstance(raw_tissue_input, list):
            raw_tissue_input = ','.join([t.strip() for t in raw_tissue_input if t.strip()])
        
        # 验证并规范化逗号分隔的字段
        raw_tissue = self._validate_comma_separated(raw_tissue_input, '组织来源 (raw_tissue)')
        # 关键词允许中文字符
        keywords = self._validate_comma_separated(
            data.get('raw_keywords', '') or '', '关键词 (raw_keywords)', allow_chinese=True
        )
        
        # 构建项目路径（三级结构）
        project_path = self._build_raw_project_path(raw_type, species, raw_tissue, raw_id)
        
        # 构建SQL插入语句
        self.db_manager.execute("""
            INSERT INTO raw_project 
            (raw_id, raw_title, raw_type, raw_species, raw_tissue, raw_DOI, raw_db_id, raw_db_link,
             raw_author, raw_article, raw_description, raw_keywords)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            raw_id,
            data.get('raw_title', ''),
            raw_type,
            species,
            raw_tissue,
            data.get('raw_DOI', ''),
            data.get('raw_db_id', ''),
            data.get('raw_db_link', ''),
            data.get('raw_author', ''),
            data.get('raw_article', ''),
            data.get('raw_description', ''),
            keywords,
        ))
        
        return self.get_raw_project_by_id(raw_id)
    
    def get_all_raw_projects(self) -> List[Dict]:
        """获取所有原始数据项目"""
        projects = self.db_manager.query("""
            SELECT * FROM raw_project ORDER BY created_at DESC
        """)
        
        result = []
        for row in projects:
            project = self._row_to_dict(row, "raw_project")
            if project:
                project = self._convert_select_values_to_labels(project, 'raw')
                result.append(project)
        
        return result
    
    def get_raw_project_by_id(self, raw_id: str) -> Optional[Dict]:
        """根据ID获取原始数据项目"""
        row = self.db_manager.query_one(
            "SELECT * FROM raw_project WHERE raw_id = %s",
            (raw_id,)
        )

        if row:
            project = self._row_to_dict(row, "raw_project")

            if project:
                # 获取项目文件列表（动态获取列名）
                files = self.db_manager.query("""
                    SELECT * FROM file_record
                    WHERE file_project_type = 'raw' AND file_project_id = %s
                """, (raw_id,))

                file_list = []
                for f in files:
                    file_dict = self._row_to_dict(f, "file_record")
                    if file_dict and 'imported_at' in file_dict and file_dict['imported_at']:
                        file_dict['imported_at'] = file_dict['imported_at'].strftime('%Y-%m-%d %H:%M:%S')
                    file_list.append(file_dict)

                project['files'] = file_list
                # 转换 select 类型字段的 value 为 label
                project = self._convert_select_values_to_labels(project, 'raw')
                return project
        return None
    
    def update_raw_project(self, data: Dict) -> bool:
        """更新原始数据项目"""
        raw_id = data.get('raw_id')
        if not raw_id:
            return False
        
        # 处理多选字段
        raw_tissue_input = data.get('raw_tissue', '')
        if isinstance(raw_tissue_input, list):
            raw_tissue_input = ','.join([t.strip() for t in raw_tissue_input if t.strip()])
        
        # 验证并规范化逗号分隔的字段
        raw_tissue = self._validate_comma_separated(raw_tissue_input, '组织来源 (raw_tissue)')
        # 关键词允许中文字符
        keywords = self._validate_comma_separated(
            data.get('raw_keywords', '') or '', '关键词 (raw_keywords)', allow_chinese=True
        )
        
        self.db_manager.execute("""
            UPDATE raw_project 
            SET raw_title = %s, raw_type = %s, raw_species = %s, raw_tissue = %s,
                raw_DOI = %s, raw_db_id = %s, raw_db_link = %s, raw_author = %s,
                raw_article = %s, raw_description = %s, raw_keywords = %s
            WHERE raw_id = %s
        """, (
            data.get('raw_title', ''),
            data.get('raw_type', ''),
            data.get('raw_species', ''),
            raw_tissue,
            data.get('raw_DOI', ''),
            data.get('raw_db_id', ''),
            data.get('raw_db_link', ''),
            data.get('raw_author', ''),
            data.get('raw_article', ''),
            data.get('raw_description', ''),
            keywords,
            raw_id
        ))
        
        return True
    
    def delete_raw_project(self, raw_id: str) -> bool:
        """删除原始数据项目"""
        try:
            project = self.get_raw_project_by_id(raw_id)
            if not project:
                return False
            
            # 删除文件记录
            self.db_manager.execute("DELETE FROM file_record WHERE file_project_id = %s", (raw_id,))
            # 删除项目记录
            self.db_manager.execute("DELETE FROM raw_project WHERE raw_id = %s", (raw_id,))
            
            # 删除项目目录
            project_path = self._build_raw_project_path(
                project.get('raw_type', ''),
                project.get('raw_species', ''),
                project.get('raw_tissue', ''),
                raw_id
            )
            if project_path.exists():
                shutil.rmtree(project_path)
            
            return True
        except Exception as e:
            print(f"删除原始数据项目失败: {e}")
            return False
    
    # ==================== 结果数据项目管理 ====================
    
    def _build_result_project_path(self, results_type: str, raw_type: str, species: str, 
                                    tissue: str, raw_project_id: str, results_id: str) -> Path:
        """构建结果数据项目路径
        
        路径格式: {results_dir}/{结果项目ID}/{分析类型}/{关联原始项目ID}/
        示例: /bio/results/RES_ABC123/DEA/RAW_XYZ789/
        
        """
        results_type_abbr = self.get_abbr('results_type', results_type) if results_type else ''
        
        # 构建完整路径: {results_dir}/{项目ID}/{分析类型}/{关联项目ID}/
        if raw_project_id:
            project_path = self.results_dir / results_id / results_type_abbr / raw_project_id
        else:
            project_path = self.results_dir / results_id / results_type_abbr
        
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path
    
    def create_result_project(self, data: Dict) -> Dict:
        """创建结果数据项目"""
        results_id = self.generate_project_id('RES')
        
        results_type = self._validate_comma_separated(data.get('results_type', ''), '结果类型 (results_type)', allow_chinese=True)
        
        # 验证并规范化逗号分隔的字段
        raw_project_id = self._validate_comma_separated(
            data.get('results_raw', ''), '关联原始数据 (results_raw)'
        )
        # 关键词允许中文字符
        keywords = self._validate_comma_separated(
            (data.get('keywords', '') or data.get('results_keywords', '') or ''), 
            '关键词 (results_keywords)', allow_chinese=True
        )
        
        # 解析和排序关联项目编号（用于路径和数据库存储）
        sorted_raw_ids = self._parse_and_sort(raw_project_id) if raw_project_id else ''
        # 对 results_raw 字段进行排序（ASCII顺序：数字 < 大写 < 小写）
        if raw_project_id:
            raw_ids_list = [r.strip() for r in raw_project_id.split(',') if r.strip()]
            sorted_raw_project_id = ','.join(sorted(raw_ids_list, key=lambda x: x.encode('utf-8')))
        else:
            sorted_raw_project_id = ''
        
        # 构建项目路径（新结构）
        project_path = self._build_result_project_path(
            results_type, '', '', '', sorted_raw_ids, results_id
        )
        
        self.db_manager.execute("""
            INSERT INTO result_project 
            (results_id, results_title, results_type, results_raw, results_description, results_keywords)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            results_id,
            data.get('results_title', ''),
            results_type,
            sorted_raw_project_id,  # 存储排序后的值
            data.get('results_description', ''),
            keywords,  # 使用验证后的结果
        ))
        
        return self.get_result_project_by_id(results_id)
    
    def get_all_result_projects(self) -> List[Dict]:
        """获取所有结果数据项目"""
        projects = self.db_manager.query("""
            SELECT * FROM result_project ORDER BY created_at DESC
        """)
        
        result = []
        for row in projects:
            project = self._row_to_dict(row, "result_project")
            if project:
                project = self._convert_select_values_to_labels(project, 'result')
                result.append(project)
        
        return result
    
    def get_result_project_by_id(self, results_id: str) -> Optional[Dict]:
        """根据ID获取结果数据项目"""
        row = self.db_manager.query_one(
            "SELECT * FROM result_project WHERE results_id = %s",
            (results_id,)
        )

        if row:
            project = self._row_to_dict(row, "result_project")

            if project:
                # 获取项目文件列表（动态获取列名）
                files = self.db_manager.query("""
                    SELECT * FROM file_record
                    WHERE file_project_type = 'result' AND file_project_id = %s
                """, (results_id,))

                file_list = []
                for f in files:
                    file_dict = self._row_to_dict(f, "file_record")
                    if file_dict and 'imported_at' in file_dict and file_dict['imported_at']:
                        file_dict['imported_at'] = file_dict['imported_at'].strftime('%Y-%m-%d %H:%M:%S')
                    file_list.append(file_dict)

                project['files'] = file_list
                # 转换 select 类型字段的 value 为 label
                project = self._convert_select_values_to_labels(project, 'result')
                return project
        return None
    
    def update_result_project(self, data: Dict) -> bool:
        """更新结果数据项目"""
        results_id = data.get('results_id')
        if not results_id:
            return False
        
        # 验证并规范化逗号分隔的字段
        raw_project_id = self._validate_comma_separated(
            data.get('results_raw', ''), '关联原始数据 (results_raw)'
        )
        # 关键词允许中文字符
        keywords = self._validate_comma_separated(
            data.get('results_keywords', '') or '', '关键词 (results_keywords)', allow_chinese=True
        )
        
        self.db_manager.execute("""
            UPDATE result_project 
            SET results_title = %s, results_type = %s, results_raw = %s,
                results_description = %s, results_keywords = %s
            WHERE results_id = %s
        """, (
            data.get('results_title', ''),
            data.get('results_type', ''),
            raw_project_id,
            data.get('results_description', ''),
            keywords,
            results_id
        ))
        
        return True
    
    def delete_result_project(self, results_id: str) -> bool:
        """删除结果数据项目"""
        try:
            project = self.get_result_project_by_id(results_id)
            if not project:
                return False
            
            # 删除文件记录
            self.db_manager.execute("DELETE FROM file_record WHERE file_project_id = %s", (results_id,))
            # 删除项目记录
            self.db_manager.execute("DELETE FROM result_project WHERE results_id = %s", (results_id,))
            
            # 获取项目信息用于构建路径
            results_type = project.get('results_type', '')
            raw_project_id = project.get('results_raw', '')
            results_type_abbr = self.get_abbr('results_type', results_type) if results_type else ''
            
            # 构建路径（新结构）
            if raw_project_id:
                project_path = self.results_dir / results_id / results_type_abbr / raw_project_id
            else:
                project_path = self.results_dir / results_id / results_type_abbr
            
            # 删除项目目录
            if project_path.exists():
                shutil.rmtree(project_path)
            
            return True
        except Exception as e:
            print(f"删除结果数据项目失败: {e}")
            return False
    
    # ==================== 文件记录管理 ====================
    
    def get_files_by_project(self, project_type: str, project_id: str) -> List[Dict]:
        """获取项目的文件列表"""
        files = self.db_manager.query("""
            SELECT * FROM file_record 
            WHERE file_project_type = %s AND file_project_id = %s 
            ORDER BY imported_at DESC
        """, (project_type, project_id))
        
        result = []
        for row in files:
            file_dict = self._row_to_dict(row, "file_record")
            if file_dict and 'imported_at' in file_dict and file_dict['imported_at']:
                file_dict['imported_at'] = file_dict['imported_at'].strftime('%Y-%m-%d %H:%M:%S')
            result.append(file_dict)
        return result
    
    def add_file_record(self, project_type: str, project_id: str, file_path: Path, metadata: Dict = None, ref_project_id: str = None, overwrite: bool = False) -> Dict:
        """添加文件记录
        
        Args:
            project_type: 'raw' 或 'result'
            project_id: 项目编号
            file_path: 文件的完整路径
            metadata: 可选的元数据字典（如果已传入则使用，否则从数据库查询）
            ref_project_id: 关联项目编号（结果文件关联的原始数据项目）
            overwrite: 是否覆盖已存在的文件（需要 file_project_id+file_project_type+file_path+file_name 均相同）
            
        Returns:
            Dict: {'success': bool, 'message': str, 'is_duplicate': bool}
        """
        try:
            # file_name: 只包含文件名（不含路径）
            file_name = file_path.name
            
            # file_path: 相对于 /bio 的路径（不包含文件名）
            try:
                dir_path = file_path.parent.relative_to(Path('/bio'))
            except ValueError:
                dir_path = file_path.parent
            
            # 检查重复文件（同一项目、同一路径下同名文件才算真正重复）
            existing = self.db_manager.query_one("""
                SELECT id FROM file_record 
                WHERE file_project_type = %s AND file_project_id = %s AND file_path = %s AND file_name = %s
            """, (project_type, project_id, str(dir_path), file_name))

            if existing:
                if not overwrite:
                    return {
                        'success': False,
                        'message': f'文件 "{file_name}" 已存在于该路径下，是否覆盖？',
                        'is_duplicate': True,
                        'existing_id': existing[0]
                    }
                else:
                    # 删除旧记录，保留新的
                    self.db_manager.execute("DELETE FROM file_record WHERE id = %s", (existing[0],))
            
            # 生成 file_property
            # =================================================================
            # 重要：只使用前端传入的 metadata，不从数据库查询
            #
            # 设计规范：
            # - file_path 和 file_property 的生成只使用前端传入的 metadata
            # - 不查询数据库的现有值（除了 raw_id 和 results_id）
            # - 如果前端没有传入某字段值，该字段使用空字符串
            # - 这是为了让用户明确知道他们设置的值会被使用
            # =================================================================
            project_metadata = metadata.copy() if metadata else {}
            
            if project_type == 'raw':
                project_metadata.setdefault('raw_type', '')
                project_metadata.setdefault('raw_species', '')
                project_metadata.setdefault('raw_tissue', '')
            else:
                project_metadata.setdefault('results_type', '')
                project_metadata.setdefault('results_raw', '')
            
            file_property = self._build_file_property(project_type, project_id, project_metadata)
            
            self.db_manager.execute("""
                INSERT INTO file_record 
                (file_name, file_path, file_property, file_size, file_type, file_project_type, file_project_id, file_project_ref_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                file_name,
                str(dir_path),
                file_property,
                file_path.stat().st_size,
                self._get_file_type(file_name),
                project_type,
                project_id,
                ref_project_id
            ))
            
            # 更新项目文件计数和总大小
            if project_type == 'raw':
                self._update_raw_file_count(project_id)
            elif project_type == 'result':
                self._update_result_file_count(project_id)
            
            return {
                'success': True,
                'message': '文件导入成功',
                'is_duplicate': False
            }
        except Exception as e:
            print(f"添加文件记录失败: {e}")
            return {
                'success': False,
                'message': f'导入失败: {str(e)}',
                'is_duplicate': False
            }
    
    def delete_file_record(self, file_id: int) -> bool:
        """删除文件记录"""
        try:
            file_record = self.db_manager.query_one(
                "SELECT * FROM file_record WHERE id = %s",
                (file_id,)
            )
            if not file_record:
                return False
            
            file_dict = self._row_to_dict(file_record, "file_record")
            project_type = file_dict.get('file_project_type')
            project_id = file_dict.get('file_project_id')
            
            self.db_manager.execute("DELETE FROM file_record WHERE id = %s", (file_id,))
            
            # 更新项目文件计数和总大小
            if project_type == 'raw':
                self._update_raw_file_count(project_id)
            elif project_type == 'result':
                self._update_result_file_count(project_id)
            
            return True
        except Exception as e:
            print(f"删除文件记录失败: {e}")
            return False
    
    def _update_raw_file_count(self, raw_id: str):
        """更新原始项目的文件计数和总大小"""
        result = self.db_manager.query_one("""
            SELECT COUNT(*), COALESCE(SUM(file_size), 0) 
            FROM file_record 
            WHERE file_project_type = 'raw' AND file_project_id = %s
        """, (raw_id,))
        
        if result:
            file_count, total_size = result
            self.db_manager.execute("""
                UPDATE raw_project SET raw_file_count = %s, raw_total_size = %s WHERE raw_id = %s
            """, (file_count, total_size, raw_id))
    
    def _update_result_file_count(self, results_id: str):
        """更新结果项目的文件计数和总大小"""
        result = self.db_manager.query_one("""
            SELECT COUNT(*), COALESCE(SUM(file_size), 0) 
            FROM file_record 
            WHERE file_project_type = 'result' AND file_project_id = %s
        """, (results_id,))
        
        if result:
            file_count, total_size = result
            self.db_manager.execute("""
                UPDATE result_project SET results_file_count = %s, results_total_size = %s WHERE results_id = %s
            """, (file_count, total_size, results_id))
    
    # ==================== 兼容性方法（供现有代码使用）====================
    
    def get_all_projects(self) -> List[Dict]:
        """获取所有项目（兼容旧API）"""
        return self.get_all_raw_projects()
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """获取项目（兼容旧API）"""
        return self.get_raw_project_by_id(project_id)
    
    def create_project(self, data: Dict) -> Dict:
        """创建项目（兼容旧API）"""
        return self.create_raw_project(data)
    
    def update_project(self, data: Dict) -> bool:
        """更新项目（兼容旧API）"""
        return self.update_raw_project(data)
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目（兼容旧API）"""
        return self.delete_raw_project(project_id)
    
    def get_all_bioresult_projects(self) -> List[Dict]:
        """获取所有生物结果项目（兼容旧API）"""
        return self.get_all_result_projects()
    
    def get_bioresult_project_by_id(self, project_id: str) -> Optional[Dict]:
        """获取生物结果项目（兼容旧API）"""
        return self.get_result_project_by_id(project_id)
    
    def create_bioresult_project(self, data: Dict) -> Dict:
        """创建生物结果项目（兼容旧API）"""
        return self.create_result_project(data)
    
    def update_bioresult_project(self, data: Dict) -> bool:
        """更新生物结果项目（兼容旧API）"""
        return self.update_result_project(data)
    
    def delete_bioresult_project(self, project_id: str) -> bool:
        """删除生物结果项目（兼容旧API）"""
        return self.delete_result_project(project_id)
    
    # ==================== 字段值处理辅助函数 ====================
    
    def _parse_and_sort(self, raw_ids: str) -> str:
        """解析逗号分隔的项目ID，按字母排序后组合
        
        支持分隔符：中文逗号 `，`、英文逗号 `,`、全角问号 `？`、英文问号 `?`
        示例: "RAW_A1？RAW_2A, RAW_sa" → 排序后: "RAW_2ARAW_A1RAW_sa"
        
        Args:
            raw_ids: 逗号分隔的项目ID字符串
            
        Returns:
            排序后组合的项目ID字符串
        """
        if not raw_ids or not raw_ids.strip():
            return ''
        
        # 解析：替换各种分隔符为英文逗号，分割，去空值
        # 替换顺序：全角问号 → 中文逗号 → 英文问号 → 英文逗号
        normalized = raw_ids.replace('？', ',').replace('，', ',').replace('?', ',').replace(',', ',')
        ids = normalized.split(',')
        ids = [pid.strip() for pid in ids if pid.strip()]
        
        if not ids:
            return ''
        
        # 按字母排序（ASCII顺序：数字 < 大写字母 < 小写字母）
        sorted_ids = sorted(ids)
        
        # 组合
        result = ''.join(sorted_ids)
        return result
    
    def _get_option_label(self, option_type: str, option_value: str) -> str:
        """根据 option_type 和 option_value 获取对应的 option_label
        
        Args:
            option_type: 选项类型（对应 field_id）
            option_value: 选项值（对应 option_value）
            
        Returns:
            选项标签（对应 option_label），如果未找到则返回原值
        """
        if not option_type or not option_value:
            return option_value or ''
        
        row = self.db_manager.query_one(
            "SELECT option_label FROM select_options WHERE option_type = %s AND option_value = %s",
            (option_type, option_value)
        )
        
        if row and row[0]:
            return row[0]
        return option_value
    
    def _get_abbr_by_label(self, field_id: str, option_value: str) -> Optional[str]:
        """根据 option_value 查找对应的 label，再从 abbr_mapping 获取缩写
        
        用于处理中文值的情况：当直接用 value 找不到缩写时，尝试通过 label 查找
        
        Args:
            field_id: 字段ID
            option_value: 选项值
            
        Returns:
            缩写，如果未找到则返回 None
        """
        if not field_id or not option_value:
            return None
        
        try:
            # 先获取 option_value 对应的 label
            label = self._get_option_label(field_id, option_value)
            if label and label != option_value:
                # 用 label 查找缩写
                abbr = self.config_manager.get_abbr_mapping(field_id, label)
                if abbr:
                    return abbr
        except Exception:
            pass
        return None
    
    def _has_required_metadata(self, project_type: str, metadata: Dict) -> bool:
        """检查 metadata 是否包含必要的字段（非空值）"""
        if not metadata:
            return False
        if project_type == 'raw':
            # 原始数据至少需要 raw_type 和 raw_species 才能生成 file_property
            return bool(metadata.get('raw_type') and metadata.get('raw_species'))
        else:
            # 结果数据至少需要 results_type 才能生成 file_property
            return bool(metadata.get('results_type'))
    
    def _build_file_property(self, project_type: str, project_id: str, metadata: Dict = None) -> str:
        """生成文件属性字符串
        
        设计规范：
        - 只使用传入的 metadata 参数，不查询数据库
        - 使用 get_abbr() 查询 abbr_mapping 获取缩写
        - file_property 格式：
          - 原始数据: {数据类型缩写}-{物种缩写}-[{组织来源缩写}]
          - 结果数据: {分析类型缩写}-[{关联项目ID（排序后组合）}]
        
        Args:
            project_type: 'raw' 或 'result'
            project_id: 项目编号
            metadata: 元数据字典（必须从调用方传入，不查询数据库）
            
        Returns:
            文件属性字符串
        """
        if project_type == 'raw':
            # 原始数据文件属性
            raw_type = metadata.get('raw_type', '') if metadata else ''
            raw_species = metadata.get('raw_species', '') if metadata else ''
            raw_tissue = metadata.get('raw_tissue', '') if metadata else ''
            
            # 获取缩写（使用 user input 值查询缩写表）
            raw_type_abbr = self.get_abbr('raw_type', raw_type)
            raw_species_abbr = self.get_abbr('raw_species', raw_species)
            
            # 组织来源取第一个值的缩写
            raw_tissue_first = raw_tissue.split(',')[0].strip() if raw_tissue else ''
            raw_tissue_abbr = self.get_abbr('raw_tissue', raw_tissue_first)
            
            # 构建属性字符串（用缩写，不是中文 label）
            if raw_tissue_abbr:
                return f"{raw_type_abbr}-{raw_species_abbr}-{raw_tissue_abbr}"
            else:
                return f"{raw_type_abbr}-{raw_species_abbr}"
        
        else:
            # 结果数据文件属性
            results_type = metadata.get('results_type', '') if metadata else ''
            results_raw = metadata.get('results_raw', '') if metadata else ''
            
            # 获取类型缩写（用 user input 值查询缩写表）
            results_type_abbr = self.get_abbr('results_type', results_type)
            
            # 解析和排序关联项目编号
            if results_raw:
                raw_ids = self._parse_and_sort(results_raw)
                return f"{results_type_abbr}-{raw_ids}"
            else:
                return results_type_abbr
    
    def merge_field_value(self, table_name: str, project_id: str, field_id: str, new_value: str) -> str:
        """合并字段值（读取数据库 → 合并 → 去重 → 排序 → 覆盖存储）
        
        处理流程：
        1. 读取数据库已有值
        2. 与前端传入值合并
        3. 去重
        4. 排序
        5. 覆盖存储
        
        示例：
        数据库: "Heart,Kidney" → 新值: "Liver,Kidney" → 结果: "Heart,Kidney,Liver"
        数据库: "Heart" → 新值: "Heart" → 结果: "Heart"（不重复）
        
        逗号处理规则：
        - 前端输入：识别中文逗号 `，` 和英文逗号 `,`
        - 数据存储：统一使用英文逗号 `,` 分隔
        - 处理时机：前端提交前将中文逗号替换为英文逗号（后端也做兼容处理）
        
        Args:
            table_name: 'raw_project' 或 'result_project'
            project_id: 项目编号（非自增ID）
            field_id: 字段名
            new_value: 新值
            
        Returns:
            追加后的字段值字符串
        """
        if not project_id or not field_id or not new_value:
            return new_value
        
        # 规范化分隔符：只处理新值，将各种分隔符统一为英文逗号
        def normalize_new_value(s):
            if not s or not isinstance(s, str):
                return s
            return s.replace('？', ',').replace('，', ',').replace('?', ',')
        
        # 检测数据库中当前使用的分隔符样式
        def detect_separator(s):
            if not s or not isinstance(s, str):
                return ','
            if '，' in s:
                return '，'
            if '？' in s or '?' in s:
                return '?'
            return ','
        
        # 分割值为列表
        def split_values(s, sep=','):
            if not s:
                return []
            return [v.strip() for v in s.split(sep) if v.strip()]
        
        new_value = normalize_new_value(new_value)
        
        # 根据表名确定ID字段
        id_field = 'raw_id' if table_name == 'raw_project' else 'results_id'
        
        # 1. 查询当前值（保留原始分隔符样式）
        row = self.db_manager.query_one(
            f"SELECT {field_id} FROM {table_name} WHERE {id_field} = %s",
            (project_id,)
        )
        
        if not row:
            return new_value
        
        current_value = row[0] if row[0] else ''
        current_separator = detect_separator(current_value)
        
        # 2. 合并并去重，然后排序
        if current_value:
            existing_ids = split_values(current_value, current_separator)
            # 分割新值（已规范化为英文逗号）
            new_ids = split_values(new_value, ',')
            # 合并
            all_ids = existing_ids + new_ids
            # 去重（保持顺序）
            unique_ids = list(dict.fromkeys(all_ids))
            # 排序（按ASCII编码排序：数字 < 大写 < 小写）
            sorted_ids = sorted(unique_ids, key=lambda x: x.encode('utf-8'))
            # 使用数据库中原有的分隔符样式
            new_value_str = current_separator.join(sorted_ids)
        else:
            # 无已有值，直接排序新值（按ASCII编码排序）
            new_ids = split_values(new_value, ',')
            sorted_ids = sorted(new_ids, key=lambda x: x.encode('utf-8'))
            new_value_str = ','.join(sorted_ids)
        
        # 3. 更新数据库
        self.db_manager.execute(
            f"UPDATE {table_name} SET {field_id} = %s WHERE {id_field} = %s",
            (new_value_str, project_id)
        )
        
        return new_value_str
    
    def get_all_processed_data(self) -> List[Dict]:
        """获取所有处理数据"""
        return self.get_files_by_project('result', '')
    
    # ==================== 目录扫描（保持原有功能）====================
    
    def scan_downloads(self) -> List[Dict]:
        """扫描下载目录"""
        download_dir = Path("/bio/downloads")
        projects = []
        
        if not download_dir.exists():
            return projects
        
        for item in download_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                project_info = self._parse_download_folder(item)
                if project_info:
                    projects.append(project_info)
        
        return projects
    
    def _parse_download_folder(self, folder: Path) -> Optional[Dict]:
        """解析下载文件夹信息"""
        name = folder.name
        
        # 检测DOI
        doi_match = re.search(r'10\.\d{4,}/[^\s]+', name)
        doi = doi_match.group(0) if doi_match else ""
        
        # 检测数据库编号
        db_id = ""
        db_link = ""
        for pattern, db_name, link_prefix in self.DB_PATTERNS:
            match = re.search(pattern, name)
            if match:
                db_id = match.group(0)
                db_link = f"{link_prefix}{db_id}"
                break
        
        # 检测数据类型
        data_type = ""
        for ext in self.FILE_TYPE_MAPPING.keys():
            if any(f.name.endswith(ext) for f in folder.iterdir() if f.is_file()):
                data_type = self.DATA_TYPE_MAPPING.get(ext, '其他')
                break
        
        # 获取文件列表
        files = []
        download_dir = Path("/bio/downloads")
        for f in folder.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                file_ext = f.suffix.lower()
                file_type = self.FILE_TYPE_MAPPING.get(file_ext, 'Other')
                # 计算相对于 /bio/downloads 的路径
                try:
                    if download_dir.exists():
                        relative_path = f.relative_to(download_dir)
                        relative_path_str = str(relative_path)
                    else:
                        # 如果 download_dir 不存在，使用文件夹名/文件名
                        relative_path_str = f"{folder.name}/{f.name}"
                except (ValueError, OSError):
                    relative_path_str = f"{folder.name}/{f.name}"
                files.append({
                    'name': f.name,
                    'size': f.stat().st_size,  # 返回原始字节数，由前端格式化
                    'type': file_type,
                    'relative_path': relative_path_str
                })
        
        return {
            'name': name,
            'doi': doi,
            'db_id': db_id,
            'db_link': db_link,
            'data_type': data_type,
            'file_count': len(files),
            'files': files,
            'path': str(folder)
        }
    
    def import_download_files(self, project_id: str, files: List, folder_name: str = None, metadata_override: Dict = None, data_type: str = 'raw', overwrite: bool = False) -> Dict:
        """导入下载文件到项目
        
        Args:
            project_id: 项目编号
            files: 文件列表
            folder_name: 源文件夹名
            metadata_override: 可选的字段值覆盖/追加（用于导入至已有项目时）
            data_type: 数据类型 ('raw' 或 'result')
            overwrite: 是否覆盖已存在的文件
        """
        if data_type == 'raw':
            return self._import_raw_files(project_id, files, folder_name, metadata_override, overwrite)
        else:
            return self._import_result_files(project_id, files, folder_name, metadata_override, overwrite)
    
    def _import_raw_files(self, project_id: str, files: List, folder_name: str = None, metadata_override: Dict = None, overwrite: bool = False) -> Dict:
        """导入原始数据文件到项目"""
        project = self.get_raw_project_by_id(project_id)
        if not project:
            return {'success': False, 'message': '项目不存在'}
        
        # 获取字段配置，确定必填字段
        raw_fields = self.config_manager.get_configs_by_table('raw') if self.config_manager else []
        required_fields = {f['field_id'] for f in raw_fields if f.get('field_necessary') == 1}
        
        # 项目级必填字段：这些字段在创建项目时设置，导入到已有项目时不需要在 metadata_override 中提供
        project_level_required_fields = {'raw_id', 'raw_title'}
        
        # 验证必填字段 - 导入至已有项目时：
        # 1. 跳过项目级必填字段（已在数据库中）
        # 2. 只验证用户实际提供的字段（metadata_override 中包含的字段）
        # 3. 对于用户未提供的字段，使用数据库中的现有值
        if metadata_override:
            for field_id, value in metadata_override.items():
                # 跳过项目级必填字段（不需要验证）
                if field_id in project_level_required_fields:
                    continue
                # 只验证必填字段
                if field_id in required_fields and not value:
                    return {'success': False, 'message': f'必填字段不能为空: {field_id}'}
        
        # 如果有 metadata_override 且包含有效值，先合并字段值到 raw_project 表
        if metadata_override:
            for field_id, value in metadata_override.items():
                if value:  # 只合并有值的字段
                    self.merge_field_value('raw_project', project_id, field_id, value)
        
        # 构建路径：只使用前端传入的 metadata，不从数据库查询
        # =================================================================
        # 设计规范：
        # - file_path 使用前端传入的 metadata_override 中的字段值
        # - 路径生成使用 get_abbr() 从 abbr_mapping 获取缩写
        # - 格式：/bio/rawdata/{数据类型缩写}/{物种缩写}/{组织来源缩写}/{项目ID}
        # - 如果前端没有传入某字段值，则使用空字符串
        # - 不查询数据库的现有值（这会导致路径与用户期望不一致）
        # =================================================================
        raw_type = (metadata_override or {}).get('raw_type', '')
        raw_species = (metadata_override or {}).get('raw_species', '')
        raw_tissue = (metadata_override or {}).get('raw_tissue', '')
        
        # 路径格式: {rawdata_dir}/{数据类型}/{物种}/{样本来源}/{项目ID}/
        project_path = self._build_raw_project_path(raw_type, raw_species, raw_tissue, project_id)

        # 获取源文件夹路径 - 拼接 /bio/downloads 前缀
        if folder_name:
            source_folder = self.downloads_dir / folder_name
            source_folder = Path(source_folder) if not isinstance(source_folder, Path) else source_folder
        else:
            source_folder = None
        
        import_count = 0
        duplicate_count = 0
        for file_info in files:
            # 支持文件名(字符串)或文件对象(带path)
            if isinstance(file_info, str):
                file_name = file_info
                file_path = source_folder / file_name if source_folder else None
            else:
                file_name = file_info.get('name', '')
                file_path = Path(file_info.get('path', '')) if file_info.get('path') else None
                if not file_path and source_folder:
                    file_path = source_folder / file_name
            
            if file_path and file_path.exists():
                dest_path = project_path / file_path.name
                
                # 先复制文件到目标路径（如果目标文件不存在）
                if not dest_path.exists():
                    try:
                        shutil.copy2(file_path, dest_path)
                    except Exception as e:
                        print(f"[ERROR] 复制文件失败: {e}")
                        continue
                
                # 再添加文件记录
                result = self.add_file_record('raw', project_id, dest_path, metadata=metadata_override, overwrite=overwrite)
                if result.get('is_duplicate'):
                    print(f"[INFO] 跳过重复文件: {file_name}")
                    duplicate_count += 1
                elif result.get('success'):
                    import_count += 1
                else:
                    print(f"[ERROR] 添加文件记录失败: {result.get('message')}")
        
        return {
            'success': True,
            'imported': import_count,
            'duplicate': duplicate_count,
            'project_id': project_id,
            'storage_path': str(project_path)
        }
    
    def _import_result_files(self, project_id: str, files: List, folder_name: str = None, metadata_override: Dict = None, overwrite: bool = False) -> Dict:
        """导入结果数据文件到项目"""
        project = self.get_result_project_by_id(project_id)
        if not project:
            return {'success': False, 'message': '结果项目不存在'}
        
        # 获取字段配置，确定必填字段
        result_fields = self.config_manager.get_configs_by_table('result') if self.config_manager else []
        required_fields = {f['field_id'] for f in result_fields if f.get('field_necessary') == 1}
        
        # 项目级必填字段：这些字段在创建项目时设置，导入到已有项目时不需要在 metadata_override 中提供
        project_level_required_fields = {'result_id', 'result_title'}
        
        # 验证必填字段 - 导入至已有项目时：
        # 1. 跳过项目级必填字段（已在数据库中）
        # 2. 只验证用户实际提供的字段（metadata_override 中包含的字段）
        # 3. 对于用户未提供的字段，使用数据库中的现有值
        if metadata_override:
            for field_id, value in metadata_override.items():
                # 跳过项目级必填字段（不需要验证）
                if field_id in project_level_required_fields:
                    continue
                # 只验证必填字段
                if field_id in required_fields and not value:
                    return {'success': False, 'message': f'必填字段不能为空: {field_id}'}
        
        # 如果有 metadata_override 且包含有效值，先合并字段值到 result_project 表
        if metadata_override:
            for field_id, value in metadata_override.items():
                if value:  # 只合并有值的字段
                    self.merge_field_value('result_project', project_id, field_id, value)
        
        # 构建路径：只使用前端传入的 metadata_override，绝不从数据库查询
        # =================================================================
        # 设计规范（7.5 文件导入完整逻辑）：
        # - file_path 使用前端传入的 metadata_override 中的字段值
        # - 路径生成使用 get_abbr() 从 abbr_mapping 获取缩写
        # - 格式：/bio/results/{项目ID}/{分析类型缩写}/{关联项目ID}
        # - 如果前端没有传入 results_type 或 results_raw，使用空字符串
        # - 绝不从数据库查询（这是与元数据合并 merge_field_value 的根本区别）
        # =================================================================
        results_type = (metadata_override or {}).get('results_type', '')
        results_raw = (metadata_override or {}).get('results_raw', '')
        
        # 注意：这里不查询数据库！
        # - 如果 metadata_override 为空，则 results_type='' 和 results_raw=''
        # - 路径会变成 /bio/results/{项目ID}/{结果类型缩写}/
        # - 这是符合设计规范的正确行为
        
        # 获取关联项目ID（用于路径生成和 file_project_ref_id）
        raw_project_ids = self._parse_and_sort(results_raw) if results_raw else ''
        
        # 获取结果类型的缩写
        results_type_abbr = self.get_abbr('results_type', results_type) if results_type else ''
        
        # 构建路径: {results_dir}/{项目ID}/{分析类型缩写}/{关联项目ID}/
        if raw_project_ids:
            project_path = self.results_dir / project_id / results_type_abbr / raw_project_ids
        else:
            project_path = self.results_dir / project_id / results_type_abbr
        project_path.mkdir(parents=True, exist_ok=True)

        # 获取源文件夹路径 - 拼接 /bio/downloads 前缀
        if folder_name:
            source_folder = self.downloads_dir / folder_name
            source_folder = Path(source_folder) if not isinstance(source_folder, Path) else source_folder
        else:
            source_folder = None
        
        import_count = 0
        duplicate_count = 0
        for file_info in files:
            # 支持文件名(字符串)或文件对象(带path)
            if isinstance(file_info, str):
                file_name = file_info
                file_path = source_folder / file_name if source_folder else None
            else:
                file_name = file_info.get('name', '')
                file_path = Path(file_info.get('path', '')) if file_info.get('path') else None
                if not file_path and source_folder:
                    file_path = source_folder / file_name
            
            if file_path and file_path.exists():
                dest_path = project_path / file_path.name
                
                # 传递 ref_project_id（results_raw 字段值）
                ref_project_id = raw_project_ids if raw_project_ids else None
                
                # 先复制文件到目标路径（如果目标文件不存在）
                if not dest_path.exists():
                    try:
                        shutil.copy2(file_path, dest_path)
                    except Exception as e:
                        print(f"[ERROR] 复制文件失败: {e}")
                        continue
                
                # 再添加文件记录
                result = self.add_file_record('result', project_id, dest_path, metadata=metadata_override, ref_project_id=ref_project_id, overwrite=overwrite)
                if result.get('is_duplicate'):
                    print(f"[INFO] 跳过重复文件: {file_name}")
                    duplicate_count += 1
                elif result.get('success'):
                    import_count += 1
                else:
                    print(f"[ERROR] 添加文件记录失败: {result.get('message')}")
        
        return {
            'success': True,
            'imported': import_count,
            'duplicate': duplicate_count,
            'project_id': project_id,
            'storage_path': str(project_path)
        }
    
    def organize_project_files(self, project_id: str) -> Dict:
        """整理项目文件"""
        project = self.get_raw_project_by_id(project_id)
        if not project:
            return {'success': False, 'message': '项目不存在'}
        
        project_path = self._build_raw_project_path(
            project.get('raw_type', ''),
            project.get('raw_species', ''),
            project.get('raw_tissue', ''),
            project_id
        )
        
        if not project_path.exists():
            return {'success': False, 'message': '项目目录不存在'}
        
        organized = {'files': [], 'folders': []}
        
        for file_path in project_path.iterdir():
            if file_path.is_file():
                file_ext = file_path.suffix.lower()
                file_type = self._get_file_type(file_path.name)
                
                target_folder = project_path / file_type
                target_folder.mkdir(exist_ok=True)
                
                new_path = target_folder / file_path.name
                file_path.rename(new_path)
                
                organized['files'].append({
                    'name': file_path.name,
                    'type': file_type,
                    'folder': file_type
                })
        
        return {'success': True, 'organized': organized}
    
    def get_directory_tree(self, root_path: str) -> Dict:
        """获取目录树"""
        root = Path(root_path)
        if not root.exists():
            return {'name': root.name, 'type': 'folder', 'children': []}
        
        def build_tree(path: Path) -> Dict:
            item = {
                'name': path.name,
                'type': 'folder' if path.is_dir() else 'file'
            }
            
            if path.is_dir():
                try:
                    children = []
                    for child in path.iterdir():
                        if not child.name.startswith('.'):
                            children.append(build_tree(child))
                    item['children'] = sorted(children, key=lambda x: (x['type'] != 'folder', x['name']))
                except PermissionError:
                    item['children'] = []
            
            if path.is_file():
                item['size'] = self._format_size(path.stat().st_size)
            
            return item
        
        return build_tree(root)
    
    def import_processed_file(self, project_id: str, file_path: str, metadata_override: Dict = None) -> Dict:
        """导入处理文件
        
        Args:
            project_id: 项目编号
            file_path: 文件路径
            metadata_override: 可选的字段值覆盖/追加（用于导入至已有项目时）
        """
        path = Path(file_path)
        if not path.exists():
            return {'success': False, 'message': '文件不存在'}
        
        # 如果有 metadata_override，先合并字段值到 result_project 表
        if metadata_override:
            for field_id, value in metadata_override.items():
                if value:
                    self.merge_field_value('result_project', project_id, field_id, value)
        
        # 只使用前端传入的值构建路径，不fallback到数据库
        results_type = metadata_override.get('results_type', '') if metadata_override else ''
        raw_project_id = metadata_override.get('results_raw', '') if metadata_override else ''
        
        results_type_abbr = self.get_abbr('results_type', results_type) if results_type else ''
        
        # 构建路径: {results_dir}/{项目ID}/{分析类型}/{关联项目ID}/
        if raw_project_id:
            project_path = self.results_dir / project_id / results_type_abbr / raw_project_id
        else:
            project_path = self.results_dir / project_id / results_type_abbr
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 复制文件到新路径
        dest_path = project_path / path.name
        shutil.copy2(path, dest_path)
        
        # 记录文件（传递 metadata_override 用于生成 file_property）
        self.add_file_record('result', project_id, dest_path, metadata=metadata_override)
        
        return {
            'success': True,
            'file': path.name,
            'project_id': project_id,
            'storage_path': str(project_path)
        }