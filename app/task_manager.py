#!/usr/bin/env python3
"""
任务管理器 - 异步任务处理
"""

import threading
import uuid
import hashlib
from pathlib import Path
from typing import Dict, List, Optional


class TaskManager:
    """异步任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.lock = threading.Lock()
    
    def create_task(self, file_ids: List[int], db_manager) -> str:
        """创建新的 Hash 计算任务
        
        Args:
            file_ids: 文件 ID 列表
            db_manager: 数据库管理器
            
        Returns:
            任务 ID
        """
        task_id = str(uuid.uuid4())
        
        with self.lock:
            self.tasks[task_id] = {
                'status': 'pending',
                'file_ids': file_ids,
                'total': len(file_ids),
                'current': 0,
                'results': {},
                'error': None,
                'db_manager': db_manager
            }
        
        return task_id
    
    def start_task(self, task_id: str):
        """启动任务（在后台线程中执行）"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        # 在后台线程中执行计算
        thread = threading.Thread(target=self._run_task, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        return True
    
    def _run_task(self, task_id: str):
        """执行 Hash 计算任务"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        try:
            # 更新状态为运行中
            with self.lock:
                task['status'] = 'running'
            
            db_manager = task['db_manager']
            file_ids = task['file_ids']
            
            # 查询文件信息
            placeholders = ','.join(['%s'] * len(file_ids))
            files = db_manager.query(f"""
                SELECT id, file_path, file_name 
                FROM file_record 
                WHERE id IN ({placeholders})
            """, file_ids)
            
            # 检查是否找到文件
            if not files:
                with self.lock:
                    task['status'] = 'failed'
                    task['error'] = f"未找到指定的文件 ID: {file_ids}"
                return
            
            # 计算每个文件的哈希值
            for idx, f in enumerate(files):
                file_id = f[0]
                file_path = Path('/bio') / f[1] / f[2]
                
                try:
                    md5, sha256 = self._calculate_file_hash(file_path)
                    
                    with self.lock:
                        task['results'][file_id] = {
                            'md5': md5,
                            'sha256': sha256
                        }
                        task['current'] = idx + 1
                
                except Exception as e:
                    with self.lock:
                        task['error'] = f"文件 {f[2]} 计算失败: {str(e)}"
                        task['status'] = 'failed'
                        return
            
            # 所有文件计算完成
            with self.lock:
                task['status'] = 'completed'
        
        except Exception as e:
            with self.lock:
                task['error'] = str(e)
                task['status'] = 'failed'
    
    def _calculate_file_hash(self, file_path: Path) -> tuple:
        """计算单个文件的 MD5 和 SHA256
        
        Args:
            file_path: 文件路径
            
        Returns:
            (md5, sha256)
        """
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        # 分块读取文件，避免内存问题
        chunk_size = 8192
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
        
        return md5_hash.hexdigest(), sha256_hash.hexdigest()
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务状态信息
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            
            return {
                'status': task['status'],
                'total': task['total'],
                'current': task['current'],
                'progress': int((task['current'] / task['total']) * 100) if task['total'] > 0 else 0,
                'results': task['results'] if task['status'] == 'completed' else {},
                'error': task['error']
            }
    
    def clean_old_tasks(self, max_age_seconds: int = 3600):
        """清理旧任务（释放内存）
        
        Args:
            max_age_seconds: 任务最大保留时间（秒）
        """
        # 简化实现：只清理已完成的任务
        with self.lock:
            to_remove = []
            for task_id, task in self.tasks.items():
                if task['status'] in ['completed', 'failed']:
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]


# 全局任务管理器实例
task_manager = TaskManager()
