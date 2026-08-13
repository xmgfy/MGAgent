---
title: 环境变量配置
description: MGAgent 所有环境变量的详细说明、默认值和使用方法
slug: /configuration/environment-variables
---

# 环境变量配置

## 概述

MGAgent 使用环境变量来控制服务行为。所有配置通过 Pydantic BaseSettings 自动加载，支持 `.env` 文件和系统环境变量。

## 配置文件

### .env 文件

```bash
# 生产环境配置
cp .env.production.example .env.production

# 本地开发直接使用 .env
```

### 环境变量文件加载顺序

1. 系统环境变量（最高优先级）
2. `.env` 文件
3. 代码中的默认值

## 变量分类

### 基础配置

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `API_HOST` | String | `0.0.0.0` | Chat 后端监听地址 |
| `API_PORT` | Int | `8000` | Chat 后端监听端口 |
| `ADMIN_API_URL` | String | `http://localhost:8001/admin/api` | Admin API 地址 |
| `DEBUG` | Boolean | `True` | 调试模式 |
| `SECRET_KEY` | String | 自动生成 | JWT 密钥 |

### MySQL 配置

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `MYSQL_HOST` | String | `localhost` | MySQL 主机地址 |
| `MYSQL_PORT` | Int | `3306` | MySQL 端口 |
| `MYSQL_USER` | String | `mgagent` | MySQL 用户名 |
| `MYSQL_PASSWORD` | String | `mgagent_password_2024` | MySQL 密码 |
| `MYSQL_DATABASE` | String | `mgagent` | MySQL 数据库名 |

### Milvus 配置

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `MILVUS_HOST` | String | `localhost` | Milvus 主机地址 |
| `MILVUS_PORT` | Int | `19530` | Milvus 端口 |
| `MILVUS_COLLECTION` | String | `mgagent_knowledge` | Milvus 集合名称 |

### MinIO 配置

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `MINIO_HOST` | String | `localhost` | MinIO 主机地址 |
| `MINIO_PORT` | Int | `9000` | MinIO API 端口 |
| `MINIO_ACCESS_KEY` | String | `minioadmin` | MinIO 访问密钥 |
| `MINIO_SECRET_KEY` | String | `minioadmin` | MinIO 密钥 |
| `MINIO_BUCKET` | String | `mgagent` | MinIO 存储桶名称 |

### 端口映射（Docker）

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `BACKEND_PORT` | Int | `8000` | Chat 后端对外端口 |
| `ADMIN_BACKEND_PORT` | Int | `8001` | Admin 后端对外端口 |
| `FRONTEND_PORT` | Int | `3000` | Chat 前端对外端口 |
| `ADMIN_FRONTEND_PORT` | Int | `3001` | Admin 前端对外端口 |

## 使用示例

### 本地开发

```bash
# 确保 .env 中已配置 MySQL + Milvus + MinIO 连接信息
# 启动 Docker 基础设施
./scripts/docker-services.sh start

# 启动服务（自动加载 .env）
./scripts/start-all.sh
```

### Docker 环境

生产环境使用 `docker-compose.prod.yml`，通过 `.env.production` 文件传递环境变量：

```yaml
# docker-compose.prod.yml
services:
  mgagent-backend:
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MILVUS_HOST=milvus
      - MILVUS_PORT=19530
      - MINIO_HOST=minio
      - MINIO_PORT=9000
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - MINIO_BUCKET=mgagent
      - ADMIN_API_URL=http://mgagent-admin-backend:8001/admin/api
      - DEBUG=False
```

## 配置模板

### .env（本地开发）

```bash
# MGAgent 本地开发配置
# 统一使用 MySQL + Milvus + MinIO 技术栈

API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# MySQL 配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=mgagent
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mgagent

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=mgagent_knowledge

# MinIO 配置
MINIO_HOST=localhost
MINIO_PORT=9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=mgagent

# Admin API 地址
ADMIN_API_URL=http://localhost:8001/admin/api
```

### .env.production（生产环境）

```bash
# MySQL 配置
MYSQL_ROOT_PASSWORD=strong_root_password
MYSQL_DATABASE=mgagent
MYSQL_USER=mgagent
MYSQL_PASSWORD=strong_password
MYSQL_PORT=3306

# Milvus 配置
MILVUS_PORT=19530
MILVUS_GRPC_PORT=9091

# MinIO 配置
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key

# 服务端口
CHAT_FRONTEND_PORT=3000
ADMIN_FRONTEND_PORT=3001
CHAT_BACKEND_PORT=8000
ADMIN_BACKEND_PORT=8001
ATTU_PORT=8003
```

## 代码中使用

### 读取配置

```python
from app.config.config import settings

# 读取基础配置
print(settings.API_PORT)         # 8000

# MySQL 连接信息
print(settings.MYSQL_HOST)      # localhost
print(settings.MYSQL_DATABASE)  # mgagent
```

### 获取数据库 URL

```python
from app.config.config import get_database_url

url = get_database_url()
# "mysql+pymysql://mgagent:password@localhost:3306/mgagent?charset=utf8mb4"
```

## 环境变量与 Docker

### docker-compose.prod.yml（生产环境）

```yaml
services:
  mgagent-backend:
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MILVUS_HOST=milvus
      - MILVUS_PORT=19530
      - MINIO_HOST=minio
      - MINIO_PORT=9000
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - MINIO_BUCKET=mgagent
      - ADMIN_API_URL=http://mgagent-admin-backend:8001/admin/api
      - DEBUG=False
```

:::tip Docker 网络
在 Docker Compose 中，服务间通信使用 **服务名**（如 `mysql`、`milvus`、`minio`），而不是 `localhost`。
:::

## 相关文档

- [Docker 配置](/configuration/docker)
- [Nginx 配置](/configuration/nginx)
