#!/usr/bin/env python3
"""
全面 API 测试脚本
测试所有 API 端点，检查错误和异常
"""

import sys
import requests
import json
import os

# 检测运行环境
if os.environ.get('CONTAINER_TEST'):
    BASE_URL = "http://localhost:8000"
else:
    BASE_URL = "http://localhost:20425"

def print_result(test_name, success, message=""):
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"[{status}] {test_name}")
    if message and not success:
        print(f"       错误: {message}")
    return success

def test_all_apis():
    """测试所有 API 端点"""
    print("=" * 60)
    print("全面 API 测试")
    print(f"测试地址: {BASE_URL}")
    print("=" * 60)
    
    all_pass = True
    results = []
    
    # ==================== 页面路由测试 ====================
    print("\n" + "=" * 60)
    print("1. 页面路由测试")
    print("=" * 60)
    
    pages = [
        ("/", "首页"),
        ("/files", "文件管理"),
        ("/raw-data", "原始数据"),
        ("/results", "结果管理"),
        ("/metadata", "元数据管理"),
    ]
    
    for path, name in pages:
        try:
            resp = requests.get(f"{BASE_URL}{path}", timeout=10)
            if resp.status_code == 200:
                results.append((f"页面 - {name}", True))
            else:
                print_result(f"页面 - {name}", False, f"状态码: {resp.status_code}")
                all_pass = False
        except Exception as e:
            print_result(f"页面 - {name}", False, str(e))
            all_pass = False
    
    # ==================== 项目 API 测试 ====================
    print("\n" + "=" * 60)
    print("2. 项目 API 测试")
    print("=" * 60)
    
    # 测试 /api/projects
    try:
        resp = requests.get(f"{BASE_URL}/api/projects", timeout=10)
        data = resp.json()
        results.append(("/api/projects", data.get('success', False)))
    except Exception as e:
        print_result("/api/projects", False, str(e))
        all_pass = False
    
    # 测试 /api/projects?table=raw
    try:
        resp = requests.get(f"{BASE_URL}/api/projects", params={"table": "raw"}, timeout=10)
        data = resp.json()
        results.append(("/api/projects?table=raw", data.get('success', False)))
    except Exception as e:
        print_result("/api/projects?table=raw", False, str(e))
        all_pass = False
    
    # 测试 /api/projects?table=result
    try:
        resp = requests.get(f"{BASE_URL}/api/projects", params={"table": "result"}, timeout=10)
        data = resp.json()
        results.append(("/api/projects?table=result", data.get('success', False)))
    except Exception as e:
        print_result("/api/projects?table=result", False, str(e))
        all_pass = False
    
    # ==================== 文件 API 测试 ====================
    print("\n" + "=" * 60)
    print("3. 文件管理 API 测试")
    print("=" * 60)
    
    apis = [
        ("GET", "/api/files/imported-projects", {}, "获取已导入项目列表"),
        ("GET", "/api/files/imported-projects", {"file_project_type": "raw"}, "筛选原始项目"),
        ("GET", "/api/files/imported-projects", {"file_project_type": "result"}, "筛选结果项目"),
        ("GET", "/api/files", {"project_id": "RAW_test001"}, "获取项目文件"),
        ("GET", "/api/files", {}, "缺少参数测试"),
        ("DELETE", "/api/files", {"file_ids": [99999]}, "删除不存在的文件"),
        ("POST", "/api/files/download", {"file_ids": [99999]}, "下载不存在的文件"),
        ("POST", "/api/files/download", {}, "下载缺少参数测试"),
    ]
    
    for method, path, params, name in apis:
        try:
            if method == "GET":
                resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=10)
            elif method == "DELETE":
                resp = requests.delete(f"{BASE_URL}{path}", json=params, timeout=10)
            elif method == "POST":
                resp = requests.post(f"{BASE_URL}{path}", json=params, timeout=10)
            
            # 检查是否返回有效响应（不是 500 错误）
            if resp.status_code == 500:
                print_result(name, False, f"服务器错误 500: {resp.text[:100]}")
                all_pass = False
            else:
                results.append((name, True))
        except Exception as e:
            print_result(name, False, str(e))
            all_pass = False
    
    # ==================== 元数据 API 测试 ====================
    print("\n" + "=" * 60)
    print("4. 元数据 API 测试")
    print("=" * 60)
    
    metadata_apis = [
        ("/api/metadata/fields", {}, "获取 raw 字段"),
        ("/api/metadata/fields", {"table": "raw"}, "获取 raw 字段 (table参数)"),
        ("/api/metadata/fields", {"table": "result"}, "获取 result 字段"),
        ("/api/metadata/fields", {"table": "file"}, "获取 file 字段"),
        ("/api/options", {"type": "raw_type"}, "获取 raw_type 选项"),
        ("/api/options", {"type": "results_type"}, "获取 results_type 选项"),
    ]
    
    for path, params, name in metadata_apis:
        try:
            resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=10)
            data = resp.json()
            if data.get('success'):
                results.append((name, True))
            else:
                print_result(name, False, data.get('message', '未知错误'))
                all_pass = False
        except Exception as e:
            print_result(name, False, str(e))
            all_pass = False
    
    # ==================== 扫描和目录 API 测试 ====================
    print("\n" + "=" * 60)
    print("5. 扫描和目录 API 测试")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{BASE_URL}/api/scan-downloads/sync", timeout=30)
        data = resp.json()
        results.append(("/api/scan-downloads/sync", data.get('success', False)))
    except Exception as e:
        print_result("/api/scan-downloads/sync", False, str(e))
        all_pass = False
    
    # ==================== 任务状态 API 测试 ====================
    print("\n" + "=" * 60)
    print("6. 任务状态 API 测试")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{BASE_URL}/api/tasks", timeout=10)
        data = resp.json()
        results.append(("/api/tasks", data.get('success', False)))
    except Exception as e:
        print_result("/api/tasks", False, str(e))
        all_pass = False
    
    # ==================== 引文解析 API 测试 ====================
    print("\n" + "=" * 60)
    print("7. 引文解析 API 测试")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{BASE_URL}/api/processed-data", timeout=10)
        data = resp.json()
        results.append(("/api/processed-data", data.get('success', False)))
    except Exception as e:
        print_result("/api/processed-data", False, str(e))
        all_pass = False
    
    # ==================== 汇总结果 ====================
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, p in results if p)
    failed = len(results) - passed
    
    for name, p in results:
        status = "✓ 通过" if p else "✗ 失败"
        print(f"  {status}  {name}")
    
    print(f"\n总计: {len(results)} 个测试, {passed} 个通过, {failed} 个失败")
    print("=" * 60)
    
    if all_pass:
        print("✓ 所有测试通过!")
    else:
        print("✗ 部分测试失败，请检查错误信息")
    print("=" * 60)
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(test_all_apis())
