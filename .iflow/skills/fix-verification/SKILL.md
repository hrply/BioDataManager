---
name: fix-verification
description: 修复后验证 - 确认问题已解决，包括原问题复测、关联功能回归、边界条件测试，确保修复无副作用
license: MIT
---

# 修复验证

## 概述

修复完成后的验证流程，确认问题已解决且无回归问题。包括原问题复测、关联功能回归、边界条件测试。

## 验证流程

### 1. 复现确认

**目的**：在修复前环境中确认问题存在

**方法**：
- 重复 issue-discovery 的验证步骤
- 截图/日志/步骤记录
- 建立问题基线

### 2. 修复实施

**原则**：
- 修复根因而非症状
- 最小化改动
- 保持代码风格一致

### 3. 验证测试

**原问题复测**：
```
用例: 原问题测试用例
预期: 问题已解决
```

**关联功能回归**：
```
用例: 与修复内容相关的测试用例
预期: 无回归问题
```

**边界条件补充**：
```
用例: 边界条件测试用例
预期: 无边界问题
```

### 4. 结果确认

**通过条件**：
- [ ] 原问题用例测试通过
- [ ] 关联功能测试通过
- [ ] 无新增问题
- [ ] 代码审查通过

**失败处理**：
- 记录失败用例
- 返回开发重新修复
- 更新验证计划

## 验证检查清单

- [ ] 原问题是否复现
- [ ] 修复是否有效
- [ ] 关联功能是否正常
- [ ] 边界情况是否通过
- [ ] 代码是否符合规范

## 使用方法

```
用户: 验证 tags 字段修复是否有效
→ fix-verification 执行完整验证流程

用户: 修复完成后需要回归测试
→ fix-verification 返回回归测试范围和建议
```

## 与其他技能配合

- issue-analysis 分析后 → fix-verification 执行修复
- loop-management 追踪时 → fix-verification 提供验证结果
- plan-query 提供回归测试用例列表

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
