# 综合功能内测计划

## 一、测试目标

验证以下核心功能的正确性：
1. 文件下载功能 - 单文件/多文件打包下载
2. 文件删除功能 - 软删除到回收站，记录同步更新
3. 导入功能 - 追加到已有项目，字段正确合并
4. 逗号分隔处理 - 中英文逗号识别与转换
5. 关联项目字段 - results_raw 存储与渲染

## 二、测试环境

| 项目 | 说明 |
|------|------|
| 测试环境 | Docker Compose 启动的容器环境 |
| 数据库 | MySQL 8.x |
| 服务端口 | 5000 |
| 测试数据目录 | /home/hrply/software/bioscience/research/biodata_manager/data/downloads/test_import |

## 三、测试用例

### 3.1 文件下载功能测试

#### TC-DL-001: 单文件下载
**目的**: 验证单个文件能正确下载到本地

**前置条件**:
1. 存在至少一个项目，包含至少一个文件

**测试步骤**:
1. 调用 `GET /api/files?project_id={project_id}` 获取文件列表
2. 提取第一个文件的 file_id
3. 调用 `POST /api/files/download`，body: `{"file_ids": [file_id]}`
4. 检查响应状态码和 Content-Disposition

**预期结果**:
- 响应状态码 200
- Content-Type: application/zip
- Content-Disposition: attachment; filename="download.zip"
- ZIP 包内包含请求的文件

**验证点**:
- [ ] 下载响应正确
- [ ] 文件内容完整

#### TC-DL-002: 多文件打包下载
**目的**: 验证多个文件能打包成一个 ZIP 下载

**前置条件**:
1. 存在至少一个项目，包含至少 3 个文件

**测试步骤**:
1. 调用 `GET /api/files?project_id={project_id}` 获取文件列表
2. 提取前 3 个文件的 file_id
3. 调用 `POST /api/files/download`，body: `{"file_ids": [id1, id2, id3]}`
4. 解压 ZIP 文件，验证包含 3 个文件

**预期结果**:
- ZIP 包内包含所有请求的文件
- 文件名与原始文件名一致

**验证点**:
- [ ] 多文件打包正确
- [ ] 文件名无丢失

#### TC-DL-003: 下载不存在的文件
**目的**: 验证下载不存在的文件ID时返回错误

**测试步骤**:
1. 调用 `POST /api/files/download`，body: `{"file_ids": [99999]}`

**预期结果**:
- 响应状态码 404
- success: false
- message: "未找到要下载的文件"

### 3.2 文件删除功能测试

#### TC-DEL-001: 删除文件到回收站
**目的**: 验证删除文件后文件移动到 /bio/recycle 目录

**前置条件**:
1. 存在至少一个项目，包含至少一个文件
2. 记录文件的原始路径

**测试步骤**:
1. 调用 `GET /api/files?project_id={project_id}` 获取文件列表
2. 提取第一个文件的 file_id 和 file_path
3. 记录原始文件是否存在
4. 调用 `POST /api/files`，body: `{"file_ids": [file_id]}`, method: DELETE
5. 检查原始路径文件是否被删除
6. 检查 /bio/recycle 目录下是否存在对应文件

**预期结果**:
- 原始路径文件不存在
- /bio/recycle 目录下存在移动后的文件

**验证点**:
- [ ] 原始文件被删除
- [ ] 文件移动到 recycle 目录

#### TC-DEL-002: 删除后记录同步更新
**目的**: 验证删除文件后 file_record 删除，项目计数更新

**前置条件**:
1. 存在至少一个项目，记录其原始 file_count

**测试步骤**:
1. 调用 `GET /api/files?project_id={project_id}` 获取文件列表
2. 记录当前文件数量 N
3. 删除一个文件
4. 再次获取文件列表，检查数量变为 N-1
5. 调用 `GET /api/projects/raw/{project_id}` 检查 raw_file_count 更新

**预期结果**:
- file_record 删除
- 项目文件计数 raw_file_count 减 1

**验证点**:
- [ ] file_record 删除
- [ ] raw_file_count 更新

#### TC-DEL-003: 删除不存在的文件
**目的**: 验证删除不存在的文件ID时返回错误

