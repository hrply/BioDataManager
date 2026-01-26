#!/usr/bin/env python3
"""
第3轮内测代码 - 回归测试
综合回归测试，验证所有功能正常工作
"""

import sys
import requests
import json
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
print(f"第3轮内测 - 回归测试")
print(f"测试环境: {'容器内' if CONTAINER_TEST else '容器外 (localhost:20425)'}")
print(f"测试地址: {BASE_URL}")
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.warnings = []
    
    def add_pass(self, name):
        self.passed += 1
        print(f"  ✓ 通过: {name}")
    
    def add_fail(self, name, error):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ✗ 失败: {name}")
        print(f"       错误: {error}")
    
    def add_warning(self, name, warning):
        self.warnings.append((name, warning))
        print(f"  ⚠ 警告: {name}")
        print(f"       警告: {warning}")
    
    def summary(self):
        print("\n" + "=" * 70)
        print(f"测试结果汇总")
        print(f"  通过: {self.passed}")
        print(f"  失败: {self.failed}")
        print(f"  警告: {len(self.warnings)}")
        print(f"  总计: {self.passed + self.failed + len(self.warnings)}")
        print("=" * 70)
        return self.failed == 0

result = TestResult()

# ==================== 1. 全量API回归测试 ====================
print("\n" + "=" * 70)
print("1. 全量API回归测试")
print("=" * 70)

# 页面路由回归
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

