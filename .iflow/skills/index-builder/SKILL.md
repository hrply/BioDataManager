---
name: index-builder
description: 内测索引创建 - 为测试计划建立多维度索引（按页面/功能/类型/优先级/field_type/轮次/API），支持快速查询
license: MIT
---

# 索引创建

## 概述

为测试计划和用例建立多维度索引系统，支持按页面、功能、类型、优先级、field_type、轮次、API 等维度快速检索。

## 索引维度

### by_page（按页面）

```
key: 页面路径
value: 相关用例ID列表

示例:
{"raw_data.html": ["TC_RAW_001", "TC_RAW_002"]}
```

### by_feature（按功能）

```
key: 功能点
value: 相关用例ID列表

示例:
{"字段渲染": ["TC_RAW_001"], "项目创建": ["TC_RAW_002"]}
```

### by_type（按用例类型）

```
key: 用例类型
value: 用例ID列表

示例:
{"正向测试": ["TC_001"], "边界测试": ["TC_002"]}
```

### by_priority（按优先级）

```
key: 优先级
value: 用例ID列表

示例:
{"P0": ["TC_P0_001"], "P1": ["TC_P1_001"]}
```

### by_field_type（按字段类型）

```
key: field_type 值
value: 相关用例ID列表

示例:
{"link": ["TC_LINK_001"], "tags": ["TC_TAGS_001"]}
```

### by_round（按轮次）

```
key: 轮次信息
value: 用例ID列表

示例:
{"第1轮冒烟": ["TC_R1_001"], "第2轮功能": ["TC_R2_001"]}
```

### by_api（按API端点）

```
key: API 路径
value: 相关用例ID列表

示例:
{"/api/metadata/fields": ["TC_API_001"]}
```

## 使用方法

### 自动触发

test-plan 完成后自动调用，创建完整索引。

### 手动触发

当测试计划更新时，可重新执行索引创建：

```
用户: 建立了新的测试计划，需要建立索引
→ 自动调用 index-builder
```

## 输出文件

**internal_testing_index.json**

JSON 格式的多维度索引文件，供 plan-query 调用。

## 依赖技能

- test-plan - 接收测试计划和用例
- plan-query - 提供索引查询服务

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