**测试步骤**:
1. 调用 `POST /api/files`，body: `{"file_ids": [99999]}`, method: DELETE

**预期结果**:
- 响应状态码 404
- success: false
- message: "未找到要删除的文件"

### 3.3 导入功能测试

#### TC-IMP-001: 导入到已有原始数据项目
**目的**: 验证导入文件到已有项目时，metadata_override 正确合并到数据库

**前置条件**:
1. 存在一个原始数据项目 RAW_XXX
2. 该项目当前 raw_type="mRNAseq", raw_species="Homo sapiens"
3. 下载目录存在测试文件

**测试步骤**:
1. 调用 `GET /api/projects/raw/{project_id}` 获取项目当前 metadata
2. 调用 `POST /api/import-download`，body:
```json
{
    "project_id": "RAW_XXX",
    "files": ["test.fastq"],
    "folder_name": "test_import",
    "metadata_override": {
        "raw_type": "蛋白组",
        "raw_species": "Mus musculus",
        "raw_tissue": "Liver"
    },
    "data_type": "raw"
}
```
3. 调用 `GET /api/projects/raw/{project_id}` 检查 metadata 更新

**预期结果**:
- raw_type 更新为 "蛋白组"
- raw_species 更新为 "Mus musculus"
- raw_tissue 更新为 "Liver"

**验证点**:
- [ ] metadata_override 合并到数据库
- [ ] 字段值正确更新

#### TC-IMP-002: 导入到已有结果数据项目
**目的**: 验证导入结果文件到已有项目时，metadata 正确处理

**前置条件**:
1. 存在一个结果数据项目 RES_YYY
2. 该项目当前 results_raw 包含 RAW_XXX

**测试步骤**:
1. 调用 `POST /api/import-download`，body:
```json
{
    "project_id": "RES_YYY",
    "files": ["result.csv"],
    "folder_name": "test_import",
    "metadata_override": {
        "results_type": "DEA",
        "results_raw": "RAW_ZZZ"
    },
    "data_type": "result"
}
```
2. 调用 `GET /api/projects/result/{project_id}` 检查 metadata

**预期结果**:
- results_raw 追加 RAW_ZZZ（去重）

**验证点**:
- [ ] results_raw 正确追加
- [ ] 去重逻辑正确

#### TC-IMP-003: 导入后路径正确生成
**目的**: 验证导入文件后，file_path 和 file_property 正确生成

**前置条件**:
1. 存在一个原始数据项目
2. 下载目录存在测试文件

**测试步骤**:
1. 调用 `POST /api/import-download`，body 包含 metadata_override
2. 调用 `GET /api/files?project_id={project_id}` 获取文件记录
3. 检查 file_path 是否符合规范: `/bio/rawdata/{类型缩写}/{物种缩写}/{组织缩写}/{项目ID}/`
4. 检查 file_property 是否符合规范: `{类型}-{物种}-{组织}`

**预期结果**:
- file_path 格式正确
- file_property 使用英文逗号分隔

**验证点**:
- [ ] file_path 格式正确
- [ ] file_property 格式正确

### 3.4 逗号分隔处理测试

#### TC-COMMA-001: 中文逗号转英文
**目的**: 验证输入中文逗号时能正确转换为英文逗号存储

**测试步骤**:
1. 调用 `POST /api/projects`，body:
```json
{
    "table": "raw",
    "raw_title": "测试项目",
    "raw_type": "mRNAseq,蛋白组",
    "raw_species": "Homo sapiens，Mus musculus",
    "raw_tissue": "Liver，Kidney"
}
```

**预期结果**:
- raw_type 存储为 "mRNAseq,蛋白组"
- raw_species 存储为 "Homo sapiens,Mus musculus"
- raw_tissue 存储为 "Liver,Kidney"

**验证点**:
- [ ] 中文逗号转换为英文逗号
- [ ] 无多余空格

#### TC-COMMA-002: 多值存储格式
**目的**: 验证多值字段使用英文逗号分隔存储

**测试步骤**:
1. 创建项目，包含多个值的字段
2. 从数据库直接查询原始值
3. 检查逗号分隔格式

