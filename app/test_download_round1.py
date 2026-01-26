#!/usr/bin/env python3
"""
文件下载功能测试 - 第1轮（容器内测试）
测试原始数据项目的文件下载功能
"""

import requests
import json
import sys
import time

BASE_URL = "http://127.0.0.1:5000"

def test_download_file(file_ids, test_name):
    """测试文件下载"""
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"文件ID: {file_ids}")
    print('='*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/files/download",
            json={"file_ids": file_ids},
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'application/zip' in content_type:
                # 下载成功
                file_size = len(response.content)
                print(f"下载成功! 文件大小: {file_size} bytes")
                return True
            else:
                print(f"失败: 期望 ZIP 文件，得到 {content_type}")
                return False
        else:
            # 返回错误信息
            try:
                error = response.json()
                print(f"错误信息: {error.get('message', '未知错误')}")
            except:
                print(f"错误: 状态码 {response.status_code}")
            return False
            
    except Exception as e:
        print(f"异常: {str(e)}")
        return False

def test_error_cases():
    """测试错误情况"""
    print("\n" + "="*60)
    print("测试错误情况")
    print("="*60)
    
    results = []
    
    # TC-DL-003: 空文件列表
    result = test_download_file([], "空文件列表")
    results.append(("空文件列表", result))
    
    # TC-DL-004: 无效文件ID
    result = test_download_file([99999], "无效文件ID")
    results.append(("无效文件ID", result))
    
    return results

def main():
    print("="*60)
    print("文件下载功能测试 - 第1轮（容器内）")
    print("="*60)
    
    # 首先检查应用是否运行
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"应用状态: 运行中 (状态码: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到应用，请确保应用已启动")
        print("启动命令: python3 -m app.server")
        sys.exit(1)
    
    # 获取已存在的文件记录用于测试
    print("\n获取测试文件列表...")
    try:
        resp = requests.get(f"{BASE_URL}/api/files/imported-projects", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') and data.get('data'):
                projects = data['data']
                print(f"找到 {len(projects)} 个项目")
                
                # 获取文件记录
                files_resp = requests.get(f"{BASE_URL}/api/files", timeout=10)
                if files_resp.status_code == 200:
                    files_data = files_resp.json()
                    if files_data.get('success') and files_data.get('data'):
                        files = files_data['data']
                        print(f"找到 {len(files)} 个文件")
                        
                        if len(files) >= 2:
                            # TC-DL-001: 单文件下载
                            single_file_id = [files[0]['id']]
                            test_download_file(single_file_id, "单文件下载")
                            
                            # TC-DL-002: 多文件下载
                            multi_file_ids = [f['id'] for f in files[:2]]
                            test_download_file(multi_file_ids, "多文件下载")
                        else:
                            print("文件数量不足，跳过下载测试")
                    else:
                        print("未找到文件记录")
                else:
                    print(f"获取文件列表失败: {files_resp.status_code}")
            else:
                print("未找到项目")
        else:
            print(f"获取项目列表失败: {resp.status_code}")
    except Exception as e:
        print(f"获取数据异常: {e}")
    
    # 测试错误情况
    error_results = test_error_cases()
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    all_passed = True
    for name, passed in error_results:
        status = "通过" if passed else "失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("第1轮测试: 通过")
    else:
        print("第1轮测试: 有失败的测试用例")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
