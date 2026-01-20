#!/usr/bin/env python3
"""
测试导入下载文件功能
"""

import requests
import json
import sys

BASE_URL = "http://localhost:20425"

def test_import_new_project():
    """测试新建项目并导入文件"""
    print("\n【测试新建项目并导入文件】")
    
    # 1. 扫描下载目录
    print("  扫描下载目录...")
    resp = requests.get(f"{BASE_URL}/api/scan-downloads/sync", timeout=30)
    data = resp.json()
    print(f"  扫描结果: {data}")
    
    if not data.get('success'):
        print("  扫描失败")
        return False
    
    # 找到测试文件夹
    test_folder_info = None
    for folder in data.get('projects', []):
        if folder.get('name') == 'test_import':
            test_folder_info = folder
            break
    
    if not test_folder_info:
        print("  未找到测试文件夹")
        return False
    
    print(f"  找到测试文件夹: {test_folder_info}")
    
    # 2. 测试新建项目并导入
    print("  测试新建项目并导入...")
    import_data = {
        "folder_name": test_folder_info.get('path'),
        "files": ["sample1.fastq", "sample2.fastq"],
        "data_type": "raw",
        "project_info": {
            "raw_title": "API测试导入项目",
            "raw_type": "mRNAseq",
            "raw_species": "Homo sapiens",
            "raw_tissue": "Lung"
        }
    }
    
    print(f"  发送数据: {json.dumps(import_data, ensure_ascii=False)}")
    
    resp = requests.post(f"{BASE_URL}/api/import-download", json=import_data, timeout=30)
    result = resp.json()
    print(f"  响应: {result}")
    
    if result.get('success'):
        print("  ✅ 导入成功!")
        return True
    else:
        print(f"  ❌ 导入失败: {result.get('message')}")
        return False

def test_import_existing_project():
    """测试导入到已有项目"""
    print("\n【测试导入到已有项目】")
    
    # 1. 先创建项目
    print("  创建项目...")
    resp = requests.post(f"{BASE_URL}/api/projects", json={
        "table": "raw",
        "raw_title": "测试导入已有项目",
        "raw_type": "mRNAseq",
        "raw_species": "Mus musculus",
        "raw_tissue": "Liver"
    }, timeout=10)
    create_result = resp.json()
    print(f"  创建项目响应: {create_result}")
    
    if not create_result.get('success'):
        print("  创建项目失败")
        return False
    
    project_id = create_result.get('project', {}).get('raw_id')
    print(f"  项目ID: {project_id}")
    
    if not project_id:
        print("  无法获取项目ID")
        return False
    
    # 2. 导入到已有项目
    import_data = {
        "project_id": project_id,
        "folder_name": "/bio/downloads/test_import",
        "files": ["sample1.fastq"],
        "data_type": "raw"
    }
    
    resp = requests.post(f"{BASE_URL}/api/import-download", json=import_data, timeout=30)
    result = resp.json()
    print(f"  导入响应: {result}")
    
    if result.get('success'):
        print("  ✅ 导入到已有项目成功!")
        return True
    else:
        print(f"  ❌ 导入失败: {result.get('message')}")
        return False

def main():
    print("=" * 60)
    print("测试导入下载文件功能")
    print("=" * 60)
    
    success1 = test_import_new_project()
    success2 = test_import_existing_project()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 所有导入测试通过!")
        return True
    else:
        print("❌ 部分测试失败")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