**预期结果**:
- 数据库存储值使用英文逗号分隔
- 无前后空格

#### TC-COMMA-003: 渲染时逗号处理
**目的**: 验证前端渲染时逗号分隔的值能正确显示

**测试步骤**:
1. 创建包含多值的项目
2. 调用 `GET /api/projects/raw/{project_id}`
3. 检查响应中的多值字段格式
4. 访问前端页面检查显示

**预期结果**:
- API 返回逗号分隔的原始值
- 前端正确渲染为标签或列表

### 3.5 关联项目字段测试

#### TC-REF-001: results_raw 存储格式
**目的**: 验证 results_raw 字段正确存储逗号分隔的项目ID

**前置条件**:
1. 存在至少 2 个原始数据项目

**测试步骤**:
1. 调用 `POST /api/projects`，body:
```json
{
    "table": "result",
    "results_title": "测试结果",
    "results_type": "DEA",
    "results_raw": "RAW_A,RAW_B,RAW_C"
}
```
2. 调用 `GET /api/projects/result/{project_id}`
3. 检查 results_raw 值

**预期结果**:
- results_raw 存储为 "RAW_A,RAW_B,RAW_C"

**验证点**:
- [ ] 逗号分隔存储
- [ ] 顺序保持

#### TC-REF-002: results_raw 排序逻辑
**目的**: 验证关联项目ID按 ASCII 顺序排序后存储

**测试步骤**:
1. 调用 `POST /api/projects`，body:
```json
{
    "table": "result",
    "results_title": "排序测试",
    "results_type": "DEA",
    "results_raw": "RAW_z,RAW_A,RAW_B,RAW_1"
}
```
2. 检查存储的 results_raw 值

**预期结果**:
- 存储顺序: "RAW_1,RAW_A,RAW_B,RAW_z" (ASCII 排序)

**验证点**:
- [ ] 按 ASCII 排序
- [ ] 数字 < 大写字母 < 小写字母

#### TC-REF-003: results_raw 去重逻辑
**目的**: 验证追加关联项目时能正确去重

**前置条件**:
1. 已存在结果项目，results_raw="RAW_A,RAW_B"

**测试步骤**:
1. 调用 `POST /api/projects/result/{project_id}/metadata`，body:
```json
{
    "field_id": "results_raw",
    "new_value": "RAW_B,RAW_C,RAW_D"
}
```

**预期结果**:
- results_raw 更新为 "RAW_A,RAW_B,RAW_C,RAW_D"
- RAW_B 不重复

**验证点**:
- [ ] 正确去重
- [ ] 保持原顺序

## 四、测试数据准备

### 4.1 测试文件
```bash
# 测试文件路径
/data/downloads/test_import/sample.fastq
/data/downloads/test_import/test_raw_001.fastq
/data/downloads/test_import/test_raw_002.fastq
/data/downloads/test_import/test_res_001.txt
/data/downloads/test_import/test_res_002.txt
```

### 4.2 预置项目
- RAW_TEST001: 测试原始数据项目
- RES_TEST001: 测试结果数据项目

## 五、执行步骤

1. 启动 Docker 服务
2. 确保数据库有初始数据
3. 准备测试文件
4. 按顺序执行测试用例
5. 记录测试结果
6. 汇总问题清单

## 六、验收标准

| 类别 | 通过标准 |
|------|---------|
| 文件下载 | TC-DL-001, TC-DL-2 通过 |
| 文件删除 | TC-DEL-001, TC-DEL-002 通过 |
| 导入功能 | TC-IMP-001, TC-IMP-002, TC-IMP-003 通过 |
| 逗号处理 | TC-COMMA-001, TC-COMMA-002 通过 |
| 关联字段 | TC-REF-001, TC-REF-002 通过 |

**通过率要求**: >= 90%

## 七、风险评估

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 数据库无初始数据 | 测试无法执行 | 确保 init_db.py 执行 |
| 测试文件不存在 | 导入测试失败 | 预先创建测试文件 |
| 网络超时 | API 测试超时 | 增加重试机制 |

---

**计划创建时间**: 2026-01-26
**预计执行时间**: 30 分钟
**测试人员**: iFlow CLI
