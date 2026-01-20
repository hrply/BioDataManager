#!/usr/bin/env python3
"""
测试结果项目导入功能
"""

import requests
import json
import sys

BASE_URL = "http://localhost:20425"

def test_import_result_new_project():
    """测试新建结果项目并导入文件"""
    print("\n【测试新建结果项目并导入文件】")
    
    # 测试新建结果项目并导入
    print("  测试新建结果项目并导入...")
    import_data = {
        "file_path": "/bio/results/test_import_result/result1.csv",
        "project_info": {
            "results_title": "API测试结果导入项目",
            "results_type": "DEA",
            "results_raw": "RAW_2Dr2LeST"  # 引用已有的 raw 项目
        }
    }
    
    print(f"  发送数据: {json.dumps(import_data, ensure_ascii=False)}")
    
    resp = requests.post(f"{BASE_URL}/api/import-processed-file", json=import_data, timeout=30)
    result = resp.json()
    print(f"  响应: {result}")
    
    if result.get('success'):
        print("  ✅ 结果项目导入成功!")
        return True
    else:
        print(f"  ❌ 导入失败: {result.get('message')}")
        return False

def test_import_result_existing_project():
    """测试导入到已有结果项目"""
    print("\n【测试导入到已有结果项目】")
    
    # 1. 先创建结果项目
    print("  创建结果项目...")
    resp = requests.post(f"{BASE_URL}/api/projects", json={
        "table": "result",
        "results_title": "测试结果导入已有项目",
        "results_type": "DEA",
        "results_raw": "RAW_2Dr2LeST"
    }, timeout=10)
    create_result = resp.json()
    print(f"  创建项目响应: {create_result}")
    
    if not create_result.get('success'):
        print("  创建项目失败")
        return False
    
    project_id = create_result.get('project', {}).get('results_id')
    print(f"  项目ID: {project_id}")
    
    if not project_id:
        print("  无法获取项目ID")
        return False
    
    # 2. 导入到已有结果项目
    import_data = {
        "project_id": project_id,
        "file_path": "/bio/results/test_import_result/result2.csv"
    }
    
    resp = requests.post(f"{BASE_URL}/api/import-processed-file", json=import_data, timeout=30)
    result = resp.json()
    print(f"  导入响应: {result}")
    
    if result.get('success'):
        print("  ✅ 导入到已有结果项目成功!")
        return True
    else:
        print(f"  ❌ 导入失败: {result.get('message')}")
        return False

def main():
    print("=" * 60)
    print("测试结果项目导入功能")
    print("=" * 60)
    
    success1 = test_import_result_new_project()
    success2 = test_import_result_existing_project()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 所有结果项目导入测试通过!")
        return True
    else:
        print("❌ 部分测试失败")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)