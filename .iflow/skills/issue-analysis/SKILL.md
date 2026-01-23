---
name: issue-analysis
description: 内测问题分析 - 根因定位与影响评估，按P0-P3优先级分类，分析问题根源和影响范围，提供修复建议
license: MIT
---

# 问题分析

## 概述

对发现的问题进行系统化分析，包括问题分类、根因定位、影响评估和修复建议。帮助团队理解问题的本质和严重程度。

## 分析流程

### 1. 问题分类

按优先级划分问题：

| 级别 | 名称 | 定义 | 示例 |
|-----|------|------|------|
| P0 | 致命 | 系统崩溃/数据丢失/核心功能失效 | 服务无法启动，数据丢失 |
| P1 | 严重 | 主要功能异常/数据错误 | 核心功能无法正常使用 |
| P2 | 一般 | 非核心功能问题/UI异常 | 次要功能异常，样式问题 |
| P3 | 轻微 | 建议优化/体验问题 | 建议改进，非必须 |

### 2. 根因定位

从四个层面逐层排查：

| 层面 | 问题类型 | 示例 |
|-----|---------|------|
| 数据层 | 数据源问题 | 数据库配置错误，编码问题 |
| 逻辑层 | 代码逻辑问题 | 条件判断错误，类型转换问题 |
| 执行层 | 环境问题 | 服务未启动，路由错误 |
| 结果层 | 渲染问题 | 模板错误，CSS问题 |

**排查方法**：逐层排查 + 代码审查

### 3. 影响范围评估

**评估因素**：
- 涉及页面数
- 涉及功能数
- 用户影响程度
- 数据影响程度

**影响等级**：

| 等级 | 描述 | 处理方式 |
|-----|------|---------|
| high | 影响核心功能 | 立即修复 |
| medium | 影响非核心功能 | 下次迭代修复 |
| low | 体验问题 | 可以容忍 |

### 4. 修复建议

**立即修复**：
- P0/P1 问题
- 影响核心功能
- 数据相关问题

**延后修复**：
- P2/P3 问题
- 非核心功能
- 体验优化

## 输出产物

- 问题清单（带优先级）
- 根因分析报告
- 影响范围评估
- 修复建议

## 使用方法

```
用户: 为什么 tags 字段没有渲染？
→ issue-analysis 自动分析

用户: 分析这个问题的原因和影响
→ 提供完整的分析报告
```

## 与其他技能配合

- issue-discovery 发现问题后 → issue-analysis 分析
- fix-verification 修复前 → issue-analysis 确认根因
- loop-management 统计时 → issue-analysis 结果作为输入

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
