#!/usr/bin/env python3
"""
BioData Manager 综合导入测试脚本
测试：新建项目导入、导入至已有项目、文件夹结构、数据库字段
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:20425"

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_section(title):
    print(f"\n--- {title} ---")

def test_new_raw_import():
    """测试新建原始数据项目导入"""
    print_header("测试1: 新建原始数据项目导入")

    # 获取字段配置
    fields_resp = requests.get(f"{BASE_URL}/api/metadata/fields?table=raw")
    fields_data = fields_resp.json()
    print(f"字段配置获取: {'成功' if fields_data['success'] else '失败'}")

    # 构建项目数据 (使用 project_info 格式，与前端一致)
    project_data = {
        "project_id": "TEST_RAW_001",
        "folder_name": "test_import",
        "files": ["sample.fastq", "test1.fastq", "test2.fastq"],
        "data_type": "raw",
        "project_info": {
            "raw_title": "测试新建原始数据项目",
            "raw_type": "mRNAseq",
            "raw_species": "Mus musculus",
            "raw_tissue": "Liver",
            "raw_keywords": "测试,内测"
        }
    }

    print_section("请求数据")
    print(f"  项目ID: {project_data['project_id']}")
    print(f"  文件: {project_data['files']}")
    print(f"  数据类型: {project_data['metadata']['raw_type']}")
    print(f"  物种: {project_data['metadata']['raw_species']}")
    print(f"  组织: {project_data['metadata']['raw_tissue']}")

    # 发送导入请求
    resp = requests.post(f"{BASE_URL}/api/import-download", json=project_data)
    result = resp.json()

    print_section("API响应")
    print(f"  成功: {result.get('success', False)}")
    if result.get('success'):
        storage_path = result['result'].get('storage_path', '')
        print(f"  存储路径: {storage_path}")
        return storage_path
    else:
        print(f"  错误: {result}")
        return None

def test_new_result_import():
    """测试新建结果数据项目导入"""
    print_header("测试2: 新建结果数据项目导入")

    # 获取字段配置
    fields_resp = requests.get(f"{BASE_URL}/api/metadata/fields?table=result")
    fields_data = fields_resp.json()
    print(f"字段配置获取: {'成功' if fields_data['success'] else '失败'}")

    # 构建项目数据
    project_data = {
        "project_id": "TEST_RES_001",
        "folder_name": "test_import",
        "files": ["test3.fastq"],
        "data_type": "result",
        "metadata": {
            "results_title": "测试新建结果数据项目",
            "results_type": "Marker",
            "results_raw": "TEST_RAW_001",
            "results_description": "测试结果数据导入"
        }
    }

    print_section("请求数据")
    print(f"  项目ID: {project_data['project_id']}")
    print(f"  文件: {project_data['files']}")
    print(f"  结果类型: {project_data['metadata']['results_type']}")
    print(f"  关联项目: {project_data['metadata']['results_raw']}")

    # 发送导入请求
    resp = requests.post(f"{BASE_URL}/api/import-download", json=project_data)
    result = resp.json()

    print_section("API响应")
    print(f"  成功: {result.get('success', False)}")
    if result.get('success'):
        storage_path = result['result'].get('storage_path', '')
        print(f"  存储路径: {storage_path}")
        return storage_path
    else:
        print(f"  错误: {result}")
        return None

def test_existing_raw_import():
    """测试导入至已有原始数据项目"""
    print_header("测试3: 导入至已有原始数据项目")

    # 获取现有项目
    resp = requests.get(f"{BASE_URL}/api/projects?table=raw")
    projects = resp.json().get('data', [])
    if not projects:
        print("  没有现有项目，跳过测试")
        return None

    existing_project = projects[0]
    project_id = existing_project.get('raw_id')
    print(f"  使用现有项目: {project_id}")

    # 获取项目当前元数据
    meta_resp = requests.get(f"{BASE_URL}/api/projects/raw/{project_id}/metadata")
    meta_data = meta_resp.json()
    print(f"  当前元数据: {meta_data.get('metadata', {})}")

    # 构建导入数据 - 追加到已有项目
    import_data = {
        "mode": "mode-existing",
        "folder_name": "test_import",
        "files": ["test3.fastq"],
        "data_type": "raw",
        "project_id": project_id,
        "metadata_override": {
            "raw_type": "mRNAseq",
            "raw_species": "Homo sapiens",
            "raw_tissue": "Heart muscle,Pancreas"  # 追加新组织
        }
    }

    print_section("请求数据")
    print(f"  项目ID: {import_data['project_id']}")
    print(f"  文件: {import_data['files']}")
    print(f"  新增组织: {import_data['metadata_override']['raw_tissue']}")

    # 发送导入请求
    resp = requests.post(f"{BASE_URL}/api/import-download", json=import_data)
    result = resp.json()

    print_section("API响应")
    print(f"  成功: {result.get('success', False)}")
    if result.get('success'):
        storage_path = result['result'].get('storage_path', '')
        print(f"  存储路径: {storage_path}")
        return project_id
    else:
        print(f"  错误: {result}")
        return None

def test_existing_result_import():
    """测试导入至已有结果数据项目"""
    print_header("测试4: 导入至已有结果数据项目")

    # 获取现有结果项目
    resp = requests.get(f"{BASE_URL}/api/projects?table=result")
    projects = resp.json().get('data', [])
    if not projects:
        print("  没有现有结果项目，跳过测试")
        return None

    existing_project = projects[0]
    project_id = existing_project.get('results_id')
    print(f"  使用现有项目: {project_id}")

    # 构建导入数据
    import_data = {
        "mode": "mode-existing",
        "folder_name": "test_import",
        "files": ["test2.fastq"],
        "data_type": "result",
        "project_id": project_id,
        "metadata_override": {
            "results_type": "ChIP-Seq",
            "results_raw": "TEST_RAW_001,TEST_RES_001"  # 追加关联项目
        }
    }

    print_section("请求数据")
    print(f"  项目ID: {import_data['project_id']}")
    print(f"  文件: {import_data['files']}")
    print(f"  新增关联项目: {import_data['metadata_override']['results_raw']}")

    # 发送导入请求
    resp = requests.post(f"{BASE_URL}/api/import-download", json=import_data)
    result = resp.json()

    print_section("API响应")
    print(f"  成功: {result.get('success', False)}")
    if result.get('success'):
        storage_path = result['result'].get('storage_path', '')
        print(f"  存储路径: {storage_path}")
        return project_id
    else:
        print(f"  错误: {result}")
        return None

def check_folder_structure():
    """检查容器内文件夹结构"""
    print_header("检查5: 容器内文件夹结构")

    import subprocess

    # 检查原始数据目录
    print_section("原始数据目录 /bio/rawdata/")
    result = subprocess.run(
        ["docker", "exec", "biodata-manager", "ls", "-laR", "/bio/rawdata/"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(result.stdout[:2000])
    else:
        print(f"错误: {result.stderr}")

    # 检查结果数据目录
    print_section("结果数据目录 /bio/results/")
    result = subprocess.run(
        ["docker", "exec", "biodata-manager", "ls", "-laR", "/bio/results/"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(result.stdout[:2000])
    else:
        print(f"错误: {result.stderr}")

def check_database():
    """检查数据库字段值"""
    print_header("检查6: 数据库字段值")

    import subprocess

    # 检查 raw_project 表
    print_section("raw_project 表")
    result = subprocess.run(
        ["docker", "exec", "biodata-manager", "python3", "-c", """
