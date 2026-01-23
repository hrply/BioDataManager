---
name: syntax-checker
description: 语法检查器 - 使用各语言对应的语法检查工具检查代码语法，而非让大语言模型读取代码进行检查
license: MIT
---

# 语法检查器

## 概述

专门使用各语言对应的语法检查工具对代码进行语法检查，避免大语言模型直接读取大量代码进行语法分析，提高检查效率和准确性。支持多种编程语言、标记语言和配置文件的语法检查。

## 核心能力

### 多语言支持

根据文件类型自动选择对应的语法检查工具：

| 语言 | 文件扩展名 | 主要工具 | 备选工具 | 安装命令 |
|-----|-----------|---------|---------|---------|
| **Python** | .py, .pyw | flake8 | pylint, mypy, py_compile | `pip install flake8 pylint mypy` |
| **JavaScript** | .js, .mjs | eslint | node -c | `npm install -g eslint` |
| **TypeScript** | .ts, .tsx | tsc, eslint | @typescript-eslint | `npm install -g typescript eslint` |
| **Java** | .java | javac | checkstyle, spotbugs | `apt install default-jdk checkstyle` |
| **Go** | .go | gofmt, go vet | golint, staticcheck | `go install golang.org/x/lint/golint@latest` |
| **Rust** | .rs | cargo check | rustc, clippy | `rustup component add clippy` |
| **C** | .c | gcc -fsyntax-only | clang-tidy | `apt install gcc clang-tidy` |
| **C++** | .cpp, .cc, .cxx | g++ -fsyntax-only | clang-tidy, cppcheck | `apt install g++ clang-tidy cppcheck` |
| **C#** | .cs | csc | dotnet build | `apt install mono-mcs` |
| **PHP** | .php | php -l | phpcs, phpstan | `apt install php-cli php-codesniffer` |
| **Ruby** | .rb | ruby -c | rubocop | `gem install rubocop` |
| **Shell** | .sh, .bash, .zsh | shellcheck | sh -n | `apt install shellcheck` |
| **Perl** | .pl, .pm | perl -c | perlcritic | `cpan Perl::Critic` |
| **Lua** | .lua | luac -p | luacheck | `luarocks install luacheck` |
| **Swift** | .swift | swiftc | swiftlint | `brew install swiftlint` |
| **Kotlin** | .kt, .kts | kotlinc -include-runtime | ktlint | `sdk install ktlint` |
| **Scala** | .scala | scalac | scalastyle | `apt install scala` |
| **R** | .r, .R | R CMD check | lintr | `R -e "install.packages('lintr')"` |
| **Dart** | .dart | dart analyze | dartanalyzer | `flutter pub global activate dart_code_metrics` |
| **Elixir** | .ex, .exs | mix compile | credo | `mix deps.get` |
| **Erlang** | .erl, .hrl | erlc | dialyzer | `apt install erlang` |
| **Haskell** | .hs | ghc -fno-code | hlint | `apt install ghc hlint` |
| **Clojure** | .clj | clojure -M | clj-kondo | `brew install clj-kondo` |
| **F#** | .fs, .fsx | dotnet build | fantomas | `dotnet tool install fantomas` |
| **OCaml** | .ml, .mli | ocamlc | dune build | `opam install dune` |
| **Scala** | .sc | scala | scalafmt | `cs setup` |
| **Groovy** | .groovy | groovy -n | codenarc | `sdk install groovy` |
| **Objective-C** | .m, .mm | gcc | clang | `apt install gcc gnustep` |
| **Solidity** | .sol | solc | solhint | `npm install -g solc solhint` |
| **Vyper** | .vy | vyc | vyperlint | `pip install vyper vyperlint` |
| **HTML** | .html, .htm | html5validator | tidy | `pip install html5validator` |
| **XML** | .xml | xmllint | xmlstarlet | `apt install libxml2-utils` |
| **JSON** | .json | python -m json.tool | jsonlint | `npm install -g jsonlint` |
| **YAML** | .yaml, .yml | python -m yaml | yamllint | `pip install pyyaml yamllint` |
| **TOML** | .toml | tomli (Python) | taplo | `pip install tomli` |
| **Markdown** | .md | markdownlint | mdl | `npm install -g markdownlint-cli` |
| **SQL** | .sql | sqlint | pgformatter | `pip install sqlint` |
| **Dockerfile** | Dockerfile | hadolint | dockerfilelint | `apt install hadolint` |
| **CSS** | .css | stylelint | csslint | `npm install -g stylelint` |
| **SCSS/SASS** | .scss, .sass | stylelint | sass-lint | `npm install -g stylelint-scss` |
| **Less** | .less | lessc | stylelint | `npm install -g less` |
| **Vue** | .vue | eslint + vue-eslint-parser | vetur | `npm install -g eslint-plugin-vue` |
| **Svelte** | .svelte | svelte-check | eslint-plugin-svelte | `npm install -g svelte-check` |
| **GraphQL** | .graphql, .gql | graphql-schema-linter | eslint-plugin-graphql | `npm install -g graphql-schema-linter` |
| **Proto** | .proto | protoc --descriptor_set_out | buf | `apt install protobuf-compiler` |
| **Terraform** | .tf | terraform validate | tflint | `terraform init` |
| **Ansible** | .yml | ansible-playbook --syntax-check | ansible-lint | `pip install ansible-lint` |
| **Puppet** | .pp | puppet parser validate | puppet-lint | `gem install puppet-lint` |
| **Chef** | .rb | foodcritic | rubocop | `gem install foodcritic` |

