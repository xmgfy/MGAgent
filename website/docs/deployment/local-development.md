---
title: 本地开发部署
description: MGAgent 本地开发环境搭建指南，安装依赖、启动和停止服务
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
| Git | >= 2.30 | 版本控制 |

## 初始化项目

### 1. 克隆代码

```bash
git clone https://github.com/xmgfy/MGAgent.git
cd MGAgent
```

### 2. 一键初始化

```bash
# 添加执行权限
chmod +x scripts/init.sh

# 运行初始化脚本
./scripts/init.sh
```

初始化脚本会自动完成：

- 安装 `mgagent-backend` 的 Python 依赖
- 安装 `mgagent-admin-backend` 的 Python 依赖
- 安装 `mgagent-frontend` 的 Node.js 依赖
- 安装 `mgagent-admin-frontend` 的 Node.js 依赖
- 创建必要的数据目录

### 3. 手动安装依赖（可选）

如需手动安装：

```bash
# Chat 后端依赖
cd mgagent-backend
pip install -r requirements.txt

# Admin 后端依赖
cd ../mgagent-admin-backend
pip install -r requirements.txt

# Chat 前端依赖
cd ../mgagent-frontend
npm install

# Admin 前端依赖
cd ../mgagent-admin-frontend
npm install
```

## 启动服务

### 一键启动

```bash
# 启动所有服务
./scripts/start-all.sh

# 停止所有服务
./scripts/stop-all.sh

# 检查服务状态
./scripts/status.sh
```

### 服务端口

| 服务 | 端口 | 日志文件 |
|------|------|---------|
| Chat 后端 | 8000 | `mgagent-backend/backend.log` |
| Admin 后端 | 8001 | `mgagent-admin-backend/admin-backend.log` |
| Chat 前端 | 5173 | `mgagent-frontend/frontend.log` |
| Admin 前端 | 5174 | `mgagent-admin-frontend/admin-frontend.log` |

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| Chat 前端 | http://localhost:5173 | 智能对话界面 |
| Admin 前端 | http://localhost:5174 | 管理后台 |
| Chat API | http://localhost:8000 | 后端 API 文档 |
| Admin API | http://localhost:8001 | 管理 API 文档 |

## 手动启动

### 启动 Chat 后端

```bash
cd mgagent-backend
export DATABASE_SCHEME=sqlite
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 启动 Admin 后端

```bash
cd mgagent-admin-backend
export DATABASE_SCHEME=sqlite
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

## 使用 MySQL 方案（可选）

如需在本地开发中使用 MySQL + Milvus 方案：

### 1. 启动基础设施

```bash
# 启动 MySQL + Milvus 基础设施
./scripts/docker-services.sh start
```

### 2. 配置环境变量

```bash
export DATABASE_SCHEME=mysql
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=mgagent
export MYSQL_PASSWORD=mgagent_password_2024
export MYSQL_DATABASE=mgagent
export MILVUS_HOST=localhost
export MILVUS_PORT=19530
```

### 3. 启动后端服务

```bash
# Chat 后端
cd mgagent-backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Admin 后端
cd ../mgagent-admin-backend
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 调试技巧

### 查看日志

```bash
# 查看后端日志
tail -f mgagent-backend/backend.log

# 查看管理台后端日志
tail -f mgagent-admin-backend/admin-backend.log

# 查看前端日志
tail -f mgagent-frontend/frontend.log
```

### 端口冲突处理

```bash
# 查看端口占用
lsof -i :8000 :8001 :5173 :5174

# 强制释放端口
kill -9 $(lsof -t -i:端口号)
```

### 重新初始化

```bash
# 停止所有服务
./scripts/stop-all.sh

# 清理数据
rm -rf mgagent-backend/data/chroma mgagent-backend/data/documents

# 重新初始化
./scripts/init.sh
./scripts/start-all.sh
```

## 下一步

- 了解 [Docker 部署](/deployment/docker-deployment)
- 配置 [环境变量](/configuration/environment-variables)
- 查看 [脚本使用指南](/development/scripts)