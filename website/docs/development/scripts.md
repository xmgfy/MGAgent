---
title: 脚本使用指南
description: MGAgent 所有工具脚本的详细使用说明和适用场景
slug: /development/scripts
---

# 脚本使用指南

## 概述

MGAgent 在 `scripts/` 目录下提供了一系列工具脚本，用于简化部署、开发和运维流程。

## 脚本列表

| 脚本 | 用途 | 适用场景 |
|------|------|---------|
| `init.sh` | 一键初始化项目 | 首次安装 |
| `start-all.sh` | 启动本地开发服务 | 本地开发（sqlite/mysql） |
| `stop-all.sh` | 停止本地开发服务 | 本地开发 |
| `status.sh` | 检查服务状态 | 运维监控 |
| `deploy.sh` | 一键生产部署 | 生产环境部署 |
| `docker-services.sh` | 基础设施服务管理 | MySQL 模式本地调试 |

## init.sh - 项目初始化

首次安装时使用，自动完成所有依赖安装和目录创建。

### 使用方法

```bash
# 添加执行权限
chmod +x scripts/init.sh

# 运行初始化
./scripts/init.sh
```

### 执行内容

1. 安装 `mgagent-backend` Python 依赖
2. 安装 `mgagent-admin-backend` Python 依赖
3. 安装 `mgagent-frontend` Node.js 依赖
4. 安装 `mgagent-admin-frontend` Node.js 依赖
5. 创建必要的数据目录
6. 设置所有脚本执行权限

### 输出示例

```
=========================================
  MGAgent 初始化脚本
=========================================

[1/6] 安装 mgagent-backend 依赖
-----------------------------------------
正在安装 Python 依赖...
Python 依赖安装完成

...

=========================================
  初始化完成!
=========================================

使用说明:
  启动服务 (SQLite): ./scripts/start-all.sh sqlite
  启动服务 (MySQL):  ./scripts/start-all.sh mysql
  停止服务:          ./scripts/stop-all.sh
  检查服务状态:      ./scripts/status.sh
```

## start-all.sh - 启动本地服务

一键启动所有本地开发服务（4 个进程），支持 SQLite 和 MySQL 两种模式。

### 使用方法

```bash
chmod +x scripts/start-all.sh

# SQLite 模式（默认，无需 Docker）
./scripts/start-all.sh sqlite

# MySQL 模式（需先启动 Docker 基础设施）
./scripts/docker-services.sh start
./scripts/start-all.sh mysql
```

### 启动的服务

| 服务 | 端口 | 日志文件 |
|------|------|---------|
| mgagent-backend | 8000 | `mgagent-backend/backend.log` |
| mgagent-admin-backend | 8001 | `mgagent-admin-backend/admin-backend.log` |
| mgagent-frontend | 5173 | `mgagent-frontend/frontend.log` |
| mgagent-admin-frontend | 5174 | `mgagent-admin-frontend/admin-frontend.log` |

### 特点

- 自动停止已运行的服务
- 使用 `nohup` 后台运行
- 记录 PID 到 `.pids/` 目录
- 启动后验证端口监听状态
- 显示访问地址

### 输出示例

```
=========================================
  MGAgent 一键启动脚本
=========================================

[0/4] 停止已运行的服务...
完成

[1/4] 启动 mgagent-backend (端口: 8000)
后端服务已启动 (PIDs: 12345)
日志文件: .../mgagent-backend/backend.log

...

=========================================
  所有服务启动完成!
=========================================

服务地址:
  - 核心前端: http://localhost:5173
  - 核心后端: http://localhost:8000
  - 管理台前端: http://localhost:5174
  - 管理台后端: http://localhost:8001
```

## stop-all.sh - 停止本地服务

安全停止所有本地开发服务，支持优雅关闭和强制终止。

### 使用方法

```bash
./scripts/stop-all.sh
```

### 停止策略

脚本采用三步停止策略：

1. **优雅停止**：发送 SIGTERM 信号，等待 3 秒
2. **强制终止**：检查残留进程，发送 SIGKILL
3. **清理验证**：最终验证所有端口已释放

### 进程查找方式

脚本通过多种方式查找需要终止的进程：

- 从 PID 文件读取
- 通过端口号查找
- 通过命令名查找（vite / uvicorn）

### 输出示例

```
[1/4] 停止 mgagent-backend
  从PID文件找到进程: 12345
  [步骤1] 优雅停止进程组: 12345
  ✓ mgagent-backend 已停止

...

验证服务状态:
  ✓ 端口 8000 已释放
  ✓ 端口 8001 已释放
  ✓ 端口 5173 已释放
  ✓ 端口 5174 已释放
所有端口已成功释放!
```

## status.sh - 服务状态检查

实时检查所有服务的运行状态和健康情况。

### 使用方法

```bash
./scripts/status.sh
```

### 检查内容

- 进程状态：端口监听、PID 文件有效性
- HTTP 访问：测试 API 健康检查端点
- 磁盘使用：显示项目所在磁盘空间

### 输出示例

```
--- 进程状态 ---

mgagent-backend:
  ✓ 端口 8000 正在监听
  进程PID: 12345
    - PID 12345: python3 -m uvicorn app.main:app

mgagent-admin-backend:
  ✓ 端口 8001 正在监听
  ...

--- 服务访问测试 ---

mgagent-backend:
  ✓ 可访问 (HTTP: 200)
  URL: http://localhost:8000/api/health

--- 磁盘使用情况 ---
/dev/disk1s1    500Gi   200Gi  300Gi    40%    /Users/xmg/...
```

