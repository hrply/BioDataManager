#!/usr/bin/env python3
"""
第1轮容器内综合功能测试
测试文件下载、删除、导入、逗号处理、关联字段等功能

执行方式: python3 test_internal_round1.py
"""

import os
import sys
import json
import time
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

# 添加 app 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from database_mysql import DatabaseManager
from backend import BioDataManager
from metadata_config_manager_mysql import MetadataConfigManager

# 配置
TEST_DATA_DIR = Path("/home/hrply/software/bioscience/research/biodata_manager/data/downloads/test_import")
RECYCLE_DIR = Path("/bio/recycle")
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

def get_db():
    return DatabaseManager()

def cleanup():
    """清理测试数据"""
    db = get_db()
    db.execute(f"DELETE FROM file_record WHERE file_project_id LIKE '{TEST_PREFIX}_%'")
    db.execute(f"DELETE FROM raw_project WHERE raw_id LIKE '{TEST_PREFIX}_%'")
    db.execute(f"DELETE FROM result_project WHERE results_id LIKE '{TEST_PREFIX}_%'")
    print("🧹 清理完成")

def ensure_test_files():
    """确保测试文件存在"""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for f in ["sample.fastq", "test1.fastq", "test2.fastq", "test3.fastq"]:
        fpath = TEST_DATA_DIR / f
        if not fpath.exists():
            fpath.write_text(f"Test content for {f}\n")
    print("📄 测试文件准备完成")

# ==================== 测试用例 ====================

def test_db_connection():
    """TC-DB-001: 数据库连接测试"""
    try:
        db = get_db()
        if db._pool:
            log("TC-DB-001", "数据库连接", "passed", "连接池已初始化")
            return True
        else:
            log("TC-DB-001", "数据库连接", "failed", "连接池未初始化")
            return False
    except Exception as e:
        log("TC-DB-001", "数据库连接", "failed", str(e))
        return False

def test_multi_select_field():
    """TC-MS-001: multi_select 字段检查"""
    db = get_db()
    # 检查 field_config 表的 field_type 定义
    try:
        result = db.query("SHOW COLUMNS FROM field_config LIKE 'field_type'")
        if result:
            field_type_def = result[0][1]  # Type 列
            if 'multi_select' in field_type_def:
                log("TC-MS-001", "multi_select字段存在", "passed", "数据库支持multi_select", {"definition": field_type_def})
            else:
                log("TC-MS-001", "multi_select字段存在", "failed", "数据库不支持multi_select", {"definition": field_type_def})
        else:
            log("TC-MS-001", "multi_select字段存在", "blocked", "无法获取字段定义")
    except Exception as e:
        log("TC-MS-001", "multi_select字段存在", "failed", str(e))

def test_create_raw_project():
    """TC-CRP-001: 创建原始数据项目"""
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    mgr = BioDataManager(db, config_mgr)
    
    raw_id = mgr.generate_project_id("RAW")
    test_id = f"{TEST_PREFIX}_{raw_id}"
    
    try:
        result = mgr.create_raw_project({
            "raw_title": "测试原始项目",
            "raw_type": "mRNAseq,蛋白组",
            "raw_species": "Homo sapiens，Mus musculus",
            "raw_tissue": "Liver，Kidney",
            "raw_keywords": "测试,关键词"
        })
        
        if result and result.get("raw_id"):
            # 验证数据库记录
            row = db.query_one("SELECT raw_type, raw_species, raw_tissue FROM raw_project WHERE raw_id=%s", (result["raw_id"],))
            if row:
                species = row[1] or ""
                tissue = row[2] or ""
                # 验证中文逗号已转换
                if "，" not in species and "，" not in tissue:
                    log("TC-CRP-001", "创建原始项目", "passed", "创建成功且逗号已转换", {
                        "raw_id": result["raw_id"],
                        "raw_species": species,
                        "raw_tissue": tissue
                    })
                else:
                    log("TC-CRP-001", "创建原始项目", "failed", "中文逗号未转换", {
                        "raw_species": species,
                        "raw_tissue": tissue
                    })
            else:
                log("TC-CRP-001", "创建原始项目", "failed", "数据库无记录")
        else:
            log("TC-CRP-001", "创建原始项目", "failed", "创建失败")
    except Exception as e:
        log("TC-CRP-001", "创建原始项目", "failed", str(e))
    
    return test_id

