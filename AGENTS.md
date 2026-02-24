# BioData Manager - 项目上下文文档

## 项目概述

BioData Manager 是一个生物信息学数据管理系统，用于管理原始测序数据、分析结果和相关元数据。该系统采用 **Python Flask + Jinja2 + Bootstrap 5** 技术栈，提供完整的项目管理、文件管理、元数据配置和文件校验功能。

### 核心功能
- **原始数据管理**：管理测序原始数据项目，支持多条件筛选和元数据配置
- **结果数据管理**：管理分析结果数据，支持关联原始数据项目
- **文件管理**：递归扫描下载目录、导入文件、文件记录管理
- **文件校验**：异步计算文件的 MD5 和 SHA256 哈希值，支持大文件校验
- **批量操作**：异步批量删除和批量导入文件，避免大文件或多文件操作超时
- **元数据配置**：动态配置字段显示和表单生成

### 最新更新
- **导入时间戳优化**：异步导入使用任务创建时间（点击导入按钮时间）作为 `imported_at`，避免异步完成时间与用户期望不符
- **递归文件扫描**：支持扫描多层子目录，自动发现所有嵌套文件
- **异步 Hash 校验**：新增文件 MD5/SHA256 哈希值计算功能，支持大文件异步处理
- **异步批量删除**：批量删除文件采用异步处理，支持大量文件删除操作
- **异步批量导入**：批量导入文件采用异步处理，支持大量文件导入操作
- **任务管理系统**：实现异步任务管理器，解决大文件计算超时问题
- **轮询优化**：异步任务状态查询间隔优化为 7.5 秒，减少服务器负载
- **校验弹窗优化**：重新设计校验弹窗列结构，MD5 和 SHA256 分列显示，新旧值对比更清晰
- **新增 CyTOF 数据类型**：添加质谱流式数据类型支持，缩写为 `cytof`
- **内测日志记录**：新增 `.test/logs/` 目录用于存储测试结果

### 技术栈
| 类别 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Flask | >=3.0.0 |
| 模板引擎 | Jinja2 | >=3.1.0 |
| 数据库 | MySQL | 8.x (LTS) |
| 前端 UI | Bootstrap 5 | 本地化 |
| HTTP 客户端 | jQuery AJAX | 本地化 |
| 异步处理 | Threading | Python 标准库 |

## 构建和运行

### Docker 部署（推荐）

```bash
# 启动服务（首次运行会自动初始化数据库）
docker-compose up -d

# 查看日志
docker-compose logs -f biodata-manager

# 停止服务
docker-compose down

# 重启服务
docker-compose restart biodata-manager
```

### 环境变量配置

创建 `.env` 文件（参考 `.env` 示例）：

```bash
# MySQL 数据库配置
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=biodata
MYSQL_USER=biodata
MYSQL_PASSWORD=biodata123

# 应用配置
BIODATA_USE_MOVE_MODE=true
INIT_DATABASE=true  # 首次运行设为 true，之后设为 false

# 元数据字段配置（按 field_seq 排序的序号，用逗号分隔）
# 注意：以下配置必须包含路径生成所需字段，否则文件无法正确导入！
# 路径生成所需字段：
#   原始数据：raw_type, raw_species, raw_tissue (用于生成 /bio/rawdata/{type}/{species}/{tissue}/{id}/)
#   结果数据：results_type, results_raw (用于生成 /bio/results/{type}/{id}[/{raw}]/)

# 新建项目-原始数据：显示的字段序号
# 必须包含：raw_type, raw_species, raw_tissue
METADATA_FIELDS_NEW_RAW=2,3,4,11
# 新建项目-结果数据：显示的字段序号
# 必须包含：results_type, results_raw
METADATA_FIELDS_NEW_RESULT=2,3,5
# 已有项目-原始数据：显示的字段序号
# 必须包含：raw_type, raw_species, raw_tissue
METADATA_FIELDS_EXIST_RAW=2,3,4,11
# 已有项目-结果数据：显示的字段序号
# 必须包含：results_type, results_raw
METADATA_FIELDS_EXIST_RESULT=2,3,5
# 原始数据管理页列表列标题：显示的字段序号
METADATA_PROJECT_ROWTITLE_RAW=0,2,3,4
# 结果管理页列表列标题：显示的字段序号
METADATA_PROJECT_ROWTITLE_RESULT=0,2,3
```

