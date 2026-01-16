#!/bin/bash
#!/usr/bin/env bash
#
# BioData Manager - Docker 入口脚本
# 生物信息学数据管理系统 - 容器启动脚本
#

set -e

echo "========================================"
echo "BioData Manager 容器启动"
echo "========================================"

# 等待MySQL就绪
wait_for_mysql() {
    echo "等待 MySQL 服务就绪..."
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if mysqladmin ping -h "${MYSQL_HOST:-mysql}" -u "${MYSQL_USER:-biodata}" -p"${MYSQL_PASSWORD:-biodata123}" --ssl=0 --silent 2>/dev/null; then
            echo "MySQL 服务已就绪!"
            return 0
        fi
        
        echo "  尝试 $attempt/$max_attempts - 等待 2 秒..."
        sleep 2
        ((attempt++))
    done
    
    echo "警告: MySQL 服务未能及时就绪，继续启动..."
    return 1
}

# 初始化数据库
init_database() {
    echo "检查并初始化数据库..."
    
    python3 /app/init_db.py
    
    if [ $? -eq 0 ]; then
        echo "数据库初始化完成"
    else
        echo "警告: 数据库初始化出现问题"
    fi
}

# 主入口
main() {
    # 等待MySQL
    wait_for_mysql
    
    # 初始化数据库
    init_database
    
    # 启动应用
    echo "启动 BioData Manager..."
    
    # 解析参数：跳过 python3 和 server.py，获取端口
    shift 2
    PORT="${1:-8000}"
    
    # 确保端口是数字
    if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
        PORT=8000
    fi
    
    echo "监听端口: $PORT"
    echo "========================================"
    
    exec python3 /app/server.py "$PORT"
}

# 执行主函数
main "$@"
