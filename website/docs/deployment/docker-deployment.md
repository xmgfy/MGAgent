---
title: Docker 部署
description: MGAgent Docker Compose 部署完整指南，分层部署 MySQL + Milvus + 应用层
slug: /deployment/docker-deployment
---

# Docker 部署

## 概述

MGAgent 使用 Docker Compose 分层部署：

| 层级 | Compose 文件 | 包含服务 |
|------|-------------|---------|
| 基础设施 | `docker-compose.infra.yml` | MySQL、Milvus、etcd、MinIO、Attu |
| 应用层 | `docker-compose.prod.yml` | Chat 后端、Admin 后端、Chat 前端、Admin 前端 |

## 方式一：一键部署脚本（推荐）

```bash
# 添加执行权限
chmod +x scripts/deploy.sh

# 首次部署前，复制配置模板
cp .env.production.example .env.production

# 启动所有服务（自动构建镜像 + 启动基础设施和应用层）
./scripts/deploy.sh up

# 其他操作
./scripts/deploy.sh down       # 停止所有服务
./scripts/deploy.sh status     # 查看状态
./scripts/deploy.sh logs       # 查看日志
./scripts/deploy.sh restart    # 重启
```

## 方式二：手动 Docker Compose

### 第一步：启动基础设施

```bash
# 启动 MySQL + Milvus + etcd + MinIO + Attu
docker compose -f docker-compose.infra.yml up -d

# 查看状态
docker compose -f docker-compose.infra.yml ps
```

**基础设施服务列表**：

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| MySQL | mysql:8.0 | 3306:3306 | 关系数据库 |
| Milvus | milvusdb/milvus:v2.4.12 | 19530:19530 | 向量数据库 |
| etcd | quay.io/coreos/etcd:v3.5.5 | 2379 (内部) | Milvus 元数据存储 |
| MinIO | minio/minio:latest | 9000:9000 | Milvus 对象存储 |
| Attu | zilliz/attu:v2.4 | 8003:3000 | Milvus 管理界面 |

### 第二步：启动应用层

```bash
# 构建并启动所有应用服务
docker compose -f docker-compose.prod.yml up -d --build

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f
```

**应用层服务列表**：

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| mgagent-backend | 自建 | 8000:8000 | Chat 后端 API |
| mgagent-admin-backend | 自建 | 8001:8001 | Admin 后端 API |
| mgagent-frontend | 自建 | 3000:80 | Chat 前端 (Nginx) |
| mgagent-admin-frontend | 自建 | 3001:80 | Admin 前端 (Nginx) |

### 第三步：访问系统

| 服务 | 地址 | 说明 |
|------|------|------|
| Chat 前端 | http://localhost:3000 | 智能对话 |
| Admin 前端 | http://localhost:3001 | 管理后台 |
| Chat API | http://localhost:8000/docs | 后端 API 文档 |
| Admin API | http://localhost:8001/docs | 管理 API 文档 |
| Attu | http://localhost:8003 | Milvus 管理界面 |

## 环境变量配置

### `.env.production`

```bash
# MySQL 配置
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=mgagent
MYSQL_USER=mgagent
MYSQL_PASSWORD=your_password

# Milvus 配置
MILVUS_HOST=milvus
MILVUS_PORT=19530
MILVUS_COLLECTION=mgagent_knowledge

# MinIO 配置
MINIO_HOST=minio
MINIO_PORT=9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=mgagent-documents

# 服务端口
BACKEND_PORT=8000
ADMIN_BACKEND_PORT=8001
FRONTEND_PORT=3000
ADMIN_FRONTEND_PORT=3001
```

:::warning 注意
在 Docker 网络中，服务间通信使用 **服务名**（`mysql`、`milvus`）而非 `localhost`。
:::

## 数据持久化

数据存储在 Docker 命名卷：

```bash
# 查看数据卷
docker volume ls

# 备份 MySQL
docker exec mgagent-mysql mysqldump -u mgagent -p mgagent > backup.sql

# 恢复 MySQL
docker exec -i mgagent-mysql mysql -u mgagent -p mgagent < backup.sql
```

## 常用命令速查

```bash
# 启动基础设施
docker compose -f docker-compose.infra.yml up -d

# 启动应用层
docker compose -f docker-compose.prod.yml up -d --build

# 停止所有
docker compose -f docker-compose.infra.yml down
docker compose -f docker-compose.prod.yml down

# 重启
docker compose -f docker-compose.prod.yml restart

# 进入容器
docker exec -it mgagent-backend bash

# 查看资源使用
docker stats

# 清理所有数据卷（谨慎）
docker compose -f docker-compose.infra.yml down -v
```

## 网络配置

所有服务通过 `mgagent-network` 外部网络互联。`docker-compose.infra.yml` 创建网络，`docker-compose.prod.yml` 加入网络。

## 相关文档

- [MySQL 基础设施部署](/deployment/mysql-deployment)
- [生产部署](/deployment/production-deployment)
- [Docker 配置](/configuration/docker)