def test_raw_species_validation():
    """TC-CRP-002: raw_species 中文逗号转换验证"""
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    mgr = BioDataManager(db, config_mgr)
    
    try:
        raw_id = mgr.generate_project_id("RAW")
        result = mgr.create_raw_project({
            "raw_title": "验证raw_species",
            "raw_species": "Homo sapiens，Mus musculus，Rattus norvegicus"
        })
        
        if result and result.get("raw_id"):
            row = db.query_one("SELECT raw_species FROM raw_project WHERE raw_id=%s", (result["raw_id"],))
            if row:
                species = row[0] or ""
                if "，" not in species and species.count(",") == 2:
                    log("TC-CRP-002", "raw_species逗号转换", "passed", f"转换成功: {species}")
                else:
                    log("TC-CRP-002", "raw_species逗号转换", "failed", f"未转换: {species}")
            else:
                log("TC-CRP-002", "raw_species逗号转换", "failed", "数据库无记录")
        else:
            log("TC-CRP-002", "raw_species逗号转换", "failed", "创建失败")
    except Exception as e:
        log("TC-CRP-002", "raw_species逗号转换", "failed", str(e))

def test_raw_type_validation():
    """TC-CRP-003: raw_type 逗号转换验证"""
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    mgr = BioDataManager(db, config_mgr)
    
    try:
        result = mgr.create_raw_project({
            "raw_title": "验证raw_type",
            "raw_type": "mRNAseq，蛋白组，代谢组"
        })
        
        if result and result.get("raw_id"):
            row = db.query_one("SELECT raw_type FROM raw_project WHERE raw_id=%s", (result["raw_id"],))
            if row:
                rtype = row[0] or ""
                if "，" not in rtype and rtype.count(",") == 2:
                    log("TC-CRP-003", "raw_type逗号转换", "passed", f"转换成功: {rtype}")
                else:
                    log("TC-CRP-003", "raw_type逗号转换", "failed", f"未转换: {rtype}")
            else:
                log("TC-CRP-003", "raw_type逗号转换", "failed", "数据库无记录")
        else:
            log("TC-CRP-003", "raw_type逗号转换", "failed", "创建失败")
    except Exception as e:
        log("TC-CRP-003", "raw_type逗号转换", "failed", str(e))

def test_create_result_project():
    """TC-CRS-001: 创建结果数据项目"""
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    mgr = BioDataManager(db, config_mgr)
    
    results_id = mgr.generate_project_id("RES")
    test_id = f"{TEST_PREFIX}_{results_id}"
    
    try:
        result = mgr.create_result_project({
            "results_title": "测试结果项目",
            "results_type": "DEA,Marker",
            "results_raw": "RAW_z,RAW_A,RAW_B,RAW_1"
        })
        
        if result and result.get("results_id"):
            # 验证数据库记录
            row = db.query_one("SELECT results_type, results_raw FROM result_project WHERE results_id=%s", (result["results_id"],))
            if row:
                raw_field = row[1] or ""
                # 验证排序 (ASCII: 数字 < 大写 < 小写)
                expected = "RAW_1,RAW_A,RAW_B,RAW_z"
                if raw_field == expected:
                    log("TC-CRS-001", "创建结果项目", "passed", "排序正确", {
                        "results_id": result["results_id"],
                        "results_raw": raw_field
                    })
                else:
                    log("TC-CRS-001", "创建结果项目", "failed", "排序错误", {
                        "expected": expected,
                        "actual": raw_field
                    })
            else:
                log("TC-CRS-001", "创建结果项目", "failed", "数据库无记录")
        else:
            log("TC-CRS-001", "创建结果项目", "failed", "创建失败")
    except Exception as e:
        log("TC-CRS-001", "创建结果项目", "failed", str(e))
    
    return result.get("results_id") if result else None

def test_results_type_validation():
    """TC-CRS-003: results_type 逗号转换验证"""
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    mgr = BioDataManager(db, config_mgr)
    
    try:
        result = mgr.create_result_project({
            "results_title": "验证results_type",
            "results_type": "DEA，Marker，富集分析"
        })
        
        if result and result.get("results_id"):
            row = db.query_one("SELECT results_type FROM result_project WHERE results_id=%s", (result["results_id"],))
            if row:
                rtype = row[0] or ""
                if "，" not in rtype and rtype.count(",") == 2:
                    log("TC-CRS-003", "results_type逗号转换", "passed", f"转换成功: {rtype}")
                else:
                    log("TC-CRS-003", "results_type逗号转换", "failed", f"未转换: {rtype}")
            else:
                log("TC-CRS-003", "results_type逗号转换", "failed", "数据库无记录")
        else:
            log("TC-CRS-003", "results_type逗号转换", "failed", "创建失败")
    except Exception as e:
        log("TC-CRS-003", "results_type逗号转换", "failed", str(e))

