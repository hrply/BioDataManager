FROM python:3.10-slim

LABEL maintainer="hrply"
LABEL description="BioData Manager - Bioinformatics Data Management System"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app \
    DEBIAN_FRONTEND=noninteractive \
    # 设置pip使用清华源
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/ \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# ==================== 使用清华源配置 ====================

# 替换为清华源
RUN rm -f /etc/apt/sources.list.d/* && \
    rm -rf /etc/apt/sources.list

# 创建清华源sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security trixie-security main contrib non-free" >> /etc/apt/sources.list


# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# 设置pip镜像
COPY pip.conf /etc/pip.conf
COPY requirements.txt /app/requirements.txt

# 复制应用代码
COPY app/ /app/

# 安装Python依赖
RUN pip install --no-cache-dir -r /app/requirements.txt

# 复制入口脚本并设置执行权限
COPY app/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 暴露端口
EXPOSE 8000

# 设置入口点
ENTRYPOINT ["/docker-entrypoint.sh"]

# 默认命令
CMD ["python3", "server.py", "8000"]
