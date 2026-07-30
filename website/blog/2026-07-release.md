---
slug: 2026-07-release
title: 2026年7月 - 双技术栈架构与文档站点
date: 2026-07-15
authors: [mgagent]
tags: [新功能, 架构升级, 文档]
description: MGAgent 重大更新：支持双技术栈架构，上线 Docusaurus 在线文档站点
---

<!-- truncate -->

## 核心更新

### 🎯 双技术栈架构支持

MGAgent 现已支持两套技术栈方案，可根据部署场景灵活选择：

- **方案一：SQLite + ChromaDB**（开发调试）
  - 轻量级单机部署
  - 无需外部依赖，快速启动
  - 适用于个人开发者和小型团队

- **方案二：MySQL + Milvus**（生产部署）
  - 高性能企业级部署
  - 支持高并发和大规模数据
  - 适用于企业生产环境

### 📚 在线文档站点上线

基于 GitHub Pages + Docusaurus 构建的完整在线文档站点已上线：

- 完整的项目文档和 API 参考
- 交互式 Mermaid 架构图
- 多语言支持（中文优先）
- 响应式设计，支持移动端

### 🔧 一键部署脚本

新增 `deploy.sh` 一键部署脚本：

```bash
# SQLite 方案
./scripts/deploy.sh sqlite

# MySQL 方案
./scripts/deploy.sh mysql

# 停止所有服务
./scripts/deploy.sh stop
```

## 优化与改进

- 优化 Docker Compose 配置，采用分层部署架构
- 大模型配置统一从数据库读取，支持动态切换
- 前端 Admin 端模型配置管理功能完善
- 修复 Mermaid 图表渲染问题

## 致谢

感谢所有为本次更新做出贡献的开发者！
