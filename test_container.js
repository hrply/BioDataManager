#!/usr/bin/env python3
import urllib.request
import json

# 1. 测试API返回
response = urllib.request.urlopen('http://localhost:8000/api/metadata/config', timeout=10)
data = json.loads(response.read().decode())
configs = data.get('config', [])
raw = [c for c in configs if c.get('field_table') == 'raw']
result = [c for c in configs if c.get('field_table') == 'result']
file = [c for c in configs if c.get('field_table') == 'file']

print("=== Docker容器内API测试 ===")
print(f"原始数据字段: {len(raw)} 个")
print(f"结果数据字段: {len(result)} 个")
print(f"文件管理字段: {len(file)} 个")

# 2. 测试页面渲染
page_response = urllib.request.urlopen('http://localhost:8000/metadata', timeout=10)
page_html = page_response.read().decode()

# 检查关键元素
checks = {
    'jQuery加载': 'jquery.min.js' in page_html,
    'Bootstrap加载': 'bootstrap.bundle.min.js' in page_html,
    '原始数据字段表': 'id="raw-field-list"' in page_html,
    '结果数据字段表': 'id="result-field-list"' in page_html,
    '文件管理字段表': 'id="file-field-list"' in page_html,
    'loadConfig函数': 'function loadConfig()' in page_html,
    'renderFieldLists函数': 'function renderFieldLists()' in page_html,
}

print("\n=== 页面元素检查 ===")
for check, passed in checks.items():
    status = "✓" if passed else "✗"
    print(f"{status} {check}\n")

all_passed = all(checks.values())
print(f"\n{'✓ 所有检查通过!' if all_passed else '✗ 部分检查失败'}\n")

print(f"\n原始数据字段将渲染 {len(raw)} 行")
print(f"结果数据字段将渲染 {len(result)} 行")
print(f"文件管理字段将渲染 {len(file)} 行")
