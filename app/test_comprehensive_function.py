#!/usr/bin/env python3
"""
综合功能内测代码
测试文件下载、删除、导入、逗号处理、关联字段等功能

执行方式: python3 test_comprehensive_function.py
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

# 添加 app 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from database_mysql import DatabaseManager

# 配置 - 容器内使用服务名，容器外使用 localhost
import os
if os.path.exists("/.dockerenv"):
    BASE_URL = "http://biodata-manager:5000"  # 容器内
else:
    BASE_URL = "http://localhost:20425"  # 容器外映射端口

TEST_DATA_DIR = Path("/home/hrply/software/bioscience/research/biodata_manager/data/downloads/test_import")
RECYCLE_DIR = Path("/bio/recycle")

# 测试结果存储
TEST_RESULTS = {
    "start_time": datetime.now().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "blocked": 0
    }
}

def log_test(tc_id, name, status, message="", details=None):
    """记录测试结果"""
    result = {
        "tc_id": tc_id,
        "name": name,
        "status": status,  # passed, failed, blocked
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    TEST_RESULTS["tests"].append(result)
    TEST_RESULTS["summary"]["total"] += 1
    if status == "passed":
        TEST_RESULTS["summary"]["passed"] += 1
        print(f"✅ {tc_id}: {name} - PASSED")
    elif status == "failed":
        TEST_RESULTS["summary"]["failed"] += 1
        print(f"❌ {tc_id}: {name} - FAILED: {message}")
    else:
        TEST_RESULTS["summary"]["blocked"] += 1
        print(f"⚠️ {tc_id}: {name} - BLOCKED: {message}")
    
    if details:
        print(f"   Details: {json.dumps(details, ensure_ascii=False, indent=2)}")

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
        return e.code, {"success": False, "message": str(e)}
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

def get_db():
    """获取数据库连接"""
    return DatabaseManager()

def cleanup_test_data():
    """清理测试数据"""
    db = get_db()
    # 删除测试项目
    db.execute("DELETE FROM file_record WHERE file_project_id LIKE 'TEST_%'")
    db.execute("DELETE FROM raw_project WHERE raw_id LIKE 'TEST_RAW_%'")
    db.execute("DELETE FROM result_project WHERE results_id LIKE 'TEST_RES_%'")
    print("🧹 测试数据清理完成")

def ensure_test_files():
    """确保测试文件存在"""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    test_files = [
        "sample.fastq",
        "test_raw_001.fastq", 
        "test_raw_002.fastq",
        "test_res_001.txt",
        "test_res_002.txt"
    ]
    for f in test_files:
        fpath = TEST_DATA_DIR / f
        if not fpath.exists():
            fpath.write_text(f"Test file content for {f}\n")
            print(f"📄 创建测试文件: {fpath}")
    print("✅ 测试文件准备完成")

# ==================== 3.1 文件下载功能测试 ====================

def test_download_single_file():
    """TC-DL-001: 单文件下载测试"""
    tc_id = "TC-DL-001"
    
    # 获取项目
    status, resp = api_get("/api/projects", {"table": "raw"})
    if not resp.get("success") or not resp.get("data"):
        log_test(tc_id, "单文件下载", "blocked", "无项目数据")
        return
    
    project = resp["data"][0]
    project_id = project.get("raw_id")
    
    # 获取文件列表
    status, resp = api_get("/api/files", {"project_id": project_id})
    if not resp.get("success") or not resp.get("files"):
        log_test(tc_id, "单文件下载", "blocked", "项目无文件")
        return
    
    file_id = resp["files"][0]["id"]
    file_name = resp["files"][0]["file_name"]
    file_path = Path("/bio") / resp["files"][0]["file_path"] / file_name
    
    # 计算原始文件 MD5
    original_md5 = ""
    if file_path.exists():
        original_md5 = hashlib.md5(file_path.read_bytes()).hexdigest()
    
    # 下载文件 - 使用特殊的下载处理
    try:
        url = f"{BASE_URL}/api/files/download"
        json_data = json.dumps({"file_ids": [file_id]}).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            status = resp.status
            content = resp.read()
            content_type = resp.headers.get("Content-Type")
            
            if status == 200 and content_type == "application/zip":
                import io
                import zipfile
                
                zip_file = io.BytesIO(content)
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    if file_name in zf.namelist():
                        log_test(tc_id, "单文件下载", "passed", "下载成功", {
                            "file_id": file_id,
                            "file_name": file_name,
                            "content_type": content_type
                        })
                    else:
                        log_test(tc_id, "单文件下载", "failed", "ZIP内无目标文件", {
                            "zip_contents": zf.namelist()
                        })
            else:
                log_test(tc_id, "单文件下载", "failed", f"响应异常: {status}", {
                    "content_type": content_type
                })
    except urllib.error.HTTPError as e:
        log_test(tc_id, "单文件下载", "failed", f"HTTP错误: {e.code}", {"message": str(e)})

def test_download_multiple_files():
    """TC-DL-002: 多文件打包下载测试"""
    tc_id = "TC-DL-002"
    
    # 获取项目
    status, resp = api_get("/api/projects", {"table": "raw"})
    if not resp.get("success") or not resp.get("data"):
        log_test(tc_id, "多文件下载", "blocked", "无项目数据")
        return
    
    project = resp["data"][0]
    project_id = project.get("raw_id")
    
    # 获取文件列表
    status, resp = api_get("/api/files", {"project_id": project_id})
    if not resp.get("success") or len(resp.get("files", [])) < 2:
        log_test(tc_id, "多文件下载", "blocked", "项目文件少于2个")
        return
    
    files = resp["files"][:3]
    file_ids = [f["id"] for f in files]
    
    # 下载 - 使用特殊的下载处理
    try:
        url = f"{BASE_URL}/api/files/download"
        json_data = json.dumps({"file_ids": file_ids}).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            status = resp.status
            content = resp.read()
            
            if status == 200:
                import io
                import zipfile
                
                zip_file = io.BytesIO(content)
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    downloaded_names = zf.namelist()
                    expected_names = [f["file_name"] for f in files]
                    
                    all_found = all(name in downloaded_names for name in expected_names)
                    if all_found:
                        log_test(tc_id, "多文件下载", "passed", "多文件打包成功", {
                            "requested_files": expected_names,
                            "downloaded_files": downloaded_names
                        })
                    else:
                        log_test(tc_id, "多文件下载", "failed", "部分文件缺失", {
                            "expected": expected_names,
                            "actual": downloaded_names
                        })
            else:
                log_test(tc_id, "多文件下载", "failed", f"响应异常: {status}")
    except urllib.error.HTTPError as e:
        log_test(tc_id, "多文件下载", "failed", f"HTTP错误: {e.code}", {"message": str(e)})

def test_download_nonexistent_file():
    """TC-DL-003: 下载不存在的文件测试"""
    tc_id = "TC-DL-003"
    
    status, resp = api_post("/api/files/download", {"file_ids": [99999]})
    
    if status == 404 and not resp.get("success"):
        log_test(tc_id, "下载不存在文件", "passed", "正确返回404", {"message": resp.get("message")})
    else:
        log_test(tc_id, "下载不存在文件", "failed", "未正确返回错误", {"status": status, "response": resp})

# ==================== 3.2 文件删除功能测试 ====================

def test_delete_file_to_recycle():
    """TC-DEL-001: 删除文件到回收站测试"""
    tc_id = "TC-DEL-001"
    
    # 获取项目
    status, resp = api_get("/api/projects", {"table": "raw"})
    if not resp.get("success") or not resp.get("data"):
        log_test(tc_id, "删除到回收站", "blocked", "无项目数据")
        return
    
    project = resp["data"][0]
    project_id = project.get("raw_id")
    
    # 获取文件列表
    status, resp = api_get("/api/files", {"project_id": project_id})
    if not resp.get("success") or not resp.get("files"):
        log_test(tc_id, "删除到回收站", "blocked", "项目无文件")
        return
    
    file_record = resp["files"][0]
    file_id = file_record["id"]
    file_name = file_record["file_name"]
    file_path = Path("/bio") / file_record["file_path"] / file_name
    
    # 记录原始文件存在
    original_exists = file_path.exists()
    
    # 删除
    status, resp = api_post("/api/files", {"file_ids": [file_id]})
    
    if resp.get("success"):
        # 检查原始文件是否删除
        original_deleted = not file_path.exists()
        
        # 检查回收站文件是否存在
        recycle_path = RECYCLE_DIR / file_record["file_path"] / file_name
        recycle_exists = recycle_path.exists()
        
        if original_deleted and recycle_exists:
            log_test(tc_id, "删除到回收站", "passed", "文件移动成功", {
                "original_deleted": original_deleted,
                "recycle_exists": recycle_exists,
                "recycle_path": str(recycle_path)
            })
        else:
            log_test(tc_id, "删除到回收站", "failed", "文件未正确移动", {
                "original_deleted": original_deleted,
                "recycle_exists": recycle_exists
            })
    else:
        log_test(tc_id, "删除到回收站", "failed", f"删除失败: {resp.get('message')}")

def test_delete_file_record_update():
    """TC-DEL-002: 删除后记录同步更新测试"""
    tc_id = "TC-DEL-002"
    
    # 获取项目
    status, resp = api_get("/api/projects", {"table": "raw"})
    if not resp.get("success") or not resp.get("data"):
        log_test(tc_id, "记录同步更新", "blocked", "无项目数据")
        return
    
    project = resp["data"][0]
    project_id = project.get("raw_id")
    
    # 获取文件列表
    status, resp = api_get("/api/files", {"project_id": project_id})
    if not resp.get("success") or not resp.get("files"):
        log_test(tc_id, "记录同步更新", "blocked", "项目无文件")
        return
    
    files_before = len(resp["files"])
    file_id = resp["files"][0]["id"]
    
    # 删除
    status, resp = api_post("/api/files", {"file_ids": [file_id]})
    
    if resp.get("success"):
        # 检查文件列表
        status2, resp2 = api_get("/api/files", {"project_id": project_id})
        files_after = len(resp2.get("files", []))
        
        if files_after == files_before - 1:
            log_test(tc_id, "记录同步更新", "passed", "文件记录正确删除", {
                "files_before": files_before,
                "files_after": files_after
            })
        else:
            log_test(tc_id, "记录同步更新", "failed", "文件计数未更新", {
                "files_before": files_before,
                "files_after": files_after
            })
    else:
        log_test(tc_id, "记录同步更新", "failed", f"删除失败: {resp.get('message')}")

def test_delete_nonexistent_file():
    """TC-DEL-003: 删除不存在的文件测试"""
    tc_id = "TC-DEL-003"
    
    status, resp = api_post("/api/files", {"file_ids": [99999]})
    
    if status == 404 and not resp.get("success"):
        log_test(tc_id, "删除不存在文件", "passed", "正确返回404", {"message": resp.get("message")})
    else:
        log_test(tc_id, "删除不存在文件", "failed", "未正确返回错误", {"status": status, "response": resp})

# ==================== 3.3 导入功能测试 ====================

def test_import_to_existing_raw_project():
    """TC-IMP-001: 导入到已有原始数据项目测试"""
    tc_id = "TC-IMP-001"
    
    # 获取项目
    status, resp = api_get("/api/projects", {"table": "raw"})
    if not resp.get("success") or not resp.get("data"):
        log_test(tc_id, "导入到已有项目", "blocked", "无项目数据")
        return
    
    project = resp["data"][0]
    project_id = project.get("raw_id")
    
    # 获取当前 metadata
    status, orig_resp = api_get(f"/api/projects/raw/{project_id}")
    if not orig_resp.get("success"):
        log_test(tc_id, "导入到已有项目", "blocked", "无法获取项目信息")
        return
    
    orig_type = orig_resp.get("project", {}).get("raw_type", "")
    
    # 导入文件
    status, resp = api_post("/api/import-download", {
        "project_id": project_id,
        "files": ["test_raw_001.fastq"],
        "folder_name": "test_import",
        "metadata_override": {
            "raw_type": "蛋白组",
            "raw_species": "Mus musculus",
            "raw_tissue": "Liver"
        },
        "data_type": "raw"
    })
    
    if resp.get("success"):
        # 检查 metadata 是否更新
        status2, new_resp = api_get(f"/api/projects/raw/{project_id}")
        if new_resp.get("success"):
            new_type = new_resp.get("project", {}).get("raw_type", "")
            new_species = new_resp.get("project", {}).get("raw_species", "")
            new_tissue = new_resp.get("project", {}).get("raw_tissue", "")
            
            if "蛋白组" in new_type and "Mus musculus" in new_species and "Liver" in new_tissue:
                log_test(tc_id, "导入到已有项目", "passed", "metadata_override 正确合并", {
                    "raw_type_before": orig_type,
                    "raw_type_after": new_type,
                    "raw_species": new_species,
                    "raw_tissue": new_tissue
                })
            else:
                log_test(tc_id, "导入到已有项目", "failed", "metadata 未正确更新", {
                    "expected_type": "包含 蛋白组",
                    "actual_type": new_type
                })
        else:
            log_test(tc_id, "导入到已有项目", "failed", "无法获取更新后的项目信息")
    else:
        log_test(tc_id, "导入到已有项目", "failed", f"导入失败: {resp.get('message')}")

def test_import_path_generation():
    """TC-IMP-003: 导入路径生成测试"""
    tc_id = "TC-IMP-003"
    
    # 获取项目
    status, resp = api_get("/api/projects", {"table": "raw"})
    if not resp.get("success") or not resp.get("data"):
        log_test(tc_id, "路径生成", "blocked", "无项目数据")
        return
    
    project = resp["data"][0]
    project_id = project.get("raw_id")
    
    # 导入文件
    status, resp = api_post("/api/import-download", {
        "project_id": project_id,
        "files": ["test_raw_002.fastq"],
        "folder_name": "test_import",
        "metadata_override": {
            "raw_type": "mRNAseq",
            "raw_species": "Homo sapiens",
            "raw_tissue": "Liver"
        },
        "data_type": "raw"
    })
    
    if resp.get("success"):
        # 获取文件记录
        status2, files_resp = api_get("/api/files", {"project_id": project_id})
        if files_resp.get("success") and files_resp.get("files"):
            file_record = files_resp["files"][-1]  # 最新导入的文件
            file_path = file_record.get("file_path", "")
            file_property = file_record.get("file_property", "")
            
            # 验证路径格式
            path_valid = "/bio/rawdata/" in file_path
            # 验证属性格式（使用英文逗号）
            prop_valid = "," not in file_property and "-" in file_property
            
            if path_valid:
                log_test(tc_id, "路径生成", "passed", "路径格式正确", {
                    "file_path": file_path,
                    "file_property": file_property
                })
            else:
                log_test(tc_id, "路径生成", "failed", "路径格式错误", {
                    "file_path": file_path
                })
        else:
            log_test(tc_id, "路径生成", "failed", "无法获取文件记录")
    else:
        log_test(tc_id, "路径生成", "failed", f"导入失败: {resp.get('message')}")

# ==================== 3.4 逗号分隔处理测试 ====================

def test_comma_chinese_to_english():
    """TC-COMMA-001: 中文逗号转英文测试"""
    tc_id = "TC-COMMA-001"
    
    # 创建项目，使用中文逗号
    status, resp = api_post("/api/projects", {
        "table": "raw",
        "raw_title": "逗号测试项目",
        "raw_type": "mRNAseq,蛋白组",
        "raw_species": "Homo sapiens，Mus musculus",
        "raw_tissue": "Liver，Kidney"
    })
    
    if resp.get("success"):
        project_id = resp.get("project", {}).get("raw_id") or resp.get("project", {}).get("id")
        if project_id:
            # 获取项目信息
            status2, proj_resp = api_get(f"/api/projects/raw/{project_id}")
            if proj_resp.get("success"):
                project = proj_resp.get("project", {})
                species = project.get("raw_species", "")
                tissue = project.get("raw_tissue", "")
                
                # 验证中文逗号已转换为英文
                has_chinese_comma_s = "，" in species
                has_chinese_comma_t = "，" in tissue
                
                if not has_chinese_comma_s and not has_chinese_comma_t:
                    log_test(tc_id, "中文逗号转换", "passed", "中文逗号已转换为英文", {
                        "raw_species": species,
                        "raw_tissue": tissue
                    })
                else:
                    log_test(tc_id, "中文逗号转换", "failed", "存在未转换的中文逗号", {
                        "raw_species": species,
                        "raw_tissue": tissue
                    })
            else:
                log_test(tc_id, "中文逗号转换", "blocked", "无法获取项目信息")
        else:
            log_test(tc_id, "中文逗号转换", "blocked", "无法获取项目ID")
    else:
        log_test(tc_id, "中文逗号转换", "failed", f"创建项目失败: {resp.get('message')}")

def test_comma_storage_format():
    """TC-COMMA-002: 多值存储格式测试"""
    tc_id = "TC-COMMA-002"
    
    # 直接查询数据库验证存储格式
    db = get_db()
    result = db.query("SELECT raw_species, raw_tissue FROM raw_project WHERE raw_title = '逗号测试项目'")
    
    if result:
        row = result[0]
        species = row[0] or ""
        tissue = row[1] or ""
        
        # 检查逗号格式
        has_english_comma = "," in species or "," in tissue
        has_spaces = " , " in species or " ," in species or " , " in tissue or " ," in tissue
        
        if has_english_comma and not has_spaces:
            log_test(tc_id, "存储格式", "passed", "使用英文逗号，无多余空格", {
                "raw_species": species,
                "raw_tissue": tissue
            })
        else:
            log_test(tc_id, "存储格式", "failed", "存储格式不正确", {
                "raw_species": species,
                "raw_tissue": tissue
            })
    else:
        log_test(tc_id, "存储格式", "blocked", "未找到测试项目")

# ==================== 3.5 关联项目字段测试 ====================

def test_results_raw_storage():
    """TC-REF-001: results_raw 存储格式测试"""
    tc_id = "TC-REF-001"
    
    # 创建结果项目
    status, resp = api_post("/api/projects", {
        "table": "result",
        "results_title": "关联字段测试",
        "results_type": "DEA",
        "results_raw": "RAW_A,RAW_B,RAW_C"
    })
    
    if resp.get("success"):
        project_id = resp.get("project", {}).get("results_id") or resp.get("project", {}).get("id")
        if project_id:
            # 获取项目信息
            status2, proj_resp = api_get(f"/api/projects/result/{project_id}")
            if proj_resp.get("success"):
                results_raw = proj_resp.get("project", {}).get("results_raw", "")
                
                if "RAW_A" in results_raw and "RAW_B" in results_raw and "RAW_C" in results_raw:
                    log_test(tc_id, "results_raw存储", "passed", "逗号分隔存储正确", {
                        "results_raw": results_raw
                    })
                else:
                    log_test(tc_id, "results_raw存储", "failed", "存储格式错误", {
                        "results_raw": results_raw
                    })
            else:
                log_test(tc_id, "results_raw存储", "blocked", "无法获取项目信息")
        else:
            log_test(tc_id, "results_raw存储", "blocked", "无法获取项目ID")
    else:
        log_test(tc_id, "results_raw存储", "failed", f"创建项目失败: {resp.get('message')}")

def test_results_raw_sorting():
    """TC-REF-002: results_raw 排序逻辑测试"""
    tc_id = "TC-REF-002"
    
    # 创建项目，使用未排序的 ID
    status, resp = api_post("/api/projects", {
        "table": "result",
        "results_title": "排序测试",
        "results_type": "DEA",
        "results_raw": "RAW_z,RAW_A,RAW_B,RAW_1"
    })
    
    if resp.get("success"):
        project_id = resp.get("project", {}).get("results_id") or resp.get("project", {}).get("id")
        if project_id:
            # 获取项目信息
            status2, proj_resp = api_get(f"/api/projects/result/{project_id}")
            if proj_resp.get("success"):
                results_raw = proj_resp.get("project", {}).get("results_raw", "")
                
                # ASCII 排序: 数字 < 大写字母 < 小写字母
                # 期望: RAW_1,RAW_A,RAW_B,RAW_z
                expected = "RAW_1,RAW_A,RAW_B,RAW_z"
                
                if results_raw == expected:
                    log_test(tc_id, "results_raw排序", "passed", "按ASCII排序正确", {
                        "input": "RAW_z,RAW_A,RAW_B,RAW_1",
                        "output": results_raw
                    })
                else:
                    log_test(tc_id, "results_raw排序", "failed", "排序不正确", {
                        "expected": expected,
                        "actual": results_raw
                    })
            else:
                log_test(tc_id, "results_raw排序", "blocked", "无法获取项目信息")
        else:
            log_test(tc_id, "results_raw排序", "blocked", "无法获取项目ID")
    else:
        log_test(tc_id, "results_raw排序", "failed", f"创建项目失败: {resp.get('message')}")

def test_results_raw_deduplication():
    """TC-REF-003: results_raw 去重逻辑测试"""
    tc_id = "TC-REF-003"
    
    # 先创建项目
    status, resp = api_post("/api/projects", {
        "table": "result",
        "results_title": "去重测试",
        "results_type": "DEA",
        "results_raw": "RAW_X,RAW_Y"
    })
    
    if resp.get("success"):
        project_id = resp.get("project", {}).get("results_id") or resp.get("project", {}).get("id")
        if project_id:
            # 追加关联项目（包含重复）
            status2, append_resp = api_post(f"/api/projects/result/{project_id}/metadata", {
                "field_id": "results_raw",
                "new_value": "RAW_Y,RAW_Z,RAW_W"
            })
            
            if append_resp.get("success"):
                # 获取项目信息
                status3, proj_resp = api_get(f"/api/projects/result/{project_id}")
                if proj_resp.get("success"):
                    results_raw = proj_resp.get("project", {}).get("results_raw", "")
                    
                    # 期望: RAW_X,RAW_Y,RAW_Z,RAW_W (RAW_Y 不重复)
                    expected = "RAW_X,RAW_Y,RAW_Z,RAW_W"
                    
                    if results_raw == expected:
                        log_test(tc_id, "results_raw去重", "passed", "去重逻辑正确", {
                            "before": "RAW_X,RAW_Y",
                            "append": "RAW_Y,RAW_Z,RAW_W",
                            "after": results_raw
                        })
                    else:
                        log_test(tc_id, "results_raw去重", "failed", "去重不正确", {
                            "expected": expected,
                            "actual": results_raw
                        })
                else:
                    log_test(tc_id, "results_raw去重", "blocked", "无法获取项目信息")
            else:
                log_test(tc_id, "results_raw去重", "failed", f"追加失败: {append_resp.get('message')}")
        else:
            log_test(tc_id, "results_raw去重", "blocked", "无法获取项目ID")
    else:
        log_test(tc_id, "results_raw去重", "failed", f"创建项目失败: {resp.get('message')}")

# ==================== 主执行流程 ====================

def main():
    print("=" * 60)
    print("🧪 BioData Manager 综合功能内测")
    print("=" * 60)
    
    # 准备环境
    print("\n📋 准备测试环境...")
    cleanup_test_data()
    ensure_test_files()
    
    # 等待服务就绪
    print("⏳ 等待服务就绪...")
    max_retries = 5
    for i in range(max_retries):
        try:
            status, resp = api_get("/api/projects")
            if resp.get("success"):
                print("✅ 服务已就绪")
                break
        except:
            pass
        time.sleep(2)
    else:
        print("❌ 服务无法访问，测试终止")
        return
    
    # 执行测试
    print("\n" + "=" * 60)
    print("📊 3.1 文件下载功能测试")
    print("=" * 60)
    test_download_single_file()
    test_download_multiple_files()
    test_download_nonexistent_file()
    
    print("\n" + "=" * 60)
    print("📊 3.2 文件删除功能测试")
    print("=" * 60)
    test_delete_file_to_recycle()
    test_delete_file_record_update()
    test_delete_nonexistent_file()
    
    print("\n" + "=" * 60)
    print("📊 3.3 导入功能测试")
    print("=" * 60)
    test_import_to_existing_raw_project()
    test_import_path_generation()
    
    print("\n" + "=" * 60)
    print("📊 3.4 逗号分隔处理测试")
    print("=" * 60)
    test_comma_chinese_to_english()
    test_comma_storage_format()
    
    print("\n" + "=" * 60)
    print("📊 3.5 关联项目字段测试")
    print("=" * 60)
    test_results_raw_storage()
    test_results_raw_sorting()
    test_results_raw_deduplication()
    
    # 输出汇总
    print("\n" + "=" * 60)
    print("📈 测试结果汇总")
    print("=" * 60)
    summary = TEST_RESULTS["summary"]
    print(f"总测试数: {summary['total']}")
    print(f"通过: {summary['passed']} ✅")
    print(f"失败: {summary['failed']} ❌")
    print(f"阻塞: {summary['blocked']} ⚠️")
    print(f"通过率: {summary['passed']/summary['total']*100:.1f}%" if summary['total'] > 0 else "N/A")
    
    # 保存结果
    TEST_RESULTS["end_time"] = datetime.now().isoformat()
    results_path = Path(__file__).parent / "results" / f"comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(TEST_RESULTS, f, ensure_ascii=False, indent=2)
    print(f"\n📄 结果已保存: {results_path}")
    
    # 返回退出码
    sys.exit(0 if summary['failed'] == 0 else 1)

if __name__ == "__main__":
    main()
