---
title: Docker 部署
description: MGAgent 使用 Docker Compose 部署的完整指南，包括 SQLite 和 MySQL 两种方案
slug: /deployment/docker-deployment
---

# Docker 部署

## 概述

MGAgent 提供两种 Docker Compose 部署方案：

| 方案 | Compose 文件 | 适用场景 |
|------|-------------|---------|
| SQLite + ChromaDB | `docker-compose.local.yml` | 快速体验、单机部署 |
| MySQL + Milvus | `docker-compose.infra.yml` + `docker-compose.mysql-app.yml` | 生产环境、大规模数据 |

## 方式一：一键部署脚本（推荐）

```bash
# 添加执行权限
chmod +x scripts/deploy.sh

# 交互式选择方案
./scripts/deploy.sh

# 或直接指定方案
./scripts/deploy.sh sqlite    # SQLite + ChromaDB
./scripts/deploy.sh mysql     # MySQL + Milvus
```

## 方式二：手动 Docker Compose

### SQLite + ChromaDB 方案

```bash
# 构建并启动所有服务
docker compose -f docker-compose.local.yml up -d --build

# 查看服务状态
docker compose -f docker-compose.local.yml ps

# 查看日志
docker compose -f docker-compose.local.yml logs -f

# 停止服务
docker compose -f docker-compose.local.yml down
```

### 服务列表

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| mgagent-backend | 自建 | 8000:8000 | Chat 后端 API |
| mgagent-admin-backend | 自建 | 8001:8001 | Admin 后端 API |
| mgagent-frontend | 自建 | 3000:80 | Chat 前端 (Nginx) |
| mgagent-admin-frontend | 自建 | 3001:80 | Admin 前端 (Nginx) |

### 环境变量

```yaml
environment:
  - DATABASE_SCHEME=sqlite
  - SQLITE_DB_PATH=./data/sqlite/app.db
  - CHROMA_PATH=./data/chroma
  - DEBUG=True
  - API_HOST=0.0.0.0
  - API_PORT=8000
```

## Docker Compose 文件详解

### docker-compose.local.yml

SQLite + ChromaDB 全栈配置，包含所有 4 个服务：

```yaml
services:
  mgagent-backend:
    build:
      context: ./mgagent-backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_SCHEME=sqlite
      - SQLITE_DB_PATH=./data/sqlite/app.db
      - CHROMA_PATH=./data/chroma
    volumes:
      - ./mgagent-backend/data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      retries: 3

  mgagent-frontend:
    build:
      context: ./mgagent-frontend
      dockerfile: Dockerfile
    depends_on:
      - mgagent-backend
    ports:
      - "3000:80"
```

### docker-compose.infra.yml

MySQL + Milvus 基础设施配置：

```yaml
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./docker/mysql/init.sql:/docker-entrypoint-initdb.d/init.sql

  milvus:
    image: milvusdb/milvus:v2.4.12
    depends_on:
      - etcd
      - minio
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000

  etcd:
    image: quay.io/coreos/etcd:v3.5.5

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z

  attu:
    image: zilliz/attu:v2.4
    ports:
      - "8003:3000"
```

### docker-compose.mysql-app.yml

MySQL + Milvus 应用层配置：

```yaml
services:
  mgagent-backend:
    build:
      context: ./mgagent-backend
    environment:
      - DATABASE_SCHEME=mysql
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MILVUS_HOST=milvus
      - MILVUS_PORT=19530

  mgagent-admin-backend:
    build:
      context: ./mgagent-admin-backend

  mgagent-frontend:
    build:
      context: ./mgagent-frontend

  mgagent-admin-frontend:
    build:
      context: ./mgagent-admin-frontend
    depends_on:
      mgagent-admin-backend:
        condition: service_healthy
```

## 常用命令

```bash
# 启动服务
docker compose -f docker-compose.local.yml up -d

# 重新构建并启动
docker compose -f docker-compose.local.yml up -d --build

# 停止服务
docker compose -f docker-compose.local.yml down

# 查看日志
docker compose -f docker-compose.local.yml logs -f --tail=100

# 进入容器
docker exec -it mgagent-backend bash

# 清理所有数据
docker compose -f docker-compose.local.yml down -v

# 查看资源使用
docker stats
```

## 数据持久化

### SQLite 方案

数据存储在本地挂载目录：

```
mgagent-backend/data/
├── sqlite/
│   └── app.db          # SQLite 数据库文件
├── chroma/             # ChromaDB 向量数据
└── documents/          # 上传的文档
```

### MySQL 方案

数据存储在 Docker 命名卷：

```bash
# 查看数据卷
docker volume ls

# 备份 MySQL
docker run --rm -v mgagent_mysql_data:/data mysql:8.0 \
  mysqldump -u root -p${MYSQL_ROOT_PASSWORD} mgagent > backup.sql

# 恢复 MySQL
docker exec -i mgagent-mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} mgagent < backup.sql
```

## 网络配置

所有服务通过 `mgagent-network` 网络互联：

```yaml
networks:
  mgagent-network:
    driver: bridge
    name: mgagent-network
```

:::tip MySQL 方案
MySQL 方案使用 `mgagent-network` 外部网络，基础设施和应用层通过该网络通信。使用 `docker-compose.infra.yml` 启动基础设施后，网络会被自动创建。
:::

## 相关文档

- [MySQL 方案部署](/deployment/mysql-deployment)
- [生产部署](/deployment/production-deployment)
- [Docker 配置](/configuration/docker)