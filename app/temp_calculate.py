@app.route('/api/files/hash/calculate', methods=['POST'])
def api_calculate_files_hash():
    """计算指定文件的 MD5 和 SHA256 哈希值（异步任务）
    
    请求体:
        file_ids: 文件ID列表
    """
    try:
        data = request.get_json()
        file_ids = data.get('file_ids', [])
        
        if not file_ids:
            return jsonify({'success': False, 'message': '缺少文件ID'}), 400
        
        # 创建异步任务
        db = get_db_manager()
        task_id = task_manager.create_task(file_ids, db)
        
        # 启动任务
        task_manager.start_task(task_id)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '任务已创建，正在计算...'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/files/hash/status/<task_id>')
def api_get_hash_task_status(task_id):
    """获取 Hash 计算任务状态
    
    Args:
        task_id: 任务ID
    """
    try:
        task_status = task_manager.get_task_status(task_id)
        
        if not task_status:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            **task_status
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
