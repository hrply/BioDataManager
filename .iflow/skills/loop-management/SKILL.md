---
name: loop-management
description: 循环内测管理 - 问题追踪与进度控制，管理问题状态流、统计测试进度、评估回归风险、控制测试轮次
license: MIT
---

# 循环管理

## 概述

内测流程的循环管理工具，负责问题追踪、进度控制、回归管理和轮次控制。支持渐进式测试策略。

## 循环结构

### 轮次定义

**周期**：通常 1-2 天/轮

**每轮内容**：
1. 问题修复验证
2. 新问题发现
3. 回归测试

**退出条件**：
- 连续 2 轮无新增问题
- 所有 P0/P1 问题已修复
- 达到预设轮次上限

### 循环流程

```
round → fix → verify → round → ...
```

## 问题追踪

### 状态流

```
新建 → 确认 → 修复中 → 已修复 → 已关闭
```

### 记录字段

| 字段 | 说明 |
|-----|------|
| ID | 问题唯一标识 |
| 描述 | 问题描述 |
| 优先级 | P0-P3 |
| 状态 | 当前状态 |
| 负责人 | 责任人 |
| 轮次 | 发现轮次 |

### 统计仪表板

| 指标 | 说明 |
|-----|------|
| total | 问题总数 |
| open | 未解决问题 |
| fixed | 已修复数 |
| closed | 已关闭数 |

## 回归管理

**回归范围**：与修复内容相关的所有功能

**回归方法**：使用 issue-discovery 四层验证模型

**触发时机**：每轮修复后必须执行

## 进度控制

### 核心指标

| 指标 | 说明 | 计算方式 |
|-----|------|---------|
| velocity | 每轮修复问题数 | fixed_count / round |
| quality | 修复成功率 | fixed_count / (fixed + reopened) |
| stability | 回归问题率 | regression_bugs / total_fixes |

### 停止条件

- 连续 2 轮无新增问题
- 所有 P0/P1 问题已修复
- 达到预设轮次上限

## 输出产物

- 问题追踪表
- 进度报告
- 回归测试报告
- 结束报告

## 使用方法

```
用户: 现在内测进度怎么样了？
→ 返回进度仪表板

用户: 第2轮测试完成，统计一下
→ 生成第2轮报告

用户: 什么时候可以结束内测？
→ 根据停止条件判断
```

## 与其他技能配合

- 所有技能状态更新 → loop-management 追踪
- fix-verification 结果 → 更新问题状态
- issue-discovery 新问题 → 更新问题列表

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
