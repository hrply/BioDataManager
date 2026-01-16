#!/usr/bin/env python3
"""
BioData Manager - Flask Server
生物信息学数据管理系统 - Flask 服务器

提供Web服务，处理API请求，管理数据库连接
"""

import os
import sys
import json
import uuid
import threading
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from datetime import datetime

# 添加app目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, request, jsonify, send_from_directory
from backend import BioDataManager
from database_mysql import DatabaseManager
from metadata_config_manager_mysql import MetadataConfigManager

# 硬编码路径配置
BIORAW_BASE_DIR = Path("/bioraw")
DATA_DIR = BIORAW_BASE_DIR / "data"
DOWNLOADS_DIR = BIORAW_BASE_DIR / "downloads"
RESULTS_DIR = BIORAW_BASE_DIR / "results"
ANALYSIS_DIR = BIORAW_BASE_DIR / "analysis"

# Flask 应用配置
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# 初始化数据库连接
db_manager = DatabaseManager()
config_manager = MetadataConfigManager(db_manager)
manager = BioDataManager(db_manager, config_manager)

# ==================== 异步任务管理 ====================

# 任务存储 {task_id: {status, progress, result, error, created_at}}
scan_tasks = {}
task_lock = threading.Lock()


def get_task(task_id: str) -> dict:
    """获取任务信息"""
    with task_lock:
        return scan_tasks.get(task_id)


def create_task(task_type: str) -> str:
    """创建新任务并返回task_id"""
    task_id = str(uuid.uuid4())[:8]
    with task_lock:
        scan_tasks[task_id] = {
            'id': task_id,
            'type': task_type,
            'status': 'pending',  # pending, running, completed, failed
            'progress': 0,
            'message': '等待开始...',
            'result': None,
            'error': None,
            'created_at': datetime.now().isoformat(),
            'completed_at': None
        }
    return task_id


def update_task(task_id: str, status: str = None, progress: int = None, 
                message: str = None, result: any = None, error: str = None):
    """更新任务状态"""
    with task_lock:
        if task_id in scan_tasks:
            if status is not None:
                scan_tasks[task_id]['status'] = status
            if progress is not None:
                scan_tasks[task_id]['progress'] = progress
            if message is not None:
                scan_tasks[task_id]['message'] = message
            if result is not None:
                scan_tasks[task_id]['result'] = result
            if error is not None:
                scan_tasks[task_id]['error'] = error
            if status in ('completed', 'failed'):
                scan_tasks[task_id]['completed_at'] = datetime.now().isoformat()


def run_scan_downloads_task(task_id: str):
    """在后台线程中执行扫描下载目录"""
    try:
        update_task(task_id, status='running', progress=10, message='正在扫描下载目录...')
        result = manager.scan_downloads()
        update_task(task_id, status='completed', progress=100, 
                   message=f'扫描完成，找到 {len(result)} 个文件夹',
                   result=result)
    except Exception as e:
        update_task(task_id, status='failed', error=str(e))


def run_scan_analysis_task(task_id: str):
    """在后台线程中执行扫描分析目录"""
    try:
        update_task(task_id, status='running', progress=10, message='正在扫描分析目录...')
        result = manager.scan_analysis()
        update_task(task_id, status='completed', progress=100,
                   message=f'扫描完成，找到 {len(result)} 个文件夹',
                   result=result)
    except Exception as e:
        update_task(task_id, status='failed', error=str(e))


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/raw-data')
def raw_data():
    """原始数据页面"""
    return render_template('raw_data.html')


@app.route('/results')
def results():
    """结果管理页面"""
    return render_template('results.html')


@app.route('/files')
def files():
    """文件管理页面"""
    return render_template('files.html')


@app.route('/metadata')
def metadata():
    """元数据管理页面"""
    return render_template('metadata.html')


# ==================== 静态文件路由 ====================

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    static_dir = Path(__file__).parent / 'static'
    return send_from_directory(static_dir, filename)


@app.route('/libs/<path:filename>')
def serve_lib(filename):
    """提供库文件"""
    libs_dir = Path(__file__).parent / 'libs'
    return send_from_directory(libs_dir, filename)


# ==================== API 路由 - 项目管理 ====================

