---
title: Docker 配置
description: MGAgent Docker Compose 配置详解，包括镜像源、网络、数据卷等
slug: /configuration/docker
---

# Docker 配置

## 概述

MGAgent 使用 Docker Compose 进行容器化部署，支持 SQLite 和 MySQL 两种方案。

## Compose 文件说明

| 文件 | 用途 | 包含服务 |
|------|------|---------|
| `docker-compose.prod.yml` | 生产环境全栈 | 4 个应用服务 |
| `docker-compose.infra.yml` | MySQL + Milvus 基础设施 | 5 个基础设施服务 |

## Docker 镜像源配置

### 配置国内镜像源

```bash
# 使用脚本配置（推荐）
./scripts/docker-services.sh setup-mirror

# 手动配置
mkdir -p ~/.docker
cat > ~/.docker/daemon.json << 'EOF'
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://docker.1panel.live",
    "https://docker.1ms.run",
    "https://docker.m.daocloud.io",
    "https://hub-mirror.c.163.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF

# 重启 Docker
sudo systemctl restart docker
```

### 检查镜像源

```bash
./scripts/docker-services.sh check-mirror
```

### 预热镜像

```bash
# 预热所有必需的 Docker 镜像
./scripts/docker-services.sh preload
```

需要预热的镜像：

| 镜像 | 用途 |
|------|------|
| `mysql:8.0` | MySQL 数据库 |
| `milvusdb/milvus:v2.4.12` | Milvus 向量数据库 |
| `quay.io/coreos/etcd:v3.5.5` | Milvus etcd 依赖 |
| `minio/minio:RELEASE.2023-03-20T20-16-18Z` | Milvus MinIO 依赖 |
| `zilliz/attu:v2.4` | Milvus 管理界面 |
| `python:3.10-slim` | 后端构建基础镜像 |
| `node:18-alpine` | 前端构建基础镜像 |
| `nginx:alpine` | 前端部署镜像 |

## 网络配置

### 网络定义

所有服务通过 `mgagent-network` 网络互联：

```yaml
networks:
  mgagent-network:
    driver: bridge
    name: mgagent-network
```

### SQLite 方案

`docker-compose.prod.yml` 内部自动创建网络：

```yaml
networks:
  mgagent-network:
    driver: bridge
```

### MySQL 方案

MySQL 方案使用外部网络，因为基础设施和应用层分属不同的 Compose 文件：

```yaml
# docker-compose.infra.yml
networks:
  mgagent-network:
    driver: bridge
    name: mgagent-network

# docker-compose.prod.yml
networks:
  mgagent-network:
    external: true
    name: mgagent-network
```

:::tip 注意
MySQL 方案必须先启动基础设施（`docker-compose.infra.yml`），网络会被自动创建。然后应用层才能加入该网络。
:::

## 数据卷配置

### SQLite 方案

SQLite 方案使用本地目录挂载：

```yaml
services:
  mgagent-backend:
    volumes:
      - ./mgagent-backend/data:/app/data
```

### MySQL 方案

MySQL 方案使用 Docker 命名卷：

```yaml
volumes:
  mysql_data:
    driver: local
  milvus_data:
    driver: local
  etcd_data:
    driver: local
  minio_data:
    driver: local
```

### 查看和管理数据卷

```bash
# 查看所有数据卷
docker volume ls

# 查看数据卷详情
docker volume inspect mgagent_mysql_data

# 备份 MySQL
docker run --rm -v mgagent_mysql_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/mysql-backup.tar.gz /data

# 恢复 MySQL
docker run --rm -v mgagent_mysql_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/mysql-backup.tar.gz -C /
```

## 服务依赖

### SQLite 方案

```yaml
services:
  mgagent-frontend:
    depends_on:
      - mgagent-backend

  mgagent-admin-frontend:
    depends_on:
      mgagent-admin-backend:
        condition: service_healthy
```

### MySQL 方案

```yaml
# 基础设施内部依赖
services:
  milvus:
    depends_on:
      - etcd
      - minio

  attu:
    depends_on:
      - milvus

# 应用层依赖
  mgagent-frontend:
    depends_on:
      - mgagent-backend

  mgagent-admin-frontend:
    depends_on:
      mgagent-admin-backend:
        condition: service_healthy
```

## 健康检查

所有服务都配置了健康检查：

```yaml
# 后端 API 健康检查
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 15s

# MySQL 健康检查
healthcheck:
  test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
  interval: 10s
  timeout: 5s
  retries: 5

# Milvus 健康检查
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
  interval: 10s
  timeout: 5s
  retries: 5
```

## 资源限制

### 生产环境配置

```yaml
services:
  mgagent-backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 1G
          cpus: '1'

  mysql:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'

  milvus:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'
```

## 日志配置

### Docker 日志轮转

在 `/etc/docker/daemon.json` 中配置：

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
```

### 查看服务日志

```bash
# SQLite 方案
docker compose -f docker-compose.prod.yml logs -f --tail=100

# MySQL 基础设施
docker compose -f docker-compose.infra.yml logs -f --tail=50

# MySQL 应用层
docker compose -f docker-compose.prod.yml logs -f --tail=50

# 单个服务日志
docker logs mgagent-backend --tail=100 -f
```

## 常用 Docker 命令

```bash
# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 构建并启动
docker compose -f docker-compose.prod.yml up -d --build

# 停止服务
docker compose -f docker-compose.prod.yml down

# 重启服务
docker compose -f docker-compose.prod.yml restart

# 进入容器
docker exec -it mgagent-backend bash

# 查看资源使用
docker stats

# 清理所有容器（保留数据卷）
docker compose -f docker-compose.prod.yml down

# 清理所有容器和数据卷
docker compose -f docker-compose.prod.yml down -v

# 查看容器状态
docker compose -f docker-compose.prod.yml ps
```

## 常见问题

### 端口冲突

```bash
# 查看端口占用
lsof -i :3000 :3001 :8000 :8001

# 修改 Compose 文件中的端口映射
ports:
  - "8000:8000"  # 改为 "8080:8000"
```

### 镜像拉取慢

```bash
# 使用国内镜像源
./scripts/docker-services.sh setup-mirror

# 预热镜像
./scripts/docker-services.sh preload
```

### 容器无法通信

```bash
# 检查网络
docker network inspect mgagent-network

# 重新创建网络
docker network rm mgagent-network
docker compose -f docker-compose.infra.yml up -d
```

## 相关文档

- [Docker 部署](/deployment/docker-deployment)
- [MySQL 方案部署](/deployment/mysql-deployment)
- [环境变量配置](/configuration/environment-variables)