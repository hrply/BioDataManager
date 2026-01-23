---
name: internal-testing-dispatcher
description: 内测调度中心 - 根据当前状态和用户意图智能路由到合适的内测技能，支持状态机管理和轮次驱动的任务分发
license: MIT
---

# 内测调度中心

## 概述

内测流程的中央调度器，负责分析用户输入和当前测试状态，决定调用哪个内测技能。实现状态机管理，自动引导测试流程的各个环节。

## 核心能力

### 状态机路由

根据测试进度自动判断下一步操作：

| 当前状态 | 下一步操作 |
|---------|-----------|
| 无测试计划 | 转到 test-plan 撰写计划 |
| 有计划无索引 | 转到 index-builder 创建索引 |
| 有计划有索引 | 根据意图判断下一步 |

### 意图识别

支持识别以下用户意图并路由到对应技能：

| 意图 | 关键词 | 目标技能 |
|-----|--------|---------|
| 发现问题 | 测试、检查、验证、渲染、字段 | issue-discovery |
| 分析问题 | 原因、根因、分析、为什么 | issue-analysis |
| 修复验证 | 修复、验证、回归、确认 | fix-verification |
| 查询计划 | 用例、计划、查询、第几轮 | plan-query |
| 循环管理 | 进度、统计、追踪、轮次 | loop-management |
| 制定计划 | 计划、用例、范围 | test-plan |
| 创建索引 | 索引、建立索引 | index-builder |

### 轮次驱动路由

根据测试轮次建议合适的技能组合：

- **第1轮（冒烟测试）**：issue-discovery, issue-analysis
- **第2轮（功能测试）**：issue-discovery, issue-analysis, fix-verification
- **第3轮（边界测试）**：issue-discovery, fix-verification
- **第N轮（回归测试）**：fix-verification, loop-management, plan-query

## 使用方法

### 自动调用

用户描述需求，iFlow 自动选择合适技能：

```
用户: 检查原始数据详情页字段渲染是否正确
→ 自动调用 issue-discovery

用户: 为什么 tags 字段没有渲染
→ 自动调用 issue-analysis

用户: 修复后需要回归测试哪些用例
→ 自动调用 fix-verification

用户: 第2轮有哪些测试用例
→ 自动调用 plan-query

用户: 现在内测进度怎么样了
→ 自动调用 loop-management
```

### 上下文持久化

自动维护测试上下文，记录：
- 当前轮次
- 计划/索引状态
- 问题统计
- 待修复问题清单

## 依赖技能

- issue-discovery - 问题发现
- test-plan - 测试计划
- index-builder - 索引创建
- plan-query - 计划查询
- issue-analysis - 问题分析
- fix-verification - 修复验证
- loop-management - 循环管理

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
