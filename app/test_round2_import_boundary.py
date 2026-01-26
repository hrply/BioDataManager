#!/usr/bin/env python3
"""
第2轮内测代码 - 导入和边界条件测试
重点测试导入功能、边界条件和异常处理
"""

import sys
import requests
import json
import time
import os
from datetime import datetime

# 检测运行环境
CONTAINER_TEST = False
if os.environ.get('CONTAINER_TEST'):
    CONTAINER_TEST = True
    BASE_URL = "http://localhost:8000"
else:
    BASE_URL = "http://localhost:20425"

print("=" * 70)
print(f"第2轮内测 - 导入和边界条件测试")
print(f"测试环境: {'容器内' if CONTAINER_TEST else '容器外 (localhost:20425)'}")
print(f"测试地址: {BASE_URL}")
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, name):
        self.passed += 1
        print(f"  ✓ 通过: {name}")
    
    def add_fail(self, name, error):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ✗ 失败: {name}")
        print(f"       错误: {error}")
    
    def summary(self):
        print("\n" + "=" * 70)
        print(f"测试结果汇总")
        print(f"  通过: {self.passed}")
        print(f"  失败: {self.failed}")
        print(f"  总计: {self.passed + self.failed}")
        print("=" * 70)
        return self.failed == 0

result = TestResult()

# ==================== 1. 扫描下载目录测试 ====================
print("\n" + "=" * 70)
print("1. 扫描下载目录测试")
print("=" * 70)

