---
title: 架构概述
description: MGAgent 系统整体架构设计、模块划分与技术选型
slug: /architecture/overview
---

# 架构概述

## 设计原则

MGAgent 的架构设计遵循以下核心原则：

1. **双技术栈支持**：同时支持 SQLite+ChromaDB 和 MySQL+Milvus 两套技术栈
2. **前后端分离**：前端和后端完全独立，便于团队协作
3. **统一接口抽象**：通过工厂模式实现数据库和向量数据库的统一接口
4. **配置驱动切换**：基于环境变量动态选择技术栈方案
5. **模块化设计**：API 按功能模块拆分（auth、users、model、knowledge 等）
6. **插件化工具**：Agent 工具采用插件化设计，易于扩展
7. **动态模型配置**：所有 LLM 配置从数据库读取，无需静态配置
8. **容器化部署**：支持 Docker Compose 一键部署

## 系统架构图

```mermaid
flowchart TB
    subgraph S1["用户层 User Layer"]
        A["Chat 前端<br/>React + TypeScript<br/>Nginx :3000"]
        B["Admin 前端<br/>React + TypeScript<br/>Nginx :3001"]
    end

    subgraph S2["API层 API Layer"]
        C["Chat 后端<br/>FastAPI :8000"]
        D["Admin 后端<br/>FastAPI :8001"]
    end

    subgraph S3["数据层 Data Layer"]
        E[("SQLite / MySQL<br/>关系数据库")]
        F[("ChromaDB / Milvus<br/>向量数据库")]
        G[("etcd & MinIO<br/>Milvus 依赖")]
        H["Document Storage<br/>文档存储"]
    end

    subgraph S4["AI能力层 AI Layer"]
        I[LangChain Agent]
        J[RAG Retriever]
        K[LLM Models]
        L["Tools<br/>计算器/数据库查询"]
    end

    subgraph S5["配置层 Config Layer"]
        M["模型配置表<br/>model_configs"]
    end

    A -- "HTTP/REST" --> C
    B -- "HTTP/REST" --> D
    C -- "查询" --> E
    C -- "读写" --> F
    C -- "读写" --> H
    D -- "管理" --> E
    C -- "调用" --> I
    I -- "使用" --> J
    I -- "调用" --> K
    I -- "调用" --> L
    J -- "查询" --> F
    F -- "依赖" --> G
    C -- "读取" --> M
    D -- "管理" --> M

    classDef userLayer fill:#f0fdf4,stroke:#22c55e,stroke-width:2px
    classDef apiLayer fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    classDef dataLayer fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    classDef aiLayer fill:#fce7f3,stroke:#ec4899,stroke-width:2px
    classDef configLayer fill:#e0e7ff,stroke:#6366f1,stroke-width:2px

    class S1 userLayer
    class S2 apiLayer
    class S3 dataLayer
    class S4 aiLayer
    class S5 configLayer
```

## 模块划分

### 后端模块

| 模块 | 路径 | 说明 |
|------|------|------|
| API 路由 | `app/api/` | RESTful API 接口定义 |
| Agent 核心 | `app/agent/` | LangChain Agent 逻辑 |
| 配置模块 | `app/config/` | 统一配置，支持双方案切换 |
| 数据库 | `app/db/` | 数据库工厂与 ORM 模型 |
| RAG 模块 | `app/rag/` | 检索增强生成，含向量库工厂 |
| 服务层 | `app/services/` | 业务逻辑（模型配置管理） |
| 工具集 | `app/tools/` | Agent 可用工具（计算器、SQL 查询） |

### 前端模块

| 模块 | 路径 | 说明 |
|------|------|------|
| Chat 前端 | `mgagent-frontend/` | 用户对话界面 |
| Admin 前端 | `mgagent-admin-frontend/` | 管理后台界面 |

### 服务端口

| 服务 | 开发端口 | 生产端口 |
|------|---------|---------|
| Chat 后端 API | 8000 | 8000 |
| Admin 后端 API | 8001 | 8001 |
| Chat 前端 | 5173 | 3000 |
| Admin 前端 | 5174 | 3001 |

## 核心数据流

### 请求处理流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant FE as 前端
    participant BE as 后端 API
    participant AG as Agent
    participant RAG as 检索器
    participant VDB as 向量数据库
    participant LLM as 大语言模型

    U->>FE: 发送消息
    FE->>BE: POST /chat
    BE->>AG: 调用 chat()
    AG->>AG: 构建工具提示
    AG->>LLM: 生成工具调用
    LLM-->>AG: 返回工具调用指令
    AG->>RAG: 调用知识库检索
    RAG->>VDB: 相似度搜索
    VDB-->>RAG: 返回相关文档
    RAG-->>AG: 返回检索结果
    AG->>LLM: 总结结果
    LLM-->>AG: 返回自然语言回答
    AG-->>BE: 返回回复
    BE-->>FE: 返回 JSON 响应
    FE-->>U: 渲染消息
```

### RAG 检索流程

```mermaid
flowchart LR
    A[用户提问] --> B["文本嵌入<br/>Embedding"]
    B --> C[向量搜索]
    C --> D{向量数据库类型}
    D -->|ChromaDB| E[ChromaDB 检索]
    D -->|Milvus| F[Milvus 检索]
    E --> G[返回相关文档]
    F --> G
    G --> H[LLM 总结回答]
```

## 技术选型

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | >= 0.100 | 高性能异步 API 框架 |
| LangChain | >= 0.2 | LLM 应用开发框架 |
| SQLAlchemy | >= 2.0 | ORM 数据库操作 |
| PyJWT | >= 2.8 | JWT 身份认证 |
| bcrypt | >= 4.0 | 密码加密 |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18 | UI 框架 |
| TypeScript | 5 | 类型安全 |
| Tailwind CSS | 3 | 样式框架 |
| Vite | 5 | 构建工具 |
| Axios | 1.6 | HTTP 客户端 |

### 基础设施

| 技术 | 用途 |
|------|------|
| Docker | 容器化部署 |
| Docker Compose | 服务编排 |
| Nginx | 前端部署与 API 代理 |
| etcd | Milvus 元数据存储 |
| MinIO | Milvus 对象存储 |

## 相关文档

- [双技术栈架构](/architecture/dual-stack)
- [数据库设计](/architecture/database)
- [模型配置架构](/architecture/model-config)