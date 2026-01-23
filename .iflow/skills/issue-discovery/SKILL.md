---
name: issue-discovery
description: 内测问题发现 - 四层验证模型（数据层→逻辑层→执行层→结果层），系统化发现UI渲染、数据展示、功能异常等问题
license: MIT
---

# 问题发现

## 概述

内测问题发现的核心方法论，采用"四层验证模型"系统化定位问题。从数据源到最终展示，逐层排查，确保问题定位准确。

## 核心原则

**代码 ≠ 逻辑 ≠ 执行 ≠ 结果**

四个层面可能存在差异，需要分别验证。

## 四层验证模型

### 第一层：数据验证

直接查询数据源，不经过应用层。

**检查点**：
- 字符集（charset）
- 配置值（config）
- 缓存（cache）
- 权限（permission）

**验证工具**：
```bash
# MySQL 数据验证
docker exec mysql mysql --default-character-set=utf8mb4 -e "SELECT ..."

# API 数据验证（绕过缓存）
curl -H 'Cache-Control: no-cache' /api/endpoint

# 文件数据验证
cat file.txt | head -20
```

**常见问题**：
| 现象 | 原因 | 解决方案 |
|-----|------|---------|
| 中文乱码 | 字符集错误 | 检查 charset |
| 数据不更新 | 缓存问题 | 清除缓存 |
| 查不到数据 | 权限问题 | 检查用户权限 |

### 第二层：逻辑验证

阅读代码，理解数据流向。

**检查点**：
- 条件判断是否正确
- 是否有提前 return 跳过逻辑
- 数据转换是否正确
- 类型处理是否完整

**代码模式识别**：
```python
# 跳过逻辑
return\s+...

# 条件判断
if\s*\(.*field_type.*\)

# 数据转换
map\s*\(|\.replace\s*\(
```

**常见问题**：
- 条件满足但提前 return
- 缺少某种 field_type 处理
- if 条件写反

### 第三层：执行验证

使用不同工具获取真实执行结果。

**工具链**：
1. curl - API 测试
2. Postman - 接口调试
3. Playwright - 浏览器自动化
4. DevTools - 前端调试

**Playwright 示例**：
```javascript
const {chromium} = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto(URL);
  const h = await p.$eval(SELECTOR, e => e.innerHTML);
  console.log(h);
  await b.close();
})();
```

**常见问题**：
- 服务未启动（`docker ps` 检查）
- 路由错误（检查 Flask/Express）
- 选择器不对（DevTools 确认）
- 元素未加载（waitForTimeout）

### 第四层：结果验证

量化对比预期与实际结果。

**对比维度**：
| 维度 | 预期 | 实际 |
|-----|------|------|
| 字段数量 | 14个 | ?个 |
| 字段值 | 逐个对比 | - |
| field_type映射 | link→<a>, tags→<span.badge> | - |
| 布局 | placeholder=1→col-md-12 | - |

## 发现流程

```
定义预期 → 获取实际 → 量化对比 → 定位原因
```

## 典型应用场景

- 检查页面字段渲染是否正确
- 验证 API 返回数据格式
- 对比不同环境数据一致性
- 排查数据展示异常问题

## 📋 问题记录

### 问题清单模板

```markdown
# 问题清单: [页面/功能名称]

## 问题列表

### ISSUE_001
- 时间: YYYY-MM-DD HH:mm:ss
- 层级: 第N层（数据/逻辑/执行/结果）
- 现象: 详细描述
- 根因: 问题原因
- 严重程度: P0/P1/P2/P3
- 状态: 待修复/修复中/已修复

### ISSUE_002
...
```

### 问题输出位置

问题记录自动保存到 `.test/plans/issues_YYYYMMDD.md`

## 📝 代码变更记录

每次问题修复后，代码变更自动记录到 `.test/logs/`：

```log
#========================================
# 代码修订记录
#========================================
时间: YYYY-MM-DD HH:mm:ss
操作: 修改
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

关联问题: ISSUE_001
修复原因: 验证逻辑过于严格，用户未修改的字段也应使用数据库值
#========================================
```

## 依赖技能

- plan-query - 查询测试用例
- index-builder - 获取测试索引

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