### 检查策略

根据文件数量和类型采用不同的检查策略：

| 场景 | 策略 | 说明 |
|-----|------|------|
| 单文件检查 | 逐个检查 | 调用对应工具检查单个文件 |
| 多文件同类型 | 批量检查 | 批量调用工具并汇总结果 |
| 多类型混合 | 分组检查 | 按类型分组后批量检查 |
| 整个项目 | 增量检查 | 只检查有变更的文件 |

### 错误处理

语法检查过程中可能遇到以下情况：

| 情况 | 处理方式 | 说明 |
|-----|---------|------|
| 工具未安装 | 跳过并提示 | 记录缺失的工具，建议安装 |
| 权限不足 | 尝试其他方式 | 或提示用户权限问题 |
| 文件不存在 | 跳过 | 记录跳过原因 |
| 工具超时 | 跳过并记录 | 避免阻塞整个检查流程 |

## 使用方法

### 自动调用

用户描述需求时自动调用：

```
用户: 检查 Python 文件语法
→ 自动调用 syntax-checker

用户: 运行 ESLint 检查 JS 代码
→ 自动调用 syntax-checker

用户: 验证项目所有文件的语法
→ 自动调用 syntax-checker

用户: 检查 Rust 代码
→ 自动调用 syntax-checker

用户: 运行 cargo check
→ 自动调用 syntax-checker
```

### 手动指定

在复杂场景中可以指定检查参数：

```
用户: syntax-checker 检查 src/*.py 只使用 flake8
→ 使用 flake8 检查指定文件

用户: syntax-checker 检查项目 生成 JSON 报告
→ 使用默认工具并输出 JSON 格式

用户: syntax-checker 检查 --language go --tool golint
→ 指定语言和工具
```

### 检查结果格式

支持多种输出格式：

| 格式 | 说明 | 使用场景 |
|-----|------|---------|
| 默认格式 | 简洁的错误信息 | 快速查看问题 |
| JSON 格式 | 结构化输出 | 程序处理、CI 集成 |
| SARIF 格式 | 安全分析结果 | 安全工具集成 |

### 返回示例

```json
{
  "success": true,
  "summary": {
    "total_files": 15,
    "checked_files": 15,
    "failed_files": 3,
    "total_errors": 12,
    "total_warnings": 5
  },
  "results": [
    {
      "file": "app/backend.py",
      "language": "python",
      "tool": "flake8",
      "status": "failed",
      "errors": [
        {
          "line": 15,
          "column": 1,
          "code": "E501",
          "message": "line too long (85 > 79 characters)",
          "type": "error"
        }
      ],
      "warnings": []
    },
    {
      "file": "src/utils.js",
      "language": "javascript",
      "tool": "eslint",
      "status": "failed",
      "errors": [
        {
          "line": 23,
          "column": 15,
          "code": "no-unused-vars",
          "message": "'unusedVar' is defined but never used",
          "type": "error"
        }
      ]
    }
  ]
}
```

## 依赖工具

### 必需工具

无需安装，直接可用的内置命令：

| 语言 | 内置命令 | 说明 |
|-----|---------|------|
| Python | `python3 -m py_compile` | 编译检查语法 |
| JavaScript | `node -c` | V8 语法检查 |
| PHP | `php -l` | PHP 语法检查 |
| Ruby | `ruby -c` | Ruby 语法检查 |
| Shell | `sh -n` | POSIX Shell 语法检查 |
| Perl | `perl -c` | Perl 语法检查 |
| Lua | `luac -p` | Lua 编译检查 |
| Go | `gofmt -e` | Go 格式化+错误检查 |
| XML | `xmllint` | XML 解析检查 |
| JSON | `python -m json.tool` | JSON 格式检查 |
| YAML | `python -c "import yaml"` | YAML 解析检查 |

