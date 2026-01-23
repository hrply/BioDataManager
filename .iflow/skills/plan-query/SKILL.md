---
name: plan-query
description: 内测计划查询 - 根据页面/功能/类型/优先级/field_type/轮次/API等多维度查询测试用例，返回用例详情和统计信息
license: MIT
---

# 计划查询

## 概述

从测试索引中快速检索用例信息，支持多种查询维度，返回用例详情、列表或统计信息。

## 查询类型

### by_page（按页面）

```
输入: 页面路径或文件名
输出: 该页面所有用例ID列表

示例:
输入: raw_data.html
输出: ["TC_RAW_001", "TC_RAW_002"]
```

### by_feature（按功能）

```
输入: 功能描述或关键词
输出: 相关用例列表

示例:
输入: 标签云渲染
输出: ["TC_TAGS_001"]
```

### by_type（按类型）

```
输入: 用例类型
输出: 该类型所有用例

示例:
输入: 边界测试
输出: ["TC_002"]
```

### by_priority（按优先级）

```
输入: 优先级 (P0/P1/P2)
输出: 该优先级所有用例

示例:
输入: P0
输出: ["TC_P0_001"]
```

### by_field_type（按字段类型）

```
输入: field_type 值
输出: 相关用例列表

示例:
输入: tags
输出: ["TC_TAGS_001", "TC_TAGS_002"]
```

### by_round（按轮次）

```
输入: 轮次信息
输出: 该轮次用例列表

示例:
输入: 第2轮
输出: ["TC_R2_001"]
```

### by_case_id（按用例ID）

```
输入: 用例ID
输出: 完整用例信息

示例:
输入: TC_RAW_001
输出:
  name: 项目详情渲染测试
  steps: ["步骤1", "步骤2"]
  expected: 渲染正确
```

### by_api（按API端点）

```
输入: API 路径
输出: 相关用例列表

示例:
输入: /api/metadata/fields
输出: ["TC_API_001"]
```

## 典型场景

### 场景1：问题发现时查询相关用例

```
场景: issue-discovery 发现 tags 渲染问题
查询: field_type=tags 的测试用例
操作: plan-query(by_field_type, tags)
输出: 所有 tags 相关用例
```

### 场景2：修复验证时查询回归范围

```
场景: fix-verification 需要回归测试
查询: 页面=raw_data.html 且 类型=正向测试
操作: plan-query(by_page, raw_data.html) + 过滤
输出: 相关用例列表
```

### 场景3：统计进度时查询优先级

```
场景: loop-management 统计进度
查询: P0 用例完成情况
操作: plan-query(by_priority, P0)
输出: 所有 P0 用例
```

## 使用方法

```
用户: raw_data.html 有哪些测试用例？
→ plan-query(by_page, raw_data.html)

用户: 第2轮测试哪些用例？
→ plan-query(by_round, 第2轮)

用户: TC_RAW_001 的详情？
→ plan-query(by_case_id, TC_RAW_001)

用户: 有哪些测试计划文档？
→ plan-query(plans)
输出: 所有计划文档列表和路径
```

## 📚 计划文档查询

### 列出所有计划

```
查询: plans
输出: 
  [
    {"id": "plan_001", "name": "字段渲染测试", "path": ".test/plans/plan_20260123_143022_字段渲染.md"},
    {"id": "plan_002", "name": "导入功能测试", "path": ".test/plans/plan_20260123_150022_导入功能.md"}
  ]
```

### 查询计划详情

```
查询: plan_20260123_143022
输出: 计划文档完整内容
```

### 查询修订记录

```
查询: logs
输出: 
  [
    {"time": "2026-01-23 14:30:22", "file": "app/backend.py", "desc": "修复验证逻辑"},
    {"time": "2026-01-23 15:00:22", "file": "app/templates/results.html", "desc": "修复created_at处理"}
  ]
```

## 依赖技能

- index-builder - 维护索引数据
- internal-testing-dispatcher - 路由查询请求

---

## 环境说明

### 代码编辑
- 所有代码修改在项目文件内进行 (`/home/hrply/software/bioscience/research/biodata_manager/`)
- 编辑文件后需要重启容器或重新加载服务

### 代码运行
- Python/Flask 代码需进入 Docker 容器内执行
- 进入容器：`docker exec -it biodatamanager-app-1 bash`
- 启动服务：`docker-compose up -d`

### Docker Compose 操作权限

以下命令可直接执行，无需询问：
- `docker-compose start/stop/restart/up/down/build/ps`
- `docker-compose logs`
- `docker exec -it <container> bash`

以下操作需要用户确认：
- 删除数据卷：`docker-compose down -v`
- 删除镜像：`docker-compose down --rmi all`

**开放数据卷操作**：当用户在 prompt 中输入 `[开放docker数据卷操作]` 时，允许执行数据卷删除操作。

### 测试与访问
- Web 界面：通过 `docker-compose ports` 定义的端口访问（默认 5000）
- 查看日志：`docker logs biodatamanager-app-1`
- 数据库连接：容器内 MySQL 端口映射

### 代码设计文档
- 代码设计的思路和逻辑可以查看 `@docs/` 目录下的文档
- `docs/应用功能设计.md` - 功能模块设计说明
- `docs/数据库设计规范.md` - 数据库结构和规范说明
