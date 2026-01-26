# 文件下载功能测试计划 - 第1轮

## 测试目标
验证原始数据项目的文件下载功能正常工作。

## 测试环境
- 容器内测试：Docker 容器内执行 Python 测试
- 容器外测试：通过 localhost:20425 端口访问应用

## 测试数据准备

### 1. 创建测试原始数据项目
```python
# 创建原始数据项目
{
    "raw_title": "测试原始数据下载_R1",
    "raw_type": "转录组",
    "raw_species": "人",
    "raw_tissue": "肝"
}
```

### 2. 导入测试文件
导入至少2个文件到该项目，用于测试单文件和多文件下载。

## 测试用例

### TC-DL-001: 单文件下载
- **描述**: 下载单个文件
- **预期**: 返回 ZIP 文件，包含1个文件
- **验证点**: 
  - 响应状态码 200
  - Content-Type: application/zip
  - ZIP 包内包含正确文件

### TC-DL-002: 多文件下载
- **描述**: 下载多个文件（打包）
- **预期**: 返回 ZIP 文件，包含全部选中文件
- **验证点**:
  - 响应状态码 200
  - Content-Type: application/zip
  - ZIP 包内包含全部选中文件

### TC-DL-003: 空文件列表
- **描述**: 不传入 file_ids
- **预期**: 返回错误信息
- **验证点**: 返回 JSON 错误消息

### TC-DL-004: 无效文件ID
- **描述**: 传入不存在的文件ID
- **预期**: 返回错误信息
- **验证点**: 返回 404 错误

## 执行步骤

### 容器内测试
```bash
# 进入容器
docker-compose exec app bash

# 执行下载测试
python3 test_download_round1.py
```

### 容器外测试
```bash
# 在宿主机执行
python3 test_download_round1_remote.py --base-url http://localhost:20425
```

## 通过标准
- 所有测试用例通过
- 单文件下载正常
- 多文件打包下载正常
- 错误处理正常