### 本地开发

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 设置环境变量
export DB_TYPE=mysql
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=biodata
export MYSQL_PASSWORD=biodata123
export MYSQL_DATABASE=biodata

# 初始化数据库（首次运行）
python3 app/init_db.py

# 启动服务
python3 app/server.py 8000
```

## 开发规范

### 代码结构

```
app/
├── server.py                         # Flask 主应用（路由 + API）
├── backend.py                        # 业务逻辑层（BioDataManager）
├── database_mysql.py                 # 数据库管理（DatabaseManager + 连接池）
├── task_manager.py                   # 异步任务管理器（TaskManager）
├── init_db.py                        # 数据库初始化脚本
├── metadata_config_manager_mysql.py  # 元数据配置管理
├── field_names.py                    # 字段名称定义
├── citation_parser.py                # 引文解析模块（BibTeX/RIS/ENW）
├── temp_calculate.py                 # 临时计算模块
├── docker-entrypoint.sh              # Docker 入口脚本
├── favicon.ico                       # 网站图标
├── index.html                        # 索引页面
│
├── templates/                        # Jinja2 模板
│   ├── base.html                     # 基础模板（导航、AJAX 封装）
│   ├── index.html                    # 首页
│   ├── raw_data.html                 # 原始数据页面
│   ├── results.html                  # 结果管理页面
│   ├── files.html                    # 文件管理页面
│   ├── metadata.html                 # 元数据配置页面
│   └── error.html                    # 错误页面
│
├── static/                           # 静态文件
│   ├── css/
│   │   ├── bootstrap.min.css         # Bootstrap CSS
│   │   ├── bootstrap-icons.css       # Bootstrap Icons
│   │   └── bootstrap-select.min.css  # Bootstrap Select
│   └── js/
│       ├── jquery.min.js             # jQuery
│       ├── bootstrap.bundle.min.js   # Bootstrap JS
│       └── bootstrap-select.min.js   # Bootstrap Select JS
│
└── .test/                            # 测试目录
    └── logs/                         # 测试日志
        ├── round1_result.json        # 第1轮测试结果
        ├── round2_result.json        # 第2轮测试结果
        └── round3_result.json        # 第3轮测试结果
```

### 数据库连接池规范

**关键原则**：
- 每个数据库操作独立获取/归还连接
- 不在实例变量中缓存连接
- 始终在 `finally` 块中释放资源

```python
# 正确示例
connection = self.get_connection()
cursor = None
try:
    cursor = connection.cursor()
    cursor.execute(query, params)
    return cursor.fetchall()
finally:
    if cursor:
        cursor.close()
    if connection:
        connection.close()  # 归还连接到池
```

### 前端 API 调用规范

**防抖控制**：
- GET 请求：200ms 防抖
- POST/PUT/DELETE 请求：500ms 防抖

```javascript
// 使用封装的 API 函数（base.html 已定义）
apiGet('/api/projects', { table: 'raw' }).then(res => { ... });
apiPost('/api/projects', data).then(res => { ... });
```

### 元数据字段类型

| field_type | 前端组件 | 存储规则 |
|-----------|---------|---------|
| `text` | 单行文本 | 原始值 |
| `textarea` | 多行文本 | 原始值 |
| `select` | 多选下拉 | 逗号分隔的 option_value |
| `link` | 超链接 | 完整 URL |
| `tags` | 标签云 | 逗号分隔的文本 |

### 逗号处理规则

- **前端输入**：识别中文逗号 `，` 和英文逗号 `,`
- **数据存储**：统一使用英文逗号 `,` 分隔
- **处理时机**：前端提交前将中文逗号替换为英文逗号

### 项目编号规则

```
格式: {TYPE}_{8位UUID}