### 推荐工具

建议安装以获得更详细的检查结果：

```bash
# ========== 静态语言 ==========
# Python
pip install flake8 pylint mypy black isort

# JavaScript/TypeScript
npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin prettier

# Java
apt install default-jdk checkstyle spotbugs
# 或使用 Maven/Gradle 插件

# Go
go install golang.org/x/lint/golint@latest
go install honnef.co/go/tools/cmd/staticcheck@latest

# Rust
rustup component add clippy rustfmt

# C/C++
apt install gcc g++ clang-tidy cppcheck

# Swift
brew install swiftlint

# Kotlin
sdk install ktlint

# ========== 脚本语言 ==========
# Ruby
gem install rubocop

# PHP
pear install PHP_CodeSniffer
composer require --dev phpstan/phpstan

# Perl
cpan Perl::Critic

# R
R -e "install.packages(c('lintr', 'styler'))"

# ========== Web 前端 ==========
# HTML/CSS
pip install html5validator
npm install -g stylelint csslint

# Vue
npm install -g eslint-plugin-vue vetur

# Svelte
npm install -g svelte-check

# ========== 基础设施 ==========
# Shell
apt install shellcheck

# Docker
apt install hadolint

# Terraform
tflint init

# SQL
pip install sqlint

# Markdown
npm install -g markdownlint-cli

# YAML
pip install yamllint

# ========== 数据格式 ==========
# GraphQL
npm install -g graphql-schema-linter

# Protocol Buffers
apt install protobuf-compiler
```

### 工具检测

技能启动时会检测可用工具：

```python
def detect_available_tools():
    """检测可用的语法检查工具"""
    tools = {
        # Python
        'flake8': shutil.which('flake8'),
        'pylint': shutil.which('pylint'),
        'mypy': shutil.which('mypy'),
        'black': shutil.which('black'),
        
        # JavaScript/TypeScript
        'eslint': shutil.which('eslint'),
        'tsc': shutil.which('tsc'),
        'prettier': shutil.which('prettier'),
        
        # Web
        'stylelint': shutil.which('stylelint'),
        'html5validator': shutil.which('html5validator'),
        'shellcheck': shutil.which('shellcheck'),
        
        # 编译型语言
        'gofmt': shutil.which('gofmt'),
        'rustc': shutil.which('rustc'),
        'cargo': shutil.which('cargo'),
        'gcc': shutil.which('gcc'),
        'g++': shutil.which('g++'),
        
        # 其他
        'hadolint': shutil.which('hadolint'),
        'sqlint': shutil.which('sqlint'),
        'markdownlint': shutil.which('markdownlint'),
        'yamllint': shutil.which('yamllint'),
    }
    return {k: v for k, v in tools.items() if v}
```

## 语言工具映射表

完整工具映射表，可直接复制到代码中使用：

