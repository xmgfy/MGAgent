# MGAgent

企业级智能体系统，基于 LangChain 构建，支持双技术栈架构，适用于企业级智能客服、知识问答、数据分析等场景。

## ✨ 核心特性

- � **智能对话**：基于大模型的多轮对话能力
- 📚 **知识库检索**：向量检索增强的 RAG 能力
- 🗄️ **数据库查询**：自然语言转 SQL 的数据库操作
- 🔧 **多工具调用**：支持 API、计算、搜索等多种工具
- � **多租户管理**：支持多用户、多知识库隔离
- ⚙️ **模型配置管理**：Admin 端统一管理大模型配置

## �️ 双技术栈架构

| 方案 | 关系数据库 | 向量数据库 | 适用场景 |
|------|-----------|-----------|----------|
| 方案1 | SQLite | ChromaDB | 轻量级开发调试 |
| 方案2 | MySQL 8.0 | Milvus 2.4 | 生产级大规模部署 |

## 🚀 快速开始

### 本地开发（SQLite 方案）

```bash
# 克隆项目
git clone https://github.com/your-github-username/mgagent.git
cd mgagent

# 一键初始化
./scripts/init.sh

# 一键启动本地服务
./scripts/start-all.sh

# 访问应用
# 主前端: http://localhost:3000
# Admin 前端: http://localhost:3001
```

### Docker 部署

```bash
# SQLite 方案
./scripts/deploy.sh sqlite

# MySQL 方案（分层部署）
./scripts/deploy.sh mysql
```

## 📖 完整文档

详细文档请访问在线文档站点：

👉 [MGAgent Documentation](https://your-github-username.github.io/mgagent)

## 🛠️ 技术栈

- **后端**: Python 3.10+, FastAPI, LangChain
- **前端**: React 18, TypeScript, Vite
- **数据库**: SQLite / MySQL 8.0
- **向量数据库**: ChromaDB / Milvus 2.4
- **部署**: Docker, Docker Compose

## 📁 项目结构

```
MGAgent/
├── mgagent-backend/          # 主后端服务
├── mgagent-admin-backend/    # Admin 后端服务
├── mgagent-frontend/         # 主前端应用
├── mgagent-admin-frontend/   # Admin 前端应用
├── docker-compose.local.yml  # SQLite 方案 Compose 配置
├── docker-compose.infra.yml  # 基础设施 Compose 配置
├── docker-compose.mysql-app.yml # 应用层 Compose 配置
├── scripts/                  # 工具脚本
├── website/                  # Docusaurus 文档站点
└── docs/                     # 其他文档
```

## 📄 许可证

MIT License
