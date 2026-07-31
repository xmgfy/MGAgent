# MGAgent 脚本使用指南

本文档详细介绍 MGAgent 项目中所有脚本的使用方法和适用场景。

---

## 📁 脚本总览

所有脚本统一存放在 `scripts/` 目录下：

| 脚本 | 类型 | 适用阶段 |
|------|------|----------|
| `init.sh` | 初始化 | 首次搭建 / 新环境部署 |
| `start-all.sh` | 本地开发 | 日常开发调试（支持 sqlite/mysql 模式） |
| `stop-all.sh` | 本地开发 | 停止本地服务 |
| `status.sh` | 本地开发 | 检查服务状态 |
| `docker-services.sh` | Docker 服务 | 基础设施服务管理 |
| `git-sync.sh` | Git 辅助 | 代码同步（本地工具，不纳入版本控制） |
| `deploy-docs.sh` | 文档部署 | 文档站点发布 |

---

## 🛠️ 阶段一：首次环境搭建

### `scripts/init.sh` — 一键初始化

**适用场景**：克隆项目后首次运行，或在新的开发环境中搭建项目。

**执行时机**：仅需执行一次（重复执行无副作用）。

**使用方法**：

```bash
cd MGAgent
chmod +x scripts/init.sh
./scripts/init.sh
```

**脚本功能**：

| 步骤 | 内容 |
|------|------|
| 1 | 安装 `mgagent-backend` Python 依赖 |
| 2 | 安装 `mgagent-admin-backend` Python 依赖 |
| 3 | 安装 `mgagent-frontend` Node.js 依赖 |
| 4 | 安装 `mgagent-admin-frontend` Node.js 依赖 |
| 5 | 创建必要目录（`.pids/`、`data/chroma/`、`data/documents/`） |
| 6 | 设置其他脚本的执行权限 |

**前置条件**：
- Python >= 3.10 已安装
- Node.js >= 18 已安装
- npm >= 9 已安装

---

## 🔧 阶段二：本地开发调试

适用于日常编码、功能开发、本地单测。支持两种模式：
- **SQLite 模式**（默认）：轻量级，无需外部数据库服务
- **MySQL 模式**：需要先启动 Docker 基础设施服务

### `scripts/start-all.sh` — 一键启动所有服务

**适用场景**：日常开发调试，需要同时启动前后端所有服务。

**使用方法**：

```bash
# SQLite 模式（默认，无需 Docker）
./scripts/start-all.sh sqlite

# MySQL 模式（需要先启动 Docker 基础设施）
./scripts/start-all.sh mysql
```

**启动的服务**：

| 服务 | 端口 | 进程 | 日志文件 |
|------|------|------|----------|
| 核心后端 | 8000 | uvicorn | `mgagent-backend/backend.log` |
| 管理台后端 | 8001 | uvicorn | `mgagent-admin-backend/admin-backend.log` |
| 核心前端 | 5173 | vite | `mgagent-frontend/frontend.log` |
| 管理台前端 | 5174 | vite | `mgagent-admin-frontend/admin-frontend.log` |

**特点**：
- 后台运行（nohup），不阻塞终端
- 支持热更新（`--reload`），代码修改后自动重启
- 自动记录进程 PID 到 `.pids/` 目录
- 根据模式自动加载对应环境配置（`.env.sqlite` / `.env.mysql`）

### `scripts/stop-all.sh` — 一键停止所有服务

**适用场景**：下班/收工停止服务，或服务异常需要重启。

**使用方法**：

```bash
./scripts/stop-all.sh
```

**停止策略**：
1. 优先从 PID 文件读取进程信息
2. 通过端口号查找监听进程
3. 通过命令名查找（vite / uvicorn）
4. 发送 SIGTERM 优雅停止 → 等待 3 秒 → SIGKILL 强制终止

### `scripts/status.sh` — 检查服务状态

**适用场景**：随时检查服务是否正常运行。

**使用方法**：

```bash
./scripts/status.sh
```

**检查内容**：
- 端口监听状态
- 进程 PID 有效性
- HTTP 可访问性测试
- 磁盘使用情况

### 完整本地开发流程

**SQLite 模式（推荐）**：

```bash
# 1. 首次初始化（仅执行一次）
./scripts/init.sh

# 2. 启动服务（SQLite 模式）
./scripts/start-all.sh sqlite

# 3. 日常编码开发（代码热更新自动生效）
#    浏览器访问:
#    - Chat 前端: http://localhost:5173
#    - Admin 前端: http://localhost:5174

# 4. 检查服务状态（可选）
./scripts/status.sh

# 5. 停止服务
./scripts/stop-all.sh
```

**MySQL 模式**：

```bash
# 1. 首次初始化（仅执行一次）
./scripts/init.sh

# 2. 启动 Docker 基础设施（MySQL + Milvus）
./scripts/docker-services.sh start

# 3. 启动应用服务（MySQL 模式）
./scripts/start-all.sh mysql

# 4. 日常编码开发
#    浏览器访问:
#    - Chat 前端: http://localhost:5173
#    - Admin 前端: http://localhost:5174

# 5. 停止服务
./scripts/stop-all.sh
./scripts/docker-services.sh stop
```

---

## 🐳 阶段三：Docker 基础设施服务管理

