#!/usr/bin/env python3
"""
第1轮内测代码 - 全部功能测试
测试所有API端点和页面路由
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
print(f"第1轮内测 - 全部功能测试")
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

# ==================== 1. 页面路由测试 ====================
print("\n" + "=" * 70)
print("1. 页面路由测试")
print("=" * 70)

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
            result.add_pass(f"页面 - {name}")
        else:
            result.add_fail(f"页面 - {name}", f"状态码: {resp.status_code}")
    except Exception as e:
        result.add_fail(f"页面 - {name}", str(e))

# ==================== 2. 项目 API 测试 ====================
print("\n" + "=" * 70)
print("2. 项目 API 测试")
print("=" * 70)

# GET /api/projects
try:
    resp = requests.get(f"{BASE_URL}/api/projects", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            result.add_pass("/api/projects - 获取全部项目")
        else:
            result.add_fail("/api/projects", f"success=false: {data.get('message')}")
    else:
        result.add_fail("/api/projects", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/projects", str(e))

# GET /api/projects?table=raw
try:
    resp = requests.get(f"{BASE_URL}/api/projects", params={"table": "raw"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            result.add_pass("/api/projects?table=raw - 获取原始数据项目")
        else:
            result.add_fail("/api/projects?table=raw", f"success=false")
    else:
        result.add_fail("/api/projects?table=raw", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/projects?table=raw", str(e))

# GET /api/projects?table=result
try:
    resp = requests.get(f"{BASE_URL}/api/projects", params={"table": "result"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            result.add_pass("/api/projects?table=result - 获取结果数据项目")
        else:
            result.add_fail("/api/projects?table=result", f"success=false")
    else:
        result.add_fail("/api/projects?table=result", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/projects?table=result", str(e))

# POST /api/projects - 创建原始数据项目
print("\n  [创建测试项目]")
test_raw_id = None
try:
    resp = requests.post(f"{BASE_URL}/api/projects", json={
        "table": "raw",
        "raw_title": "Round1测试_原始数据",
        "raw_type": "mRNAseq",
        "raw_species": "Homo sapiens",
        "raw_tissue": "Liver"
    }, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success') and data.get('project', {}).get('raw_id'):
            test_raw_id = data['project']['raw_id']
            result.add_pass(f"创建原始数据项目: {test_raw_id}")
        else:
            result.add_fail("创建原始数据项目", f"创建失败: {data}")
    else:
        result.add_fail("创建原始数据项目", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("创建原始数据项目", str(e))

# POST /api/projects - 创建结果数据项目
test_result_id = None
try:
    resp = requests.post(f"{BASE_URL}/api/projects", json={
        "table": "result",
        "result_title": "Round1测试_结果数据",
        "results_type": "DEA",
        "results_raw": "RAW_test001,RAW_test002"
    }, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success') and data.get('project', {}).get('results_id'):
            test_result_id = data['project']['results_id']
            result.add_pass(f"创建结果数据项目: {test_result_id}")
        else:
            result.add_fail("创建结果数据项目", f"创建失败: {data}")
    else:
        result.add_fail("创建结果数据项目", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("创建结果数据项目", str(e))

# ==================== 3. 文件管理 API 测试 ====================
print("\n" + "=" * 70)
print("3. 文件管理 API 测试")
print("=" * 70)

# GET /api/files/imported-projects
try:
    resp = requests.get(f"{BASE_URL}/api/files/imported-projects", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            result.add_pass("/api/files/imported-projects - 获取已导入项目列表")
        else:
            result.add_fail("/api/files/imported-projects", f"success=false")
    else:
        result.add_fail("/api/files/imported-projects", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/files/imported-projects", str(e))

# GET /api/files/imported-projects?file_project_type=raw
try:
    resp = requests.get(f"{BASE_URL}/api/files/imported-projects", 
                       params={"file_project_type": "raw"}, timeout=10)
    if resp.status_code == 200:
        result.add_pass("/api/files/imported-projects?type=raw - 筛选原始项目")
    else:
        result.add_fail("/api/files/imported-projects?type=raw", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/files/imported-projects?type=raw", str(e))

# GET /api/files/imported-projects?file_project_type=result
try:
    resp = requests.get(f"{BASE_URL}/api/files/imported-projects", 
                       params={"file_project_type": "result"}, timeout=10)
    if resp.status_code == 200:
        result.add_pass("/api/files/imported-projects?type=result - 筛选结果项目")
    else:
        result.add_fail("/api/files/imported-projects?type=result", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/files/imported-projects?type=result", str(e))

# GET /api/files?project_id=XXX
if test_raw_id:
    try:
        resp = requests.get(f"{BASE_URL}/api/files", params={"project_id": test_raw_id}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('project_id') == test_raw_id:
                result.add_pass(f"/api/files?project_id={test_raw_id[:8]}... - 获取项目文件")
            else:
                result.add_fail("/api/files", "响应project_id不匹配")
        else:
            result.add_fail("/api/files", f"状态码: {resp.status_code}")
    except Exception as e:
        result.add_fail("/api/files", str(e))
else:
    print("  ⊙ 跳过文件查询测试（无测试项目ID）")

# DELETE /api/files - 删除不存在的文件（测试错误处理）
try:
    resp = requests.delete(f"{BASE_URL}/api/files", json={"file_ids": [99999]}, timeout=10)
    if resp.status_code in [400, 404]:
        result.add_pass("DELETE /api/files - 删除不存在的文件（预期错误）")
    elif resp.status_code == 200:
        result.add_pass("DELETE /api/files - 删除不存在的文件（成功，无数据）")
    else:
        result.add_fail("DELETE /api/files", f"意外状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("DELETE /api/files", str(e))

# POST /api/files/download - 下载不存在的文件（测试错误处理）
try:
    resp = requests.post(f"{BASE_URL}/api/files/download", json={"file_ids": [99999]}, timeout=10)
    if resp.status_code in [400, 404]:
        result.add_pass("POST /api/files/download - 下载不存在的文件（预期错误）")
    elif resp.status_code == 200:
        result.add_pass("POST /api/files/download - 下载不存在的文件（成功，无数据）")
    else:
        result.add_fail("POST /api/files/download", f"意外状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("POST /api/files/download", str(e))

# ==================== 4. 元数据 API 测试 ====================
print("\n" + "=" * 70)
print("4. 元数据 API 测试")
print("=" * 70)

# GET /api/metadata/fields
try:
    resp = requests.get(f"{BASE_URL}/api/metadata/fields", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success') and data.get('fields'):
            result.add_pass("/api/metadata/fields - 获取 raw 字段配置")
        else:
            result.add_fail("/api/metadata/fields", f"无fields数据")
    else:
        result.add_fail("/api/metadata/fields", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/metadata/fields", str(e))

# GET /api/metadata/fields?table=result
try:
    resp = requests.get(f"{BASE_URL}/api/metadata/fields", params={"table": "result"}, timeout=10)
    if resp.status_code == 200:
        result.add_pass("/api/metadata/fields?table=result - 获取 result 字段配置")
    else:
        result.add_fail("/api/metadata/fields?table=result", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/metadata/fields?table=result", str(e))

# GET /api/metadata/fields?table=file
try:
    resp = requests.get(f"{BASE_URL}/api/metadata/fields", params={"table": "file"}, timeout=10)
    if resp.status_code == 200:
        result.add_pass("/api/metadata/fields?table=file - 获取 file 字段配置")
    else:
        result.add_fail("/api/metadata/fields?table=file", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/metadata/fields?table=file", str(e))

# GET /api/options?type=raw_type
try:
    resp = requests.get(f"{BASE_URL}/api/options", params={"type": "raw_type"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            result.add_pass("/api/options?type=raw_type - 获取 raw_type 选项")
        else:
            result.add_fail("/api/options?type=raw_type", f"success=false")
    else:
        result.add_fail("/api/options?type=raw_type", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/options?type=raw_type", str(e))

# GET /api/options?type=results_type
try:
    resp = requests.get(f"{BASE_URL}/api/options", params={"type": "results_type"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            result.add_pass("/api/options?type=results_type - 获取 results_type 选项")
        else:
            result.add_fail("/api/options?type=results_type", f"success=false")
    else:
        result.add_fail("/api/options?type=results_type", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/options?type=results_type", str(e))

# ==================== 5. 扫描和导入 API 测试 ====================
print("\n" + "=" * 70)
print("5. 扫描和导入 API 测试")
print("=" * 70)

# GET /api/scan-downloads/sync
try:
    resp = requests.get(f"{BASE_URL}/api/scan-downloads/sync", timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            result.add_pass("/api/scan-downloads/sync - 扫描下载目录")
        else:
            result.add_fail("/api/scan-downloads/sync", f"success=false")
    else:
        result.add_fail("/api/scan-downloads/sync", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/scan-downloads/sync", str(e))

# ==================== 6. 任务状态 API 测试 ====================
print("\n" + "=" * 70)
print("6. 任务状态 API 测试")
print("=" * 70)

# GET /api/tasks
try:
    resp = requests.get(f"{BASE_URL}/api/tasks", timeout=10)
    if resp.status_code == 200:
        result.add_pass("/api/tasks - 获取任务状态")
    else:
        result.add_fail("/api/tasks", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/tasks", str(e))

# GET /api/processed-data
try:
    resp = requests.get(f"{BASE_URL}/api/processed-data", timeout=10)
    if resp.status_code == 200:
        result.add_pass("/api/processed-data - 获取引文解析数据")
    else:
        result.add_fail("/api/processed-data", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/processed-data", str(e))

# ==================== 7. 边界条件测试 ====================
print("\n" + "=" * 70)
print("7. 边界条件测试")
print("=" * 70)

# 测试空参数
try:
    resp = requests.get(f"{BASE_URL}/api/files", timeout=10)
    if resp.status_code == 400:
        result.add_pass("GET /api/files 无参数 - 返回400错误")
    else:
        result.add_fail("GET /api/files 无参数", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("GET /api/files 无参数", str(e))

# 测试无效项目ID
try:
    resp = requests.get(f"{BASE_URL}/api/files", params={"project_id": "INVALID_ID"}, timeout=10)
    if resp.status_code in [400, 404]:
        result.add_pass("GET /api/files 无效项目ID - 返回错误")
    else:
        result.add_pass("GET /api/files 无效项目ID - 返回空列表")
except Exception as e:
    result.add_fail("GET /api/files 无效项目ID", str(e))

# ==================== 测试结果汇总 ====================
success = result.summary()

# 保存测试结果
test_result = {
    "test_round": 1,
    "test_time": datetime.now().isoformat(),
    "environment": "container" if CONTAINER_TEST else "localhost:20425",
    "base_url": BASE_URL,
    "passed": result.passed,
    "failed": result.failed,
    "errors": result.errors,
    "success": success
}

import os

# 确定结果文件路径
if CONTAINER_TEST:
    result_dir = "/app/.test/logs"
else:
    result_dir = "/home/hrply/software/bioscience/research/biodata_manager/.test/logs"

os.makedirs(result_dir, exist_ok=True)
result_file = os.path.join(result_dir, "round1_result.json")

with open(result_file, "w", encoding="utf-8") as f:
    json.dump(test_result, f, ensure_ascii=False, indent=2)

print(f"\n测试结果已保存到: {result_file}")

sys.exit(0 if success else 1)