```python
LANGUAGE_TOOLS = {
    'python': {
        'extensions': ['.py', '.pyw', '.pyi'],
        'tools': [
            {'name': 'flake8', 'install': 'pip install flake8', 'priority': 1},
            {'name': 'pylint', 'install': 'pip install pylint', 'priority': 2},
            {'name': 'mypy', 'install': 'pip install mypy', 'priority': 3},
            {'name': 'py_compile', 'install': None, 'builtin': True, 'priority': 10},
        ]
    },
    'javascript': {
        'extensions': ['.js', '.mjs', '.cjs'],
        'tools': [
            {'name': 'eslint', 'install': 'npm install -g eslint', 'priority': 1},
            {'name': 'node -c', 'install': None, 'builtin': True, 'priority': 10},
        ]
    },
    'typescript': {
        'extensions': ['.ts', '.tsx'],
        'tools': [
            {'name': 'tsc', 'install': 'npm install -g typescript', 'priority': 1},
            {'name': 'eslint', 'install': 'npm install -g eslint', 'priority': 2},
        ]
    },
    'java': {
        'extensions': ['.java'],
        'tools': [
            {'name': 'javac', 'install': 'apt install default-jdk', 'priority': 1},
            {'name': 'checkstyle', 'install': 'apt install checkstyle', 'priority': 2},
        ]
    },
    'go': {
        'extensions': ['.go'],
        'tools': [
            {'name': 'gofmt', 'install': None, 'builtin': True, 'priority': 1},
            {'name': 'go vet', 'install': 'go install golang.org/x/tools/cmd/vet@latest', 'priority': 2},
            {'name': 'golint', 'install': 'go install golang.org/x/lint/golint@latest', 'priority': 3},
        ]
    },
    'rust': {
        'extensions': ['.rs'],
        'tools': [
            {'name': 'cargo check', 'install': 'rustup component add rust-src', 'priority': 1},
            {'name': 'rustc --emit=metadata', 'install': None, 'builtin': True, 'priority': 10},
        ]
    },
    'c': {
        'extensions': ['.c', '.h'],
        'tools': [
            {'name': 'gcc -fsyntax-only', 'install': 'apt install gcc', 'priority': 1},
            {'name': 'clang-tidy', 'install': 'apt install clang-tidy', 'priority': 2},
        ]
    },
    'cpp': {
        'extensions': ['.cpp', '.cc', '.cxx', '.hpp'],
        'tools': [
            {'name': 'g++ -fsyntax-only', 'install': 'apt install g++', 'priority': 1},
            {'name': 'clang-tidy', 'install': 'apt install clang-tidy', 'priority': 2},
        ]
    },
    'php': {
        'extensions': ['.php'],
        'tools': [
            {'name': 'php -l', 'install': 'apt install php-cli', 'priority': 1},
            {'name': 'phpcs', 'install': 'pear install PHP_CodeSniffer', 'priority': 2},
        ]
    },
    'ruby': {
        'extensions': ['.rb'],
        'tools': [
            {'name': 'ruby -c', 'install': None, 'builtin': True, 'priority': 1},
            {'name': 'rubocop', 'install': 'gem install rubocop', 'priority': 2},
        ]
    },
    'shell': {
        'extensions': ['.sh', '.bash', '.zsh'],
        'tools': [
            {'name': 'shellcheck', 'install': 'apt install shellcheck', 'priority': 1},
            {'name': 'sh -n', 'install': None, 'builtin': True, 'priority': 10},
        ]
    },
    'perl': {
        'extensions': ['.pl', '.pm'],
        'tools': [
            {'name': 'perl -c', 'install': None, 'builtin': True, 'priority': 1},
        ]
    },
    'lua': {
        'extensions': ['.lua'],
        'tools': [
            {'name': 'luac -p', 'install': 'apt install lua5.3', 'priority': 1},
        ]
    },
    'swift': {
        'extensions': ['.swift'],
        'tools': [
            {'name': 'swiftc', 'install': 'xcode-select --install', 'priority': 1},
            {'name': 'swiftlint', 'install': 'brew install swiftlint', 'priority': 2},
        ]
    },
    'kotlin': {
        'extensions': ['.kt', '.kts'],
        'tools': [
            {'name': 'kotlinc', 'install': 'sdk install kotlin', 'priority': 1},
            {'name': 'ktlint', 'install': 'sdk install ktlint', 'priority': 2},
        ]
    },
    'html': {
        'extensions': ['.html', '.htm'],
        'tools': [
            {'name': 'html5validator', 'install': 'pip install html5validator', 'priority': 1},
        ]
    },
    'css': {
        'extensions': ['.css'],
        'tools': [
            {'name': 'stylelint', 'install': 'npm install -g stylelint', 'priority': 1},
        ]
    },
    'markdown': {
        'extensions': ['.md', '.markdown'],
        'tools': [
            {'name': 'markdownlint', 'install': 'npm install -g markdownlint-cli', 'priority': 1},
        ]
    },
    'json': {
        'extensions': ['.json'],
        'tools': [
            {'name': 'python -m json.tool', 'install': None, 'builtin': True, 'priority': 1},
        ]
    },
    'yaml': {
        'extensions': ['.yaml', '.yml'],
        'tools': [
            {'name': 'python -c "import yaml"', 'install': None, 'builtin': True, 'priority': 1},
            {'name': 'yamllint', 'install': 'pip install yamllint', 'priority': 2},
        ]
    },
    'dockerfile': {
        'extensions': ['Dockerfile', 'Containerfile'],
        'tools': [
            {'name': 'hadolint', 'install': 'apt install hadolint', 'priority': 1},
        ]
    },
    'sql': {
        'extensions': ['.sql'],
        'tools': [
            {'name': 'sqlint', 'install': 'pip install sqlint', 'priority': 1},
        ]
    },
    'vue': {
        'extensions': ['.vue'],
        'tools': [
            {'name': 'eslint --ext .vue', 'install': 'npm install -g eslint-plugin-vue', 'priority': 1},
        ]
    },
    'solidity': {
        'extensions': ['.sol'],
        'tools': [
            {'name': 'solc', 'install': 'npm install -g solc', 'priority': 1},
            {'name': 'solhint', 'install': 'npm install -g solhint', 'priority': 2},
        ]
    },
    'terraform': {
        'extensions': ['.tf'],
        'tools': [
            {'name': 'terraform validate', 'install': 'terraform init', 'priority': 1},
            {'name': 'tflint', 'install': 'tflint init', 'priority': 2},
        ]
    },
}
```

