#!/usr/bin/env python3
"""
文件管理 API 测试脚本
测试文件: /api/files/imported-projects, /api/files, /api/files (DELETE), /api/files/download
"""

import sys
import requests
import json
import os

# 检测运行环境：容器内使用内部端口
if os.environ.get('CONTAINER_TEST'):
    BASE_URL = "http://localhost:8000"
else:
    BASE_URL = "http://localhost:20425"

def print_result(test_name, success, message=""):
    """打印测试结果"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"[{status}] {test_name}")
    if message and not success:
        print(f"       错误: {message}")
    return success

def test_get_imported_projects():
    """测试获取已导入项目列表 API"""
    print("\n" + "=" * 60)
    print("测试: GET /api/files/imported-projects")
    print("=" * 60)
    
    all_pass = True
    
    # 测试 1: 无参数查询
    print("\n[测试 1.1] 无参数查询所有项目")
    try:
        resp = requests.get(f"{BASE_URL}/api/files/imported-projects", timeout=10)
        data = resp.json()
        if print_result("返回成功", data.get('success'), data.get('message')):
            print(f"       项目数量: {data.get('total', 0)}")
            if data.get('data'):
                print(f"       示例项目: {json.dumps(data['data'][0], ensure_ascii=False)}")
    except Exception as e:
        print_result("返回成功", False, str(e))
        all_pass = False
    
    # 测试 2: 按项目类型筛选 (raw)
    print("\n[测试 1.2] 按项目类型筛选 (file_project_type=raw)")
    try:
        resp = requests.get(f"{BASE_URL}/api/files/imported-projects", 
                           params={"file_project_type": "raw"}, timeout=10)
        data = resp.json()
        if print_result("返回成功", data.get('success'), data.get('message')):
            print(f"       项目数量: {data.get('total', 0)}")
    except Exception as e:
        print_result("返回成功", False, str(e))
        all_pass = False
    
    # 测试 3: 按项目类型筛选 (result)
    print("\n[测试 1.3] 按项目类型筛选 (file_project_type=result)")
    try:
        resp = requests.get(f"{BASE_URL}/api/files/imported-projects", 
                           params={"file_project_type": "result"}, timeout=10)
        data = resp.json()
        if print_result("返回成功", data.get('success'), data.get('message')):
            print(f"       项目数量: {data.get('total', 0)}")
    except Exception as e:
        print_result("返回成功", False, str(e))
        all_pass = False
    
    # 测试 4: 按项目编号筛选
    print("\n[测试 1.4] 按项目编号筛选 (file_project_ids=RAW_test001)")
    try:
        resp = requests.get(f"{BASE_URL}/api/files/imported-projects", 
                           params={"file_project_ids": "RAW_test001"}, timeout=10)
        data = resp.json()
        if print_result("返回成功", data.get('success'), data.get('message')):
            print(f"       项目数量: {data.get('total', 0)}")
    except Exception as e:
        print_result("返回成功", False, str(e))
        all_pass = False
    
    # 测试 5: 多项目编号筛选 (OR逻辑)
    print("\n[测试 1.5] 多项目编号筛选 (file_project_ids=RAW_test001,RAW_test002)")
    try:
        resp = requests.get(f"{BASE_URL}/api/files/imported-projects", 
                           params={"file_project_ids": "RAW_test001,RAW_test002"}, timeout=10)
        data = resp.json()
        if print_result("返回成功", data.get('success'), data.get('message')):
            print(f"       项目数量: {data.get('total', 0)}")
    except Exception as e:
        print_result("返回成功", False, str(e))
        all_pass = False
    
    return all_pass

def test_get_project_files():
    """测试获取项目文件列表 API"""
    print("\n" + "=" * 60)
    print("测试: GET /api/files")
    print("=" * 60)
    
    all_pass = True
    
    # 测试 1: 缺少项目编号
    print("\n[测试 2.1] 缺少项目编号应返回错误")
    try:
        resp = requests.get(f"{BASE_URL}/api/files", timeout=10)
        data = resp.json()
        if resp.status_code == 400:
            print_result("返回400错误", True)
        elif not data.get('success'):
            print_result("返回失败", True, data.get('message'))
        else:
            print_result("返回400错误", False, "期望400但得到成功")
    except Exception as e:
        print_result("返回失败", False, str(e))
        all_pass = False
    
    # 测试 2: 查询不存在的项目
    print("\n[测试 2.2] 查询不存在的项目 (project_id=NOT_EXIST)")
    try:
        resp = requests.get(f"{BASE_URL}/api/files", 
                           params={"project_id": "NOT_EXIST"}, timeout=10)
        data = resp.json()
        if print_result("返回成功", data.get('success'), data.get('message')):
            print(f"       文件数量: {data.get('total', 0)}")
    except Exception as e:
        print_result("返回成功", False, str(e))
        all_pass = False
    
    # 测试 3: 查询存在的项目 (需要先有测试数据)
    print("\n[测试 2.3] 查询存在的项目 (project_id=RAW_test001)")
    try:
        resp = requests.get(f"{BASE_URL}/api/files", 
                           params={"project_id": "RAW_test001"}, timeout=10)
        data = resp.json()
        if print_result("返回成功", data.get('success'), data.get('message')):
            print(f"       文件数量: {data.get('total', 0)}")
            if data.get('files'):
                print(f"       示例文件: {json.dumps(data['files'][0], ensure_ascii=False)}")
    except Exception as e:
        print_result("返回成功", False, str(e))
        all_pass = False
    
    return all_pass

def test_delete_files():
    """测试删除文件 API"""
    print("\n" + "=" * 60)
    print("测试: DELETE /api/files")
    print("=" * 60)
    
    all_pass = True
    
    # 测试 1: 缺少文件ID
    print("\n[测试 3.1] 缺少文件ID应返回错误")
    try:
        resp = requests.delete(f"{BASE_URL}/api/files", json={}, timeout=10)
        data = resp.json()
        if resp.status_code == 400:
            print_result("返回400错误", True)
        elif not data.get('success'):
            print_result("返回失败", True, data.get('message'))
        else:
            print_result("返回400错误", False, "期望400但得到成功")
    except Exception as e:
        print_result("返回失败", False, str(e))
        all_pass = False
    
    # 测试 2: 删除不存在的文件ID
    print("\n[测试 3.2] 删除不存在的文件ID (file_ids=[99999])")
    try:
        resp = requests.delete(f"{BASE_URL}/api/files", 
                              json={"file_ids": [99999]}, timeout=10)
        data = resp.json()
        if resp.status_code == 404:
            print_result("返回404错误", True)
        elif not data.get('success'):
            print_result("返回失败", True, data.get('message'))
        else:
            print_result("返回失败", False, "期望404或失败")
    except Exception as e:
        print_result("返回失败", False, str(e))
        all_pass = False
    
    return all_pass

def test_download_files():
    """测试下载文件 API"""
    print("\n" + "=" * 60)
    print("测试: POST /api/files/download")
    print("=" * 60)
    
    all_pass = True
    
    # 测试 1: 缺少文件ID
    print("\n[测试 4.1] 缺少文件ID应返回错误")
    try:
        resp = requests.post(f"{BASE_URL}/api/files/download", json={}, timeout=10)
        data = resp.json()
        if resp.status_code == 400:
            print_result("返回400错误", True)
        elif not data.get('success'):
            print_result("返回失败", True, data.get('message'))
        else:
            print_result("返回400错误", False, "期望400但得到成功")
    except Exception as e:
        print_result("返回失败", False, str(e))
        all_pass = False
    
    # 测试 2: 下载不存在的文件
    print("\n[测试 4.2] 下载不存在的文件 (file_ids=[99999])")
    try:
        resp = requests.post(f"{BASE_URL}/api/files/download", 
                            json={"file_ids": [99999]}, timeout=10)
        if resp.status_code == 404:
            print_result("返回404错误", True)
        elif resp.status_code == 200:
            print_result("返回文件", False, "期望404但得到文件")
        else:
            print_result("返回404错误", False, f"状态码: {resp.status_code}")
    except Exception as e:
        print_result("返回失败", False, str(e))
        all_pass = False
    
    return all_pass

def main():
    """主测试函数"""
    print("=" * 60)
    print("BioData Manager - 文件管理 API 测试")
    print(f"测试地址: {BASE_URL}")
    print("=" * 60)
    
    results = []
    
    results.append(("获取已导入项目列表 API", test_get_imported_projects()))
    results.append(("获取项目文件列表 API", test_get_project_files()))
    results.append(("删除文件 API", test_delete_files()))
    results.append(("下载文件 API", test_download_files()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_pass = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status}  {name}")
        if not passed:
            all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("所有测试通过!")
    else:
        print("部分测试失败，请检查错误信息")
    print("=" * 60)
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
