---
slug: 2026-04-release
title: 2026年4月 - 项目启动与基础功能
date: 2026-04-10
authors: [mgagent]
tags: [项目启动, 基础功能]
description: MGAgent 项目正式启动，发布基础版本
---

<!-- truncate -->

## 项目启动

MGAgent 企业级智能体系统正式发布！

### 🌟 核心功能首发

- **智能对话**：基于大模型的多轮对话能力
- **上下文理解**：支持多轮对话上下文记忆
- **意图识别**：精准理解用户意图
- **流式响应**：实时流式输出，提升交互体验

### 🏗️ 架构设计

MGAgent 采用现代化技术栈构建：

- **后端**：FastAPI + LangChain + SQLAlchemy
- **前端**：React + TypeScript + Tailwind CSS
- **存储**：SQLite / MySQL + ChromaDB / Milvus
- **部署**：Docker Compose 容器化部署

### 📁 项目结构

```
MGAgent/
├── app/                    # 后端应用
│   ├── api/                # API 路由
│   ├── agent/              # Agent 核心
│   ├── config/             # 配置模块
│   ├── db/                 # 数据库
│   ├── rag/                # RAG 模块
│   ├── services/           # 服务层
│   └── tools/              # 工具集
├── mgagent-frontend/       # Chat 前端
├── mgagent-admin-frontend/ # Admin 前端
├── scripts/                # 部署脚本
└── docker/                 # Docker 配置
```

### 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/xmgfy/mgagent.git

# 进入目录
cd mgagent

# SQLite 方案一键启动
./scripts/deploy.sh sqlite

# 或 MySQL 方案一键启动
./scripts/deploy.sh mysql
```

## 致谢

感谢每一位参与项目开发和测试的朋友！