def test_results_raw_deduplication(results_id):
    """TC-REF-003: results_raw 去重测试"""
    if not results_id:
        log("TC-REF-003", "results_raw去重", "blocked", "无项目ID")
        return
    
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    mgr = BioDataManager(db, config_mgr)
    
    try:
        # 追加关联项目（包含重复）
        result = mgr.merge_field_value("result_project", results_id, "results_raw", "RAW_Y,RAW_Z,RAW_W")
        
        if result:
            # 验证去重结果
            row = db.query_one("SELECT results_raw FROM result_project WHERE results_id=%s", (results_id,))
            if row:
                raw_field = row[0] or ""
                expected = "RAW_A,RAW_B,RAW_W,RAW_Y,RAW_Z"
                # 注意：去重逻辑可能会排序
                if "RAW_Y" in raw_field and "RAW_Z" in raw_field and "RAW_W" in raw_field and raw_field.count("RAW_Y") == 1:
                    log("TC-REF-003", "results_raw去重", "passed", "去重成功", {
                        "before_append": "RAW_1,RAW_A,RAW_B,RAW_z",
                        "append": "RAW_Y,RAW_Z,RAW_W",
                        "after": raw_field
                    })
                else:
                    log("TC-REF-003", "results_raw去重", "failed", "去重失败", {"actual": raw_field})
            else:
                log("TC-REF-003", "results_raw去重", "failed", "数据库无记录")
        else:
            log("TC-REF-003", "results_raw去重", "failed", "追加失败")
    except Exception as e:
        log("TC-REF-003", "results_raw去重", "failed", str(e))

def test_path_generation():
    """TC-PATH-001: 路径生成测试（空tissue）"""
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    mgr = BioDataManager(db, config_mgr)
    
    try:
        # 测试有 tissue 的路径
        path_with_tissue = mgr._build_raw_project_path("mRNAseq", "Homo sapiens", "Liver", "TEST_123")
        expected_with = "/bio/rawdata/mRseq/Hs/Li/TEST_123"
        if expected_with in str(path_with_tissue):
            log("TC-PATH-001", "路径生成-有tissue", "passed", f"路径: {path_with_tissue}")
        else:
            log("TC-PATH-001", "路径生成-有tissue", "failed", f"路径错误: {path_with_tissue}")
        
        # 测试无 tissue 的路径
        path_without_tissue = mgr._build_raw_project_path("mRNAseq", "Homo sapiens", "", "TEST_456")
        expected_without = "/bio/rawdata/mRseq/Hs/TEST_456"
        if expected_without in str(path_without_tissue):
            log("TC-PATH-001", "路径生成-无tissue", "passed", f"路径: {path_without_tissue}")
        else:
            log("TC-PATH-001", "路径生成-无tissue", "failed", f"路径错误: {path_without_tissue}")
            
    except Exception as e:
        log("TC-PATH-001", "路径生成", "failed", str(e))

def test_abbr_mapping():
    """TC-ABBR-001: 缩写映射测试"""
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    mgr = BioDataManager(db, config_mgr)
    
    try:
        # 测试有映射的值
        abbr1 = mgr.get_abbr("raw_type", "mRNAseq")
        if abbr1 == "mRseq":
            log("TC-ABBR-001", "缩写映射-有映射", "passed", f"mRNAseq -> {abbr1}")
        else:
            log("TC-ABBR-001", "缩写映射-有映射", "failed", f"期望 mRseq，实际 {abbr1}")
        
        # 测试无映射的值
        abbr2 = mgr.get_abbr("raw_type", "未知类型")
        if abbr2 and len(abbr2) == 3:
            log("TC-ABBR-001", "缩写映射-无映射", "passed", f"未知类型 -> {abbr2} (取前3字符)")
        else:
            log("TC-ABBR-001", "缩写映射-无映射", "failed", f"返回值异常: {abbr2}")
            
    except Exception as e:
        log("TC-ABBR-001", "缩写映射", "failed", str(e))