TYPE:
- 原始数据: RAW
- 结果数据: RES

UUID规则:
- 字符集: 0-9, A-Z, a-z (共62个字符)
- 长度: 8位
- 示例: RAW_A1B2C3D4, RES_X9Y8Z7W6
```

## 核心功能模块

### 文件扫描（递归）

**功能特性**：
- 递归扫描 `/bio/downloads` 目录下的所有子目录（不限深度）
- 按顶层文件夹分组显示所有文件
- 自动计算每个顶层文件夹的文件总数
- 保留 DOI、数据库编号、数据类型检测功能
- 正确计算文件相对于 `/bio/downloads` 的相对路径

**相关方法**：
- `scan_downloads()` - 扫描下载目录（递归）
- `_parse_download_folder_recursive()` - 递归解析文件夹信息
- `_collect_files_recursive()` - 递归收集所有文件

**目录结构示例**：
```
/bio/downloads/
├── IBD/
│   ├── sample1.fastq
│   └── data/
│       ├── sample2.fastq
│       └── subfolder/
│           └── sample3.fastq
└── Cancer/
    └── analysis/
        └── result.csv
```

扫描结果将显示：
- **IBD** 文件夹：包含 3 个文件
- **Cancer** 文件夹：包含 1 个文件

### 文件校验（异步 Hash 计算）

**功能特性**：
- 异步计算文件的 MD5 和 SHA256 哈希值
- 支持大文件（GB 级别）计算，不会超时
- 实时显示计算进度（当前/总数，百分比）
- 批量计算多个文件
- 将哈希值保存到数据库

**技术实现**：
- **TaskManager**：异步任务管理器，使用后台线程执行计算
- **分块读取**：8KB 分块读取文件，避免内存问题
- **轮询机制**：前端每 7.5 秒查询一次任务状态
- **进度反馈**：实时显示计算进度和完成状态

**相关 API**：
- `POST /api/files/hash/calculate` - 创建异步计算任务，返回任务 ID
- `GET /api/files/hash/status/<task_id>` - 查询任务状态和进度
- `POST /api/files/hash/save` - 保存哈希值到数据库

**前端流程**：
1. 点击"校验"按钮打开校验弹窗
2. 选择要校验的文件
3. 点击"校验选中"创建异步任务
4. 系统立即返回任务 ID（不等待计算）
5. 前端每 7.5 秒轮询查询任务状态
6. 显示计算进度（正在计算 X/Y 文件）
7. 计算完成后显示结果（旧 Hash 值 vs 新 Hash 值）
8. 点击"保存校验"保存到数据库

**校验弹窗列设计（最新）**：

弹窗表格包含以下列：
1. 复选框 - 用于选择要校验的文件
2. 文件名 - 显示文件名称
3. 属性 - 显示文件属性
4. **MD5** - 显示 MD5 哈希值（旧值和新值对比）
5. **SHA256** - 显示 SHA256 哈希值（旧值和新值对比）

**MD5 列显示格式**：
```
旧：xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
新：xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**SHA256 列显示格式**：
```
旧：xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
新：xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**说明**：
- 初始状态："新："显示为灰色占位符 `-`
- 计算完成后：新 Hash 值替换占位符
- 字体大小：SHA256 列使用 0.875em 字体避免换行
- 弹窗宽度：95vw（页面宽度的 95%）

**大文件测试结果**：
- 47GB 文件计算时间：约 2-3 分钟
- API 响应时间：0 秒（立即返回）
- 超时问题：已彻底解决

### 批量删除文件（异步）

**功能特性**：
- 异步批量删除文件，支持大量文件删除操作
- 文件会被移动到回收站 `/bio/recycle`
- 不会因为文件过多或过大而超时
- 实时显示删除进度
- 自动更新项目文件计数

**技术实现**：
- **TaskManager**：异步任务管理器，使用后台线程执行删除
- **移动到回收站**：删除的文件会被移动到 `/bio/recycle` 目录
- **轮询机制**：前端每 7.5 秒查询一次任务状态
- **错误处理**：单个文件删除失败不影响其他文件

**相关 API**：
- `POST /api/files/delete/async` - 创建异步删除任务，返回任务 ID
- `GET /api/task/status/<task_id>` - 查询任务状态和进度

**前端流程**：
1. 在文件详情页选择要删除的文件
2. 点击"删除选中"按钮
3. 确认删除操作
4. 系统立即返回任务 ID（不等待删除完成）
5. 前端每 7.5 秒轮询查询任务状态
6. 显示删除进度
7. 删除完成后自动刷新列表并关闭弹窗

### 批量导入文件（异步）

**功能特性**：
- 异步批量导入文件，支持大量文件导入操作
- 支持新建项目和已有项目两种模式
- 支持原始数据和结果数据两种数据类型
- 不会因为文件过多或过大而超时
- 实时显示导入进度
- **导入时间戳优化**：使用任务创建时间（点击导入按钮时间）作为 `imported_at`，确保时间戳准确反映用户操作时间

**技术实现**：
- **TaskManager**：异步任务管理器，使用后台线程执行导入
- **路径生成**：根据元数据自动生成正确的文件存储路径
- **轮询机制**：前端每 7.5 秒查询一次任务状态
- **错误处理**：单个文件导入失败不影响其他文件
- **导入时间戳**：在 `import_files_async` 方法开始时获取当前时间，传递给 `add_file_record` 方法

**相关 API**：
- `POST /api/files/import/async` - 创建异步导入任务，返回任务 ID
- `GET /api/task/status/<task_id>` - 查询任务状态和进度

**前端流程**：
1. 在导入页面选择要导入的文件
2. 选择目标项目或创建新项目
3. 填写必要的元数据信息
4. 点击"导入"按钮
5. 系统立即返回任务 ID（不等待导入完成）
6. 前端每 7.5 秒轮询查询任务状态
7. 显示导入进度
8. 导入完成后自动刷新列表并关闭弹窗

**导入时间戳实现细节**：
- `backend.py:799-808` - `add_file_record` 方法添加 `imported_at` 参数
- `backend.py:1334-1344` - `_import_raw_files` 方法传递 `imported_at` 参数
- `backend.py:1414-1424` - `_import_result_files` 方法传递 `imported_at` 参数
- `backend.py:1290-1304` - `import_download_files` 方法传递 `imported_at` 参数
- `backend.py:1730-1754` - `import_files_async` 方法使用 `datetime.now()` 作为导入时间

### 引文解析

**支持的格式**：
- BibTeX (.bib)
- RIS (.ris)
- EndNote (.enw)

**相关方法**：
- `CitationParser` 类 - 引文解析器

### 数据类型配置

**原始数据类型（raw_type）**：

| 选项值 | 显示名称 | 缩写 | 序号 |
|--------|---------|------|------|
| mRNAseq | 转录组 | mRseq | 1 |
| Long-Read RNAseq | 长读转录组 | LRseq | 2 |
| lncRNAseq | lncRNAseq | lncseq | 3 |
| miRNAseq | miRNAseq | miseq | 4 |
| sRNAseq | 小RNA转录组 | srseq | 5 |
| epitRNAseq | 表观转录组 | epitseq | 6 |
| scRNAseq | 单细胞转录组 | scseq | 7 |
| LR-scRNAseq | 长读单细胞转录组 | LR_sc | 8 |
| 蛋白组 | 蛋白组 | pro | 9 |
| 磷酸化组 | 磷酸化组 | pho | 10 |
| 泛素化组 | 泛素化组 | ubi | 11 |
| 乙酰化组 | 乙酰化组 | acety | 12 |
| SUMO PTMome | SUMO PTMome | sumo | 13 |
| 甲基化组 | 甲基化组 | meth | 14 |
| 糖基化组 | 糖基化组 | glyco | 15 |
| 棕榈酰化组 | 棕榈酰化组 | pal | 16 |
| 代谢组 | 代谢组 | metab | 17 |
| 脂质组学 | 脂质组学 | lipo | 18 |
| 免疫组学 | 免疫组学 | immuno | 19 |
| **CyTOF** | **质谱流式** | **cytof** | **20** |
| 空间多组学 | 空间多组学 | spatial | 21 |

**新增 CyTOF 支持**：
- 选项值：`CyTOF`
- 显示名称：`质谱流式`
- 缩写：`cytof`
- 文件路径示例：`/bio/rawdata/cytof/{物种缩写}/{组织缩写}/{项目编号}/{文件名}`

## 数据库设计

### 核心数据表

| 表名 | 用途 |
|------|------|
| `field_config` | 元数据字段配置表 |
| `raw_project` | 原始数据项目表 |
| `result_project` | 结果数据项目表 |
| `file_record` | 文件记录表 |
| `select_options` | 下拉选项表 |
| `abbr_mapping` | 缩写映射表 |

### file_record 表结构（最新）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| file_name | VARCHAR(255) | 文件名 |
| file_path | VARCHAR(500) | 文件相对路径 |
| file_property | VARCHAR(500) | 文件属性 |
| file_size | BIGINT | 文件大小（字节） |
| file_type | VARCHAR(50) | 文件类型 |
| file_project_type | ENUM('raw','result') | 项目类型 |
| file_project_id | VARCHAR(50) | 项目编号 |
| file_project_ref_id | VARCHAR(50) | 关联项目编号 |
| file_MD5 | CHAR(32) | 文件 MD5 哈希值 |
| file_SHA256 | CHAR(64) | 文件 SHA256 哈希值 |
| imported_at | DATETIME | 导入时间（任务创建时间） |

**imported_at 字段说明**：
- 默认值：`CURRENT_TIMESTAMP`
- 异步导入时使用任务创建时间（点击导入按钮时间）
- 同步导入时使用文件实际插入数据库时间
- 格式：`YYYY-MM-DD HH:MM:SS`

### 文件存储路径规则

**原始数据文件路径**：
```
/bio/rawdata/{数据类型缩写}/{物种缩写}/{组织来源缩写}/{项目编号}/{文件名}
示例: /bio/rawdata/mRseq/Hs/Li/RAW_A1B2C3D4/sample1.fastq.gz
示例（CyTOF）: /bio/rawdata/cytof/Hs/Li/RAW_X1Y2Z3/sample.fcs
```

**结果数据文件路径**：
```
/bio/results/{分析类型}/{项目编号}[/{关联项目编号}]/{文件名}
示例: /bio/results/DEA/RES_X1Y2Z3/RAW_A1RAW_B2/heatmap.png
```

**回收站路径**：
```
/bio/recycle/{原文件相对路径}/{文件名}
示例: /bio/recycle/rawdata/mRseq/Hs/Li/RAW_A1B2C3D4/sample1.fastq.gz
```

## API 接口

### 页面路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页 |
| GET | `/raw-data` | 原始数据列表 |
| GET | `/results` | 结果管理列表 |
| GET | `/files` | 文件管理 |
| GET | `/metadata` | 元数据配置 |

### API 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/projects` | 获取项目列表 |
| POST | `/api/projects` | 创建项目 |
| DELETE | `/api/projects/<type>/<id>` | 删除项目 |
| GET | `/api/metadata/config` | 获取元数据配置 |
| GET | `/api/scan-downloads` | 扫描下载目录（异步） |
| GET | `/api/scan-downloads/sync` | 扫描下载目录（同步） |
| POST | `/api/files/import` | 导入文件（同步） |
| POST | `/api/files/import/async` | 导入文件（异步，带导入时间戳） |
| GET | `/api/files` | 获取项目文件列表（含 Hash 值和导入时间） |
| DELETE | `/api/files` | 删除文件记录（同步） |
| POST | `/api/files/delete/async` | 删除文件记录（异步） |
| GET | `/api/files/imported-projects` | 获取已导入项目列表 |
| POST | `/api/files/hash/calculate` | 异步计算文件哈希值 |
| GET | `/api/files/hash/status/<task_id>` | 查询哈希计算任务状态 |
| POST | `/api/files/hash/save` | 保存哈希值到数据库 |
| POST | `/api/files/download` | 下载文件 |
| GET | `/api/task/status/<task_id>` | 查询异步任务状态 |
| GET | `/api/tasks` | 获取所有任务列表 |