## 集成说明

### 与其他技能的配合

syntax-checker 可以与以下技能配合使用：

| 配合技能 | 场景 | 说明 |
|---------|------|------|
| fix-verification | 修复后语法验证 | 验证修复不引入新语法错误 |
| issue-analysis | 问题分析 | 辅助判断问题是语法还是逻辑 |
| test-plan | 测试计划 | 在测试计划中标记语法检查步骤 |

### 在 CI/CD 中使用

可以将 syntax-checker 集成到 CI/CD 流程：

```yaml
# GitHub Actions 示例
name: Syntax Check

on: [push, pull_request]

jobs:
  syntax-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install tools
        run: |
          pip install flake8
          npm install -g eslint
      
      - name: Run syntax checks
        run: |
          # Python
          find . -name "*.py" -exec flake8 {} +
          
          # JavaScript
          find . -name "*.js" -exec eslint {} +
          
          # Shell
          find . -name "*.sh" -exec shellcheck {} +
```

### 配置文件

支持通过配置文件自定义检查规则：

```json
// .syntax-checker.json
{
  "version": "1.0",
  "languages": {
    "python": {
      "tool": "flake8",
      "options": ["--max-line-length=120", "--ignore=E501,W503"],
      "extensions": [".py", ".pyw"]
    },
    "javascript": {
      "tool": "eslint",
      "options": ["--ext .js", "--cache", "--max-warnings=10"],
      "extensions": [".js", ".mjs"]
    },
    "shell": {
      "tool": "shellcheck",
      "options": ["--severity=warning"],
      "extensions": [".sh", ".bash"]
    }
  },
  "exclude": [
    "node_modules/**",
    "*.min.js",
    "dist/**",
    "build/**",
    ".git/**"
  ],
  "output": {
    "format": "json",
    "path": "syntax-check-results.json"
  },
  "parallel": true,
  "timeout": 30000
}
```

## 注意事项

### 性能考虑

- 大型项目建议使用增量检查
- 避免同时运行多个同类工具
- 设置合理的超时时间
- 使用缓存机制减少重复检查

### 环境差异

- 不同环境的工具版本可能不同
- 建议在 Dockerfile 中固定工具版本
- 跨平台工具的参数可能略有差异
- Windows/Linux/macOS 的工具路径可能不同

### 安全提示

- 语法检查工具可能执行代码片段
- 避免对不可信输入使用 eval 类功能
- 在隔离环境中运行外部工具
- 不要在生产环境运行未验证的工具

## 常见问题

### 问：为什么不用大语言模型检查语法？

大语言模型检查语法存在以下问题：

1. **效率低**：读取大量代码消耗大量 token
2. **不准确**：可能漏检或误判复杂语法
3. **成本高**：频繁调用增加使用成本
4. **速度慢**：网络延迟和模型推理耗时

专用工具检查语法更高效、更准确、更经济。

### 问：如何添加新的语言支持？

在 `LANGUAGE_TOOLS` 映射表中添加新条目：

```python
LANGUAGE_TOOLS = {
    '新语言': {
        'extensions': ['.ext1', '.ext2'],
        'tools': [
            {'name': 'primary_tool', 'install': '安装命令', 'priority': 1},
            {'name': 'backup_tool', 'install': '备选安装命令', 'priority': 2},
        ]
    }
}
```

然后在 `detect_available_tools()` 中添加工具检测逻辑。

### 问：工具检查出错怎么办？

1. 检查工具是否正确安装：`which <tool_name>`
2. 查看工具版本是否兼容：`tool_name --version`
3. 尝试更新工具到最新版本
4. 查看工具官方文档获取帮助
5. 尝试使用备选工具

### 问：如何只检查特定文件类型？

支持通过文件扩展名过滤：

```
用户: syntax-checker 只检查 .py 和 .js 文件
→ 只检查 Python 和 JavaScript 文件

用户: syntax-checker 检查 src/ --include "*.ts,*.tsx"
→ 只检查 TypeScript 文件
```

### 问：如何跳过某些文件或目录？

使用配置文件中的 `exclude` 字段：

```json
{
  "exclude": [
    "node_modules/**",
    "*.min.js",
    "vendor/**",
    "tests/__snapshots__/**"
  ]
}
```

或者在命令行指定：

```
syntax-checker --exclude "node_modules/**" --exclude "dist/**"
```