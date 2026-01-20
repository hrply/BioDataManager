#!/usr/bin/env python3
"""
BioData Manager 远程API测试脚本
模拟远程访问服务器进行功能测试
"""

import requests
import json
import sys

BASE_URL = "http://localhost:20425"
PASS = 0
FAIL = 0

def test_endpoint(name, url, expected_success=True, check_data=None):
    global PASS, FAIL
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') == expected_success:
                if check_data:
                    for key, value in check_data.items():
                        if key not in data or data[key] != value:
                            print(f"❌ {name}: 数据验证失败 - {key}")
                            FAIL += 1
                            return
                print(f"✅ {name}")
                PASS += 1
            else:
                print(f"❌ {name}: 期望success={expected_success}")
                FAIL += 1
        else:
            print(f"❌ {name}: HTTP {resp.status_code}")
            FAIL += 1
    except Exception as e:
        print(f"❌ {name}: {e}")
        FAIL += 1

def test_post(name, url, data, expected_success=True):
    global PASS, FAIL
    try:
        resp = requests.post(url, json=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('success') == expected_success:
                print(f"✅ {name}")
                PASS += 1
            else:
                print(f"❌ {name}: {result}")
                FAIL += 1
        else:
            print(f"❌ {name}: HTTP {resp.status_code}")
            FAIL += 1
    except Exception as e:
        print(f"❌ {name}: {e}")
        FAIL += 1

def test_post_with_result(name, url, data, expected_success=True):
    """POST测试并返回结果"""
    global PASS, FAIL
    try:
        resp = requests.post(url, json=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('success') == expected_success:
                print(f"✅ {name}")
                PASS += 1
                return result
            else:
                print(f"❌ {name}: {result}")
                FAIL += 1
                return None
        else:
            print(f"❌ {name}: HTTP {resp.status_code}")
            FAIL += 1
            return None
    except Exception as e:
        print(f"❌ {name}: {e}")
        FAIL += 1
        return None

def main():
    global PASS, FAIL
    PASS = 0
    FAIL = 0
    
    print("=" * 60)
    print("BioData Manager 远程API测试")
    print("=" * 60)
    
    # 1. 基础连接测试
    print("\n【1. 基础连接测试】")
    test_endpoint("服务器首页", f"{BASE_URL}/")
    
    # 2. 字段配置测试
    print("\n【2. 字段配置测试】")
    test_endpoint("原始数据字段", f"{BASE_URL}/api/fields?table=raw")
    test_endpoint("结果数据字段", f"{BASE_URL}/api/fields?table=result")
    test_endpoint("文件管理字段", f"{BASE_URL}/api/fields?table=file")
    test_endpoint("全部字段配置", f"{BASE_URL}/api/metadata/config")
    
    # 3. 下拉选项测试
    print("\n【3. 下拉选项测试】")
    test_endpoint("数据类型选项", f"{BASE_URL}/api/options?type=raw_type")
    test_endpoint("物种选项", f"{BASE_URL}/api/options?type=raw_species")
    test_endpoint("组织来源选项", f"{BASE_URL}/api/options?type=raw_tissue")
    
    # 4. 项目列表测试
    print("\n【4. 项目列表测试】")
    test_endpoint("原始项目列表", f"{BASE_URL}/api/projects?table=raw")
    test_endpoint("结果项目列表", f"{BASE_URL}/api/projects?table=result")
    
    # 5. 项目CRUD测试
    print("\n【5. 项目CRUD测试】")
    
    # 创建原始项目
    result = test_post_with_result("创建原始项目", f"{BASE_URL}/api/projects", {
        "table": "raw",
        "raw_title": "测试项目001",
        "raw_type": "mRNAseq",
        "raw_species": "Homo sapiens",
        "raw_tissue": "Lung"
    })
    
    created_raw_id = None
    if result and 'project' in result:
        created_raw_id = result['project'].get('raw_id')
        print(f"   创建的项目ID: {created_raw_id}")
    
    # 创建结果项目
    result2 = test_post_with_result("创建结果项目", f"{BASE_URL}/api/projects", {
        "table": "result",
        "results_title": "测试结果001",
        "results_type": "DEA",
        "results_raw": created_raw_id if created_raw_id else ""
    })
    
    created_result_id = None
    if result2 and 'project' in result2:
        created_result_id = result2['project'].get('results_id')
        print(f"   创建的结果ID: {created_result_id}")
    
    # 6. 页面路由测试
    print("\n【6. 页面路由测试】")
    test_endpoint("首页", f"{BASE_URL}/")
    test_endpoint("原始数据页面", f"{BASE_URL}/raw-data")
    test_endpoint("结果页面", f"{BASE_URL}/results")
    test_endpoint("文件管理页面", f"{BASE_URL}/files")
    test_endpoint("元数据配置页面", f"{BASE_URL}/metadata")
    
    # 7. 文件管理测试
    print("\n【7. 文件管理测试】")
    test_endpoint("扫描下载目录", f"{BASE_URL}/api/scan-downloads/sync")
    
    # 8. 任务状态测试
    print("\n【8. 任务状态测试】")
    test_endpoint("任务列表", f"{BASE_URL}/api/tasks")
    
    # 结果汇总
    print("\n" + "=" * 60)
    print(f"测试结果: {PASS} 通过, {FAIL} 失败")
    if FAIL == 0:
        print("🎉 所有测试通过!")
    print("=" * 60)
    
    return FAIL == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
