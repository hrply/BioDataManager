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
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from database_mysql import DatabaseManager
from metadata_config_manager_mysql import MetadataConfigManager
from field_names import *


class BioDataManager:
    """生物数据管理器"""
    
    # 数据类型映射
    DATA_TYPE_MAPPING = {
        'fastq': 'rnaseq',
        'sam': 'rnaseq',
        'bam': 'rnaseq',
        'h5ad': 'singlecell',
        'mtx': 'singlecell',
        'raw': 'proteomics',
        'mzml': 'proteomics',
        'wiff': 'proteomics',
        'fcs': 'mass_cytometry',
        'csv': 'other',
        'tsv': 'other',
        'txt': 'other',
        'h5': 'other',
    }
    
    # 文件类型映射
    FILE_TYPE_MAPPING = {
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
        '.jpeg': 'Image',
        '.zip': 'Archive',
        '.gz': 'Compressed Data',
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
    
    # 物种名称映射
    SPECIES_NAMES = {
        'Homo sapiens': '人类',
        'Mus musculus': '小鼠',
        'Rattus norvegicus': '大鼠',
        'Danio rerio': '斑马鱼',
        'Drosophila melanogaster': '果蝇',
        'Caenorhabditis elegans': '秀丽隐杆线虫',
        'Arabidopsis thaliana': '拟南芥',
        'Saccharomyces cerevisiae': '酿酒酵母',
        'Escherichia coli': '大肠杆菌',
        'Bacillus subtilis': '枯草芽孢杆菌',
        'Sus scrofa': '猪',
        'Gallus gallus': '鸡',
        'Macaca mulatta': '恒河猴',
    }
    
    def __init__(self, db_manager: DatabaseManager, config_manager: MetadataConfigManager):
        self.db_manager = db_manager
        self.config_manager = config_manager
        
        # 路径配置（数据库设计规范要求）
        self.data_dir = Path("/bioraw/data")
        self.downloads_dir = Path("/bioraw/downloads")
        self.results_dir = Path("/bioraw/results")
        
        # 基础数据目录
        self.base_data_dir = Path("/ssd/bioraw/raw_data")
        
        # 初始化序列
        self._init_sequences()
    
    def _init_sequences(self):
        """初始化ID序列"""
        self.db_manager.execute("""
            CREATE TABLE IF NOT EXISTS project_id_sequence (
                id VARCHAR(50) PRIMARY KEY,
                counter INT DEFAULT 0
            )
        """)
        self.db_manager.execute("""
            CREATE TABLE IF NOT EXISTS bioresult_id_sequence (
                id VARCHAR(50) PRIMARY KEY,
                counter INT DEFAULT 0
            )
        """)
    
    def get_next_project_id(self) -> str:
        """获取下一个项目ID"""
        try:
            result = self.db_manager.query_one("SELECT counter FROM project_id_sequence WHERE id = 'project'")
            if result:
                counter = result[0] + 1
                self.db_manager.execute("UPDATE project_id_sequence SET counter = %s WHERE id = 'project'", (counter,))
            else:
                counter = 1
                self.db_manager.execute("INSERT INTO project_id_sequence (id, counter) VALUES ('project', %s)", (counter,))
            return f"PRJ-{str(counter).zfill(3)}"
        except Exception:
            return f"PRJ-{datetime.now().strftime('%H%M')}"
    
    def get_next_bioresult_id(self) -> str:
        """获取下一个生物结果项目ID"""
        try:
            result = self.db_manager.query_one("SELECT counter FROM bioresult_id_sequence WHERE id = 'bioresult'")
            if result:
                counter = result[0] + 1
                self.db_manager.execute("UPDATE bioresult_id_sequence SET counter = %s WHERE id = 'bioresult'", (counter,))
            else:
                counter = 1
                self.db_manager.execute("INSERT INTO bioresult_id_sequence (id, counter) VALUES ('bioresult', %s)", (counter,))
            return f"PRD-{str(counter).zfill(3)}"
        except Exception:
            return f"PRD-{datetime.now().strftime('%H%M')}"
    
    def create_project(self, data: Dict) -> Dict:
        """创建新项目"""
        project_id = self.get_next_project_id()
        
        # 构建项目路径
        project_path = self.base_data_dir / f"{project_id}_{data.get('title', 'Untitled')}"
        
        # 处理多选字段
        organism = data.get('organism', '')
        if isinstance(organism, list):
            organism = ', '.join(organism)
        
        data_types = data.get('data_type', '')
        if isinstance(data_types, list):
            data_types = ', '.join(data_types)
        
        tags = data.get('tags', [])
        if isinstance(tags, list):
            tags = json.dumps(tags, ensure_ascii=False)
        
        created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建SQL插入语句
        columns = ['id', 'title', 'created_date', 'path']
        values = [project_id, data.get('title', ''), created_date, str(project_path)]
        
        # 添加元数据字段
        config = self.config_manager.get_all_configs()
        for field in config:
            field_name = field['field_name']
            if field_name in data and field_name not in ['data_type', 'organism']:
                if field['field_type'] in ['multi_select', 'select']:
                    value = data[field_name]
                    if isinstance(value, list):
                        value = ', '.join(value)
                else:
                    value = data.get(field_name, '')
                columns.append(field_name)
                values.append(value)
        
        # 添加必需字段
        columns.extend(['doi', 'db_id', 'data_type', 'organism', 'tags'])
        values.extend([
            data.get('doi', ''),
            data.get('db_id', ''),
            data_types,
            organism,
            tags
        ])
        
        placeholders = ['%s'] * len(values)
        
        sql = f"INSERT INTO projects ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        self.db_manager.execute(sql, values)
        
        # 创建项目目录
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 生成README文档
        self._generate_project_readme(project_id, data)
        
        # 获取完整项目信息
        return self.get_project_by_id(project_id)
    
    def _generate_project_readme(self, project_id: str, data: Dict):
        """生成项目README文档"""
        project_path = self.base_data_dir / f"{project_id}_{data.get('title', 'Untitled')}"
        readme_path = project_path / "README.md"
        
        # 获取项目信息用于README
        project = self.get_project_by_id(project_id)
        if not project:
            return
        
        # 构建文件列表
        file_list = ""
        if project_path.exists():
            for f in project_path.iterdir():
                if f.is_file() and f.name != "README.md":
                    size = self._format_size(f.stat().st_size)
                    file_list += f"- `{f.name}` ({size})\n"
        
        readme_content = f"""# {project.get('title', 'Untitled')}

**项目ID**: {project_id}
**创建日期**: {project.get('created_date', '')}

## 基本信息

- **数据类型**: {project.get('data_type', 'N/A')}
- **物种**: {project.get('organism', 'N/A')}
- **DOI**: {project.get('doi', 'N/A')}
- **数据库编号**: {project.get('db_id', 'N/A')}

## 项目描述

{project.get('description', '暂无描述')}

## 文件列表

{file_list if file_list else '暂无文件'}

---
*此文档由 BioData Manager 自动生成*
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def get_all_projects(self) -> List[Dict]:
        """获取所有项目"""
        try:
            config = self.config_manager.get_all_configs()
            field_names = ['id', 'title', 'created_date'] + [c['field_name'] for c in config]
            
            projects = self.db_manager.query("""
                SELECT * FROM projects ORDER BY created_date DESC
            """)
            
            result = []
            for row in projects:
                project = dict(zip(field_names, row))
                project['path'] = str(self.base_data_dir / f"{project['id']}_{project['title']}")
                
                # 兼容性字段名
                project['raw_id'] = project['id']
                
                # 格式化显示
                project['data_type_label'] = self.get_data_type_label(project.get('data_type', ''))
                project['organism_label'] = self.get_organism_label(project.get('organism', ''))
                
                # 获取文件计数
                project['file_count'] = self._get_file_count(project['id'])
                
                result.append(project)
            
            return result
        except Exception as e:
            print(f"获取项目列表失败: {e}")
            return []
    
    def _get_file_count(self, project_id: str) -> int:
        """获取项目文件数量"""
        try:
            result = self.db_manager.query_one(
                "SELECT COUNT(*) FROM files WHERE project_id = %s",
                (project_id,)
            )
            return result[0] if result else 0
        except Exception:
            return 0
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """根据ID获取项目"""
        try:
            config = self.config_manager.get_all_configs()
            field_names = ['id', 'title', 'created_date'] + [c['field_name'] for c in config]
            
            row = self.db_manager.query_one(
                f"SELECT {', '.join(field_names)} FROM projects WHERE id = %s",
                (project_id,)
            )
            
            if row:
                project = dict(zip(field_names, row))
                project['path'] = str(self.base_data_dir / f"{project['id']}_{project['title']}")
                project['data_type_label'] = self.get_data_type_label(project.get('data_type', ''))
                project['organism_label'] = self.get_organism_label(project.get('organism', ''))
                
                # 解析标签
                try:
                    project['tags'] = json.loads(project.get('tags', '[]'))
                except (json.JSONDecodeError, TypeError):
                    project['tags'] = []
                
                # 获取文件列表
                project['files'] = self._get_project_files(project_id)
                
                return project
            return None
        except Exception as e:
            print(f"获取项目失败: {e}")
            return None
    
    def _get_project_files(self, project_id: str) -> List[Dict]:
        """获取项目文件列表"""
        try:
            files = self.db_manager.query(
                "SELECT * FROM files WHERE project_id = %s ORDER BY file_name",
                (project_id,)
            )
            return [dict(zip(['id', 'project_id', 'file_name', 'file_path', 'file_type', 'file_size', 'created_at'], f)) for f in files]
        except Exception:
            return []
    
    def update_project(self, data: Dict) -> bool:
        """更新项目"""
        project_id = data.get('id')
        if not project_id:
            return False
        
        updates = []
        values = []
        
        # 动态构建更新语句
        config = self.config_manager.get_all_configs()
        allowed_fields = ['title', 'description'] + [c['field_name'] for c in config]
        
        for field in allowed_fields:
            if field in data:
                value = data[field]
                if isinstance(value, list):
                    value = ', '.join(value)
                updates.append(f"{field} = %s")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(project_id)
        
        sql = f"UPDATE projects SET {', '.join(updates)} WHERE id = %s"
        self.db_manager.execute(sql, values)
        
        # 更新README
        project = self.get_project_by_id(project_id)
        if project:
            self._generate_project_readme(project_id, project)
        
        return True
    
    def delete_bioresult_project(self, project_id: str) -> bool:
        """删除结果项目"""
        try:
            # 获取项目信息
            project = self.get_bioresult_project_by_id(project_id)
            if not project:
                return False
            
            # 删除数据库记录
            self.db_manager.execute("DELETE FROM processed_files WHERE project_id = %s", (project_id,))
            self.db_manager.execute("DELETE FROM bioresult_projects WHERE id = %s", (project_id,))
            
            # 删除项目目录
            project_path = Path(self.results_dir) / f"{project_id}_{project.get('title', '')}"
            if project_path.exists():
                shutil.rmtree(project_path)
            
            return True
        except Exception as e:
            print(f"删除结果项目失败: {e}")
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        try:
            # 获取项目信息
            project = self.get_project_by_id(project_id)
            if not project:
                return False
            
            # 删除数据库记录
            self.db_manager.execute("DELETE FROM files WHERE project_id = %s", (project_id,))
            self.db_manager.execute("DELETE FROM projects WHERE id = %s", (project_id,))
            
            # 删除项目目录
            project_path = self.base_data_dir / f"{project_id}_{project.get('title', '')}"
            if project_path.exists():
                shutil.rmtree(project_path)
            
            return True
        except Exception as e:
            print(f"删除项目失败: {e}")
            return False
    
    def get_data_type_label(self, data_type: str) -> str:
        """获取数据类型标签"""
        if not data_type:
            return "未分类"
        
        # 处理逗号分隔的多值，直接返回原始值（避免导入不存在的常量）
        types = [t.strip() for t in data_type.split(',')]
        return ', '.join(types) if types else "未分类"
    
    def get_organism_label(self, organism: str) -> str:
        """获取物种显示标签"""
        if not organism:
            return "未指定"
        
        # 处理逗号分隔的多值
        organisms = [o.strip() for o in organism.split(',')]
        labels = []
        
        for o in organisms:
            label = self.SPECIES_NAMES.get(o, o)
            labels.append(label)
        
        return ', '.join(labels) if labels else "未指定"
    
    def scan_downloads(self) -> List[Dict]:
        """扫描下载目录"""
        projects = []
        
        if not self.downloads_dir.exists():
            return projects
        
        for item in self.downloads_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 尝试从目录名解析信息
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
        for ext, dtype in self.FILE_TYPE_MAPPING.items():
            if any(f.name.endswith(ext) for f in folder.iterdir() if f.is_file()):
                data_type = self.DATA_TYPE_MAPPING.get(ext, 'other')
                break
        
        # 获取文件列表
        files = []
        for f in folder.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                file_ext = f.suffix.lower()
                file_type = self.FILE_TYPE_MAPPING.get(file_ext, 'Other')
                files.append({
                    'name': f.name,
                    'size': self._format_size(f.stat().st_size),
                    'type': file_type
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
    
    def import_download_files(self, project_id: str, files: List[str]) -> Dict:
        """导入下载文件到项目"""
        project = self.get_project_by_id(project_id)
        if not project:
            return {'success': False, 'message': '项目不存在'}
        
        project_path = self.base_data_dir / f"{project_id}_{project.get('title', '')}"
        import_count = 0
        
        for file_info in files:
            file_path = Path(file_info.get('path', ''))
            if file_path.exists():
                dest_path = project_path / file_path.name
                shutil.copy2(file_path, dest_path)
                import_count += 1
                
                # 记录到数据库
                self._add_file_record(project_id, dest_path)
        
        # 更新README
        self._generate_project_readme(project_id, project)
        
        return {
            'success': True,
            'imported': import_count,
            'project_id': project_id
        }
    
    def _add_file_record(self, project_id: str, file_path: Path):
        """添加文件记录到数据库"""
        try:
            file_ext = file_path.suffix.lower()
            file_type = self.FILE_TYPE_MAPPING.get(file_ext, 'Other')
            
            self.db_manager.execute("""
                INSERT INTO files (project_id, file_name, file_path, file_type, file_size)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                project_id,
                file_path.name,
                str(file_path),
                file_type,
                file_path.stat().st_size
            ))
        except Exception as e:
            print(f"添加文件记录失败: {e}")
    
    def organize_project_files(self, project_id: str) -> Dict:
        """整理项目文件"""
        project = self.get_project_by_id(project_id)
        if not project:
            return {'success': False, 'message': '项目不存在'}
        
        project_path = self.base_data_dir / f"{project_id}_{project.get('title', '')}"
        if not project_path.exists():
            return {'success': False, 'message': '项目目录不存在'}
        
        organized = {'files': [], 'folders': []}
        
        # 按类型创建子目录并移动文件
        type_folders = {
            'raw Sequencing Data': 'raw_data',
            'Alignment File': 'alignment',
            'Single-cell Data': 'singlecell',
            'Mass Spectrometry Data': 'mass_spec',
            'Flow Cytometry Data': 'flow_cytometry',
            'Table/Report': 'tables',
            'Image': 'images',
            'Document': 'documents',
            'Compressed Data': 'compressed',
            'Other': 'other'
        }
        
        for file_path in project_path.iterdir():
            if file_path.is_file() and file_path.name != "README.md":
                file_ext = file_path.suffix.lower()
                file_type = self.FILE_TYPE_MAPPING.get(file_ext, 'Other')
                
                target_folder_name = type_folders.get(file_type, 'other')
                target_folder = project_path / target_folder_name
                target_folder.mkdir(exist_ok=True)
                
                new_path = target_folder / file_path.name
                file_path.rename(new_path)
                
                organized['files'].append({
                    'name': file_path.name,
                    'type': file_type,
                    'folder': target_folder_name
                })
        
        # 更新README
        self._generate_project_readme(project_id, project)
        
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
    
    # ==================== 生物结果项目管理 ====================
    
    def create_bioresult_project(self, data: Dict) -> Dict:
        """创建生物结果项目"""
        project_id = self.get_next_bioresult_id()
        
        project_path = self.results_dir / f"{project_id}_{data.get('title', 'Untitled')}"
        project_path.mkdir(parents=True, exist_ok=True)
        
        created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.db_manager.execute("""
            INSERT INTO bioresult_projects 
            (id, title, description, data_type, analysis_type, software, parameters, authors, created_date, path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            project_id,
            data.get('title', ''),
            data.get('description', ''),
            data.get('data_type', ''),
            data.get('analysis_type', ''),
            data.get('software', ''),
            data.get('parameters', ''),
            data.get('authors', ''),
            created_date,
            str(project_path)
        ))
        
        return self.get_bioresult_project_by_id(project_id)
    
    def get_all_bioresult_projects(self) -> List[Dict]:
        """获取所有生物结果项目"""
        projects = self.db_manager.query("""
            SELECT * FROM bioresult_projects ORDER BY created_date DESC
        """)
        
        result = []
        for row in projects:
            project = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'data_type': row[3],
                'analysis_type': row[4],
                'software': row[5],
                'parameters': row[6],
                'authors': row[7],
                'created_date': row[8],
                'path': row[9]
            }
            # 兼容性字段名
            project['results_id'] = project['id']
            project['analysis_type_label'] = project.get('analysis_type', '')
            result.append(project)
        
        return result
    
    def get_bioresult_project_by_id(self, project_id: str) -> Optional[Dict]:
        """根据ID获取生物结果项目"""
        row = self.db_manager.query_one(
            "SELECT * FROM bioresult_projects WHERE id = %s",
            (project_id,)
        )
        
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'data_type': row[3],
                'analysis_type': row[4],
                'software': row[5],
                'parameters': row[6],
                'authors': row[7],
                'created_date': row[8],
                'path': row[9]
            }
        return None
    
    def update_bioresult_project(self, data: Dict) -> bool:
        """更新生物结果项目"""
        project_id = data.get('id')
        if not project_id:
            return False
        
        self.db_manager.execute("""
            UPDATE bioresult_projects 
            SET title = %s, description = %s, data_type = %s, 
                analysis_type = %s, software = %s, parameters = %s, authors = %s
            WHERE id = %s
        """, (
            data.get('title', ''),
            data.get('description', ''),
            data.get('data_type', ''),
            data.get('analysis_type', ''),
            data.get('software', ''),
            data.get('parameters', ''),
            data.get('authors', ''),
            project_id
        ))
        
        return True
    
    def delete_bioresult_project(self, project_id: str) -> bool:
        """删除生物结果项目"""
        try:
            project = self.get_bioresult_project_by_id(project_id)
            if not project:
                return False
            
            self.db_manager.execute("DELETE FROM bioresult_projects WHERE id = %s", (project_id,))
            
            # 删除项目目录
            project_path = Path(project['path'])
            if project_path.exists():
                shutil.rmtree(project_path)
            
            return True
        except Exception as e:
            print(f"删除生物结果项目失败: {e}")
            return False
    
    # ==================== 处理数据管理 ====================
    
    def get_all_processed_data(self) -> List[Dict]:
        """获取所有处理数据"""
        data = self.db_manager.query("""
            SELECT * FROM processed_files ORDER BY indexed_at DESC
        """)
        
        return [dict(zip(
            ['id', 'project_id', 'file_name', 'file_path', 'file_type', 'file_size', 'indexed_at'],
            row
        )) for row in data]
    
    def _get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        ext = Path(filename).suffix.lower()
        return self.FILE_TYPE_MAPPING.get(ext, 'Other')
    
    def import_processed_file(self, project_id: str, file_path: str) -> Dict:
        """导入处理文件"""
        path = Path(file_path)
        if not path.exists():
            return {'success': False, 'message': '文件不存在'}
        
        self.db_manager.execute("""
            INSERT INTO processed_files (project_id, file_name, file_path, file_type, file_size)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            project_id,
            path.name,
            str(path),
            self._get_file_type(path.name),
            path.stat().st_size
        ))
        
        return {'success': True, 'file': path.name}
