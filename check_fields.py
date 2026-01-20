#!/usr/bin/env python3
import urllib.request
import json

# 获取API数据
response = urllib.request.urlopen('http://localhost:8000/api/metadata/config', timeout=10)
data = json.loads(response.read().decode())
configs = data.get('config', [])

# 统计各类字段
raw = [c for c in configs if c.get('field_table') == 'raw']
result = [c for c in configs if c.get('field_table') == 'result']
file = [c for c in configs if c.get('field_table') == 'file']

print("=== API返回的字段数据 ===")
print(f"原始数据字段: {len(raw)}")
print(f"结果数据字段: {len(result)}")
print(f"文件管理字段: {len(file)}")

# 打印字段详情
print("\n=== 原始数据字段详情 ===")
for f in raw:
    print(f"  - {f['field_id']}: {f['field_name']} ({f['field_type']})")

print("\n=== 结果数据字段详情 ===")
for f in result:
    print(f"  - {f['field_id']}: {f['field_name']} ({f['field_type']})")

print("\n=== 文件管理字段详情 ===")
for f in file:
    print(f"  - {f['field_id']}: {f['field_name']} ({f['field_type']})")