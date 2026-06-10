FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 环境参数 - 必须通过 --build-arg 指定
ARG ENVIRONMENT

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY deploy/gunicorn_config.py .

# 复制对应环境的启动脚本
COPY deploy/${ENVIRONMENT}/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 暴露端口（仅作文档说明）
EXPOSE 8000

# 使用启动脚本启动
ENTRYPOINT ["/app/start.sh"]