## 常见任务

### 添加新的元数据字段

1. 在 `field_config` 表中插入新字段配置
2. 如果是 `select` 类型，在 `select_options` 表中添加选项
3. 如果需要缩写映射，在 `abbr_mapping` 表中添加映射
4. 更新 `.env` 文件中的 `METADATA_FIELDS_*` 配置
5. 重启服务

### 修改字段显示顺序

修改 `.env` 文件中的字段序号配置：
```bash
# 调整字段顺序（逗号分隔的 field_seq）
METADATA_FIELDS_NEW_RAW=2,3,4,11,5
```

### 数据库初始化

```bash
# Docker 容器内运行
docker-compose exec biodata-manager python3 init_db.py

# 或本地运行
python3 app/init_db.py

# 强制重建模式（清空所有配置数据）
python3 app/init_db.py --force
```

### 添加新的数据类型（如 CyTOF）

1. 修改 `app/init_db.py` 中的三个位置：
   - `raw_type` 字段配置的 `field_options` JSON 数组
   - `raw_type_options` 列表
   - `raw_type_abbrs` 列表
2. 运行初始化脚本：
   ```bash
   docker-compose exec biodata-manager python3 init_db.py
   ```
3. 刷新页面即可看到新选项

### 测试文件扫描功能

```bash
# 创建测试目录结构
mkdir -p /bio/downloads/IBD/data/subfolder
mkdir -p /bio/downloads/Cancer/analysis

# 创建测试文件
touch /bio/downloads/IBD/sample1.fastq
touch /bio/downloads/IBD/data/sample2.fastq
touch /bio/downloads/IBD/data/subfolder/sample3.fastq
touch /bio/downloads/Cancer/analysis/result.csv

# 访问文件管理页面，点击"扫描"按钮
# 应该能看到 IBD 文件夹包含 3 个文件，Cancer 文件夹包含 1 个文件
```

