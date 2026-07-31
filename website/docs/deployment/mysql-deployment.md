---
title: MySQL 方案部署
description: MGAgent MySQL + Milvus 方案分层部署指南，包括基础设施和应用层
slug: /deployment/mysql-deployment
---

# MySQL 方案部署

## 概述

MySQL + Milvus 方案采用 **分层部署** 架构，将基础设施和应用层分离管理：

| 层级 | Compose 文件 | 包含服务 |
|------|-------------|---------|
| 基础设施 | `docker-compose.infra.yml` | MySQL、Milvus、etcd、MinIO、Attu |
| 应用层 | `docker-compose.prod.yml` | Chat 后端、Admin 后端、Chat 前端、Admin 前端 |

:::info 为什么分层
分层部署的好处是：
- 基础设施独立管理，重启应用不影响数据库
- 可以单独升级应用层而不中断数据服务
- 更灵活的资源分配和扩展
:::

## 前置条件

- Docker >= 20.10
- Docker Compose >= 2.0
- 至少 4 GB 可用内存
- 至少 10 GB 可用磁盘空间

## 第一步：配置镜像源（可选）

```bash
# 配置国内 Docker 镜像源
./scripts/docker-services.sh setup-mirror

# 检查镜像源配置
./scripts/docker-services.sh check-mirror
```

## 第二步：启动基础设施

```bash
# 方式一：使用脚本（推荐）
./scripts/docker-services.sh start

# 方式二：直接使用 Docker Compose
docker compose -f docker-compose.infra.yml up -d
```

### 基础设施服务列表

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| MySQL | mysql:8.0 | 3306:3306 | 关系数据库 |
| Milvus | milvusdb/milvus:v2.4.12 | 19530:19530 | 向量数据库 |
| etcd | quay.io/coreos/etcd:v3.5.5 | 2379 (内部) | Milvus 元数据存储 |
| MinIO | minio/minio:latest | 9000:9000 | Milvus 对象存储 |
| Attu | zilliz/attu:v2.4 | 8003:3000 | Milvus 管理界面 |

### 检查基础设施状态

```bash
# 查看服务状态
./scripts/docker-services.sh status

# 或使用 Docker Compose
docker compose -f docker-compose.infra.yml ps

# 等待基础设施就绪
sleep 20
```

### 验证 MySQL 连接

```bash
docker exec -it mgagent-mysql mysql -u mgagent -pmgagent_password_2024 -e "SELECT 1"
```

### 验证 Milvus 连接

```bash
# 检查 Milvus 健康状态
curl http://localhost:19530/healthz

# 通过 Attu 管理界面验证
# 访问 http://localhost:8003
```

## 第三步：启动应用层

```bash
# 方式一：使用 deploy.sh 脚本（已包含上述步骤）
./scripts/deploy.sh mysql

# 方式二：手动启动
docker compose -f docker-compose.prod.yml up -d --build
```

### 应用层服务列表

| 服务 | 端口 | 说明 |
|------|------|------|
| mgagent-backend | 8000:8000 | Chat 后端 API |
| mgagent-admin-backend | 8001:8001 | Admin 后端 API |
| mgagent-frontend | 3000:80 | Chat 前端 (Nginx) |
| mgagent-admin-frontend | 3001:80 | Admin 前端 (Nginx) |

### 环境变量配置

应用层通过 `.env.mysql` 文件连接基础设施：

```yaml
env_file:
  - .env.mysql
```

`.env.mysql` 中配置以下连接信息：

```
MYSQL_HOST=mysql          # Docker 内部服务名
MYSQL_PORT=3306
MYSQL_USER=mgagent
MYSQL_PASSWORD=${MYSQL_PASSWORD}
MYSQL_DATABASE=mgagent
MILVUS_HOST=milvus        # Docker 内部服务名
MILVUS_PORT=19530
```

:::warning 重要
在 Docker 网络中，服务间通信使用 **服务名** 而非 `localhost`。例如：
- MySQL 地址：`mysql:3306`（不是 `localhost:3306`）
- Milvus 地址：`milvus:19530`（不是 `localhost:19530`）
:::

## 访问系统

| 服务 | 地址 | 说明 |
|------|------|------|
| Chat 前端 | http://localhost:3000 | 智能对话 |
| Admin 前端 | http://localhost:3001 | 管理后台 |
| Attu | http://localhost:8003 | Milvus 管理 |
| MySQL | localhost:3306 | 数据库连接 |
| Milvus | localhost:19530 | 向量库连接 |

## 管理基础设施

```bash
# 查看基础设施状态
./scripts/docker-services.sh status

# 查看基础设施日志
./scripts/docker-services.sh logs

# 重启基础设施
./scripts/docker-services.sh restart

# 停止基础设施
./scripts/docker-services.sh stop

# 预热所有镜像
./scripts/docker-services.sh preload
```

## 环境变量文件

创建 `.env.mysql` 文件自定义配置：

```bash
cat > .env.mysql << 'EOF'
# MySQL 配置
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=mgagent
MYSQL_USER=mgagent
MYSQL_PASSWORD=your_password
MYSQL_PORT=3306

# Milvus 配置
MILVUS_PORT=19530
MILVUS_GRPC_PORT=9091

# 服务端口配置
BACKEND_PORT=8000
ADMIN_BACKEND_PORT=8001
FRONTEND_PORT=3000
ADMIN_FRONTEND_PORT=3001
EOF
```

## 数据迁移

### 从 SQLite 迁移到 MySQL

```bash
# 1. 启动 MySQL 基础设施
./scripts/docker-services.sh start

# 2. 启动应用层（MySQL 方案）
./scripts/deploy.sh mysql

# 3. 在 Admin 后台重新上传知识库文档
# （SQLite 的 ChromaDB 数据需要重新导入到 Milvus）
```

:::tip 注意
由于向量数据库的特殊性（ChromaDB 和 Milvus 的数据格式不兼容），知识库数据需要通过 Admin 后台重新上传。
:::

## 常见问题

### 基础设施启动慢

MySQL 和 Milvus 首次启动需要初始化数据，可能需要 1-2 分钟。使用 `healthcheck` 等待就绪。

### 连接被拒绝

确认基础设施已完全启动：

```bash
docker compose -f docker-compose.infra.yml ps
```

### Milvus 无法连接

检查 etcd 和 MinIO 是否正常运行：

```bash
docker logs mgagent-etcd --tail=50
docker logs mgagent-minio --tail=50
```

## 相关文档

- [双技术栈架构](/architecture/dual-stack)
- [Docker 部署](/deployment/docker-deployment)
- [生产部署](/deployment/production-deployment)
- [常见问题](/troubleshooting/common-issues)