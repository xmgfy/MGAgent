---
title: 配置说明
description: MGAgent 系统配置详解，包括环境变量、模型配置和技术栈选择
slug: /getting-started/configuration
---

# 配置说明

## 技术栈选择

MGAgent 支持两套技术栈方案，通过 `DATABASE_SCHEME` 环境变量切换：

### 方案对比

| 特性 | SQLite + ChromaDB | MySQL + Milvus |
|------|-------------------|----------------|
| 环境变量 | `DATABASE_SCHEME=sqlite` | `DATABASE_SCHEME=mysql` |
| 关系数据库 | SQLite 3.x | MySQL 8.0 |
| 向量数据库 | ChromaDB 0.5+ | Milvus 2.4 |
| 适用场景 | 单机开发调试 | 生产级部署 |
| 部署复杂度 | 简单 | 中等 |
| Compose 文件 | `docker-compose.local.yml` | `docker-compose.infra.yml` + `docker-compose.mysql-app.yml` |

### 切换方式

#### 环境变量

```bash
# SQLite 方案（默认）
export DATABASE_SCHEME=sqlite

# MySQL 方案
export DATABASE_SCHEME=mysql
```

#### Docker Compose

```bash
# SQLite 方案
docker compose -f docker-compose.local.yml up -d

# MySQL 方案（分层部署）
docker compose -f docker-compose.infra.yml up -d
docker compose -f docker-compose.mysql-app.yml up -d
```

## 模型配置

:::info 配置说明
MGAgent 采用 **数据库驱动** 的模型配置方式，所有 LLM 相关配置存储在 `model_configs` 表中，通过 Admin 后台管理。
:::

### 配置步骤

1. 启动系统并登录 Admin 后台
2. 进入 **模型管理** 页面
3. 点击 **新增模型**
4. 填写模型信息并保存
5. 点击 **测试连接** 验证可用性
6. 点击 **启用** 使模型生效

### 配置字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| 名称 | String(100) | 配置唯一标识名称 |
| API Key | String(500) | LLM 服务 API 密钥 |
| API Base | String(200) | API 基础 URL |
| 模型名称 | String(100) | LLM 模型标识 |

### API 接口

```bash
# 获取当前活跃的模型配置
GET /model/config

# 获取所有模型配置列表
GET /model/configs

# 创建新的模型配置
POST /model/configs
Content-Type: application/json

{
  "name": "my-model",
  "api_key": "sk-xxx",
  "api_base": "https://api.openai.com/v1",
  "model_name": "gpt-4o-mini"
}

# 更新模型配置
PUT /model/configs/{config_id}

# 激活指定的模型配置
POST /model/configs/{config_id}/activate

# 测试模型连接
GET /model/test
```

## 端口配置

### 默认端口映射

| 服务 | 开发模式 | Docker 模式 | 说明 |
|------|---------|------------|------|
| Chat 后端 | 8000 | 8000 | API 服务 |
| Admin 后端 | 8001 | 8001 | 管理 API |
| Chat 前端 | 5173 | 3000 | 用户界面 |
| Admin 前端 | 5174 | 3001 | 管理界面 |
| MySQL | - | 3306 | 数据库 |
| Milvus | - | 19530 | 向量库 |
| Attu | - | 8003 | Milvus 管理 |

### 自定义端口

通过环境变量文件修改端口配置：

```bash
# 创建配置文件
cat > .env.prod << 'EOF'
BACKEND_PORT=8000
ADMIN_BACKEND_PORT=8001
FRONTEND_PORT=3000
ADMIN_FRONTEND_PORT=3001
MYSQL_PORT=3306
MILVUS_PORT=19530
EOF
```

## 数据库配置

### MySQL 方案

```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=mgagent
MYSQL_PASSWORD=mgagent_password_2024
MYSQL_DATABASE=mgagent
```

### SQLite 方案

```bash
SQLITE_DB_PATH=./data/app.db
CHROMA_PERSIST_DIR=./data/chroma
```

## 调试配置

```bash
# 启用调试模式
DEBUG=True

# 设置 API 地址
API_HOST=0.0.0.0
API_PORT=8000

# Admin API 地址
ADMIN_API_URL=http://localhost:8001/admin/api
```

:::tip 调试模式
启用 `DEBUG=True` 后，FastAPI 会输出详细的请求日志，便于开发调试。生产环境建议设置为 `False`。
:::

## 相关文档

- [环境变量配置](/configuration/environment-variables)
- [数据库设计](/architecture/database)
- [模型配置架构](/architecture/model-config)