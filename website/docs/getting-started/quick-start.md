---
title: 快速开始
description: MGAgent 快速上手指南，包括 Docker 部署和本地开发两种模式
slug: /getting-started/quick-start
---

# 快速开始

:::tip 推荐方式
推荐使用 **Docker Compose** 一键部署，最快 5 分钟即可完成全部搭建。
:::

## 方式一：Docker 一键部署（推荐）

### 1. 运行部署脚本

```bash
# 添加执行权限
chmod +x scripts/deploy.sh

# 交互式选择方案
./scripts/deploy.sh
```

### 2. 选择部署方案

脚本提供两种技术栈方案：

| 选项 | 方案 | 适用场景 |
|------|------|---------|
| 1 | SQLite + ChromaDB | 轻量级单机部署，开发调试 |
| 2 | MySQL + Milvus | 高性能生产部署，大规模数据 |

```bash
# 或直接指定方案
./scripts/deploy.sh sqlite    # SQLite + ChromaDB
./scripts/deploy.sh mysql     # MySQL + Milvus
```

### 3. 访问系统

| 服务 | 地址 | 说明 |
|------|------|------|
| Chat 前端 | http://localhost:3000 | 智能对话助手 |
| Admin 前端 | http://localhost:3001 | 管理后台 |
| Chat API | http://localhost:8000 | 后端 API |
| Admin API | http://localhost:8001 | 管理 API |

**MySQL + Milvus 方案额外服务：**

| 服务 | 地址 | 说明 |
|------|------|------|
| Attu | http://localhost:8003 | Milvus 向量库管理界面 |
| MySQL | localhost:3306 | 关系数据库 |
| Milvus | localhost:19530 | 向量数据库 |

### 4. 部署脚本命令速查

```bash
./scripts/deploy.sh sqlite      # 启动 SQLite 方案
./scripts/deploy.sh mysql       # 启动 MySQL 方案
./scripts/deploy.sh stop        # 停止所有服务
./scripts/deploy.sh restart     # 重启服务
./scripts/deploy.sh status      # 查看状态
./scripts/deploy.sh logs        # 查看日志
./scripts/deploy.sh cleanup     # 清理所有数据
```

### 5. 默认账号

```
管理员: admin / admin123
MySQL:  mgagent / mgagent_password_2024
```

## 方式二：本地开发模式

### 1. 初始化项目

```bash
# 一键初始化（安装依赖、创建目录）
chmod +x scripts/init.sh
./scripts/init.sh
```

该脚本会自动完成：
- 安装 `mgagent-backend` Python 依赖
- 安装 `mgagent-admin-backend` Python 依赖
- 安装 `mgagent-frontend` Node.js 依赖
- 安装 `mgagent-admin-frontend` Node.js 依赖
- 创建必要的数据目录

### 2. 启动服务

```bash
# 启动所有服务
./scripts/start-all.sh

# 停止所有服务
./scripts/stop-all.sh

# 检查服务状态
./scripts/status.sh
```

### 3. 手动启动（可选）

如需单独启动某个服务：

```bash
# Chat 后端 (端口: 8000)
cd mgagent-backend
# 使用 .env.sqlite 配置
source .env.sqlite
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Admin 后端 (端口: 8001)
cd mgagent-admin-backend
# 使用 .env.sqlite 配置
source .env.sqlite
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Chat 前端 (端口: 5173)
cd mgagent-frontend
npm run dev

# Admin 前端 (端口: 5174)
cd mgagent-admin-frontend
npm run dev
```

### 4. 本地开发访问地址

| 服务 | 地址 |
|------|------|
| Chat 前端 | http://localhost:5173 |
| Admin 前端 | http://localhost:5174 |
| Chat API | http://localhost:8000 |
| Admin API | http://localhost:8001 |

## 方式三：Docker Compose 直接部署

```bash
# SQLite + ChromaDB 方案
docker compose -f docker-compose.prod.yml up -d --build

# MySQL + Milvus 方案（分层部署）
# 第一步：启动基础设施
docker compose -f docker-compose.infra.yml up -d
# 第二步：启动应用层
docker compose -f docker-compose.prod.yml up -d --build
```

## 配置模型

登录 Admin 后台后，在 **模型管理** 页面配置 LLM 模型：

1. 点击 **新增模型**
2. 填写模型名称、API Key、API Base URL
3. 点击 **测试连接** 验证配置
4. 点击 **启用** 使模型生效

:::warning 重要
所有大模型配置统一在 Admin 后台管理和存储，不再使用本地静态配置文件。模型配置存储在数据库的 `model_configs` 表中，支持多套配置和动态切换。
:::

## 下一步

- 了解 [架构设计](/architecture/overview)
- 配置 [环境变量](/configuration/environment-variables)
- 查看 [常见问题](/troubleshooting/faq)