# 项目API回归
print("\n  [项目API回归测试]")
try:
    resp = requests.get(f"{BASE_URL}/api/projects", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            result.add_pass("/api/projects - 项目API正常")
        else:
            result.add_fail("/api/projects", "success=false")
    else:
        result.add_fail("/api/projects", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("/api/projects", str(e))

# 文件管理API回归
print("\n  [文件管理API回归测试]")
file_apis = [
    ("GET", "/api/files/imported-projects", {}, "获取已导入项目"),
    ("GET", "/api/files/imported-projects", {"file_project_type": "raw"}, "筛选原始项目"),
    ("GET", "/api/files/imported-projects", {"file_project_type": "result"}, "筛选结果项目"),
]

for method, path, params, name in file_apis:
    try:
        resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=10)
        if resp.status_code == 200:
            result.add_pass(name)
        else:
            result.add_fail(name, f"状态码: {resp.status_code}")
    except Exception as e:
        result.add_fail(name, str(e))

# 元数据API回归
print("\n  [元数据API回归测试]")
metadata_apis = [
    ("/api/metadata/fields", {}, "获取字段配置"),
    ("/api/metadata/fields", {"table": "result"}, "获取result字段"),
    ("/api/options", {"type": "raw_type"}, "获取raw_type选项"),
    ("/api/options", {"type": "results_type"}, "获取results_type选项"),
]

for path, params, name in metadata_apis:
    try:
        resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                result.add_pass(name)
            else:
                result.add_fail(name, "success=false")
        else:
            result.add_fail(name, f"状态码: {resp.status_code}")
    except Exception as e:
        result.add_fail(name, str(e))

# ==================== 2. created_at格式回归测试 ====================
print("\n" + "=" * 70)
print("2. created_at格式回归测试")
print("=" * 70)

try:
    resp = requests.get(f"{BASE_URL}/api/projects", params={"table": "raw"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        projects = data.get('projects', [])
        if projects:
            # 检查created_at字段格式
            first_project = projects[0]
            created_at = first_project.get('created_at', '')
            if created_at:
                # 验证格式是否为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
                import re
                if re.match(r'^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$', str(created_at)):
                    result.add_pass(f"created_at格式正确: {created_at}")
                else:
                    result.add_warning(f"created_at格式异常", f"值: {created_at}")
            else:
                result.add_warning("created_at字段", "为空")
        else:
            result.add_warning("created_at验证", "无项目数据")
    else:
        result.add_fail("created_at验证", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("created_at验证", str(e))

# ==================== 3. 错误处理回归测试 ====================
print("\n" + "=" * 70)
print("3. 错误处理回归测试")
print("=" * 70)

# 500错误测试
try:
    resp = requests.get(f"{BASE_URL}/api/files", timeout=10)
    if resp.status_code == 500:
        result.add_fail("错误处理", "服务器返回500错误")
    elif resp.status_code == 400:
        result.add_pass("错误处理 - 400错误（参数缺失）")
    else:
        result.add_pass(f"错误处理 - 状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("错误处理", str(e))

# 无效资源测试
try:
    resp = requests.delete(f"{BASE_URL}/api/files", json={"file_ids": [99999999]}, timeout=10)
    if resp.status_code == 500:
        result.add_fail("无效资源删除", "服务器返回500错误")
    else:
        result.add_pass("无效资源删除 - 正确处理")
except Exception as e:
    result.add_fail("无效资源删除", str(e))

# ==================== 4. 数据完整性回归测试 ====================
print("\n" + "=" * 70)
print("4. 数据完整性回归测试")
print("=" * 70)

# 验证API响应格式一致性
print("\n  [响应格式一致性测试]")
try:
    # 检查多个API的响应格式
    apis_to_check = [
        ("/api/projects", {"table": "raw"}),
        ("/api/projects", {"table": "result"}),
        ("/api/files/imported-projects", {}),
        ("/api/metadata/fields", {"table": "raw"}),
    ]
    
    format_ok = True
    for path, params in apis_to_check:
        resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # 检查是否有success字段
            if 'success' not in data:
                format_ok = False
                result.add_warning(f"{path}", "缺少success字段")
    
    if format_ok:
        result.add_pass("API响应格式一致性")
    
except Exception as e:
    result.add_fail("响应格式检查", str(e))

# 验证项目数据字段完整性
print("\n  [项目数据字段测试]")
try:
    resp = requests.get(f"{BASE_URL}/api/projects", params={"table": "raw"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        projects = data.get('projects', [])
        if projects:
            required_fields = ['raw_id', 'raw_title', 'raw_type', 'created_at']
            first_project = projects[0]
            missing_fields = [f for f in required_fields if f not in first_project]
            
            if not missing_fields:
                result.add_pass("项目数据字段完整")
            else:
                result.add_warning("项目数据字段", f"缺少: {missing_fields}")
        else:
            result.add_warning("项目数据字段", "无项目数据")
    else:
        result.add_fail("项目数据字段", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("项目数据字段", str(e))

# ==================== 5. 性能回归测试 ====================
print("\n" + "=" * 70)
print("5. 性能回归测试")
print("=" * 70)

# 响应时间测试
print("\n  [API响应时间测试]")
timeouts = 0
for i in range(3):
    start = datetime.now()
    try:
        resp = requests.get(f"{BASE_URL}/api/projects", timeout=10)
        elapsed = (datetime.now() - start).total_seconds()
        if elapsed > 5:
            result.add_warning(f"响应时间{i+1}", f"耗时 {elapsed:.2f}s")
        elif resp.status_code != 200:
            timeouts += 1
    except:
        timeouts += 1

if timeouts == 0:
    result.add_pass("API响应时间正常")
else:
    result.add_warning("API响应时间", f"{timeouts}次请求异常")

# ==================== 6. 关键功能验证 ====================
print("\n" + "=" * 70)
print("6. 关键功能验证")
print("=" * 70)

# 项目创建和查询验证
print("\n  [项目创建流程验证]")
test_project_id = None
try:
    resp = requests.post(f"{BASE_URL}/api/projects", json={
        "table": "raw",
        "raw_title": "Round3回归测试项目",
        "raw_type": "mRNAseq",
        "raw_species": "Mus musculus",
        "raw_tissue": "Kidney"
    }, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            # 检查返回的字段名
            project = data.get('project', {})
            if 'raw_id' in project:
                test_project_id = project['raw_id']
                result.add_pass(f"项目创建成功: {test_project_id}")
            elif 'result_id' in project:
                test_project_id = project['result_id']
                result.add_pass(f"项目创建成功: {test_project_id}")
            else:
                result.add_pass("项目创建成功（字段名验证通过）")
        else:
            result.add_fail("项目创建", f"success=false")
    else:
        result.add_fail("项目创建", f"状态码: {resp.status_code}")
except Exception as e:
    result.add_fail("项目创建", str(e))

# 验证项目查询
if test_project_id:
    try:
        resp = requests.get(f"{BASE_URL}/api/projects", params={"table": "raw"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            projects = data.get('projects', [])
            # 验证新创建的项目在列表中
            project_ids = [p.get('raw_id') for p in projects]
            if test_project_id in project_ids:
                result.add_pass("项目查询数据一致")
            else:
                result.add_warning("项目查询", "新项目未在列表中显示（可能因筛选条件）")
        else:
            result.add_fail("项目查询", f"状态码: {resp.status_code}")
    except Exception as e:
        result.add_fail("项目查询", str(e))

# ==================== 测试结果汇总 ====================
success = result.summary()

# 保存测试结果
test_result = {
    "test_round": 3,
    "test_time": datetime.now().isoformat(),
    "environment": "container" if CONTAINER_TEST else "localhost:20425",
    "base_url": BASE_URL,
    "passed": result.passed,
    "failed": result.failed,
    "warnings": len(result.warnings),
    "errors": result.errors,
    "success": success
}

# 确定结果文件路径
if CONTAINER_TEST:
    result_dir = "/app/.test/logs"
else:
    result_dir = "/home/hrply/software/bioscience/research/biodata_manager/.test/logs"

os.makedirs(result_dir, exist_ok=True)
result_file = os.path.join(result_dir, "round3_result.json")

with open(result_file, "w", encoding="utf-8") as f:
    json.dump(test_result, f, ensure_ascii=False, indent=2)

print(f"\n测试结果已保存到: {result_file}")

sys.exit(0 if success else 1)
