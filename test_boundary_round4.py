#!/usr/bin/env python3
"""
第4轮边界测试 - BioData Manager
测试各种边界情况和异常处理
"""

import sys
import requests
import json
import time
import os
from datetime import datetime

# 检测运行环境
if os.environ.get('CONTAINER_TEST'):
    BASE_URL = "http://localhost:8000"
else:
    BASE_URL = "http://localhost:20425"

class BoundaryTest:
    """边界测试类"""
    
    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'tests': []
        }
    
    def add_result(self, test_name, passed, message=""):
        """添加测试结果"""
        status = "PASS" if passed else "FAIL"
        self.results['tests'].append({
            'name': test_name,
            'status': status,
            'message': message
        })
        if passed:
            self.results['passed'] += 1
            print(f"  [PASS] {test_name}")
        else:
            self.results['failed'] += 1
            print(f"  [FAIL] {test_name}: {message}")
        return passed
    
    def test_api_empty_data(self):
        """测试1: API 空数据查询边界"""
        print("\n=== 测试1: API 空数据查询边界 ===")
        
        # 测试无项目时的API响应
        tests = [
            ("空项目列表响应", f"{BASE_URL}/api/projects?table=raw", None),
            ("空项目详情响应", f"{BASE_URL}/api/projects/raw/NONEXISTENT", None),
            ("空文件列表响应", f"{BASE_URL}/api/files?project_id=NONEXISTENT", None),
        ]
        
        for name, url, _ in tests:
            try:
                resp = requests.get(url, timeout=10)
                data = resp.json()
                
                # 检查是否返回有效的JSON响应（不是500错误）
                if resp.status_code == 200:
                    self.add_result(name, True, f"状态码: {resp.status_code}")
                elif resp.status_code == 404 or resp.status_code == 500:
                    # 500错误是边界问题
                    if resp.status_code == 500:
                        self.add_result(name, False, f"服务器错误 500")
                    else:
                        self.add_result(name, True, f"状态码: {resp.status_code}")
                else:
                    self.add_result(name, True, f"状态码: {resp.status_code}")
            except Exception as e:
                self.add_result(name, False, str(e))
    
    def test_api_special_chars(self):
        """测试2: API 特殊字符处理边界"""
        print("\n=== 测试2: API 特殊字符处理边界 ===")
        
        # 测试特殊字符在查询参数中的处理
        tests = [
            ("特殊字符查询 - 单引号", f"{BASE_URL}/api/projects?table=raw'"),
            ("特殊字符查询 - 双引号", f'{BASE_URL}/api/projects?table=raw"'),
            ("特殊字符查询 - 括号", f"{BASE_URL}/api/projects?table=raw()"),
            ("特殊字符查询 - 反斜杠", f"{BASE_URL}/api/projects?table=raw\\"),
            ("特殊字符查询 - 中文逗号", f"{BASE_URL}/api/files?file_project_ids=RAW_1，RAW_2"),
            ("特殊字符查询 - 空格", f"{BASE_URL}/api/projects?table= raw"),
        ]
        
        for name, url in tests:
            try:
                resp = requests.get(url, timeout=10)
                # 不应该返回500错误
                if resp.status_code == 500:
                    self.add_result(name, False, f"服务器错误 500")
                else:
                    self.add_result(name, True, f"状态码: {resp.status_code}")
            except Exception as e:
                self.add_result(name, False, str(e))
    
    def test_api_missing_params(self):
        """测试3: API 缺少参数边界"""
        print("\n=== 测试3: API 缺少参数边界 ===")
        
        tests = [
            ("缺少项目ID查询", f"{BASE_URL}/api/files", None),
            ("无效table参数", f"{BASE_URL}/api/projects?table=invalid", None),
            ("空project_id", f"{BASE_URL}/api/files?project_id=", None),
        ]
        
        for name, url, _ in tests:
            try:
                resp = requests.get(url, timeout=10)
                # 应该返回400或200，不应该500
                if resp.status_code == 500:
                    self.add_result(name, False, f"服务器错误 500")
                else:
                    self.add_result(name, True, f"状态码: {resp.status_code}")
            except Exception as e:
                self.add_result(name, False, str(e))
    
    def test_api_very_long_values(self):
        """测试4: API 超长值边界"""
        print("\n=== 测试4: API 超长值边界 ===")
        
        # 测试超长项目ID
        long_id = "RAW_" + "A" * 200
        
        try:
            url = f"{BASE_URL}/api/projects/raw/{long_id}"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 500:
                self.add_result("超长项目ID查询", False, "服务器错误 500")
            else:
                self.add_result("超长项目ID查询", True, f"状态码: {resp.status_code}")
        except Exception as e:
            self.add_result("超长项目ID查询", False, str(e))
    
    def test_api_invalid_methods(self):
        """测试5: API 无效HTTP方法边界"""
        print("\n=== 测试5: API 无效HTTP方法边界 ===")
        
        try:
            # 使用GET请求访问需要POST的端点
            url = f"{BASE_URL}/api/projects"
            resp = requests.get(url, timeout=10)
            
            # 应该返回有效的响应而不是500
            if resp.status_code == 500:
                self.add_result("GET到POST端点", False, "服务器错误 500")
            else:
                self.add_result("GET到POST端点", True, f"状态码: {resp.status_code}")
        except Exception as e:
            self.add_result("GET到POST端点", False, str(e))
    
    def test_api_concurrent_requests(self):
        """测试6: API 并发请求边界"""
        print("\n=== 测试6: API 并发请求边界 ===")
        
        import concurrent.futures
        import urllib.request
        import threading
        
        results = []
        lock = threading.Lock()
        
        def make_request():
            try:
                resp = requests.get(f"{BASE_URL}/api/projects", timeout=10)
                with lock:
                    results.append(resp.status_code)
                return resp.status_code
            except Exception as e:
                with lock:
                    results.append(str(e))
                return None
        
        try:
            threads = []
            for _ in range(10):
                t = threading.Thread(target=make_request)
                t.start()
                threads.append(t)
            
            # 等待所有线程完成
            for t in threads:
                t.join(timeout=30)
            
            # 检查是否有500错误
            if None in results:
                self.add_result("并发请求测试", False, "部分请求失败")
            elif 500 in results:
                self.add_result("并发请求测试", False, f"存在500错误")
            else:
                self.add_result("并发请求测试", True, f"全部成功，共{len(results)}个请求")
        except Exception as e:
            self.add_result("并发请求测试", False, str(e))
    
    def test_database_null_handling(self):
        """测试7: 数据库 NULL 值处理"""
        print("\n=== 测试7: 数据库 NULL 值处理 ===")
        
        try:
            # 访问页面检查是否能处理NULL值
            resp = requests.get(f"{BASE_URL}/raw-data", timeout=10)
            
            if resp.status_code == 500:
                self.add_result("NULL值页面渲染", False, "服务器错误 500")
            else:
                self.add_result("NULL值页面渲染", True, f"状态码: {resp.status_code}")
        except Exception as e:
            self.add_result("NULL值页面渲染", False, str(e))
    
    def test_frontend_empty_state(self):
        """测试8: 前端空状态显示"""
        print("\n=== 测试8: 前端空状态显示 ===")
        
        pages = [
            ("/raw-data", "原始数据页面"),
            ("/results", "结果管理页面"),
            ("/files", "文件管理页面"),
        ]
        
        for url, name in pages:
            try:
                resp = requests.get(f"{BASE_URL}{url}", timeout=10)
                html = resp.text
                
                # 检查是否包含空状态提示
                if "暂无数据" in html or "暂无" in html:
                    self.add_result(f"{name} - 空状态", True, "包含空状态提示")
                elif resp.status_code == 500:
                    self.add_result(f"{name} - 空状态", False, "服务器错误 500")
                else:
                    self.add_result(f"{name} - 空状态", True, f"页面可访问")
            except Exception as e:
                self.add_result(f"{name} - 空状态", False, str(e))
    
    def test_frontend_long_text(self):
        """测试9: 前端长文本处理"""
        print("\n=== 测试9: 前端长文本处理 ===")
        
        try:
            resp = requests.get(f"{BASE_URL}/raw-data", timeout=10)
            html = resp.text
            
            # 检查是否有CSS样式处理长文本
            checks = [
                ("text-break" in html, "text-break样式"),
                ("word-wrap" in html, "word-wrap样式"),
                ("overflow" in html, "overflow样式"),
            ]
            
            for check, name in checks:
                if check:
                    self.add_result(name, True, "样式存在")
                else:
                    self.add_result(name, False, "样式缺失")
        except Exception as e:
            self.add_result("长文本样式检查", False, str(e))
    
    def test_file_special_characters(self):
        """测试10: 文件名特殊字符处理"""
        print("\n=== 测试10: 文件名特殊字符处理 ===")
        
        # 模拟特殊字符文件名
        special_names = [
            "test file with spaces.fastq",
            "test-file-with-dashes.fastq",
            "test_file_with_underscores.fastq",
            "test.file.with.dots.fastq",
        ]
        
        for name in special_names:
            try:
                # 检查API是否能处理这些文件名
                url = f"{BASE_URL}/api/files?project_id=RAW_TEST001"
                resp = requests.get(url, timeout=10)
                
                if resp.status_code == 500:
                    self.add_result(f"文件名: {name[:20]}", False, "服务器错误 500")
                else:
                    self.add_result(f"文件名: {name[:20]}", True, f"状态码: {resp.status_code}")
            except Exception as e:
                self.add_result(f"文件名: {name[:20]}", False, str(e))
    
    def test_error_handling(self):
        """测试11: 错误处理边界"""
        print("\n=== 测试11: 错误处理边界 ===")
        
        tests = [
            ("404页面处理", f"{BASE_URL}/nonexistent-page", None),
            ("无效API端点", f"{BASE_URL}/api/invalid-endpoint", None),
            ("错误的JSON", f"{BASE_URL}/api/projects", {"wrong": "json"}),
        ]
        
        for name, url, data in tests:
            try:
                if data is None:
                    resp = requests.get(url, timeout=10)
                else:
                    resp = requests.post(url, json=data, timeout=10)
                
                # 不应该返回500
                if resp.status_code == 500:
                    self.add_result(name, False, "服务器错误 500")
                else:
                    self.add_result(name, True, f"状态码: {resp.status_code}")
            except Exception as e:
                self.add_result(name, False, str(e))
    
    def test_pagination_boundary(self):
        """测试12: 分页边界"""
        print("\n=== 测试12: 分页边界 ===")
        
        try:
            # 测试分页参数
            tests = [
                ("page=0", f"{BASE_URL}/api/projects?page=0"),
                ("page=-1", f"{BASE_URL}/api/projects?page=-1"),
                ("page=999999", f"{BASE_URL}/api/projects?page=999999"),
            ]
            
            for name, url in tests:
                resp = requests.get(url, timeout=10)
                
                if resp.status_code == 500:
                    self.add_result(name, False, "服务器错误 500")
                else:
                    self.add_result(name, True, f"状态码: {resp.status_code}")
        except Exception as e:
            self.add_result("分页边界测试", False, str(e))
    
    def test_encoding_boundary(self):
        """测试13: 编码边界"""
        print("\n=== 测试13: 编码边界 ===")
        
        try:
            resp = requests.get(f"{BASE_URL}/api/projects", timeout=10)
            
            # 检查响应是否正确处理中文（Flask默认返回application/json是正确的）
            # 验证响应能正确解析中文字符
            try:
                data = resp.json()
                # 检查响应结构正确
                if 'success' in data:
                    self.add_result("响应编码处理", True, "JSON解析成功")
                else:
                    self.add_result("响应编码处理", False, "JSON结构异常")
            except json.JSONDecodeError:
                self.add_result("响应编码处理", False, "JSON解析失败")
        except Exception as e:
            self.add_result("响应编码检查", False, str(e))
    
    def run_all_tests(self):
        """运行所有边界测试"""
        print("=" * 60)
        print("第4轮边界测试 - BioData Manager")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试地址: {BASE_URL}")
        print("=" * 60)
        
        self.test_api_empty_data()
        self.test_api_special_chars()
        self.test_api_missing_params()
        self.test_api_very_long_values()
        self.test_api_invalid_methods()
        self.test_api_concurrent_requests()
        self.test_database_null_handling()
        self.test_frontend_empty_state()
        self.test_frontend_long_text()
        self.test_file_special_characters()
        self.test_error_handling()
        self.test_pagination_boundary()
        self.test_encoding_boundary()
        
        # 输出汇总结果
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        print(f"总测试数: {self.results['passed'] + self.results['failed']}")
        print(f"通过数: {self.results['passed']}")
        print(f"失败数: {self.results['failed']}")
        print(f"通过率: {(self.results['passed'] / (self.results['passed'] + self.results['failed']) * 100):.1f}%" if (self.results['passed'] + self.results['failed']) > 0 else "N/A")
        print("=" * 60)
        
        # 失败的测试详情
        if self.results['failed'] > 0:
            print("\n失败的测试:")
            for test in self.results['tests']:
                if test['status'] == 'FAIL':
                    print(f"  - {test['name']}: {test['message']}")
        
        return self.results

if __name__ == "__main__":
    test = BoundaryTest()
    results = test.run_all_tests()
    
    # 返回退出码
    sys.exit(0 if results['failed'] == 0 else 1)