@app.route('/api/projects')
def api_get_projects():
    """获取所有项目"""
    try:
        projects = manager.get_all_projects()
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/project')
def api_get_project():
    """获取特定项目"""
    project_id = request.args.get('id')
    if not project_id:
        return jsonify({'success': False, 'message': '缺少项目ID'})
    try:
        project = manager.get_project_by_id(project_id)
        if project:
            return jsonify({'success': True, 'project': project})
        else:
            return jsonify({'success': False, 'message': '项目不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/create-project', methods=['POST'])
def api_create_project():
    """创建新项目"""
    try:
        data = request.get_json()
        project = manager.create_project(data)
        return jsonify({'success': True, 'project': project})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/update-project', methods=['POST'])
def api_update_project():
    """更新项目"""
    try:
        data = request.get_json()
        success = manager.update_project(data)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/delete-project', methods=['POST'])
def api_delete_project():
    """删除项目"""
    try:
        data = request.get_json()
        project_id = data.get('id')
        if not project_id:
            return jsonify({'success': False, 'message': '缺少项目ID'})
        success = manager.delete_project(project_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== API 路由 - 结果数据 ====================

@app.route('/api/bioresult-projects')
def api_get_bioresult_projects():
    """获取生物结果项目"""
    try:
        projects = manager.get_all_bioresult_projects()
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/bioresult-project', methods=['POST'])
def api_bioresult_project():
    """处理生物结果项目操作"""
    try:
        data = request.get_json()
        action = data.get('action', 'create')
        if action == 'create':
            project = manager.create_bioresult_project(data)
            return jsonify({'success': True, 'project': project})
        elif action == 'update':
            success = manager.update_bioresult_project(data)
            return jsonify({'success': success})
        elif action == 'delete':
            project_id = data.get('id')
            success = manager.delete_bioresult_project(project_id)
            return jsonify({'success': success})
        else:
            return jsonify({'success': False, 'message': '未知操作'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== API 路由 - 文件管理 ====================

@app.route('/api/scan-downloads')
def api_scan_downloads():
    """扫描下载目录 - 异步版本"""
    try:
        task_id = create_task('scan_downloads')
        # 启动后台线程执行扫描
        thread = threading.Thread(target=run_scan_downloads_task, args=(task_id,), daemon=True)
        thread.start()
        return jsonify({
            'success': True, 
            'task_id': task_id,
            'message': '扫描任务已启动'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/scan-downloads/sync')
def api_scan_downloads_sync():
    """扫描下载目录 - 同步版本(保留兼容)"""
    try:
        projects = manager.scan_downloads()
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/import-download', methods=['POST'])
def api_import_download():
    """导入下载文件"""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        files = data.get('files', [])
        if not project_id or not files:
            return jsonify({'success': False, 'message': '缺少参数'})
        result = manager.import_download_files(project_id, files)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/organize-files', methods=['POST'])
def api_organize_files():
    """整理项目文件"""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'message': '缺少项目ID'})
        result = manager.organize_project_files(project_id)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/directory-tree')
def api_directory_tree():
    """获取目录树"""
    try:
        tree = manager.get_directory_tree(str(DOWNLOADS_DIR))
        return jsonify({'success': True, 'tree': tree})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/processed-data')
def api_get_processed_data():
    """获取处理数据列表"""
    try:
        data = manager.get_all_processed_data()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/import-processed-file', methods=['POST'])
def api_import_processed_file():
    """导入处理文件"""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        file_path = data.get('file_path')
        if not project_id or not file_path:
            return jsonify({'success': False, 'message': '缺少参数'})
        result = manager.import_processed_file(project_id, file_path)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/scan-analysis')
def api_scan_analysis():
    """扫描分析目录 - 异步版本"""
    try:
        task_id = create_task('scan_analysis')
        # 启动后台线程执行扫描
        thread = threading.Thread(target=run_scan_analysis_task, args=(task_id,), daemon=True)
        thread.start()
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '扫描任务已启动'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/scan-analysis/sync')
def api_scan_analysis_sync():
    """扫描分析目录 - 同步版本(保留兼容)"""
    try:
        analysis_data = manager.scan_analysis()
        return jsonify({'success': True, 'analysis': analysis_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/import-analysis', methods=['POST'])
def api_import_analysis():
    """导入分析数据"""
    try:
        data = request.get_json()
        folder_path = data.get('folder_path')
        if not folder_path:
            return jsonify({'success': False, 'message': '缺少文件夹路径'})
        result = manager.import_analysis_folder(folder_path)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== API 路由 - 元数据配置 ====================

@app.route('/api/metadata/config')
def api_get_metadata_config():
    """获取元数据配置"""
    try:
        config = config_manager.get_all_configs()
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/metadata/config', methods=['POST'])
def api_metadata_config():
    """添加元数据配置"""
    try:
        data = request.get_json()
        config = config_manager.add_config(data)
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/metadata/config/update', methods=['POST'])
def api_update_metadata_config():
    """更新元数据配置"""
    try:
        data = request.get_json()
        success = config_manager.update_config(data)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/metadata/config/delete', methods=['POST'])
def api_delete_metadata_config():
    """删除元数据配置"""
    try:
        data = request.get_json()
        config_id = data.get('id')
        if not config_id:
            return jsonify({'success': False, 'message': '缺少配置ID'})
        success = config_manager.delete_config(config_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/save-metadata-order', methods=['POST'])
def api_save_metadata_order():
    """保存元数据排序"""
    try:
        data = request.get_json()
        configs = data.get('configs', [])
        if not configs:
            return jsonify({'success': False, 'message': '缺少配置'})
        success = config_manager.save_order(configs)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 错误处理 ====================

@app.errorhandler(404)
def page_not_found(e):
    """404错误处理"""
    return render_template('error.html', error=e), 404


@app.errorhandler(500)
def internal_server_error(e):
    """500错误处理"""
    return render_template('error.html', error=e), 500


# ==================== API 路由 - 异步任务管理 ====================

@app.route('/api/task/status/<task_id>')
def api_task_status(task_id: str):
    """获取任务状态"""
    task = get_task(task_id)
    if task:
        return jsonify({'success': True, 'task': task})
    return jsonify({'success': False, 'message': '任务不存在'})


@app.route('/api/tasks')
def api_all_tasks():
    """获取所有任务列表"""
    with task_lock:
        tasks = list(scan_tasks.values())
    # 返回最近10个任务
    tasks = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
    return jsonify({'success': True, 'tasks': tasks})


# ==================== 启动函数 ====================

def run_server(port=8000):
    """运行Flask服务器"""
    # 确保数据目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"BioData Manager Flask 服务器运行在端口 {port}")
    print(f"数据目录: {DATA_DIR}")
    print(f"下载目录: {DOWNLOADS_DIR}")
    print(f"结果目录: {RESULTS_DIR}")
    print(f"分析目录: {ANALYSIS_DIR}")
    
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)