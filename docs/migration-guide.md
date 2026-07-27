# MGAgent 数据迁移指南：SQLite → MySQL + ChromaDB → Milvus

## 概述

本文档说明如何将 MGAgent 项目的数据源从 SQLite + ChromaDB 迁移到 MySQL + Milvus 组合。

## 架构变化

| 组件 | 旧方案 | 新方案 |
|------|--------|--------|
| 关系数据库 | SQLite (chat.db) | MySQL 8.0 |
| 向量数据库 | ChromaDB | Milvus 2.4 |
| 向量嵌入 | TF-IDF / OpenAI | 保持不变 |

## 前置条件

1. **Docker Desktop** 已安装并运行
2. **Python 3.9+** 已安装
3. **Git** 已安装（用于代码管理）

## 快速开始

### 1. 启动基础设施服务

```bash
cd /path/to/MGAgent

# 启动 MySQL + Milvus
./scripts/docker-services.sh start

# 查看服务状态
./scripts/docker-services.sh status
```

### 2. 安装 Python 依赖

```bash
# mgagent-backend
cd mgagent-backend
pip install -r requirements.txt

# mgagent-admin-backend
cd ../mgagent-admin-backend
pip install -r requirements.txt
```

### 3. 执行数据迁移

```bash
# 在项目根目录执行
cd /path/to/MGAgent
python scripts/migrate_data.py
```

### 4. 启动应用

```bash
# 启动所有服务
./scripts/start-all.sh
```

## Docker 服务说明

### 服务列表

| 服务 | 端口 | 说明 |
|------|------|------|
| MySQL | 3306 | 关系数据库 |
| Milvus | 19530 | 向量数据库 |
| Milvus gRPC | 9091 | Milvus gRPC 接口 |
| Attu | 8000 | Milvus 管理界面 |
| etcd | 2379 | Milvus 元数据存储 |
| MinIO | 9000 | Milvus 对象存储 |

### 环境变量配置

`.env.docker` 文件包含默认配置：

```env
# MySQL 配置
MYSQL_ROOT_PASSWORD=mgagent_root_2024
MYSQL_DATABASE=mgagent
MYSQL_USER=mgagent
MYSQL_PASSWORD=mgagent_password_2024

# Milvus 配置
MILVUS_PORT=19530
MILVUS_GRPC_PORT=9091
```

### 常用命令

```bash
# 查看服务日志
./scripts/docker-services.sh logs

# 重启服务
./scripts/docker-services.sh restart

# 停止服务
./scripts/docker-services.sh stop
```

## 数据库连接

### 连接 MySQL

```bash
mysql -h localhost -P 3306 -u mgagent -pmgagent_password_2024 mgagent
```

### 连接 Milvus

通过 Attu Web UI 访问：http://localhost:8000

连接参数：
- Host: `milvus` 或 `localhost`
- Port: `19530`

## 数据模型

### MySQL 表结构

| 表名 | 说明 |
|------|------|
| tenants | 租户信息 |
| admins | 管理员信息 |
| admin_sessions | 管理员会话 |
| model_configs | 模型配置 |
| system_notifications | 系统通知 |
| users | 用户信息 |
| chat_sessions | 聊天会话 |
| chat_messages | 聊天消息 |
| documents | 文档信息 |
| anonymous_stats | 匿名用户统计 |

### Milvus 集合结构

集合名称：`mgagent_knowledge`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(64) | 主键 |
| content | VARCHAR(65535) | 文档内容 |
| metadata | JSON | 元数据 |
| embedding | FLOAT_VECTOR(1536) | 向量嵌入 |

## 代码变更说明

### 数据库配置

**文件**: `mgagent-backend/app/config/settings.py`

```python
# 旧配置
DATABASE_URL: str = "sqlite:///./data/chat.db"

# 新配置
DATABASE_URL: str = "mysql+pymysql://mgagent:mgagent_password_2024@localhost:3306/mgagent?charset=utf8mb4"
MILVUS_HOST: str = "localhost"
MILVUS_PORT: int = 19530
MILVUS_COLLECTION: str = "mgagent_knowledge"
```

**文件**: `mgagent-backend/app/db/database.py`

新增 MySQL 连接配置，包括：
- `pool_pre_ping=True` - 自动检测断开的连接
- `pool_recycle=3600` - 每小时回收连接
- `pool_size=10` - 连接池大小
- `max_overflow=20` - 最大溢出连接数

### 模型更新

**文件**: `mgagent-backend/app/db/models.py`

主要变更：
- String 字段指定长度（如 `String(64)`, `String(100)`）
- DateTime 使用 `server_default=func.now()`
- Boolean 类型保持不变
- `ChatMessage.id` 添加 `autoincrement=True`

### 向量存储

**新增文件**: `mgagent-backend/app/rag/milvus_service.py`

Milvus 服务类，提供：
- `connect()` - 连接 Milvus
- `add_documents()` - 添加文档
- `similarity_search()` - 相似度搜索
- `delete_by_ids()` - 删除向量
- `clear_all()` - 清空数据

**更新文件**: `mgagent-backend/app/rag/retriever.py`

使用 Milvus 替代 ChromaDB 实现向量检索。

## 故障排查

### MySQL 连接失败

```bash
# 检查 MySQL 容器状态
docker compose -f docker-compose.yml ps

# 查看 MySQL 日志
docker compose -f docker-compose.yml logs mysql

# 测试连接
mysql -h localhost -P 3306 -u mgagent -pmgagent_password_2024 -e "SELECT 1"
```

### Milvus 连接失败

```bash
# 检查 Milvus 容器状态
docker compose -f docker-compose.yml ps

# 查看 Milvus 日志
docker compose -f docker-compose.yml logs milvus

# 通过 Attu 检查
# 访问 http://localhost:8000
```

### 数据迁移失败

```bash
# 确保 MySQL 和 Milvus 都已启动
./scripts/docker-services.sh status

# 重新执行迁移
python scripts/migrate_data.py
```

## 回滚方案

如果需要回滚到旧版本：

1. 停止 Docker 服务
   ```bash
   ./scripts/docker-services.sh stop
   ```

2. 将配置改回 SQLite
   ```python
   DATABASE_URL: str = "sqlite:///./data/chat.db"
   ```

3. 使用旧版代码

## 性能对比

| 指标 | SQLite + ChromaDB | MySQL + Milvus |
|------|-------------------|----------------|
| 数据量 | 小规模 (< 1000条) | 大规模 (> 100万条) |
| 查询速度 | 慢 | 快 (向量搜索) |
| 并发支持 | 低 | 高 |
| 可扩展性 | 差 | 好 |
| 生产就绪 | 否 | 是 |

## 技术支持

如有问题，请查看：
1. Docker 日志：`./scripts/docker-services.sh logs`
2. 应用日志：查看终端输出
3. 数据库日志：查看 MySQL/Milvus 容器日志