from database_mysql import DatabaseManager
db = DatabaseManager()
results = db.query('SELECT raw_id, raw_type, raw_species, raw_tissue, raw_keywords FROM raw_project ORDER BY created_at DESC LIMIT 5')
for row in results:
    print(f\"  {row[0]}: type={row[1]}, species={row[2]}, tissue={row[3]}, keywords={row[4]}\")
"""],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"错误: {result.stderr}")

    # 检查 result_project 表
    print_section("result_project 表")
    result = subprocess.run(
        ["docker", "exec", "biodata-manager", "python3", "-c", """
from database_mysql import DatabaseManager
db = DatabaseManager()
results = db.query('SELECT results_id, results_type, results_raw FROM result_project ORDER BY created_at DESC LIMIT 5')
for row in results:
    print(f\"  {row[0]}: type={row[1]}, raw={row[2]}\")
"""],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"错误: {result.stderr}")

def main():
    print("="*60)
    print("  BioData Manager 综合导入测试")
    print("="*60)

    # 测试1: 新建原始数据项目导入
    test_new_raw_import()

    # 测试2: 新建结果数据项目导入
    test_new_result_import()

    # 测试3: 导入至已有原始数据项目
    test_existing_raw_import()

    # 测试4: 导入至已有结果数据项目
    test_existing_result_import()

    # 检查5: 文件夹结构
    check_folder_structure()

    # 检查6: 数据库字段
    check_database()

    print("\n" + "="*60)
    print("  测试完成")
    print("="*60)

if __name__ == "__main__":
    main()