## deploy.sh - 生产部署

一键 Docker 生产部署脚本，使用 `docker-compose.prod.yml` 编排所有服务（基础设施 + 应用层）。

### 使用方法

```bash
# 添加执行权限
chmod +x scripts/deploy.sh

# 首次部署前，复制配置模板
cp .env.production.example .env.production
# 修改生产环境配置（密码、端口等）
vim .env.production

# 启动所有服务（自动构建镜像）
./scripts/deploy.sh up

# 停止所有服务
./scripts/deploy.sh down

# 重启所有服务
./scripts/deploy.sh restart

# 查看服务状态
./scripts/deploy.sh status

# 查看日志
./scripts/deploy.sh logs            # 所有服务
./scripts/deploy.sh logs backend    # 指定服务

# 重新构建镜像（不使用缓存）
./scripts/deploy.sh build

# 清理所有容器和数据卷（谨慎使用）
./scripts/deploy.sh cleanup
```

### 部署流程

```mermaid
flowchart LR
    A[deploy.sh up] --> B{检查环境}
    B --> C{检查 .env.production}
    C --> D[Docker Compose 构建镜像]
    D --> E[启动 MySQL/Milvus]
    E --> F[启动应用层服务]
    F --> G[健康检查验证]
    G --> H[部署完成]
```

### 管理的服务

| 服务 | 端口 | 说明 |
|------|------|------|
| mgagent-frontend | 3000 | Chat 前端（Nginx） |
| mgagent-admin-frontend | 3001 | Admin 前端（Nginx） |
| mgagent-backend | 8000 | Chat API |
| mgagent-admin-backend | 8001 | Admin API |
| MySQL | 3306 | 关系数据库 |
| Milvus | 19530 | 向量数据库 |
| Attu | 8003 | Milvus 管理界面 |

### 特点

- 彩色输出，清晰易懂
- 自动检查 Docker 环境和配置文件
- 健康检查验证每个服务
- 支持数据卷持久化
- 一键清理所有资源（需确认）

### 输出示例

```
=========================================
  MGAgent 生产环境部署
=========================================

[1/5] 检查环境...
✓ Docker 环境正常
✓ 环境变量检查通过

[2/5] 启动 Docker Compose 服务...
[3/5] 等待服务就绪...
[4/5] 健康检查验证...
[5/5] 显示访问信息...

=========================================
  所有服务已启动
=========================================

访问地址:
  Chat 前端:   http://localhost:3000
  Admin 前端:  http://localhost:3001
  Chat API:    http://localhost:8000/docs
  Admin API:   http://localhost:8001/docs
  Attu UI:     http://localhost:8003
```

## docker-services.sh - 基础设施管理

专门管理 MySQL + Milvus 基础设施服务的脚本。

### 使用方法

```bash
# 启动基础设施
./scripts/docker-services.sh start

# 停止基础设施
./scripts/docker-services.sh stop

# 重启基础设施
./scripts/docker-services.sh restart

# 查看状态
./scripts/docker-services.sh status

# 查看日志
./scripts/docker-services.sh logs

# 预热所有镜像
./scripts/docker-services.sh preload

# 配置国内镜像源
./scripts/docker-services.sh setup-mirror

# 检查镜像源配置
./scripts/docker-services.sh check-mirror
```

### 管理的服务

| 服务 | 说明 |
|------|------|
| MySQL | 关系数据库 |
| Milvus | 向量数据库 |
| etcd | Milvus 元数据存储 |
| MinIO | Milvus 对象存储 |
| Attu | Milvus 管理界面 |

### 镜像预热

`preload` 命令会预热所有必要的 Docker 镜像：

```bash
./scripts/docker-services.sh preload

# 预热 MySQL + Milvus 相关镜像:
#   mysql:8.0
#   milvusdb/milvus:v2.4.12
#   quay.io/coreos/etcd:v3.5.5
#   minio/minio:RELEASE.2023-03-20T20-16-18Z
#   zilliz/attu:v2.4
```

## 快速参考卡片

```bash
# 首次使用
./scripts/init.sh

# 本地开发（SQLite 模式，无需 Docker）
./scripts/start-all.sh sqlite       # 启动
./scripts/status.sh                 # 检查
./scripts/stop-all.sh               # 停止

# 本地开发（MySQL 模式，需 Docker）
./scripts/docker-services.sh start  # 启动基础设施
./scripts/start-all.sh mysql        # 启动应用
./scripts/docker-services.sh stop   # 停止基础设施

# 生产环境部署
cp .env.production.example .env.production  # 首次配置
./scripts/deploy.sh up              # 启动所有服务
./scripts/deploy.sh down            # 停止所有服务
./scripts/deploy.sh status          # 查看状态
./scripts/deploy.sh logs            # 查看日志
./scripts/deploy.sh restart         # 重启
```

## 注意事项

:::warning 脚本权限
首次使用脚本前，需要添加执行权限：
```bash
chmod +x scripts/*.sh
```
:::

:::tip 路径自适配
所有脚本内部路径已实现自适配，无论在哪个目录执行都能正确定位项目根目录。
:::

:::warning macOS 兼容性
`docker-services.sh` 已兼容 macOS 环境下 `timeout` 命令不可用的问题，使用 `perl` 作为替代方案。
:::

## 相关文档

- [本地开发部署](/deployment/local-development)
- [Docker 部署](/deployment/docker-deployment)
- [MySQL 方案部署](/deployment/mysql-deployment)