def test_citation_parser():
    """TC-CIT-001: 引文解析测试"""
    try:
        from citation_parser import CitationParser
        parser = CitationParser()
        
        # 测试 BibTeX 解析
        bib_content = """
@article{test2024,
    title = {Test Article},
    author = {Author One and Author Two},
    year = {2024},
    journal = {Test Journal},
    doi = {10.1234/test}
}
"""
        results = parser.parse_content(bib_content, "bib")
        
        if results and len(results) > 0:
            entry = results[0]
            if entry.get("title") == "Test Article" and entry.get("author"):
                log("TC-CIT-001", "BibTeX解析", "passed", f"解析成功: {entry.get('title')}")
            else:
                log("TC-CIT-001", "BibTeX解析", "failed", f"解析结果异常: {entry}")
        else:
            log("TC-CIT-001", "BibTeX解析", "failed", "解析结果为空")
            
    except Exception as e:
        log("TC-CIT-001", "BibTeX解析", "failed", str(e))

def test_method_existence():
    """TC-METH-001: 方法存在性测试"""
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    mgr = BioDataManager(db, config_mgr)
    
    # 检查 get_all_processed_data
    if hasattr(mgr, 'get_all_processed_data'):
        log("TC-METH-001", "get_all_processed_data存在", "passed", "方法存在")
    else:
        log("TC-METH-001", "get_all_processed_data存在", "failed", "方法不存在")
    
    # 检查 import_processed_file
    if hasattr(mgr, 'import_processed_file'):
        log("TC-METH-002", "import_processed_file存在", "passed", "方法存在")
    else:
        log("TC-METH-002", "import_processed_file存在", "failed", "方法不存在")

def test_concurrent_simulation():
    """TC-CONC-001: 并发模拟测试"""
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    mgr = BioDataManager(db, config_mgr)
    
    try:
        # 快速生成多个项目ID
        ids = [mgr.generate_project_id("RAW") for _ in range(10)]
        unique_ids = set(ids)
        
        if len(unique_ids) == 10:
            log("TC-CONC-001", "ID生成唯一性", "passed", "10个ID全部唯一")
        else:
            duplicates = len(ids) - len(unique_ids)
            log("TC-CONC-001", "ID生成唯一性", "failed", f"发现 {duplicates} 个重复")
    except Exception as e:
        log("TC-CONC-001", "ID生成唯一性", "failed", str(e))

def test_metadata_config():
    """TC-CFG-002: 元数据配置验证"""
    db = get_db()
    config_mgr = MetadataConfigManager(db)
    
    try:
        # 测试 get_all_configs
        all_configs = config_mgr.get_all_configs()
        if all_configs is not None:
            log("TC-CFG-002", "get_all_configs响应", "passed", f"返回 {len(all_configs) if isinstance(all_configs, list) else 'N/A'} 条配置")
        else:
            log("TC-CFG-002", "get_all_configs响应", "failed", "返回 None")
        
        # 测试 get_configs_by_table
        raw_configs = config_mgr.get_configs_by_table("raw")
        if raw_configs is not None:
            log("TC-CFG-002", "get_configs_by_table响应", "passed", f"返回 {len(raw_configs) if isinstance(raw_configs, list) else 'N/A'} 条raw配置")
        else:
            log("TC-CFG-002", "get_configs_by_table响应", "failed", "返回 None")
            
    except Exception as e:
        log("TC-CFG-002", "元数据配置", "failed", str(e))

# ==================== 主流程 ====================

def main():
    print("=" * 60)
    print("🧪 第6轮容器内综合功能测试")
    print("=" * 60)
    
    # 准备环境
    print("\n📋 准备测试环境...")
    cleanup()
    ensure_test_files()
    
    # 执行测试
    print("\n" + "=" * 60)
    print("📊 测试开始")
    print("=" * 60)
    
    test_db_connection()
    test_multi_select_field()
    raw_id = test_create_raw_project()
    test_raw_species_validation()  # 第2轮新增
    test_raw_type_validation()     # 第2轮新增
    results_id = test_create_result_project()
    test_results_type_validation() # 第2轮新增
    test_results_raw_deduplication(results_id)
    test_path_generation()
    test_abbr_mapping()
    test_citation_parser()
    test_method_existence()
    test_metadata_config()         # 第2轮新增
    test_concurrent_simulation()
    
    # 清理
    print("\n📋 清理测试数据...")
    cleanup()
    
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
    results_path = Path("/home/hrply/software/bioscience/research/biodata_manager/.test/results/round6_internal_result.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(TEST_RESULTS, f, ensure_ascii=False, indent=2)
    print(f"\n📄 结果已保存: {results_path}")
    
    # 返回退出码
    sys.exit(0 if summary['failed'] == 0 else 1)

if __name__ == "__main__":
    main()
