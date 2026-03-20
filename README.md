# BioData Manager

生物信息学数据管理系统，用于管理原始测序数据、分析结果和相关元数据。

## 功能特性

- **原始数据管理**：管理测序原始数据项目，支持多条件筛选和元数据配置
- **结果数据管理**：管理分析结果数据，支持关联原始数据项目
- **文件管理**：递归扫描下载目录、导入文件、文件记录管理
- **文件校验**：异步计算文件的 MD5 和 SHA256 哈希值，支持大文件校验
- **批量操作**：异步批量删除和批量导入文件，避免大文件或多文件操作超时
- **元数据配置**：动态配置字段显示和表单生成

## 快速开始

### Docker 部署（推荐）

```bash
# 启动服务（首次运行会自动初始化数据库）
docker-compose up -d

# 查看日志
docker-compose logs -f biodata-manager

# 停止服务
docker-compose down
```

### 环境变量配置

创建 `.env` 文件：

```bash
# MySQL 数据库配置
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=biodata
MYSQL_USER=biodata
MYSQL_PASSWORD=biodata123

# 应用配置
BIODATA_USE_MOVE_MODE=true
INIT_DATABASE=true  # 首次运行设为 true，之后设为 false
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Flask >=3.0.0 |
| 模板引擎 | Jinja2 >=3.1.0 |
| 数据库 | MySQL 8.x (LTS) |
| 前端 UI | Bootstrap 5 |
| 异步处理 | Python Threading |

## 最近更新

- **递归子目录文件导入修复** (2026-03-20)：修复从递归扫描结果中导入子目录文件时，只导入顶层文件夹文件的问题
- **导入时间戳优化**：异步导入使用任务创建时间作为 `imported_at`
- **递归文件扫描**：支持扫描多层子目录，自动发现所有嵌套文件
- **异步 Hash 校验**：新增文件 MD5/SHA256 哈希值计算功能
- **异步批量删除/导入**：支持大量文件操作，避免超时

## 文档

详细文档请参阅 [AGENTS.md](./AGENTS.md)

## 许可证

MIT License
