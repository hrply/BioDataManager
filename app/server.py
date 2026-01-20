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
import random
import string
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from datetime import datetime

# 添加app目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, request, jsonify, send_from_directory
from backend import BioDataManager
from database_mysql import DatabaseManager
from metadata_config_manager_mysql import MetadataConfigManager
from citation_parser import CitationParser

# 硬编码路径配置（数据库设计规范要求）
BIORAW_BASE_DIR = Path("/bioraw")
RAW_DATA_DIR = BIORAW_BASE_DIR / "rawdata"
DOWNLOADS_DIR = Path("/bio") / "downloads"
RESULTS_DIR = Path("/bio") / "results"

# Flask 应用配置
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# 延迟初始化
_db_manager = None
_config_manager = None
_manager = None

def get_db_manager():
    """获取数据库管理器，延迟初始化"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def get_config_manager():
    """获取配置管理器，延迟初始化"""
    global _config_manager
    if _config_manager is None:
        _config_manager = MetadataConfigManager(get_db_manager())
    return _config_manager

def get_manager():
    """获取业务管理器，延迟初始化"""
    global _manager
    if _manager is None:
        try:
            _manager = BioDataManager(get_db_manager(), get_config_manager())
        except Exception as e:
            print(f"警告: 业务管理器初始化失败: {e}")
            _manager = None
    return _manager

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
        result = get_manager().scan_downloads()
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
    projects = []
    try:
        mgr = get_manager()
        if mgr:
            projects = mgr.get_all_raw_projects()
    except Exception as e:
        print(f"获取原始数据项目列表失败: {e}")
    return render_template('raw_data.html', projects=projects)


@app.route('/results')
def results():
    """结果管理页面"""
    bioresult_projects = []
    try:
        mgr = get_manager()
        if mgr:
            bioresult_projects = mgr.get_all_result_projects()
    except Exception as e:
        print(f"获取结果项目列表失败: {e}")
    return render_template('results.html', bioresult_projects=bioresult_projects)


@app.route('/files')
def files():
    """文件管理页面"""
    projects = []
    try:
        mgr = get_manager()
        if mgr:
            projects = mgr.get_all_raw_projects()
    except Exception as e:
        print(f"获取项目列表失败: {e}")
    return render_template('files.html', projects=projects)


@app.route('/metadata')
def metadata():
    """元数据管理页面"""
    raw_configs = []
    result_configs = []
    file_configs = []
    try:
        config_mgr = get_config_manager()
        if config_mgr:
            all_configs = config_mgr.get_all_configs()
            for c in all_configs:
                if c.get('field_table') == 'raw':
                    raw_configs.append(c)
                elif c.get('field_table') == 'result':
                    result_configs.append(c)
                elif c.get('field_table') == 'file':
                    file_configs.append(c)
    except Exception as e:
        print(f"获取元数据配置失败: {e}")
    
    return render_template('metadata.html', 
                           raw_configs=raw_configs,
                           result_configs=result_configs,
                           file_configs=file_configs)


# ==================== 全局错误处理 ====================

@app.errorhandler(500)
def handle_500(error):
    """处理500错误，防止服务崩溃"""
    print(f"服务器错误: {error}")
    return jsonify({'success': False, 'message': '服务器内部错误，请稍后重试'}), 500


@app.errorhandler(404)
def handle_404(error):
    """处理404错误"""
    return jsonify({'success': False, 'message': '请求的资源不存在'}), 404


@app.errorhandler(Exception)
def handle_exception(error):
    """全局异常处理，防止未捕获的异常导致服务崩溃"""
    print(f"未捕获的异常: {error}")
    return jsonify({'success': False, 'message': '请求处理失败，请稍后重试'}), 500


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


# ==================== API 路由 - 字段配置 ====================

@app.route('/api/fields')
def api_get_fields():
    """获取字段配置"""
    field_table = request.args.get('table', '')
    try:
        if field_table:
            configs = get_config_manager().get_configs_by_table(field_table)
        else:
            configs = get_config_manager().get_all_configs()
        return jsonify({'success': True, 'fields': configs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/options')
def api_get_options():
    """获取下拉选项"""
    option_type = request.args.get('type', '')
    if not option_type:
        return jsonify({'success': False, 'message': '缺少option_type参数'})
    try:
        options = get_config_manager().get_select_options(option_type)
        return jsonify({'success': True, 'options': options})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== API 路由 - 项目管理 ====================

@app.route('/api/projects')
def api_get_projects():
    """获取项目列表（支持table参数）"""
    table = request.args.get('table', '')
    try:
        if table == 'raw':
            projects = get_manager().get_all_raw_projects()
        elif table == 'result':
            projects = get_manager().get_all_result_projects()
        else:
            # 默认返回原始数据项目
            projects = get_manager().get_all_raw_projects()
        return jsonify({'success': True, 'data': projects, 'total': len(projects)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/bioresult-projects')
def api_get_bio_result_projects():
    """获取结果项目列表（兼容旧版前端）"""
    try:
        projects = get_manager().get_all_result_projects()
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/projects', methods=['POST'])
def api_create_project():
    """创建项目"""
    try:
        data = request.get_json()
        table = data.get('table', 'raw')
        
        if table == 'raw':
            project = get_manager().create_raw_project(data)
        elif table == 'result':
            project = get_manager().create_result_project(data)
        else:
            return jsonify({'success': False, 'message': '无效的table类型'})
        
        return jsonify({'success': True, 'project': project})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/projects/raw/<raw_id>')
def api_get_raw_project(raw_id):
    """获取原始数据项目"""
    try:
        project = get_manager().get_raw_project_by_id(raw_id)
        if project:
            return jsonify({'success': True, 'project': project})
        else:
            return jsonify({'success': False, 'message': '项目不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/projects/raw/<raw_id>', methods=['PUT'])
def api_update_raw_project(raw_id):
    """更新原始数据项目"""
    try:
        data = request.get_json()
        data['raw_id'] = raw_id
        success = get_manager().update_raw_project(data)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/projects/raw/<raw_id>', methods=['DELETE'])
def api_delete_raw_project(raw_id):
    """删除原始数据项目"""
    try:
        success = get_manager().delete_raw_project(raw_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/projects/result/<results_id>')
def api_get_result_project(results_id):
    """获取结果数据项目"""
    try:
        project = get_manager().get_result_project_by_id(results_id)
        if project:
            return jsonify({'success': True, 'project': project})
        else:
            return jsonify({'success': False, 'message': '项目不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/projects/result/<results_id>', methods=['PUT'])
def api_update_result_project(results_id):
    """更新结果数据项目"""
    try:
        data = request.get_json()
        data['results_id'] = results_id
        success = get_manager().update_result_project(data)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/projects/result/<results_id>', methods=['DELETE'])
def api_delete_result_project(results_id):
    """删除结果数据项目"""
    try:
        success = get_manager().delete_result_project(results_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== API 路由 - 兼容性（旧API）====================

@app.route('/api/project')
def api_get_project():
    """获取特定项目（兼容旧API）"""
    project_id = request.args.get('id')
    if not project_id:
        return jsonify({'success': False, 'message': '缺少项目ID'})
    try:
        project = get_manager().get_project_by_id(project_id)
        if project:
            return jsonify({'success': True, 'project': project})
        else:
            return jsonify({'success': False, 'message': '项目不存在'})
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
        projects = get_manager().scan_downloads()
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
        project_info = data.get('project_info', {})
        folder_name = data.get('folder_name')
        
        # 如果没有 project_id但有 project_info，则创建新项目
        if not project_id and project_info:
            project = get_manager().create_project(project_info)
            # create_project 返回的是项目字典（包含 raw_id）
            if not project:
                return jsonify({'success': False, 'message': '创建项目失败'})
            # 获取项目ID
            project_id = project.get('raw_id') or project.get('results_id') or project.get('id')
            if not project_id:
                return jsonify({'success': False, 'message': '创建项目成功但无法获取项目ID'})
        
        if not project_id or not files:
            return jsonify({'success': False, 'message': '缺少参数'})
        result = get_manager().import_download_files(project_id, files, folder_name)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== API 路由 - 引文解析 ====================

@app.route('/api/parse-citation', methods=['POST'])
def api_parse_citation():
    """解析引文文件 (支持 .bib, .ris, .enw 格式)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        # 检查文件格式
        filename = file.filename.lower()
        if not filename.endswith(('.bib', '.ris', '.enw')):
            return jsonify({
                'success': False, 
                'message': f'不支持的文件格式，仅支持 .bib, .ris, .enw'
            })
        
        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(
            suffix=Path(filename).suffix, 
            delete=False,
            mode='w',
            encoding='utf-8'
        ) as tmp:
            tmp.write(file.read().decode('utf-8'))
            tmp_path = tmp.name
        
        try:
            # 解析引文文件
            parser = CitationParser()
            citations = parser.parse_file(tmp_path)
            
            if not citations:
                return jsonify({
                    'success': False, 
                    'message': '未能解析文件内容，请检查文件格式是否正确'
                })
            
            # 转换为项目数据
            projects = []
            for citation in citations:
                project_data = parser.citation_to_project(citation)
                projects.append({
                    'citation': citation,
                    'project': project_data,
                })
            
            return jsonify({
                'success': True,
                'count': len(projects),
                'citations': projects
            })
            
        finally:
            # 清理临时文件
            import os
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
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
        result = get_manager().organize_project_files(project_id)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/directory-tree')
