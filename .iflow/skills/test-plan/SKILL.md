---
name: test-plan
description: 内测计划撰写 - 定义测试范围、设计测试用例（正向/边界/异常/关联）、制定验收标准和轮次时间安排
license: MIT
---

# 测试计划撰写

## 概述

内测计划的制定工具，帮助定义测试范围、设计测试用例、制定验收标准和时间安排。支持轮次驱动的渐进式测试策略。

## 核心能力

### 1. 定义测试范围

**需要回答的问题**：
- 测试哪些页面？
- 测试哪些功能点？
- 涉及哪些数据流？
- 边界条件有哪些？

**输出**：测试范围清单

### 2. 设计测试用例

**测试类型**：

| 类型 | 说明 | 示例 |
|-----|------|-----|
| 正向测试 | 正常流程，验证功能正常 | 正常输入，期望正确处理 |
| 边界测试 | 空值、特殊字符、超长文本 | 空字符串、特殊字符、超长输入 |
| 异常测试 | 错误输入、系统异常 | 非法输入、服务超时 |
| 关联测试 | 跨页面/跨功能影响 | 一个修改影响其他功能 |

**用例模板**：
```yaml
id: TC_模块_序号
name: 测试用例名称
precondition: 前置条件
steps:
  - 步骤1
  - 步骤2
  - 步骤3
expected: 预期结果
priority: P0/P1/P2
```

### 3. 制定验收标准

**量化指标**：
- API 响应时间 < 200ms
- 字段渲染正确率 100%
- 无 JS 错误

**质量要求**：
- UI 布局符合设计
- 交互流畅无卡顿

**停止标准**：
- 致命 bug 未修复
- 核心功能失效
- 数据丢失风险

### 4. 时间安排

**轮次计划**：

| 轮次 | 焦点 | 内容 |
|-----|------|-----|
| 第1轮 | 冒烟测试 | 核心功能验证 |
| 第2轮 | 功能测试 | 完整流程验证 |
| 第3轮 | 边界测试 | 异常情况验证 |
| 第N轮 | 回归测试 | 修复验证 |

**退出条件**：连续 2 轮无新问题 + 存量问题均修复

## 使用方法

### 交互式规划

提供功能需求或代码变更点，自动生成测试计划：

```
输入: 新增 tags 字段渲染功能
输出:
  - 测试范围: raw_data.html, results.html
  - 测试用例: TC_TAGS_001, TC_TAGS_002, TC_TAGS_003
  - 验收标准: 字段正确渲染，无JS错误
  - 时间安排: 3轮测试
```

### 手工指定

```
输入: 测试 raw_data.html 页面字段渲染
输出:
  - 测试范围: raw_data.html
  - 测试用例: 基于页面自动生成
  - 验收标准: 14个字段全部正确渲染
```

## 输出产物

- 测试范围清单
- 测试用例集合
- 验收标准文档
- 时间计划表

## 📄 自动文档生成

### 计划文档 (`.test/plans/`)

制定计划时，自动在项目目录 `.test/plans/` 下生成 MD 格式的计划文档：

```markdown
# 测试计划: [功能名称]

## 基本信息
- 创建时间: YYYY-MM-DD HH:mm:ss
- 计划轮次: N 轮
- 负责人: AI Agent

## 测试范围
- 涉及页面: xxx
- 涉及功能: xxx
- 涉及数据流: xxx

## 测试用例
| ID | 名称 | 类型 | 优先级 |
|----|------|------|--------|
| TC_001 | 用例名称 | 正向 | P0 |

## 验收标准
- [ ] 标准1
- [ ] 标准2

## 轮次安排
| 轮次 | 焦点 | 内容 | 状态 |
|------|------|------|------|
| 第1轮 | 冒烟测试 | 核心功能验证 | 待执行 |
```

**生成时机**: 每次调用 `exit_plan_mode` 或手动触发计划生成时

**文件命名**: `plan_YYYYMMDD_HHMMSS_功能名称.md`

### 代码修订记录 (`.test/logs/`)

代码修改时自动记录变更日志：

```log
#========================================
# 代码修订记录
#========================================
时间: YYYY-MM-DD HH:mm:ss
操作: [修改/新增/删除]
文件: app/backend.py
行号: 1081-1092
变更类型: 功能修复

【修改前】
if metadata_override:
    missing_required = []
    for field_id in required_fields:
        if not metadata_override.get(field_id):
            missing_required.append(field_id)

【修改后】
if metadata_override:
    for field_id, value in metadata_override.items():
        if field_id in required_fields and not value:
            return {'success': False, 'message': f'必填字段不能为空: {field_id}'}

原因: 修复验证逻辑过于严格的问题
#========================================
```

**生成时机**: 每次使用 `replace` 或 `write_file` 修改代码时自动生成

**文件命名**: `changes_YYYYMMDD_序号.log`

## 依赖技能

- index-builder - 为计划创建索引
- plan-query - 查询和检索用例

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
