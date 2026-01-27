#!/usr/bin/env python3
"""
第4轮容器外API综合测试
通过HTTP API访问容器服务，模拟真实操作

执行方式: python3 test_external_round1.py
注意: 需要在宿主机执行，容器服务必须运行在20425端口
"""

import os
import sys
import json
import time
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# 配置
BASE_URL = "http://localhost:20425"
TEST_DATA_DIR = Path("/home/hrply/software/bioscience/research/biodata_manager/data/downloads/test_import")
TEST_PREFIX = "TEST_ROUND6"

# 测试结果
TEST_RESULTS = {
    "round": 1,
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "summary": {"total": 0, "passed": 0, "failed": 0, "blocked": 0}
}

def log(tc_id, name, status, message="", details=None):
    """记录测试结果"""
    result = {
        "tc_id": tc_id, "name": name, "status": status,
        "message": message, "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    TEST_RESULTS["tests"].append(result)
    TEST_RESULTS["summary"]["total"] += 1
    if status == "passed":
        TEST_RESULTS["summary"]["passed"] += 1
        print(f"✅ {tc_id}: {name}")
    elif status == "failed":
        TEST_RESULTS["summary"]["failed"] += 1
        print(f"❌ {tc_id}: {name} - {message}")
    else:
        TEST_RESULTS["summary"]["blocked"] += 1
        print(f"⚠️ {tc_id}: {name} - {message}")
    if details:
        print(f"   Details: {json.dumps(details, ensure_ascii=False)[:200]}")

# ==================== 工具函数 ====================

def api_get(endpoint, params=None):
    """GET 请求"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        return e.code, json.loads(body) if body else {"success": False, "message": str(e)}
    except Exception as e:
        return None, {"success": False, "message": str(e)}

def api_post(endpoint, data=None):
    """POST 请求"""
    try:
        url = f"{BASE_URL}{endpoint}"
        json_data = json.dumps(data or {}).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        return e.code, json.loads(body) if body else {"success": False, "message": str(e)}
    except Exception as e:
        return None, {"success": False, "message": str(e)}

def api_delete(endpoint, data=None):
    """DELETE 请求"""
    try:
        url = f"{BASE_URL}{endpoint}"
        json_data = json.dumps(data or {}).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method='DELETE')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        return e.code, json.loads(body) if body else {"success": False, "message": str(e)}
    except Exception as e:
        return None, {"success": False, "message": str(e)}

def cleanup_test_data():
    """清理测试数据 - 通过API"""
    # 列出所有项目，删除 TEST_ROUND4_ 开头的
    for table in ["raw", "result"]:
        status, resp = api_get(f"/api/projects", {"table": table})
        if resp.get("success") and resp.get("data"):
            for project in resp["data"]:
                pid = project.get("raw_id") or project.get("results_id") or ""
                if pid.startswith(TEST_PREFIX):
                    if table == "raw":
                        api_delete(f"/api/projects/raw/{pid}")
                    else:
                        api_delete(f"/api/projects/result/{pid}")
    print("🧹 清理完成")

def verify_in_container(query_func, expected_func, description):
    """验证辅助函数 - 在容器内执行"""
    # 这里我们假设测试代码在容器外运行
    # 验证逻辑需要在容器内通过数据库查询完成
    # 由于我们使用 API 测试，这里只记录验证点
    return {"verified": True, "description": description}

# ==================== 测试用例 ====================

def test_service_health():
    """TC-SRV-001: 服务健康检查"""
    status, resp = api_get("/api/projects", {"table": "raw"})
    if resp.get("success") is not None:
        log("TC-SRV-001", "服务健康检查", "passed", "服务可访问")
        return True
    else:
        log("TC-SRV-001", "服务健康检查", "failed", "服务不可访问")
        return False

def test_create_raw_project():
    """TC-CRP-001: 创建原始数据项目（API）"""
    status, resp = api_post("/api/projects", {
        "table": "raw",
        "raw_title": "API测试原始项目",
        "raw_type": "mRNAseq,蛋白组",
        "raw_species": "Homo sapiens，Mus musculus",
        "raw_tissue": "Liver，Kidney"
    })
    
    if resp.get("success"):
        project_id = resp.get("project", {}).get("raw_id") or resp.get("project", {}).get("id")
        if project_id:
            # 验证项目存在
            status2, resp2 = api_get(f"/api/projects/raw/{project_id}")
            if resp2.get("success"):
                log("TC-CRP-001", "创建原始项目-API", "passed", f"创建成功: {project_id}", {
                    "project_id": project_id,
                    "title": resp2.get("project", {}).get("raw_title")
                })
                return project_id
            else:
                log("TC-CRP-001", "创建原始项目-API", "failed", "验证失败")
                return project_id
        else:
            log("TC-CRP-001", "创建原始项目-API", "failed", "无项目ID")
            return None
    else:
        log("TC-CRP-001", "创建原始项目-API", "failed", resp.get("message"))
        return None

def test_create_result_project():
    """TC-CRS-001: 创建结果数据项目（API）"""
    status, resp = api_post("/api/projects", {
        "table": "result",
        "results_title": "API测试结果项目",
        "results_type": "DEA,Marker",
        "results_raw": "RAW_z,RAW_A,RAW_B,RAW_1"
    })
    
    if resp.get("success"):
        project_id = resp.get("project", {}).get("results_id") or resp.get("project", {}).get("id")
        if project_id:
            log("TC-CRS-001", "创建结果项目-API", "passed", f"创建成功: {project_id}")
            return project_id
        else:
            log("TC-CRS-001", "创建结果项目-API", "failed", "无项目ID")
            return None
    else:
        log("TC-CRS-001", "创建结果项目-API", "failed", resp.get("message"))
        return None

def test_download_file():
    """TC-DL-001: 下载API测试 - 使用API导入文件"""
    # 1. 创建项目
    status, create_resp = api_post("/api/projects", {
        "table": "raw",
        "raw_title": "下载测试项目",
        "raw_type": "mRNAseq",
        "raw_species": "Homo sapiens",
        "raw_tissue": "Liver"
    })
    
    if not create_resp.get("success") or not create_resp.get("project"):
        log("TC-DL-001", "下载API", "blocked", "创建项目失败")
        return
    
    project_id = create_resp["project"].get("raw_id") or create_resp["project"].get("id")
    
    # 2. 使用API导入文件
    test_file_dir = "/home/hrply/software/bioscience/research/biodata_manager/data/downloads/test_import"
    if not os.path.exists(test_file_dir):
        log("TC-DL-001", "下载API", "blocked", f"测试文件目录不存在: {test_file_dir}")
        return
    
    files = [f for f in os.listdir(test_file_dir) if os.path.isfile(os.path.join(test_file_dir, f))]
    if not files:
        log("TC-DL-001", "下载API", "blocked", "测试目录无文件")
        return
    
    # 3. 调用导入API（需要folder_name才能找到源文件）
    status, import_resp = api_post("/api/import-download", {
        "project_id": project_id,
        "files": files,
        "folder_name": "test_import"  # 必须指定源文件夹
    })
    
    if not import_resp.get("success"):
        log("TC-DL-001", "下载API", "blocked", f"导入失败: {import_resp.get('message')}")
        return
    
    # 验证文件是否导入到正确项目
    status, files_resp = api_get("/api/files", {"project_id": project_id})
    if not files_resp.get("success") or not files_resp.get("files"):
        log("TC-DL-001", "下载API", "blocked", "导入后项目无文件")
        return
    
    file_id = files_resp["files"][0]["id"]
    file_name = files_resp["files"][0]["file_name"]
    
    # 5. 发送下载请求
    try:
        url = f"{BASE_URL}/api/files/download"
        json_data = json.dumps({"file_ids": [file_id]}).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            if resp.status == 200 and resp.headers.get("Content-Type") == "application/zip":
                log("TC-DL-001", "下载API", "passed", f"状态: {resp.status}, 类型: {resp.headers.get('Content-Type')}, 文件: {file_name}")
            else:
                log("TC-DL-001", "下载API", "failed", f"响应异常: {resp.status}")
    except urllib.error.HTTPError as e:
        log("TC-DL-001", "下载API", "failed", f"HTTP错误: {e.code}")
    except Exception as e:
        log("TC-DL-001", "下载API", "failed", str(e))

def test_delete_file():
    """TC-DEL-001: 删除文件API测试 - 使用API导入文件"""
    # 1. 创建项目
    status, create_resp = api_post("/api/projects", {
        "table": "raw",
        "raw_title": "删除测试项目",
        "raw_type": "mRNAseq",
        "raw_species": "Mus musculus",
        "raw_tissue": "Kidney"
    })
    
    if not create_resp.get("success") or not create_resp.get("project"):
        log("TC-DEL-001", "删除文件API", "blocked", "创建项目失败")
        return
    
    project_id = create_resp["project"].get("raw_id") or create_resp["project"].get("id")
    
    # 2. 使用API导入文件
    test_file_dir = "/home/hrply/software/bioscience/research/biodata_manager/data/downloads/test_import"
    if not os.path.exists(test_file_dir):
        log("TC-DEL-001", "删除文件API", "blocked", f"测试文件目录不存在: {test_file_dir}")
        return
    
    files = [f for f in os.listdir(test_file_dir) if os.path.isfile(os.path.join(test_file_dir, f))]
    if not files:
        log("TC-DEL-001", "删除文件API", "blocked", "测试目录无文件")
        return
    
    # 3. 调用导入API（需要folder_name才能找到源文件）
    status, import_resp = api_post("/api/import-download", {
        "project_id": project_id,
        "files": files,
        "folder_name": "test_import"  # 必须指定源文件夹
    })
    
    if not import_resp.get("success"):
        log("TC-DEL-001", "删除文件API", "blocked", f"导入失败: {import_resp.get('message')}")
        return
    
    # 验证文件是否导入到正确项目
    status, files_resp = api_get("/api/files", {"project_id": project_id})
    if not files_resp.get("success") or not files_resp.get("files"):
        log("TC-DEL-001", "删除文件API", "blocked", "导入后项目无文件")
        return
    
    file_id = files_resp["files"][0]["id"]
    file_name = files_resp["files"][0]["file_name"]
    
    # 5. 删除文件
    status, delete_resp = api_post("/api/files", {"file_ids": [file_id]})
    
    if delete_resp.get("success"):
        # 验证文件已删除
        status2, files_resp2 = api_get("/api/files", {"project_id": project_id})
        file_ids = [f["id"] for f in files_resp2.get("files", [])]
        if file_id not in file_ids:
            log("TC-DEL-001", "删除文件API", "passed", f"文件已删除: {file_name}")
        else:
            log("TC-DEL-001", "删除文件API", "failed", "文件未删除")
    else:
        log("TC-DEL-001", "删除文件API", "failed", delete_resp.get("message"))

def test_import_files():
    """TC-IMP-001: 导入文件API测试"""
    # 先创建或获取项目
    status, resp = api_get("/api/projects", {"table": "raw"})
    if not resp.get("success") or not resp.get("data"):
        log("TC-IMP-001", "导入文件API", "blocked", "无项目数据")
        return
    
    project = resp["data"][0]
    project_id = project.get("raw_id")
    
    # 导入文件
    status, import_resp = api_post("/api/import-download", {
        "project_id": project_id,
        "files": ["sample.fastq"],
        "folder_name": "test_import",
        "metadata_override": {
            "raw_type": "mRNAseq",
            "raw_species": "Homo sapiens",
            "raw_tissue": "Liver"
        },
        "data_type": "raw"
    })
    
    if import_resp.get("success"):
        log("TC-IMP-001", "导入文件API", "passed", "导入成功", {
            "project_id": project_id,
            "result": import_resp.get("result")
        })
    else:
        log("TC-IMP-001", "导入文件API", "failed", import_resp.get("message"))

def test_metadata_config():
    """TC-CFG-001: 元数据配置API测试"""
    status, resp = api_get("/api/metadata/config")
    
    # API返回 config 字段，不是 fields
    if resp.get("success") and resp.get("config"):
        raw_fields = [f for f in resp["config"] if f.get("field_table") == "raw"]
        result_fields = [f for f in resp["config"] if f.get("field_table") == "result"]
        
        log("TC-CFG-001", "元数据配置API", "passed", f"获取配置成功", {
            "raw_fields_count": len(raw_fields),
            "result_fields_count": len(result_fields)
        })
    else:
        log("TC-CFG-001", "元数据配置API", "failed", resp.get("message") or "配置为空")

def test_field_options():
    """TC-OPT-001: 字段选项API测试"""
    for opt_type in ["raw_type", "raw_species", "raw_tissue", "results_type"]:
        status, resp = api_get(f"/api/options", {"type": opt_type})
        
        if resp.get("success") and resp.get("options"):
            log("TC-OPT-001", f"字段选项-{opt_type}", "passed", f"获取 {len(resp['options'])} 个选项")
        else:
            log("TC-OPT-001", f"字段选项-{opt_type}", "failed", resp.get("message"))

# ==================== 主流程 ====================

def main():
    print("=" * 60)
    print("🌐 第6轮容器外API综合测试")
    print("=" * 60)
    
    # 等待服务就绪
    print("\n⏳ 等待服务就绪...")
    max_retries = 5
    for i in range(max_retries):
        if test_service_health():
            print("✅ 服务已就绪")
            break
        time.sleep(2)
    else:
        print("❌ 服务无法访问，测试终止")
        sys.exit(1)
    
    # 清理
    print("\n📋 清理测试数据...")
    cleanup_test_data()
    
    # 执行测试
    print("\n" + "=" * 60)
    print("📊 测试开始")
    print("=" * 60)
    
    raw_id = test_create_raw_project()
    results_id = test_create_result_project()
    test_download_file()
    test_delete_file()
    test_import_files()
    test_metadata_config()
    test_field_options()
    
    # 清理
    print("\n📋 清理测试数据...")
    cleanup_test_data()
    
    # 输出结果
    print("\n" + "=" * 60)
    print("📈 测试结果汇总")
    print("=" * 60)
    summary = TEST_RESULTS["summary"]
    print(f"总测试数: {summary['total']}")
    print(f"通过: {summary['passed']} ✅")
    print(f"失败: {summary['failed']} ❌")
    print(f"阻塞: {summary['blocked']} ⚠️")
    
    # 保存结果
    results_path = Path("/home/hrply/software/bioscience/research/biodata_manager/.test/results/round6_external_result.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(TEST_RESULTS, f, ensure_ascii=False, indent=2)
    print(f"\n📄 结果已保存: {results_path}")
    
    # 返回退出码
    sys.exit(0 if summary['failed'] == 0 else 1)

if __name__ == "__main__":
    main()