def api_directory_tree():
    """获取目录树"""
    try:
        tree = get_manager().get_directory_tree(str(DOWNLOADS_DIR))
        return jsonify({'success': True, 'tree': tree})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/processed-data')
def api_get_processed_data():
    """获取处理数据列表"""
    try:
        data = get_manager().get_all_processed_data()
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
        project_info = data.get('project_info', {})
        
        # 如果没有 project_id 但有 project_info，则创建新项目
        if not project_id and project_info:
            project = get_manager().create_project(project_info)
            if not project:
                return jsonify({'success': False, 'message': '创建项目失败'})
            project_id = project.get('results_id') or project.get('raw_id') or project.get('id')
            if not project_id:
                return jsonify({'success': False, 'message': '创建项目成功但无法获取项目ID'})
        
        if not project_id or not file_path:
            return jsonify({'success': False, 'message': '缺少参数'})
        result = get_manager().import_processed_file(project_id, file_path)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== API 路由 - 元数据配置 ====================

@app.route('/api/metadata/config')
def api_get_metadata_config():
    """获取元数据配置（兼容旧API）"""
    try:
        config = get_config_manager().get_all_configs()
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/metadata/fields')
def api_get_metadata_fields():
    """获取指定表类型的元数据字段（兼容旧API）"""
    field_table = request.args.get('table', 'raw')
    try:
        config = get_config_manager().get_configs_by_table(field_table)
        return jsonify({'success': True, 'fields': config})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/metadata/config', methods=['POST'])
