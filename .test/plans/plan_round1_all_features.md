# 第1轮内测计划 - 全部功能测试

## 测试目标
全面测试 biodata_manager 应用的全部功能，包括页面路由、API接口、导入功能、文件管理等。

## 测试环境
- **容器内测试**: Docker 容器内执行 Python 测试
- **容器外测试**: 通过 localhost:20425 端口访问应用

## 测试范围

### 1. 页面路由测试
| 用例编号 | 测试场景 | 预期结果 | 优先级 |
|---------|---------|---------|--------|
| P001 | 访问首页 / | 返回 200，渲染首页 | P0 |
| P002 | 访问文件管理 /files | 返回 200，渲染文件管理页 | P0 |
| P003 | 访问原始数据 /raw-data | 返回 200，渲染原始数据页 | P0 |
| P004 | 访问结果管理 /results | 返回 200，渲染结果管理页 | P0 |
| P005 | 访问元数据管理 /metadata | 返回 200，渲染元数据管理页 | P1 |

### 2. 项目 API 测试
| 用例编号 | API | 测试场景 | 预期结果 | 优先级 |
|---------|-----|---------|---------|--------|
| API001 | GET /api/projects | 获取全部项目 | 返回 success=true | P0 |
| API002 | GET /api/projects?table=raw | 获取原始数据项目 | 返回 raw 项目列表 | P0 |
| API003 | GET /api/projects?table=result | 获取结果数据项目 | 返回 result 项目列表 | P0 |
| API004 | POST /api/projects | 创建原始数据项目 | 创建成功，返回新项目 | P0 |
| API005 | POST /api/projects | 创建结果数据项目 | 创建成功，返回新项目 | P0 |

### 3. 文件管理 API 测试
| 用例编号 | API | 测试场景 | 预期结果 | 优先级 |
|---------|-----|---------|---------|--------|
| API006 | GET /api/files/imported-projects | 获取已导入项目列表 | 返回项目列表 | P0 |
| API007 | GET /api/files/imported-projects?type=raw | 筛选原始项目 | 返回匹配的原始项目 | P0 |
| API008 | GET /api/files/imported-projects?type=result | 筛选结果项目 | 返回匹配的结果项目 | P0 |
| API009 | GET /api/files?project_id=XXX | 获取项目文件列表 | 返回文件列表 | P0 |
| API010 | DELETE /api/files | 删除文件（不存在ID） | 返回错误，不崩溃 | P1 |
| API011 | POST /api/files/download | 下载文件（不存在ID） | 返回错误，不崩溃 | P1 |

### 4. 元数据 API 测试
| 用例编号 | API | 测试场景 | 预期结果 | 优先级 |
|---------|-----|---------|---------|--------|
| API012 | GET /api/metadata/fields | 获取 raw 字段配置 | 返回字段列表 | P0 |
| API013 | GET /api/metadata/fields?table=result | 获取 result 字段配置 | 返回字段列表 | P0 |
| API014 | GET /api/metadata/fields?table=file | 获取 file 字段配置 | 返回字段列表 | P0 |
| API015 | GET /api/options?type=raw_type | 获取 raw_type 选项 | 返回选项列表 | P0 |
| API016 | GET /api/options?type=results_type | 获取 results_type 选项 | 返回选项列表 | P0 |

### 5. 扫描和导入 API 测试
| 用例编号 | API | 测试场景 | 预期结果 | 优先级 |
|---------|-----|---------|---------|--------|
| API017 | GET /api/scan-downloads/sync | 扫描下载目录 | 返回扫描结果 | P0 |
| API018 | POST /api/import-download | 新建项目导入文件 | 导入成功 | P0 |
| API019 | POST /api/import-download | 导入到已有项目 | 导入成功 | P0 |

### 6. 任务状态 API 测试
| 用例编号 | API | 测试场景 | 预期结果 | 优先级 |
|---------|-----|---------|---------|--------|
| API020 | GET /api/tasks | 获取任务状态 | 返回任务列表 | P1 |
| API021 | GET /api/processed-data | 获取引文解析数据 | 返回数据列表 | P1 |

### 7. 前端功能测试（DOM结构）
| 用例编号 | 测试场景 | 预期结果 | 优先级 |
|---------|---------|---------|--------|
| DOM001 | 首页 Bootstrap 加载 | 无 JS 错误 | P0 |
| DOM002 | 文件管理页面筛选器 | 筛选器正常显示 | P0 |
| DOM003 | 原始数据页面项目列表 | 列表正常渲染 | P0 |
| DOM004 | 结果管理页面项目列表 | 列表正常渲染 | P0 |
| DOM005 | Bootstrap 样式完整性 | 无 CSS 加载错误 | P0 |

## 测试数据准备

### 测试环境检查
```python
def check_test_environment():
    """检查测试环境"""
    checks = {
        "BASE_URL": "http://localhost:20425",
        "容器内": "http://localhost:8000",
        "MySQL连接": "通过 API 验证",
        "下载目录": "/bio/downloads"
    }
    return checks
```

### 测试项目数据
```python
test_raw_project = {
    "raw_title": "Round1测试_原始数据",
    "raw_type": "mRNAseq",
    "raw_species": "Homo sapiens",
    "raw_tissue": "Liver"
}

test_result_project = {
    "result_title": "Round1测试_结果数据",
    "results_type": "差异分析 (DEA)",
    "results_raw": "RAW_test001,RAW_test002"
}
```

## 执行步骤

### 阶段1: 容器内测试
```bash
# 进入容器
docker exec -it biodata-manager bash

# 执行测试
cd /home/hrply/software/bioscience/research/biodata_manager
python3 test_all_apis.py
python3 test_import.py
python3 test_frontend.py
```

### 阶段2: 容器外测试
```bash
# 在宿主机执行
cd /home/hrply/software/bioscience/research/biodata_manager
python3 test_all_apis.py
python3 test_import.py
python3 test_remote_api.py
```

## 通过标准
- 所有 P0 测试用例通过
- 无 500 服务器错误
- API 响应格式正确
- 前端页面正常渲染

## 风险评估
| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 数据库无测试数据 | 中 | 测试API响应格式，不依赖具体数据 |
| 网络超时 | 低 | 设置合理的 timeout |
| 容器不稳定 | 中 | 先检查容器健康状态 |

## 输出产物
- 测试执行日志
- 失败用例清单
- 问题修复建议

---

**计划制定日期**: 2026-01-25
**测试轮次**: 第1轮
