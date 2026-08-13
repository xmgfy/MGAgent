---
title: 项目结构
description: MGAgent 项目目录结构、关键文件说明和代码组织方式
slug: /development/project-structure
---

# 项目结构

## 目录树

```
MGAgent/
├── mgagent-backend/              # Chat 后端服务
│   ├── app/
│   │   ├── api/                  # API 路由定义
│   │   │   └── routes.py         # Chat 相关路由
│   │   ├── agent/                # Agent 核心逻辑
│   │   │   ├── core.py           # EnterpriseAgent 实现
│   │   │   └── prompt.py         # 提示词模板
│   │   ├── config/               # 配置模块
│   │   │   ├── config.py         # 统一 MySQL + Milvus + MinIO 配置
│   │   │   └── settings.py       # 基础设置
│   │   ├── db/                   # 数据库模块
│   │   │   ├── database.py       # 数据库工厂
│   │   │   ├── models.py         # ORM 模型定义
│   │   │   └── crud.py           # 数据操作
│   │   ├── rag/                  # RAG 模块
│   │   │   ├── vector_factory.py # 向量数据库工厂
│   │   │   ├── retriever.py      # 向量检索器
│   │   │   ├── loader.py         # 文档加载器
│   │   │   └── milvus_service.py # Milvus 服务
│   │   ├── services/             # 业务服务
│   │   │   └── model_config_service.py
│   │   ├── tools/                # Agent 工具集
│   │   │   ├── calculator.py     # 计算器工具
│   │   │   ├── sql_query.py      # SQL 查询工具
│   │   │   └── mcp_server.py     # MCP 服务
│   │   ├── main.py               # FastAPI 入口
│   │   └── __init__.py
│   ├── data/                     # 数据存储目录
│   │   └── documents/            # 上传的文档
│   ├── Dockerfile                # Docker 构建文件
│   ├── .env.mysql                # 环境配置
│   └── requirements.txt          # Python 依赖
│
├── mgagent-admin-backend/        # Admin 后端服务
│   ├── app/
│   │   ├── api/                  # API 路由
│   │   │   ├── auth.py           # 认证接口
│   │   │   ├── users.py          # 用户管理
│   │   │   ├── admins.py         # 管理员管理
│   │   │   ├── tenants.py        # 租户管理
│   │   │   ├── model.py          # 模型配置管理
│   │   │   ├── knowledge.py      # 知识库管理
│   │   │   ├── storage.py        # 存储管理
│   │   │   ├── vector.py         # 向量库管理
│   │   │   ├── system.py         # 系统管理
│   │   │   ├── dashboard.py     # 仪表盘
│   │   │   └── routes.py         # 路由汇总
│   │   ├── config/               # 配置模块
│   │   ├── db/                   # 数据库模块
│   │   ├── rag/                  # RAG 模块
│   │   ├── services/             # 业务服务
│   │   └── main.py               # FastAPI 入口
│   ├── Dockerfile
│   └── requirements.txt
│
├── mgagent-frontend/             # Chat 前端
│   ├── src/
│   │   ├── components/           # UI 组件
│   │   │   ├── AuthModal.tsx     # 认证弹窗
│   │   │   ├── ChatHeader.tsx    # 聊天头部
│   │   │   ├── ChatHistory.tsx   # 历史会话
│   │   │   ├── ChatInput.tsx     # 输入框
│   │   │   ├── MessageBubble.tsx # 消息气泡
│   │   │   ├── Sidebar.tsx       # 侧边栏
│   │   │   └── TypingIndicator.tsx
│   │   ├── api/
│   │   │   └── client.ts         # API 客户端
│   │   ├── App.tsx               # 主应用
│   │   ├── main.tsx              # 入口文件
│   │   └── index.css             # 全局样式
│   ├── nginx.conf                # Nginx 配置
│   ├── Dockerfile
│   ├── vite.config.ts
│   └── package.json
│
├── mgagent-admin-frontend/       # Admin 前端
│   ├── src/
│   │   ├── pages/                # 页面组件
│   │   │   ├── Dashboard.tsx     # 仪表盘
│   │   │   ├── Login.tsx         # 登录页
│   │   │   ├── UserManagement.tsx
│   │   │   ├── ModelManagement.tsx
│   │   │   ├── KnowledgeBase.tsx
│   │   │   ├── StorageDB.tsx
│   │   │   ├── VectorDB.tsx
│   │   │   └── SystemManagement.tsx
│   │   ├── components/           # UI 组件
│   │   ├── api/client.ts         # API 客户端
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
│
├── docker/
│   └── mysql/
│       └── init.sql              # MySQL 初始化脚本
│
├── scripts/                      # 工具脚本
│   ├── init.sh                   # 一键初始化
│   ├── start-all.sh              # 一键启动本地服务
│   ├── stop-all.sh               # 一键停止本地服务
│   ├── status.sh                 # 服务状态检查
│   ├── deploy.sh                 # 一键生产部署
│   └── docker-services.sh        # 基础设施服务管理
│
├── docker-compose.prod.yml       # 生产环境全栈配置
├── docker-compose.infra.yml      # MySQL + Milvus 基础设施
├── .env.production.example      # 生产环境配置模板
├── .env.docker                  # Docker 基础设施配置
└── README.md
```

## 关键文件说明

| 文件 | 说明 |
|------|------|
| `app/config/config.py` | 统一 MySQL + Milvus + MinIO 配置 |
| `app/db/database.py` | 统一创建 MySQL 引擎 |
| `app/rag/vector_factory.py` | 统一创建 Milvus 实例 |
| `app/services/model_config_service.py` | 模型配置服务，从数据库读取和管理模型配置 |
| `app/agent/core.py` | Agent 核心逻辑，工具调用和对话处理 |
| `docker-compose.prod.yml` | 生产环境全栈 Docker Compose 配置 |
| `docker-compose.infra.yml` | MySQL + Milvus 基础设施 Docker Compose 配置 |
| `.env.mysql` | 环境变量文件 |
| `scripts/deploy.sh` | 一键生产部署脚本 |
| `scripts/docker-services.sh` | Docker 基础设施服务管理脚本 |
| `scripts/init.sh` | 一键项目初始化脚本 |
| `scripts/start-all.sh` | 本地开发一键启动脚本 |

## 后端架构模式

### FastAPI 应用结构

```python
# app/main.py - 应用入口
from fastapi import FastAPI
from app.config.config import settings
from app.db.database import init_db
from app.api.routes import router

app = FastAPI(title="MGAgent API")
app.include_router(router)

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "env_file": settings.ENV_FILE
    }
```

### 数据库工厂模式

```python
# app/db/database.py
def init_engine():
    engine = _create_mysql_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal
```

### 向量数据库工厂模式

```python
# app/rag/vector_factory.py
def create_vector_db():
    return MilvusService()
```

## 前端架构模式

### React + TypeScript 应用结构

```typescript
// src/App.tsx - 主应用
import { BrowserRouter, Routes, Route } from 'react-router-dom'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  )
}
```

### API 客户端封装

```typescript
// src/api/client.ts
import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

## Docker 构建结构

### 后端 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 前端 Dockerfile

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 相关文档

- [脚本使用指南](/development/scripts)
- [API 参考](/development/api-reference)
- [技术栈架构](/architecture/dual-stack)