def api_metadata_config():
    """添加元数据配置"""
    try:
        data = request.get_json()
        config = get_config_manager().add_config(data)
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/metadata/config/update', methods=['POST'])
def api_update_metadata_config():
    """更新元数据配置"""
    try:
        data = request.get_json()
        success = get_config_manager().update_config(data)
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
        success = get_config_manager().delete_config(config_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/metadata/config/columns')
def api_get_metadata_columns():
    """获取 field_config 表的列信息（用于前端动态生成列标题）"""
    try:
        columns = get_config_manager().get_field_config_columns()
        return jsonify({'success': True, 'columns': columns})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/metadata/config/batch-update', methods=['POST'])
def api_batch_update_metadata_config():
    """批量更新元数据配置"""
    try:
        data = request.get_json()
        configs = data.get('configs', [])
        if not configs:
            return jsonify({'success': False, 'message': '缺少配置'})
        
        success = True
        for config_data in configs:
            config_id = config_data.get('id')
            if not config_id:
                continue
            if not get_config_manager().update_config(config_data):
                success = False
        
        return jsonify({'success': success, 'message': '批量更新成功' if success else '部分更新失败'})
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
        success = get_config_manager().save_order(configs)
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
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"BioData Manager Flask 服务器运行在端口 {port}")
    print(f"原始数据目录: {RAW_DATA_DIR}")
    print(f"下载目录: {DOWNLOADS_DIR}")
    print(f"结果目录: {RESULTS_DIR}")
    
    # 使用 threaded=True 支持并发请求，优化连接池配置
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False, 
        threaded=True,
        passthrough_errors=True
    )


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
