# MGAgent 🤖 - 企业级智能体系统

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Node Version](https://img.shields.io/badge/Node-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://react.dev/)

> 🔥 **MGAgent** 是一款面向企业场景的智能体系统，基于 LangChain 框架构建，具备知识库检索、数据分析、多工具调用等核心能力，支持多租户管理和灵活的模型配置。

---

## 📋 目录

- [✨ 功能特性](#-功能特性)
- [🏗️ 架构设计](#-架构设计)
- [🚀 快速开始](#-快速开始)
- [📷 界面预览](#-界面预览)
- [🔧 技术栈](#-技术栈)
- [📁 项目结构](#-项目结构)
- [🤝 贡献指南](#-贡献指南)
- [📄 许可证](#-许可证)

---

## ✨ 功能特性

### 🎯 核心能力

| 功能 | 描述 |
|------|------|
| **智能对话** | 基于大语言模型的自然语言交互，支持流式响应 |
| **知识库检索** | RAG技术实现企业文档智能检索，支持PDF/TXT/DOCX/MD格式 |
| **数据库查询** | 自动生成SQL查询业务数据，支持表结构查看和数据检索 |
| **计算器** | 内置数学计算工具，处理复杂数值计算 |
| **多工具调用** | Agent自动选择合适的工具完成复杂任务 |

### 🔐 权限管理

- **多租户架构**：支持平台管理员和租户管理员分级管理
- **用户审批**：新用户注册需管理员审批后方可使用
- **角色控制**：平台管理员、租户管理员、普通用户三级权限
- **会话隔离**：用户只能访问自己的对话历史

### ⚙️ 系统管理

- **模型配置**：支持配置多种LLM模型（OpenAI兼容），动态切换
- **模型测试**：一键测试模型连接可用性
- **向量数据库**：管理Chroma向量库，支持数据查看和搜索
- **存储管理**：数据库表结构查看和SQL执行
- **系统监控**：实时监控系统状态和资源使用

---

## 🏗️ 架构设计

```mermaid
flowchart TB
    subgraph 用户层 [User Layer]
        A[Chat Frontend<br/>React + TypeScript<br/>localhost:5173]
        B[Admin Frontend<br/>React + TypeScript<br/>localhost:5174]
    end

    subgraph API层 [API Layer]
        C[Chat Backend<br/>FastAPI<br/>localhost:8000]
        D[Admin Backend<br/>FastAPI<br/>localhost:8001]
    end

    subgraph 数据层 [Data Layer]
        E[(SQLite Database<br/>chat.db)]
        F[(Chroma Vector DB<br/>chroma.sqlite3)]
        G[Document Storage<br/>data/documents/]
    end

    subgraph AI能力层 [AI Layer]
        H[LangChain Agent]
        I[RAG Retriever]
        J[LLM Models]
        K[Tools<br/>计算器/数据库查询]
    end

    A -- HTTP/REST --> C
    B -- HTTP/REST --> D
    C -- 查询 --> E
    C -- 读写 --> F
    C -- 读写 --> G
    D -- 查询/管理 --> E
    C -- 调用 --> H
    H -- 使用 --> I
    H -- 调用 --> J
    H -- 调用 --> K
    I -- 查询 --> F

    style 用户层 fill:#f0fdf4,stroke:#22c55e,stroke-width:2px
    style API层 fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
    style 数据层 fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    style AI能力层 fill:#fce7f3,stroke:#ec4899,stroke-width:2px
```

### 架构特点

1. **前后端分离**：前端和后端完全独立，便于团队协作和技术选型
2. **共享数据库**：Chat后端和Admin后端共享同一个SQLite数据库，保证数据一致性
3. **模块化设计**：API按功能模块拆分（auth、users、model、knowledge等）
4. **插件化工具**：Agent工具采用插件化设计，易于扩展新功能
5. **动态模型配置**：Chat后端运行时从Admin后端获取模型配置，无需重启服务

---

## 🚀 快速开始

### 环境要求

- **Python** >= 3.10
- **Node.js** >= 18
- **npm** >= 9

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/xmgfy/MGAgent.git
cd MGAgent
```

#### 2. 安装后端依赖

```bash
# 安装 Chat 后端依赖
cd mgagent-backend
pip install -r requirements.txt

# 安装 Admin 后端依赖
cd ../mgagent-admin-backend
pip install -r requirements.txt
```

#### 3. 安装前端依赖

```bash
# 安装 Chat 前端依赖
cd ../mgagent-frontend
npm install

# 安装 Admin 前端依赖
cd ../mgagent-admin-frontend
npm install
```

#### 4. 启动服务

```bash
# 方式一：使用启动脚本（推荐）
./start-all.sh

# 方式二：手动启动
# Chat 后端
cd mgagent-backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Admin 后端
cd ../mgagent-admin-backend
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Chat 前端
cd ../mgagent-frontend
npm run dev

# Admin 前端
cd ../mgagent-admin-frontend
npm run dev
```

#### 5. 访问系统

| 服务 | 地址 |
|------|------|
| Chat 前端 | http://localhost:5173 |
| Admin 前端 | http://localhost:5174 |
| Chat API | http://localhost:8000 |
| Admin API | http://localhost:8001 |

#### 6. 默认账号

```
Admin 账号: admin / admin123
```

#### 7. 配置模型

登录 Admin 后台后，在**模型管理**页面配置您的 LLM 模型：

1. 点击"新增模型"
2. 填写模型名称、API Key、API Base URL
3. 点击"测试连接"验证配置
4. 点击"启用"使模型生效

> **注意**：模型配置完全在 Admin 后台进行，`.env` 文件中的模型配置仅作为备用，主逻辑已改为从 Admin 后端动态获取配置。

---

## 📷 界面预览

### 🎨 Chat 前端界面

![Chat Interface](docs/images/chat-interface.png)

**功能特点**：
- 会话管理：支持创建、查看、删除对话
- 文件上传：支持 PDF/TXT/DOCX/MD 格式文件作为对话上下文
- 匿名使用：未登录用户可免费使用3次
- 用户认证：登录后可查看完整对话历史

### 🖥️ Admin 管理后台

![Admin Dashboard](docs/images/admin-dashboard.png)

**功能特点**：
- 用户审批：管理新用户注册申请
- 模型管理：配置和切换LLM模型
- 知识库管理：上传和管理企业文档
- 系统监控：查看系统状态和资源使用

### 📊 模型管理界面

![Model Management](docs/images/model-management.png)

**功能特点**：
- 支持配置多个模型
- 一键测试模型连接
- 动态切换活跃模型
- 无需重启服务即可生效

### 📚 知识库管理界面

![Knowledge Base](docs/images/knowledge-base.png)

**功能特点**：
- 支持多种文档格式上传
- 自动进行文本分割和向量化
- 支持文档搜索和预览
- 文档状态实时追踪

---

## 🔧 技术栈

### 后端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| **FastAPI** | >= 0.100 | 高性能异步API框架 |
| **LangChain** | >= 0.2 | LLM应用开发框架 |
| **LangChain OpenAI** | >= 0.1 | OpenAI模型集成 |
| **ChromaDB** | >= 0.5 | 向量数据库 |
| **SQLAlchemy** | >= 2.0 | ORM数据库操作 |
| **PyJWT** | >= 2.8 | JWT认证 |
| **bcrypt** | >= 4.0 | 密码加密 |

### 前端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| **React** | 18 | UI框架 |
| **TypeScript** | 5 | 类型安全 |
| **Tailwind CSS** | 3 | 样式框架 |
| **Framer Motion** | 11 | 动画效果 |
| **Lucide React** | 0.314 | 图标库 |
| **Axios** | 1.6 | HTTP客户端 |
| **Vite** | 5 | 构建工具 |

---

## 📁 项目结构

```
MGAgent/
├── mgagent-backend/           # Chat 后端
│   ├── app/
│   │   ├── api/routes.py     # API路由
│   │   ├── agent/core.py     # Agent核心逻辑
│   │   ├── rag/              # RAG模块
│   │   ├── tools/            # 工具集
│   │   └── db/               # 数据库模型和CRUD
│   ├── data/                 # 数据存储目录
│   └── requirements.txt
├── mgagent-frontend/          # Chat 前端
│   ├── src/
│   │   ├── components/        # UI组件
│   │   ├── api/client.ts     # API客户端
│   │   └── App.tsx           # 主应用
│   └── package.json
├── mgagent-admin-backend/     # Admin 后端
│   ├── app/
│   │   ├── api/              # API路由
│   │   └── db/               # 数据库模型和CRUD
│   └── requirements.txt
├── mgagent-admin-frontend/    # Admin 前端
│   ├── src/
│   │   ├── pages/            # 页面组件
│   │   ├── components/       # UI组件
│   │   └── api/client.ts     # API客户端
│   └── package.json
├── scripts/                  # 启动脚本
│   ├── start-all.sh
│   ├── stop-all.sh
│   └── status.sh
└── README.md
```

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！如果你想为 MGAgent 做出贡献，请遵循以下步骤：

### 贡献流程

1. **Fork 项目**：点击右上角的 Fork 按钮
2. **创建分支**：`git checkout -b feature/your-feature`
3. **提交代码**：`git commit -m "feat: add your feature"`
4. **推送分支**：`git push origin feature/your-feature`
5. **创建 PR**：在 GitHub 上创建 Pull Request

### 代码规范

- **Python**：遵循 PEP 8 规范
- **TypeScript/React**：遵循 ESLint 规则
- **提交信息**：使用 Conventional Commits 格式

### 开发环境

```bash
# 安装 pre-commit 钩子
pip install pre-commit
pre-commit install
```

---

## 📄 许可证

MGAgent 采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

## 📞 联系方式

如有问题或建议，欢迎通过以下方式联系我们：

- 📧 邮箱：gqq1185805174@gmail.com
- 🐙 GitHub：[https://github.com/xmgfy/MGAgent](https://github.com/xmgfy/MGAgent)

---

**如果这个项目对你有帮助，请给我们一个 ⭐ Star！**

Made with ❤️ by the MGAgent Team