`docker-services.sh` **仅管理基础设施服务**（MySQL + Milvus），应用层服务请使用 `start-all.sh`。

### `scripts/docker-services.sh` — 基础设施管理

**适用场景**：
- MySQL 模式本地调试时，先启动数据库服务
- 为生产部署预热镜像
- 配置国内 Docker 镜像源加速

**所有命令**：

```bash
# 配置国内 Docker 镜像源（首次使用建议执行）
./scripts/docker-services.sh setup-mirror

# 检查当前镜像源配置
./scripts/docker-services.sh check-mirror

# 预热镜像（提前拉取所需镜像）
./scripts/docker-services.sh preload

# 启动 MySQL + Milvus 基础设施服务
./scripts/docker-services.sh start

# 停止基础设施服务
./scripts/docker-services.sh stop

# 重启基础设施服务
./scripts/docker-services.sh restart

# 查看基础设施服务状态
./scripts/docker-services.sh status

# 查看基础设施服务日志
./scripts/docker-services.sh logs
```

**包含的 Docker 容器（5 个基础设施服务）**：

| 容器 | 镜像 | 说明 |
|------|------|------|
| MySQL | `mysql:8.0` | 关系数据库 |
| Milvus | `milvusdb/milvus:v2.4.12` | 向量数据库 |
| etcd | `quay.io/coreos/etcd:v3.5.5` | Milvus 元数据存储 |
| MinIO | `minio/minio:RELEASE.2023-03-20` | Milvus 对象存储 |
| Attu | `zilliz/attu:v2.4` | Milvus 可视化管理 |

**Compose 文件**：`docker-compose.infra.yml`

**国内镜像加速**：

脚本内置 6 个国内 Docker 镜像源，可大幅加速镜像拉取速度：
- `https://docker.1panel.live`
- `https://docker.1ms.run`
- `https://docker.m.daocloud.io`
- `https://hub-mirror.c.163.com`
- `https://docker.mirrors.ustc.edu.cn`
- `https://mirror.ccs.tencentyun.com`

**镜像拉取策略**：
1. 先尝试直接拉取（使用 daemon.json 配置的镜像源）
2. 若失败，逐个尝试国内镜像源代理拉取
3. 若全部失败，最后尝试直接从 Docker Hub 拉取

> ⚠️ **重要**：`docker-services.sh` 只管理基础设施，不包含后端和前端应用。应用层服务请使用 `./scripts/start-all.sh` 启动。

---

## 🚀 阶段四：生产部署交付

> 生产部署需要自行配置 Docker Compose，参考 `docker-compose.infra.yml` 管理基础设施，应用层通过 CI/CD 流水线或手动 Docker 部署。

---

## 📦 辅助工具：Git 版本管理

### `scripts/git-sync.sh` — Git 同步

**适用场景**：辅助代码同步到 GitHub 和 Gitee。

> ⚠️ 此脚本为本地工具，已在 `.gitignore` 中忽略，不纳入版本控制。

**使用方法**：

```bash
./scripts/git-sync.sh status                          # 查看状态
./scripts/git-sync.sh commit "feat: 新增功能描述"      # 提交并推送
./scripts/git-sync.sh push                            # 推送代码
./scripts/git-sync.sh pull                            # 拉取代码
./scripts/git-sync.sh sync                            # 一站式同步
```

**功能**：
- 同时推送到 GitHub 和 Gitee 两个远程仓库
- 支持拉取、提交、推送的一站式操作

---

## 🗺️ 完整使用路线图

```
┌─────────────────────────────────────────────────────────────────────┐
│                     本地开发调试路线                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SQLite 模式（默认，推荐用于日常开发）                               │
│  ──────────────────────────────────────────────────────────          │
│  1. ./scripts/init.sh                初始化项目（首次）              │
│  2. ./scripts/start-all.sh sqlite    启动 SQLite 模式服务           │
│  3. 日常编码开发（热更新自动生效）                                  │
│     访问: http://localhost:5173 / 5174                              │
│  4. ./scripts/status.sh              随时检查服务状态                │
│  5. ./scripts/stop-all.sh            停止服务                       │
│                                                                     │
│  MySQL 模式（用于复杂功能测试）                                     │
│  ──────────────────────────────────────────────────────────          │
│  1. ./scripts/init.sh                初始化项目（首次）              │
│  2. ./scripts/docker-services.sh start  启动 MySQL + Milvus        │
│  3. ./scripts/start-all.sh mysql     启动 MySQL 模式服务            │
│  4. 日常编码开发                                                    │
│     访问: http://localhost:5173 / 5174                              │
│  5. ./scripts/stop-all.sh            停止应用服务                   │
│  6. ./scripts/docker-services.sh stop  停止基础设施                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

---

## ⚠️ 注意事项

1. **首次使用前**请确保已执行 `./scripts/init.sh` 完成依赖安装
2. **SQLite 模式**无需 Docker 环境，开箱即用，适合日常开发
3. **MySQL 模式**需要 Docker 环境支持，适合复杂功能测试
4. **脚本路径**：所有脚本统一在 `scripts/` 目录下
5. **git-sync.sh** 为本地辅助工具，已加入 `.gitignore`，不会被提交到远程仓库
6. 执行 `chmod +x scripts/*.sh` 可一次性设置所有脚本的执行权限