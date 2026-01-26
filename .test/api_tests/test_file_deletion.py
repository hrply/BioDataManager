#!/usr/bin/env python3
"""
文件删除功能内测代码 - 验证删除是否将文件移动到回收站
"""

import os
import sys
import json
import uuid
import argparse
from datetime import datetime
import requests

CONTAINER_HTTP_PORT = os.getenv('CONTAINER_HTTP_PORT', '20425')


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def run_cmd(cmd):
    """执行命令并返回输出"""
    return os.popen(cmd).read().strip()


def main():
    port = CONTAINER_HTTP_PORT
    base_url = f"http://localhost:{port}"
    
    results = {'total': 0, 'passed': 0, 'failed': 0, 'tests': []}
    
    log("=" * 50)
    log("文件删除功能测试 - 验证移动到回收站")
    log("=" * 50)
    
    test_id = f"TEST_{uuid.uuid4().hex[:8].upper()}"
    test_file = f"test_{uuid.uuid4().hex[:4]}.fastq"
    test_path = f"rawdata/TEST/{test_id}"
    container_path = f"/bio/{test_path}/{test_file}"
    recycle_path = f"/bio/recycle/{test_path}/{test_file}"
    
    try:
        # 1. 创建测试文件
        log(f"1. 创建测试文件: {test_id}")
        # 使用 printf 避免换行符问题
        file_content = "@Test\nACGT\n+\nIIII"
        run_cmd(f"docker exec biodata-manager bash -c 'mkdir -p /bio/{test_path} && printf \"{file_content}\" > {container_path}'")
        
        if run_cmd(f"docker exec biodata-manager test -f {container_path} && echo exists") == "exists":
            log("   ✓ 文件创建成功")
            results['total'] += 1
            results['passed'] += 1
            results['tests'].append({'id': 'TC01', 'name': '创建测试文件', 'status': 'passed'})
        else:
            log("   ✗ 文件创建失败")
            results['total'] += 1
            results['failed'] += 1
            results['tests'].append({'id': 'TC01', 'name': '创建测试文件', 'status': 'failed', 'message': '文件创建失败'})
            return results
        
        # 2. 插入数据库记录并获取ID
        log("2. 插入数据库记录")
        escaped = (test_file.replace("'", "\\'"), test_path.replace("'", "\\'"), test_id.replace("'", "\\'"))
        insert_sql = f"INSERT INTO file_record (file_name, file_path, file_property, file_size, file_type, file_project_type, file_project_id, imported_at) VALUES ('{escaped[0]}', '{escaped[1]}', '测试', 20, 'fastq', 'raw', '{escaped[2]}', NOW()); SELECT LAST_INSERT_ID()"
        
        mysql_cmd = f'docker exec biodata-mysql mysql -u biodata -pbiodata123 biodata -e "{insert_sql}"'
        result = os.popen(mysql_cmd).read()
        
        # 解析结果获取 file_id
        lines = result.strip().split('\n')
        file_id = lines[-1] if lines else "0"
        
        if file_id and int(file_id) > 0:
            log(f"   ✓ 数据库记录创建成功: ID={file_id}")
            results['total'] += 1
            results['passed'] += 1
            results['tests'].append({'id': 'TC02', 'name': '创建数据库记录', 'status': 'passed'})
        else:
            log(f"   ✗ 数据库记录创建失败: {result}")
            results['total'] += 1
            results['failed'] += 1
            results['tests'].append({'id': 'TC02', 'name': '创建数据库记录', 'status': 'failed'})
            return results
        
        # 3. 调用删除API
        log("3. 调用删除API")
        response = requests.delete(f"{base_url}/api/files", json={'file_ids': [int(file_id)]}, timeout=30)
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            log(f"   ✓ 删除API调用成功: {data}")
            results['total'] += 1
            results['passed'] += 1
            results['tests'].append({'id': 'TC03', 'name': '删除API调用', 'status': 'passed'})
        else:
            log(f"   ✗ 删除API调用失败: {response.status_code} - {data}")
            results['total'] += 1
            results['failed'] += 1
            results['tests'].append({'id': 'TC03', 'name': '删除API调用', 'status': 'failed'})
            return results
        
        # 4. 验证文件在回收站
        import time
        time.sleep(1)
        
        log("4. 验证文件在回收站")
        in_recycle = run_cmd(f"docker exec biodata-manager test -f {recycle_path} && echo exists") == "exists"
        
        if in_recycle:
            log(f"   ✓ 文件在回收站: {recycle_path}")
            results['total'] += 1
            results['passed'] += 1
            results['tests'].append({'id': 'TC04', 'name': '文件在回收站', 'status': 'passed'})
        else:
            log(f"   ✗ 文件不在回收站: {recycle_path}")
            results['total'] += 1
            results['failed'] += 1
            results['tests'].append({'id': 'TC04', 'name': '文件在回收站', 'status': 'failed', 'message': f'不在: {recycle_path}'})
        
        # 5. 验证原文件被删除
        log("5. 验证原文件被删除")
        original_gone = run_cmd(f"docker exec biodata-manager test -f {container_path} && echo exists") != "exists"
        
        if original_gone:
            log("   ✓ 原文件已删除")
            results['total'] += 1
            results['passed'] += 1
            results['tests'].append({'id': 'TC05', 'name': '原文件删除', 'status': 'passed'})
        else:
            log("   ✗ 原文件仍存在")
            results['total'] += 1
            results['failed'] += 1
            results['tests'].append({'id': 'TC05', 'name': '原文件删除', 'status': 'failed'})
        
    finally:
        # 清理
        log("6. 清理测试数据")
        run_cmd(f"docker exec biodata-manager rm -f {container_path} 2>/dev/null")
        run_cmd(f"docker exec biodata-manager rm -f {recycle_path} 2>/dev/null")
        if 'file_id' in dir() and file_id and int(file_id) > 0:
            run_cmd(f"docker exec biodata-mysql mysql -u biodata -pbiodata123 biodata -e 'DELETE FROM file_record WHERE id={file_id}' 2>/dev/null")
        log("   清理完成")
    
    # 输出结果
    log("-" * 50)
    log(f"总计: {results['total']} | 通过: {results['passed']} | 失败: {results['failed']}")
    log("=" * 50)
    
    # 保存结果
    os.makedirs('.test/results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'.test/results/file_deletion_test_{timestamp}.json', 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存至: .test/results/file_deletion_test_{timestamp}.json")
    
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
