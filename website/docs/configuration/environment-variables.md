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
# 复制模板
cp .env.example .env

# 编辑配置
vim .env
```

### 环境变量文件加载顺序

1. 系统环境变量（最高优先级）
2. `.env` 文件
3. 代码中的默认值

## 变量分类

### 基础配置

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `DATABASE_SCHEME` | `sqlite` / `mysql` | `sqlite` | 技术栈方案选择 |
| `API_HOST` | String | `0.0.0.0` | Chat 后端监听地址 |
| `API_PORT` | Int | `8000` | Chat 后端监听端口 |
| `ADMIN_API_URL` | String | `http://localhost:8001/admin/api` | Admin API 地址 |
| `DEBUG` | Boolean | `True` | 调试模式 |
| `SECRET_KEY` | String | 自动生成 | JWT 密钥 |

### SQLite 方案

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `SQLITE_DB_PATH` | String | `data/chat.db` | SQLite 数据库文件路径 |
| `CHROMA_PERSIST_DIR` | String | `data/chroma` | ChromaDB 持久化目录 |

### MySQL 方案

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

### 文档存储

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `DOCUMENT_DIR` | String | `data/documents` | 上传文档存储目录 |

### 端口映射（Docker）

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `BACKEND_PORT` | Int | `8000` | Chat 后端对外端口 |
| `ADMIN_BACKEND_PORT` | Int | `8001` | Admin 后端对外端口 |
| `FRONTEND_PORT` | Int | `3000` | Chat 前端对外端口 |
| `ADMIN_FRONTEND_PORT` | Int | `3001` | Admin 前端对外端口 |

## 使用示例

### SQLite 方案（最简配置）

```bash
# .env 文件
DATABASE_SCHEME=sqlite
DEBUG=True
```

### MySQL 方案

```bash
# .env 文件
DATABASE_SCHEME=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=mgagent
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mgagent
MILVUS_HOST=localhost
MILVUS_PORT=19530
DEBUG=False
```

### Docker 环境

Docker Compose 通过 `environment` 关键字传递环境变量：

```yaml
# docker-compose.local.yml
services:
  mgagent-backend:
    environment:
      - DATABASE_SCHEME=sqlite
      - SQLITE_DB_PATH=./data/sqlite/app.db
      - CHROMA_PATH=./data/chroma
      - DEBUG=True
```

## 配置模板

### .env.example

```bash
# MGAgent 环境变量配置示例
# 复制此文件为 .env 并修改配置

# 技术栈方案: sqlite 或 mysql
DATABASE_SCHEME=sqlite

# 后端服务配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Admin API 地址
ADMIN_API_URL=http://localhost:8001/admin/api

# JWT 密钥（生产环境请使用固定值）
# SECRET_KEY=your_secret_key_here

# SQLite 配置（DATABASE_SCHEME=sqlite 时使用）
SQLITE_DB_PATH=./data/app.db
CHROMA_PERSIST_DIR=./data/chroma

# MySQL 配置（DATABASE_SCHEME=mysql 时使用）
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=mgagent
# MYSQL_PASSWORD=your_password
# MYSQL_DATABASE=mgagent

# Milvus 配置（DATABASE_SCHEME=mysql 时使用）
# MILVUS_HOST=localhost
# MILVUS_PORT=19530
# MILVUS_COLLECTION=mgagent_knowledge

# 文档存储目录
DOCUMENT_DIR=./data/documents
```

### .env.prod（生产环境）

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

# 服务端口
BACKEND_PORT=8000
ADMIN_BACKEND_PORT=8001
FRONTEND_PORT=3000
ADMIN_FRONTEND_PORT=3001

# 调试模式关闭
DEBUG=False
```

## 代码中使用

### 读取配置

```python
from app.config.config import settings

# 读取基础配置
print(settings.DATABASE_SCHEME)  # "sqlite"
print(settings.API_PORT)         # 8000

# 条件判断
if settings.DATABASE_SCHEME == "mysql":
    # MySQL 方案
    pass
else:
    # SQLite 方案
    pass
```

### 获取数据库 URL

```python
from app.config.config import get_database_url

url = get_database_url()
# SQLite: "sqlite:////path/to/app.db"
# MySQL: "mysql+pymysql://mgagent:password@localhost:3306/mgagent?charset=utf8mb4"
```

## 环境变量与 Docker

### docker-compose.local.yml

```yaml
services:
  mgagent-backend:
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - DATABASE_SCHEME=sqlite
      - SQLITE_DB_PATH=./data/sqlite/app.db
      - CHROMA_PATH=./data/chroma
      - ADMIN_API_URL=http://mgagent-admin-backend:8001/admin/api
      - DEBUG=True
```

### docker-compose.mysql-app.yml

```yaml
services:
  mgagent-backend:
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - DATABASE_SCHEME=mysql
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=${MYSQL_USER:-mgagent}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD:-mgagent_password_2024}
      - MYSQL_DATABASE=${MYSQL_DATABASE:-mgagent}
      - MILVUS_HOST=milvus
      - MILVUS_PORT=19530
      - ADMIN_API_URL=http://mgagent-admin-backend:8001/admin/api
      - DEBUG=False
```

:::tip Docker 网络
在 Docker Compose 中，服务间通信使用 **服务名**（如 `mysql`、`milvus`），而不是 `localhost`。
:::

## 相关文档

- [Docker 配置](/configuration/docker)
- [Nginx 配置](/configuration/nginx)
- [双技术栈架构](/architecture/dual-stack)