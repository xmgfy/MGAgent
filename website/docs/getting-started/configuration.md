---
title: 配置说明
description: MGAgent 系统配置详解，包括环境变量、模型配置和技术栈说明
slug: /getting-started/configuration
---

# 配置说明

## 技术栈说明

MGAgent 统一使用 **MySQL + Milvus + MinIO** 技术栈，不再支持 SQLite / ChromaDB 方案。

- **关系数据库**：MySQL 8.0
- **向量数据库**：Milvus 2.4
- **文件存储**：MinIO

```bash
# 本地开发（需先启动 Docker 基础设施）
./scripts/docker-services.sh start
./scripts/start-all.sh

# 生产环境一键部署
./scripts/deploy.sh up

# 或手动使用 Docker Compose
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
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

通过 `.env.production` 文件修改端口配置：

```bash
# 复制生产环境配置模板
cp .env.production.example .env.production

# 编辑配置
cat >> .env.production << 'EOF'
CHAT_FRONTEND_PORT=3000
ADMIN_FRONTEND_PORT=3001
CHAT_BACKEND_PORT=8000
ADMIN_BACKEND_PORT=8001
MYSQL_PORT=3306
MILVUS_PORT=19530
ATTU_PORT=8003
EOF
```

## 数据库配置

```bash
# 编辑 .env（本地开发）或 .env.production（生产环境）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=mgagent
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mgagent
```

## 调试配置

```bash
# 启用调试模式（在 .env 中）
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
