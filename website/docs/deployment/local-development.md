---
title: 本地开发部署
description: MGAgent 本地开发环境搭建指南，安装依赖、启动 MySQL + Milvus 基础设施和应用服务
slug: /deployment/local-development
---

# 本地开发部署

## 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Python | >= 3.10 | 推荐使用 3.11+ |
| Node.js | >= 18 | 推荐使用 20 LTS |
| npm | >= 9 | 包管理工具 |
| pip | >= 23 | Python 包管理 |
| Docker | >= 20.10 | 用于启动 MySQL + Milvus 基础设施 |
| Docker Compose | >= 2.0 | 服务编排 |
| Git | >= 2.30 | 版本控制 |

## 初始化项目

### 1. 克隆代码

```bash
git clone https://github.com/xmgfy/MGAgent.git
cd MGAgent
```

### 2. 一键初始化

```bash
chmod +x scripts/init.sh
./scripts/init.sh
```

初始化脚本自动完成：

- 安装 `mgagent-backend` 的 Python 依赖
- 安装 `mgagent-admin-backend` 的 Python 依赖
- 安装 `mgagent-frontend` 的 Node.js 依赖
- 安装 `mgagent-admin-frontend` 的 Node.js 依赖
- 创建必要的数据目录

## 启动基础设施

### 启动 MySQL + Milvus + etcd + MinIO

```bash
chmod +x scripts/docker-services.sh
./scripts/docker-services.sh start
```

**服务列表**：

| 服务 | 端口 | 说明 |
|------|------|------|
| MySQL | 3306 | 关系数据库 |
| Milvus | 19530 | 向量数据库 |
| Attu | 8003 | Milvus 管理界面 |

### 验证基础设施

```bash
# 查看状态
./scripts/docker-services.sh status

# 检查 MySQL
docker exec -it mgagent-mysql mysql -u mgagent -pmgagent_password_2024 -e "SELECT 1"

# 检查 Milvus
curl http://localhost:19530/healthz
```

## 启动应用服务

### 一键启动

```bash
# 启动所有 4 个应用服务
./scripts/start-all.sh

# 停止所有服务
./scripts/stop-all.sh

# 检查服务状态
./scripts/status.sh
```

**启动的服务**：

| 服务 | 端口 | 日志文件 |
|------|------|---------|
| Chat 后端 | 8000 | `mgagent-backend/backend.log` |
| Admin 后端 | 8001 | `mgagent-admin-backend/admin-backend.log` |
| Chat 前端 | 5173 | `mgagent-frontend/frontend.log` |
| Admin 前端 | 5174 | `mgagent-admin-frontend/admin-frontend.log` |

### 访问地址

| 服务 | 地址 |
|------|------|
| Chat 前端 | http://localhost:5173 |
| Admin 前端 | http://localhost:5174 |
| Chat API | http://localhost:8000 |
| Admin API | http://localhost:8001 |
| Attu | http://localhost:8003 |

## 手动启动（可选）

### 启动 Chat 后端

```bash
cd mgagent-backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 启动 Admin 后端

```bash
cd mgagent-admin-backend
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 启动 Chat 前端

```bash
cd mgagent-frontend
npm run dev
```

### 启动 Admin 前端

```bash
cd mgagent-admin-frontend
npm run dev -- --port 5174
```

## 本地 Embedding 模型部署（可选）

如需使用本地 Embedding 模型替代云端 API：

```bash
cd mgagent-admin-backend

# 安装依赖
pip install sentence-transformers

# 下载模型
python scripts/download_local_models.py --list          # 查看可用模型
python scripts/download_local_models.py --model bge-small-zh   # 下载
```

然后在 Admin 后台 → 模型管理 → Embedding 模型 中启用。

### 可用模型列表

| 模型 ID | 模型名称 | 维度 | 大小 | 说明 |
|---------|---------|------|------|------|
| bge-small-zh | BAAI/bge-small-zh-v1.5 | 512 | ~100MB | 轻量级，适合调试 |
| bge-base-zh | BAAI/bge-base-zh-v1.5 | 768 | ~400MB | 效果均衡 |
| bge-large-zh | BAAI/bge-large-zh-v1.5 | 1024 | ~1.3GB | 最佳效果 |
| bge-m3 | BAAI/bge-m3 | 1024 | ~2.3GB | 中英双语 |

## 调试技巧

### 查看日志

```bash
tail -f mgagent-backend/backend.log
tail -f mgagent-admin-backend/admin-backend.log
```

### 端口冲突处理

```bash
# 查看端口占用
lsof -i :8000 :8001 :5173 :5174

# 释放端口
kill -9 $(lsof -t -i:端口号)
```

### 完全重置

```bash
# 停止所有
./scripts/stop-all.sh
./scripts/docker-services.sh stop

# 清理 Docker 数据卷（清空 MySQL + Milvus 数据）
docker compose -f docker-compose.infra.yml down -v

# 重新启动
./scripts/docker-services.sh start
./scripts/start-all.sh
```

## 下一步

- 了解 [Docker 部署](/deployment/docker-deployment)
- 配置 [环境变量](/configuration/environment-variables)
- 查看 [脚本使用指南](/development/scripts)
