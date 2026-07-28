# MGAgent 脚本使用指南

本文档详细介绍 MGAgent 项目中所有脚本的使用方法和适用场景。

---

## 📁 脚本总览

所有脚本统一存放在 `scripts/` 目录下：

| 脚本 | 类型 | 适用阶段 |
|------|------|----------|
| `init.sh` | 初始化 | 首次搭建 / 新环境部署 |
| `start-all.sh` | 本地开发 | 日常开发调试 |
| `stop-all.sh` | 本地开发 | 停止本地服务 |
| `status.sh` | 本地开发 | 检查服务状态 |
| `deploy.sh` | 生产部署 | Docker 容器化部署 |
| `docker-services.sh` | Docker 服务 | 数据库服务管理 |
| `migrate_data.py` | 数据迁移 | 方案切换时的数据迁移 |
| `git-sync.sh` | Git 辅助 | 代码同步（本地工具，不纳入版本控制） |

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

适用于日常编码、功能开发、本地单测。默认使用 **SQLite + ChromaDB 方案**（轻量级，无需外部数据库服务）。

### `scripts/start-all.sh` — 一键启动所有服务

**适用场景**：日常开发调试，需要同时启动前后端所有服务。

**使用方法**：

```bash
./scripts/start-all.sh
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

```bash
# 1. 首次初始化（仅执行一次）
./scripts/init.sh

# 2. 启动服务
./scripts/start-all.sh

# 3. 日常编码开发（代码热更新自动生效）
#    浏览器访问:
#    - Chat 前端: http://localhost:5173
#    - Admin 前端: http://localhost:5174

# 4. 检查服务状态（可选）
./scripts/status.sh

# 5. 停止服务
./scripts/stop-all.sh
```

---

## 🐳 阶段三：Docker 数据库服务管理

当需要使用 **MySQL + Milvus 方案** 时，需要先启动数据库服务。

### `scripts/docker-services.sh` — Docker 服务管理

**适用场景**：
- 本地调试 MySQL + Milvus 方案
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

# 启动 MySQL + Milvus 服务
./scripts/docker-services.sh start

# 停止服务
./scripts/docker-services.sh stop

# 重启服务
./scripts/docker-services.sh restart

# 查看服务状态
./scripts/docker-services.sh status

# 查看日志
./scripts/docker-services.sh logs

# 执行数据迁移
./scripts/docker-services.sh migrate
```

**包含的 Docker 容器**：

| 容器 | 镜像 | 说明 |
|------|------|------|
| MySQL | `mysql:8.0` | 关系数据库 |
| Milvus | `milvusdb/milvus:v2.4.12` | 向量数据库 |
| etcd | `quay.io/coreos/etcd:v3.5.5` | Milvus 元数据存储 |
| MinIO | `minio/minio:RELEASE.2023-03-20` | Milvus 对象存储 |
| Attu | `zilliz/attu:v2.4` | Milvus 可视化管理 |

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

---

## 🚀 阶段四：生产部署交付

### `scripts/deploy.sh` — 一键部署

**适用场景**：生产环境完整部署，一键拉起整套应用（含数据库 + 后端 + 前端）。

**使用方法**：

```bash
# 添加执行权限
chmod +x scripts/deploy.sh

# 交互式选择方案（推荐）
./scripts/deploy.sh

# 直接指定方案
./scripts/deploy.sh sqlite    # SQLite + ChromaDB（轻量级）
./scripts/deploy.sh mysql     # MySQL + Milvus（生产级）
```

**所有命令**：

```bash
./scripts/deploy.sh sqlite      # 启动 SQLite + ChromaDB 方案
./scripts/deploy.sh mysql       # 启动 MySQL + Milvus 方案
./scripts/deploy.sh stop        # 停止所有服务
./scripts/deploy.sh restart     # 重启服务（交互式选择方案）
./scripts/deploy.sh status      # 查看服务状态
./scripts/deploy.sh logs        # 查看实时日志
./scripts/deploy.sh cleanup     # 清理所有容器和数据卷（不可恢复）
```

**方案对比**：

| 特性 | `sqlite` 方案 | `mysql` 方案 |
|------|--------------|-------------|
| 关系数据库 | SQLite（内嵌） | MySQL 8.0（容器） |
| 向量数据库 | ChromaDB（内嵌） | Milvus 2.4（容器） |
| 部署复杂度 | 低 | 中 |
| 适用场景 | 单机小规模 | 大规模生产 |
| Compose 文件 | `docker-compose.local.yml` | `docker-compose.prod.yml` |

**端口映射**：

| 服务 | SQLite 方案端口 | MySQL 方案端口 |
|------|----------------|---------------|
| Chat 前端 | 3000 | 3000 |
| Admin 前端 | 3001 | 3001 |
| Chat API | 8000 | 8000 |
| Admin API | 8001 | 8001 |
| MySQL | — | 3306 |
| Milvus | — | 19530 |
| Attu | — | 8003 |

**默认账号**：
```
Admin 账号: admin / admin123
MySQL 账号: mgagent / mgagent_password_2024
```

---

## 🔄 阶段五：数据迁移

### `scripts/migrate_data.py` — 数据迁移

**适用场景**：从 SQLite + ChromaDB 方案切换到 MySQL + Milvus 方案时，需要迁移历史数据。

**使用方法**：

```bash
# 方式一：通过 docker-services.sh 调用
./scripts/docker-services.sh migrate

# 方式二：直接执行
python3 scripts/migrate_data.py
```

**迁移内容**：
- SQLite 表数据 → MySQL 对应表
- ChromaDB 向量数据 → Milvus 集合

**前置条件**：
- 目标 MySQL 和 Milvus 服务已启动
- `DATABASE_SCHEME` 已设置为 `mysql`

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
│  1. ./scripts/init.sh                初始化项目（首次）              │
│  2. ./scripts/start-all.sh           启动服务（SQLite 方案）        │
│  3. 日常编码开发（热更新自动生效）                                  │
│     访问: http://localhost:5173 / 5174                              │
│  4. ./scripts/status.sh              随时检查服务状态                │
│  5. ./scripts/stop-all.sh            停止服务                       │
│                                                                     │
│  ┌─── 如需 MySQL+Milvus 本地调试 ───────────────────────────┐       │
│  │  2a. ./scripts/docker-services.sh setup-mirror           │       │
│  │      配置国内 Docker 镜像源                              │       │
│  │  2b. ./scripts/docker-services.sh preload                │       │
│  │      预热所需镜像                                        │       │
│  │  2c. ./scripts/docker-services.sh start                 │       │
│  │      启动 MySQL + Milvus 服务                            │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     生产部署交付路线                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. ./scripts/docker-services.sh setup-mirror  配置镜像源（推荐）   │
│  2. ./scripts/deploy.sh sqlite|mysql            选择方案部署        │
│  3. ./scripts/deploy.sh status                  检查服务状态        │
│  4. ./scripts/deploy.sh logs                    查看运行日志        │
│  5. ./scripts/deploy.sh stop                    停止服务           │
│                                                                     │
│  数据迁移:                                                          │
│  python3 scripts/migrate_data.py                SQLite → MySQL     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ 注意事项

1. **首次使用前**请确保已执行 `./scripts/init.sh` 完成依赖安装
2. **MySQL + Milvus 方案**需要 Docker 环境支持
3. **脚本路径变更**：所有脚本已统一归档至 `scripts/` 目录，原根目录下的脚本已移除
4. **git-sync.sh** 为本地辅助工具，已加入 `.gitignore`，不会被提交到远程仓库
5. 执行 `chmod +x scripts/*.sh` 可一次性设置所有脚本的执行权限