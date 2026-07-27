# MGAgent Backend Dockerfile
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p data/documents data/chroma

# 设置环境变量
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV DATABASE_URL=mysql+pymysql://mgagent:mgagent_password_2024@mysql:3306/mgagent?charset=utf8mb4
ENV MILVUS_HOST=milvus
ENV MILVUS_PORT=19530
ENV ADMIN_API_URL=http://mgagent-admin-backend:8001/admin/api
ENV DEBUG=False

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