### 测试文件校验功能

```bash
# 1. 导入文件到项目
# 2. 访问文件管理页面
# 3. 点击项目的"校验"按钮
# 4. 选择要校验的文件
# 5. 点击"校验选中"
# 6. 系统会异步计算哈希值，显示进度
# 7. 计算完成后显示旧 Hash 值和新 Hash 值（MD5 和 SHA256 分列显示）
# 8. 点击"保存校验"保存到数据库
```

### 测试异步批量删除功能

```bash
# 1. 导入多个文件到项目
# 2. 访问文件管理页面，点击项目的"查看"按钮
# 3. 选择多个文件
# 4. 点击"删除选中"按钮
# 5. 确认删除
# 6. 系统会异步删除文件，显示进度
# 7. 删除完成后自动刷新列表
# 8. 检查 /bio/recycle 目录，文件应该被移动到那里
```

### 测试异步批量导入功能

```bash
# 1. 在下载目录准备多个文件
# 2. 访问文件管理页面，点击"扫描"按钮
# 3. 选择一个文件夹，点击"导入"
# 4. 选择目标项目或创建新项目
# 5. 填写必要的元数据信息
# 6. 点击"导入"
# 7. 系统会异步导入文件，显示进度
# 8. 导入完成后自动刷新列表
# 9. 查看文件详情，确认导入时间戳正确显示
```

