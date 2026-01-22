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
        """
        if not full_name:
            return 'UNK'
        
        try:
            # 尝试从缩写映射表获取
            abbr = self.config_manager.get_abbr_mapping(field_id, full_name)
            if abbr:
                return abbr
        except Exception:
            # 如果表不存在或查询失败，使用默认逻辑
            pass
        
        # 默认：取前3个字符（保留英文和数字）
        abbr = ''.join(c for c in full_name[:3] if c.isalnum())
        if len(abbr) < 3:
            abbr = abbr.ljust(3, '_')
        # 如果还是空（纯中文），取前3个字符
        if not abbr:
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
        raw_type = data.get('raw_type', '')
        species = data.get('raw_species', '')
        raw_tissue = data.get('raw_tissue', '')
        
        # 处理多选字段
        if isinstance(raw_tissue, list):
            raw_tissue = ','.join([t.strip() for t in raw_tissue if t.strip()])
        
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
            (data.get('raw_keywords', '') or '').replace('，', ','),
        ))
        
        return self.get_raw_project_by_id(raw_id)
    
    def get_all_raw_projects(self) -> List[Dict]:
        """获取所有原始数据项目"""
        projects = self.db_manager.query("""
            SELECT * FROM raw_project ORDER BY created_at DESC
        """)
        
        result = []
        for row in projects:
            project = {
                'id': row[0],
                'raw_id': row[1],
                'raw_title': row[2],
                'raw_type': row[3],
                'raw_species': row[4],
                'raw_tissue': row[5],
                'raw_DOI': row[6],
                'raw_db_id': row[7],
                'raw_db_link': row[8],
                'raw_author': row[9],
                'raw_article': row[10],
                'raw_description': row[11],
                'raw_keywords': row[12],
                'raw_file_count': row[13],
                'raw_total_size': row[14],
                'created_at': row[15],
                'updated_at': row[16]
            }
            result.append(project)
        
        return result
    
    def get_raw_project_by_id(self, raw_id: str) -> Optional[Dict]:
        """根据ID获取原始数据项目"""
        row = self.db_manager.query_one(
            "SELECT * FROM raw_project WHERE raw_id = %s",
            (raw_id,)
        )

        if row:
            # 获取项目文件列表
            files = self.db_manager.query("""
                SELECT id, file_name, file_path, file_size, imported_at
                FROM file_record
                WHERE file_project_type = 'raw' AND file_project_id = %s
            """, (raw_id,))

            file_list = []
            for f in files:
                file_list.append({
                    'id': f[0],
                    'file_name': f[1],
                    'file_path': f[2],
                    'file_size': f[3],
                    'imported_at': f[4].strftime('%Y-%m-%d %H:%M:%S') if f[4] else None
                })

            return {
                'id': row[0],
                'raw_id': row[1],
                'raw_title': row[2],
                'raw_type': row[3],
                'raw_species': row[4],
                'raw_tissue': row[5],
                'raw_DOI': row[6],
                'raw_db_id': row[7],
                'raw_db_link': row[8],
                'raw_author': row[9],
                'raw_article': row[10],
                'raw_description': row[11],
                'raw_keywords': row[12],
                'raw_file_count': row[13],
                'raw_total_size': row[14],
                'created_at': row[15],
                'updated_at': row[16],
                'files': file_list
            }
        return None
    
    def update_raw_project(self, data: Dict) -> bool:
        """更新原始数据项目"""
        raw_id = data.get('raw_id')
        if not raw_id:
            return False
        
        # 处理多选字段
        raw_tissue = data.get('raw_tissue', '')
        if isinstance(raw_tissue, list):
            raw_tissue = ','.join([t.strip() for t in raw_tissue if t.strip()])
        
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
            (data.get('raw_keywords', '') or '').replace('，', ','),
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
        
        results_type = data.get('results_type', '')
        raw_project_id = data.get('results_raw', '')
        
        # 解析和排序关联项目编号（用于路径）
        sorted_raw_ids = self._parse_and_sort_project_ids(raw_project_id) if raw_project_id else ''
        
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
            raw_project_id,  # 存储原始值（逗号分隔）
            data.get('results_description', ''),
            (data.get('keywords', '') or data.get('results_keywords', '') or '').replace('，', ','),
        ))
        
        return self.get_result_project_by_id(results_id)
    
    def get_all_result_projects(self) -> List[Dict]:
        """获取所有结果数据项目"""
        projects = self.db_manager.query("""
            SELECT * FROM result_project ORDER BY created_at DESC
        """)
        
        result = []
        for row in projects:
            project = {
                'id': row[0],
                'results_id': row[1],
                'results_title': row[2],
                'results_type': row[3],
                'results_raw': row[4],
                'results_description': row[5],
                'results_keywords': row[6],
                'results_file_count': row[7],
                'results_total_size': row[8],
                'created_at': row[9],
                'updated_at': row[10]
            }
            result.append(project)
        
        return result
    
    def get_result_project_by_id(self, results_id: str) -> Optional[Dict]:
        """根据ID获取结果数据项目"""
        row = self.db_manager.query_one(
            "SELECT * FROM result_project WHERE results_id = %s",
            (results_id,)
        )

        if row:
            # 获取项目文件列表
            files = self.db_manager.query("""
                SELECT id, file_name, file_path, file_size, imported_at
                FROM file_record
                WHERE file_project_type = 'result' AND file_project_id = %s
            """, (results_id,))

            file_list = []
            for f in files:
                file_list.append({
                    'id': f[0],
                    'file_name': f[1],
                    'file_path': f[2],
                    'file_size': f[3],
                    'imported_at': f[4].strftime('%Y-%m-%d %H:%M:%S') if f[4] else None
                })

            return {
                'id': row[0],
                'results_id': row[1],
                'results_title': row[2],
                'results_type': row[3],
                'results_raw': row[4],
                'results_description': row[5],
                'results_keywords': row[6],
                'results_file_count': row[7],
                'results_total_size': row[8],
                'created_at': row[9],
                'updated_at': row[10],
                'files': file_list
            }
        return None
    
    def update_result_project(self, data: Dict) -> bool:
        """更新结果数据项目"""
        results_id = data.get('results_id')
        if not results_id:
            return False
        
        self.db_manager.execute("""
            UPDATE result_project 
            SET results_title = %s, results_type = %s, results_raw = %s,
                results_description = %s, results_keywords = %s
            WHERE results_id = %s
        """, (
            data.get('results_title', ''),
            data.get('results_type', ''),
            data.get('results_raw', ''),
            data.get('results_description', ''),
            (data.get('results_keywords', '') or '').replace('，', ','),
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
            result.append({
                'id': row[0],
                'file_name': row[1],
                'file_path': row[2],
                'file_size': row[3],
                'file_type': row[4],
                'file_project_type': row[5],
                'file_project_id': row[6],
                'imported_at': row[7]
            })
        return result
    
    def add_file_record(self, project_type: str, project_id: str, file_path: Path, metadata: Dict = None) -> bool:
        """添加文件记录
        
        Args:
            project_type: 'raw' 或 'result'
            project_id: 项目编号
            file_path: 文件的完整路径
            metadata: 可选的元数据字典（如果已传入则使用，否则从数据库查询）
        """
        try:
            # file_name: 只包含文件名（不含路径）
            file_name = file_path.name
            
            # file_path: 相对于 /bio 的路径（不包含文件名）
            try:
                dir_path = file_path.parent.relative_to(Path('/bio'))
            except ValueError:
                dir_path = file_path.parent
            
            # 生成 file_property
            project_metadata = metadata.copy() if metadata else {}
            
            # 如果没有传入 metadata，从数据库查询
            if not metadata:
                if project_type == 'raw':
                    row = self.db_manager.query_one(
                        "SELECT raw_type, raw_species, raw_tissue FROM raw_project WHERE raw_id = %s",
                        (project_id,)
                    )
                    if row:
                        project_metadata = {
                            'raw_type': row[0] or '',
                            'raw_species': row[1] or '',
                            'raw_tissue': row[2] or ''
                        }
                else:
                    row = self.db_manager.query_one(
                        "SELECT results_type, results_raw FROM result_project WHERE results_id = %s",
                        (project_id,)
                    )
                    if row:
                        project_metadata = {
                            'results_type': row[0] or '',
                            'results_raw': row[1] or ''
                        }
            
            file_property = self._build_file_property(project_type, project_id, project_metadata)
            
            self.db_manager.execute("""
                INSERT INTO file_record 
                (file_name, file_path, file_property, file_size, file_type, file_project_type, file_project_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                file_name,
                str(dir_path),
                file_property,
                file_path.stat().st_size,
                self._get_file_type(file_name),
                project_type,
                project_id
            ))
            
            # 更新项目文件计数和总大小
            if project_type == 'raw':
                self._update_raw_file_count(project_id)
            elif project_type == 'result':
                self._update_result_file_count(project_id)
            
            return True
        except Exception as e:
            print(f"添加文件记录失败: {e}")
            return False
    
    def delete_file_record(self, file_id: int) -> bool:
        """删除文件记录"""
        try:
            file_record = self.db_manager.query_one(
                "SELECT * FROM file_record WHERE id = %s",
                (file_id,)
            )
            if not file_record:
                return False
            
            project_type = file_record[5]
            project_id = file_record[6]
            
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
    
    def _parse_and_sort_project_ids(self, raw_ids: str) -> str:
        """解析逗号分隔的项目ID，按字母排序后组合
        
        支持中英文逗号分隔
        示例: "RAW_A1，RAW_2A, RAW_sa" → 排序后: "RAW_2ARAW_A1RAW_sa"
        
        Args:
            raw_ids: 逗号分隔的项目ID字符串
            
        Returns:
            排序后组合的项目ID字符串
        """
        if not raw_ids or not raw_ids.strip():
            return ''
        
        # 解析：替换中文逗号为英文逗号，分割，去空值
        ids = raw_ids.replace('，', ',').split(',')
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
    
    def _build_file_property(self, project_type: str, project_id: str, metadata: Dict = None) -> str:
        """生成文件属性字符串
        
        生成规则：
        - 原始数据 (raw): {数据类型label}-{物种label}-[{组织来源label}]
        - 结果数据 (result): {结果类型label}-[{关联项目编号（排序后组合）}]
        
        Args:
            project_type: 'raw' 或 'result'
            project_id: 项目编号
            metadata: 可选的元数据字典（如果已传入则使用，否则从数据库查询）
            
        Returns:
            文件属性字符串
        """
        if project_type == 'raw':
            # 原始数据文件属性
            raw_type = metadata.get('raw_type', '') if metadata else ''
            raw_species = metadata.get('raw_species', '') if metadata else ''
            raw_tissue = metadata.get('raw_tissue', '') if metadata else ''
            
            # 获取 label（使用第一个值，因为组织来源可能是逗号分隔的多值）
            raw_type_label = self._get_option_label('raw_type', raw_type)
            raw_species_label = self._get_option_label('raw_species', raw_species)
            
            # 组织来源取第一个值的 label
            raw_tissue_first = raw_tissue.split(',')[0].strip() if raw_tissue else ''
            raw_tissue_label = self._get_option_label('raw_tissue', raw_tissue_first)
            
            # 构建属性字符串
            if raw_tissue_label:
                return f"{raw_type_label}-{raw_species_label}-{raw_tissue_label}"
            else:
                return f"{raw_type_label}-{raw_species_label}"
        
        else:
            # 结果数据文件属性
            results_type = metadata.get('results_type', '') if metadata else ''
            results_raw = metadata.get('results_raw', '') if metadata else ''
            
            # 获取类型 label
            results_type_label = self._get_option_label('results_type', results_type)
            
            # 解析和排序关联项目编号
            if results_raw:
                raw_ids = self._parse_and_sort_project_ids(results_raw)
                return f"{results_type_label}-{raw_ids}"
            else:
                return results_type_label
    
    def append_field_value(self, table_name: str, project_id: str, field_id: str, new_value: str) -> str:
        """追加字段值（去重）
        
        当前值: "Lung" → 新值: "Liver" → 结果: "Lung,Liver"
        当前值: "Lung" → 新值: "Lung" → 结果: "Lung"（不重复）
        
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
        
        # 根据表名确定ID字段
        id_field = 'raw_id' if table_name == 'raw_project' else 'results_id'
        
        # 1. 查询当前值
        row = self.db_manager.query_one(
            f"SELECT {field_id} FROM {table_name} WHERE {id_field} = %s",
            (project_id,)
        )
        
        if not row:
            return new_value
        
        current_value = row[0] if row[0] else ''
        print(f"[DEBUG] append_field_value: {table_name}.{field_id} for {project_id}")
        print(f"[DEBUG]   current_value: '{current_value}'")
        print(f"[DEBUG]   new_value: '{new_value}'")
        
        # 2. 追加新值（去重）
        if current_value:
            existing_ids = current_value.split(',')
            # 对于 results_raw 字段，需要去重但保持逗号分隔格式
            if field_id == 'results_raw':
                all_ids = [i.strip() for i in existing_ids + [new_value] if i.strip()]
                unique_ids = list(dict.fromkeys(all_ids))  # 保持顺序去重
                new_value_str = ','.join(unique_ids)
            else:
                values = list(set(existing_ids + [new_value]))
                values = [v for v in values if v]  # 去除空字符串
                new_value_str = ','.join(values)
        else:
            new_value_str = new_value
        
        print(f"[DEBUG]   result: '{new_value_str}'")
        
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
    
    def import_download_files(self, project_id: str, files: List, folder_name: str = None, metadata_override: Dict = None, data_type: str = 'raw') -> Dict:
        """导入下载文件到项目
        
        Args:
            project_id: 项目编号
            files: 文件列表
            folder_name: 源文件夹名
            metadata_override: 可选的字段值覆盖/追加（用于导入至已有项目时）
            data_type: 数据类型 ('raw' 或 'result')
        """
        if data_type == 'raw':
            return self._import_raw_files(project_id, files, folder_name, metadata_override)
        else:
            return self._import_result_files(project_id, files, folder_name, metadata_override)
    
    def _import_raw_files(self, project_id: str, files: List, folder_name: str = None, metadata_override: Dict = None) -> Dict:
        """导入原始数据文件到项目"""
        project = self.get_raw_project_by_id(project_id)
        if not project:
            return {'success': False, 'message': '项目不存在'}
        
        # 如果有 metadata_override，先追加字段值到 raw_project 表
        if metadata_override:
            for field_id, value in metadata_override.items():
                if value:
                    self.append_field_value('raw_project', project_id, field_id, value)
        
        # 只使用前端传入的值构建路径
        raw_type = metadata_override.get('raw_type', '') if metadata_override else ''
        raw_species = metadata_override.get('raw_species', '') if metadata_override else ''
        raw_tissue = metadata_override.get('raw_tissue', '') if metadata_override else ''
        
        # 路径格式: {rawdata_dir}/{项目ID}/{raw_type}/{raw_species}/{raw_tissue}/
        project_path = self._build_raw_project_path(raw_type, raw_species, raw_tissue, project_id)

        # 获取源文件夹路径 - 拼接 /bio/downloads 前缀
        if folder_name:
            source_folder = self.downloads_dir / folder_name
            source_folder = Path(source_folder) if not isinstance(source_folder, Path) else source_folder
        else:
            source_folder = None
        
        import_count = 0
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
                shutil.copy2(file_path, dest_path)
                self.add_file_record('raw', project_id, dest_path)
                import_count += 1
        
        return {
            'success': True,
            'imported': import_count,
            'project_id': project_id,
            'storage_path': str(project_path)
        }
    
    def _import_result_files(self, project_id: str, files: List, folder_name: str = None, metadata_override: Dict = None) -> Dict:
        """导入结果数据文件到项目"""
        project = self.get_result_project_by_id(project_id)
        if not project:
            return {'success': False, 'message': '结果项目不存在'}
        
        print(f"[DEBUG] _import_result_files: project_id={project_id}")
        print(f"[DEBUG] _import_result_files: metadata_override={metadata_override}")
        print(f"[DEBUG] _import_result_files: current project results_raw={project.get('results_raw', '')}")
        
        # 如果有 metadata_override，先追加字段值到 result_project 表
        if metadata_override:
            for field_id, value in metadata_override.items():
                if value:
                    print(f"[DEBUG] append_field_value: {field_id} = {value}")
                    self.append_field_value('result_project', project_id, field_id, value)
        
        # 只使用前端传入的值构建路径
        results_type = metadata_override.get('results_type', '') if metadata_override else ''
        raw_project_ids = ''
        
        if metadata_override and metadata_override.get('results_raw'):
            raw_project_ids = self._parse_and_sort_project_ids(metadata_override['results_raw'])
            print(f"[DEBUG] path will use raw_project_ids: {raw_project_ids}")
        
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
                shutil.copy2(file_path, dest_path)
                self.add_file_record('result', project_id, dest_path)
                import_count += 1
        
        return {
            'success': True,
            'imported': import_count,
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
        
        # 如果有 metadata_override，先追加字段值到 result_project 表
        if metadata_override:
            for field_id, value in metadata_override.items():
                if value:
                    self.append_field_value('result_project', project_id, field_id, value)
        
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
        
        # 记录文件
        self.add_file_record('result', project_id, dest_path)
        
        return {
            'success': True,
            'file': path.name,
            'project_id': project_id,
            'storage_path': str(project_path)
        }