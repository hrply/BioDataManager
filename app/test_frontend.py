#!/usr/bin/env python3
"""
前端功能测试脚本
测试文件管理页面的前端功能
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

def test_page_load():
    """测试页面加载"""
    print("\n" + "=" * 60)
    print("测试: 页面加载")
    print("=" * 60)
    
    all_pass = True
    
    # 测试 1: 访问文件管理页面
    print("\n[测试 1.1] 访问文件管理页面")
    try:
        resp = requests.get(f"{BASE_URL}/files", timeout=10)
        if resp.status_code == 200:
            print_result("页面加载成功", True)
            # 检查页面是否包含必要的元素
            content = resp.text
            if '文件管理' in content:
                print_result("页面标题正确", True)
            else:
                print_result("页面标题正确", False, "未找到'文件管理'标题")
                all_pass = False
            
            if 'api/files/imported-projects' in content:
                print_result("JavaScript API引用存在", True)
            else:
                print_result("JavaScript API引用存在", False, "未找到API引用")
                all_pass = False
        else:
            print_result("页面加载成功", False, f"状态码: {resp.status_code}")
            all_pass = False
    except Exception as e:
        print_result("页面加载成功", False, str(e))
        all_pass = False
    
    return all_pass

def test_api_integration():
    """测试API集成"""
    print("\n" + "=" * 60)
    print("测试: API 集成")
    print("=" * 60)
    
    all_pass = True
    
    # 测试 1: 获取已导入项目列表
    print("\n[测试 2.1] 获取已导入项目列表")
    try:
        resp = requests.get(f"{BASE_URL}/api/files/imported-projects", timeout=10)
        data = resp.json()
        if data.get('success'):
            print_result("API返回成功", True)
            print(f"       项目数量: {data.get('total', 0)}")
        else:
            print_result("API返回成功", False, data.get('message'))
            all_pass = False
    except Exception as e:
        print_result("API返回成功", False, str(e))
        all_pass = False
    
    # 测试 2: 带筛选参数查询
    print("\n[测试 2.2] 带筛选参数查询")
    try:
        resp = requests.get(f"{BASE_URL}/api/files/imported-projects", 
                           params={"file_project_type": "raw"}, timeout=10)
        data = resp.json()
        if data.get('success'):
            print_result("筛选查询成功", True)
            print(f"       筛选后项目数量: {data.get('total', 0)}")
        else:
            print_result("筛选查询成功", False, data.get('message'))
            all_pass = False
    except Exception as e:
        print_result("筛选查询成功", False, str(e))
        all_pass = False
    
    # 测试 3: 获取项目文件
    print("\n[测试 2.3] 获取项目文件")
    try:
        resp = requests.get(f"{BASE_URL}/api/files", 
                           params={"project_id": "RAW_test001"}, timeout=10)
        data = resp.json()
        if data.get('success'):
            print_result("获取文件列表成功", True)
            print(f"       文件数量: {data.get('total', 0)}")
        else:
            print_result("获取文件列表成功", False, data.get('message'))
            all_pass = False
    except Exception as e:
        print_result("获取文件列表成功", False, str(e))
        all_pass = False
    
    return all_pass

def test_api_error_handling():
    """测试API错误处理"""
    print("\n" + "=" * 60)
    print("测试: API 错误处理")
    print("=" * 60)
    
    all_pass = True
    
    # 测试 1: 缺少必需参数
    print("\n[测试 3.1] 缺少必需参数 (project_id)")
    try:
        resp = requests.get(f"{BASE_URL}/api/files", timeout=10)
        if resp.status_code == 400:
            print_result("返回400错误", True)
        else:
            print_result("返回400错误", False, f"状态码: {resp.status_code}")
            all_pass = False
    except Exception as e:
        print_result("返回400错误", False, str(e))
        all_pass = False
    
    # 测试 2: 删除不存在的文件
    print("\n[测试 3.2] 删除不存在的文件")
    try:
        resp = requests.delete(f"{BASE_URL}/api/files", 
                              json={"file_ids": [99999]}, timeout=10)
        if resp.status_code == 404:
            print_result("返回404错误", True)
        else:
            print_result("返回404错误", False, f"状态码: {resp.status_code}")
            all_pass = False
    except Exception as e:
        print_result("返回404错误", False, str(e))
        all_pass = False
    
    return all_pass

def main():
    """主测试函数"""
    print("=" * 60)
    print("BioData Manager - 前端功能测试")
    print(f"测试地址: {BASE_URL}")
    print("=" * 60)
    
    results = []
    
    results.append(("页面加载测试", test_page_load()))
    results.append(("API 集成测试", test_api_integration()))
    results.append(("API 错误处理测试", test_api_error_handling()))
    
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
        print("所有前端测试通过!")
    else:
        print("部分测试失败，请检查错误信息")
    print("=" * 60)
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