### 添加 Hash 字段到现有数据库

如果数据库是在添加 Hash 功能之前创建的，需要手动添加字段：

```sql
ALTER TABLE file_record 
ADD COLUMN file_MD5 CHAR(32) DEFAULT NULL COMMENT '文件MD5哈希值' AFTER file_project_ref_id,
ADD COLUMN file_SHA256 CHAR(64) DEFAULT NULL COMMENT '文件SHA256哈希值' AFTER file_MD5;
```

### 使用命令行查询数据库（解决中文乱码）

```bash
# 使用 utf8mb4 字符集查询，避免中文显示为乱码
docker-compose exec mysql mysql -uroot -prootpassword --default-character-set=utf8mb4 biodata -e "查询语句"

# 示例：查看所有数据类型选项
docker-compose exec mysql mysql -uroot -prootpassword --default-character-set=utf8mb4 biodata -e "SELECT option_value, option_label FROM select_options WHERE option_type = 'raw_type';"
```

## 相关文档

- [应用功能设计](./docs/应用功能设计.md) - 详细的功能模块设计文档
- [数据库设计规范](./docs/数据库设计规范.md) - 完整的数据库表结构和设计说明

## 注意事项

1. **文件路径配置**：系统使用硬编码路径 `/bio/rawdata`、`/bio/downloads`、`/bio/results`，确保 Docker 卷映射正确
2. **连接池管理**：数据库连接池大小为 20，支持并发请求
3. **字段配置依赖**：文件导入路径生成依赖特定字段（raw_type, raw_species, raw_tissue），确保这些字段在配置中包含
4. **环境变量更新**：修改环境变量后需要重启服务才能生效
5. **中文逗号处理**：前端已实现中文逗号自动转换为英文逗号，后端无需额外处理
6. **递归扫描性能**：深层嵌套目录结构可能影响扫描性能，建议合理组织目录层级
7. **隐藏文件**：扫描时会自动跳过以 `.` 开头的文件和目录
8. **大文件校验**：Hash 计算使用异步任务处理，大文件不会导致请求超时
9. **任务管理器**：任务状态存储在内存中，服务重启后任务会丢失，建议定期清理已完成任务
10. **Hash 值格式**：MD5 为 32 位十六进制字符串，SHA256 为 64 位十六进制字符串
11. **校验弹窗**：MD5 和 SHA256 分列显示，每列包含旧值和新值两行，便于对比
12. **弹窗宽度**：校验弹窗宽度为 95vw，确保长 Hash 值不换行
13. **轮询间隔**：所有异步任务状态查询间隔为 7.5 秒，减少服务器负载
14. **批量操作**：批量删除和批量导入都采用异步处理，避免超时问题
15. **回收站**：删除的文件会被移动到 `/bio/recycle` 目录，不会永久删除
16. **导入时间戳**：异步导入使用任务创建时间，确保时间戳准确反映用户操作时间
17. **字符集问题**：使用命令行查询数据库时，必须指定 `--default-character-set=utf8mb4` 参数，否则中文会显示为乱码
18. **模板缓存**：修改 Jinja2 模板文件后需要重启服务才能生效

## 版本信息

- **项目版本**: 1.4.0
- **数据库版本**: MySQL 8.x (LTS)
- **Python 版本**: 3.10
- **文档更新**: 2026-02-24
- **最新功能**: 
  - 导入时间戳优化（使用任务创建时间）
  - 递归文件扫描（多层子目录支持）
  - 异步 Hash 校验（支持大文件）
  - 异步批量删除（支持大量文件）
  - 异步批量导入（支持大量文件）
  - 文件 MD5/SHA256 计算
  - 任务管理系统
  - 轮询优化（7.5秒间隔）
  - 校验弹窗优化（MD5/SHA256 分列显示）
  - 回收站机制（文件移动而非永久删除）
  - 新增 CyTOF 数据类型（质谱流式）