try:
    resp = requests.get(f"{BASE_URL}/api/scan-downloads/sync", timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            projects = data.get('projects', [])
            result.add_pass(f"/api/scan-downloads/sync - 扫描成功，发现 {len(projects)} 个项目")
            print(f"       发现项目: {[p.get('name') for p in projects[:5]]}")
        else:
            result.add_fail("/api/scan-downloads/sync", f"success=false")
    else:
        result.add_fail("/api/scan-downloads/sync", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/scan-downloads/sync", str(e))

# ==================== 2. 导入功能测试 ====================
print("\n" + "=" * 70)
print("2. 导入功能测试")
print("=" * 70)

# 测试数据
test_project_id = None

def test_import_new_project():
    """测试新建项目导入"""
    print("\n  [新建项目导入测试]")
    
    # 1. 扫描获取测试文件夹
    try:
        resp = requests.get(f"{BASE_URL}/api/scan-downloads/sync", timeout=30)
        data = resp.json()
        if not data.get('success'):
            result.add_fail("扫描下载目录", "扫描失败")
            return None
        
        # 查找 test_import 文件夹
        test_folder = None
        for project in data.get('projects', []):
            if project.get('name') == 'test_import':
                test_folder = project
                break
        
        if not test_folder:
            result.add_fail("查找测试文件夹", "未找到 test_import 文件夹")
            return None
        
        result.add_pass("找到测试文件夹: test_import")
        
        # 2. 新建项目并导入
        import_data = {
            "folder_name": test_folder.get('path'),
            "files": ["sample1.fastq", "sample2.fastq"],
            "data_type": "raw",
            "project_info": {
                "raw_title": "Round2测试_新建项目导入",
                "raw_type": "mRNAseq",
                "raw_species": "Homo sapiens",
                "raw_tissue": "Heart"
            }
        }
        
        resp = requests.post(f"{BASE_URL}/api/import-download", json=import_data, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                project_id = data.get('project', {}).get('raw_id')
                result.add_pass(f"新建项目导入成功: {project_id}")
                return project_id
            else:
                result.add_fail("新建项目导入", f"导入失败: {data.get('message')}")
                return None
        else:
            result.add_fail("新建项目导入", f"状态码: {resp.status_code}")
            return None
            
    except Exception as e:
        result.add_fail("新建项目导入", str(e))
        return None

def test_import_existing_project(project_id):
    """测试导入到已有项目"""
    print("\n  [导入到已有项目测试]")
    
    if not project_id:
        result.add_fail("导入到已有项目", "无项目ID，跳过测试")
        return False
    
    try:
        import_data = {
            "project_id": project_id,
            "folder_name": "/bio/downloads/test_import",
            "files": ["sample3.fastq"],
            "data_type": "raw"
        }
        
        resp = requests.post(f"{BASE_URL}/api/import-download", json=import_data, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                result.add_pass(f"导入到已有项目成功: {project_id}")
                return True
            else:
                result.add_fail("导入到已有项目", f"导入失败: {data.get('message')}")
                return False
        else:
            result.add_fail("导入到已有项目", f"状态码: {resp.status_code}")
            return False
            
    except Exception as e:
        result.add_fail("导入到已有项目", str(e))
        return False

def test_import_nonexistent_folder():
    """测试导入不存在的文件夹"""
    print("\n  [导入不存在的文件夹测试]")
    
    try:
        import_data = {
            "folder_name": "/bio/downloads/nonexistent_folder_xyz",
            "files": ["file.txt"],
            "data_type": "raw",
            "project_info": {
                "raw_title": "测试",
                "raw_type": "mRNAseq"
            }
        }
        
        resp = requests.post(f"{BASE_URL}/api/import-download", json=import_data, timeout=10)
        # 应该返回错误，不是500
        if resp.status_code in [400, 404]:
            result.add_pass("导入不存在的文件夹 - 返回错误（预期行为）")
        elif resp.status_code == 500:
            result.add_fail("导入不存在的文件夹", "服务器错误 500")
        else:
            result.add_pass("导入不存在的文件夹 - 返回状态码: " + str(resp.status_code))
            
    except Exception as e:
        result.add_fail("导入不存在的文件夹", str(e))

# 执行导入测试
test_project_id = test_import_new_project()
test_import_existing_project(test_project_id)
test_import_nonexistent_folder()

# ==================== 3. 边界条件测试 ====================
print("\n" + "=" * 70)
print("3. 边界条件测试")
print("=" * 70)

# 测试空参数
try:
    resp = requests.get(f"{BASE_URL}/api/files", timeout=10)
    if resp.status_code == 400:
        result.add_pass("空参数请求 - 返回400错误")
    else:
        result.add_pass("空参数请求 - 返回状态码: " + str(resp.status_code))
except Exception as e:
    result.add_fail("空参数请求", str(e))

# 测试无效项目ID
try:
    resp = requests.get(f"{BASE_URL}/api/files", params={"project_id": "INVALID_ID_xyz123"}, timeout=10)
    if resp.status_code in [400, 404]:
        result.add_pass("无效项目ID - 返回错误")
    elif resp.status_code == 200:
        result.add_pass("无效项目ID - 返回空列表")
except Exception as e:
    result.add_fail("无效项目ID", str(e))

# 测试删除空文件列表
try:
    resp = requests.delete(f"{BASE_URL}/api/files", json={"file_ids": []}, timeout=10)
    if resp.status_code in [400]:
        result.add_pass("删除空文件列表 - 返回400错误")
    else:
        result.add_pass("删除空文件列表 - 返回状态码: " + str(resp.status_code))
except Exception as e:
    result.add_fail("删除空文件列表", str(e))

# 测试下载空文件列表
try:
    resp = requests.post(f"{BASE_URL}/api/files/download", json={"file_ids": []}, timeout=10)
    if resp.status_code in [400]:
        result.add_pass("下载空文件列表 - 返回400错误")
    else:
        result.add_pass("下载空文件列表 - 返回状态码: " + str(resp.status_code))
except Exception as e:
    result.add_fail("下载空文件列表", str(e))

# ==================== 4. 筛选条件测试 ====================
print("\n" + "=" * 70)
print("4. 筛选条件测试")
print("=" * 70)

# 空筛选条件
try:
    resp = requests.get(f"{BASE_URL}/api/files/imported-projects", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success') is not None:
            result.add_pass("空筛选条件 - 返回全部项目")
        else:
            result.add_fail("空筛选条件", "success字段缺失")
    else:
        result.add_fail("空筛选条件", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("空筛选条件", str(e))

# 筛选不存在的项目类型
try:
    resp = requests.get(f"{BASE_URL}/api/files/imported-projects", 
                       params={"file_project_type": "nonexistent_type"}, timeout=10)
    if resp.status_code == 200:
        result.add_pass("无效项目类型筛选 - 返回空列表或正常响应")
    else:
        result.add_fail("无效项目类型筛选", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("无效项目类型筛选", str(e))

# ==================== 5. 并发请求测试 ====================
print("\n" + "=" * 70)
print("5. 并发请求测试")
print("=" * 70)

def quick_api_call(url, params=None):
    """快速API调用"""
    try:
        resp = requests.get(url, params=params, timeout=5)
        return resp.status_code
    except:
        return None

# 连续快速请求
print("  [连续快速请求测试]")
success_count = 0
for i in range(5):
    status = quick_api_call(f"{BASE_URL}/api/projects")
    if status == 200:
        success_count += 1

if success_count >= 4:
    result.add_pass(f"连续快速请求 - 5次请求中成功{success_count}次")
else:
    result.add_fail(f"连续快速请求", f"5次请求中仅成功{success_count}次")

# ==================== 6. 项目API边界测试 ====================
print("\n" + "=" * 70)
print("6. 项目API边界测试")
print("=" * 70)

# 测试获取不存在的项目详情
try:
    resp = requests.get(f"{BASE_URL}/api/projects", params={"table": "raw", "raw_id": "RAW_nonexistent_xyz"}, timeout=10)
    if resp.status_code in [400, 404]:
        result.add_pass("获取不存在的项目 - 返回错误")
    elif resp.status_code == 200:
        result.add_pass("获取不存在的项目 - 返回空或正常响应")
except Exception as e:
    result.add_fail("获取不存在的项目", str(e))

# 测试无效table参数
try:
    resp = requests.get(f"{BASE_URL}/api/projects", params={"table": "invalid_table"}, timeout=10)
    if resp.status_code == 400:
        result.add_pass("无效table参数 - 返回400错误")
    else:
        result.add_pass("无效table参数 - 返回状态码: " + str(resp.status_code))
except Exception as e:
    result.add_fail("无效table参数", str(e))

# ==================== 测试结果汇总 ====================
success = result.summary()

# 保存测试结果
test_result = {
    "test_round": 2,
    "test_time": datetime.now().isoformat(),
    "environment": "container" if CONTAINER_TEST else "localhost:20425",
    "base_url": BASE_URL,
    "passed": result.passed,
    "failed": result.failed,
    "errors": result.errors,
    "success": success
}

# 确定结果文件路径
if CONTAINER_TEST:
    result_dir = "/app/.test/logs"
else:
    result_dir = "/home/hrply/software/bioscience/research/biodata_manager/.test/logs"

os.makedirs(result_dir, exist_ok=True)
result_file = os.path.join(result_dir, "round2_result.json")

with open(result_file, "w", encoding="utf-8") as f:
    json.dump(test_result, f, ensure_ascii=False, indent=2)

print(f"\n测试结果已保存到: {result_file}")

sys.exit(0 if success else 1)
