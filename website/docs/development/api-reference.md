---
title: API 参考
description: MGAgent API 接口详细说明，包括认证、聊天、管理等所有端点
slug: /development/api-reference
---

# API 参考

## 概述

MGAgent 提供两套 RESTful API 服务：

| API | 基础路径 | 端口 | 说明 |
|-----|---------|------|------|
| Chat API | `/api` | 8000 | 用户对话相关接口 |
| Admin API | `/admin/api` | 8001 | 管理后台接口 |

## 认证

### 登录

```bash
# Chat 前端登录
POST /api/auth/login

# Admin 后台登录
POST /admin/api/auth/login
```

**请求体：**

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应：**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "admin-001",
    "username": "admin",
    "role": "platform_admin"
  }
}
```

### 使用 Token

```bash
# 所有需要认证的请求都要携带 Token
Authorization: Bearer <access_token>
```

## Chat API

### 健康检查

```bash
GET /api/health
```

```json
{
  "status": "ok",
  "scheme": "mysql",
  "vector_db": "milvus",
  "file_storage": "minio",
  "version": "2.3.0"
}
```

### 发送消息

```bash
POST /api/chat
```

**请求体：**

```json
{
  "message": "帮我查询上个月的销售数据",
  "session_id": "session-001"
}
```

**响应：**

```json
{
  "response": "根据查询结果，上个月的销售总额为...",
  "session_id": "session-001",
  "tool_used": ["rag_retrieve", "query_database"]
}
```

### 流式对话

```bash
POST /api/chat/stream
```

使用 SSE (Server-Sent Events) 方式流式返回响应。

### 会话管理

```bash
# 获取会话列表
GET /api/sessions

# 创建新会话
POST /api/sessions

# 获取会话消息
GET /api/sessions/{session_id}/messages

# 删除会话
DELETE /api/sessions/{session_id}
```

### 用户注册

```bash
POST /api/auth/register
```

**请求体：**

```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure_password"
}
```

### 匿名使用

```bash
# 获取匿名使用次数
GET /api/anonymous/stats

# 匿名对话（无需登录）
POST /api/anonymous/chat
```

## Admin API

### 仪表盘

```bash
# 获取系统概览
GET /admin/api/dashboard/stats

# 获取最近活动
GET /admin/api/dashboard/recent-activity
```

**响应：**

```json
{
  "total_users": 150,
  "active_users": 120,
  "total_sessions": 5000,
  "total_documents": 85,
  "system_status": "healthy"
}
```

### 用户管理

```bash
# 获取用户列表
GET /admin/api/users?page=1&page_size=20&status=pending

# 获取单个用户
GET /admin/api/users/{user_id}

# 审批用户
POST /admin/api/users/{user_id}/approve

# 拒绝用户
POST /admin/api/users/{user_id}/reject

# 删除用户
DELETE /admin/api/users/{user_id}

# 更新用户
PUT /admin/api/users/{user_id}
```

### 管理员管理

```bash
# 获取管理员列表
GET /admin/api/admins

# 创建管理员
POST /admin/api/admins

# 更新管理员
PUT /admin/api/admins/{admin_id}

# 删除管理员
DELETE /admin/api/admins/{admin_id}
```

### 租户管理

```bash
# 获取租户列表
GET /admin/api/tenants

# 创建租户
POST /admin/api/tenants

# 更新租户
PUT /admin/api/tenants/{tenant_id}

# 删除租户
DELETE /admin/api/tenants/{tenant_id}
```

### 模型配置管理

```bash
# 获取当前活跃的模型配置
GET /admin/api/model/config

# 获取所有模型配置
GET /admin/api/model/configs

# 创建新模型配置
POST /admin/api/model/configs
```

**请求体：**

```json
{
  "name": "GPT-4o Mini",
  "api_key": "sk-xxx",
  "api_base": "https://api.openai.com/v1",
  "model_name": "gpt-4o-mini"
}
```

```bash
# 更新模型配置
PUT /admin/api/model/configs/{config_id}

# 删除模型配置
DELETE /admin/api/model/configs/{config_id}

# 激活模型配置
POST /admin/api/model/configs/{config_id}/activate

# 测试模型连接
GET /admin/api/model/test
```

### 知识库管理

```bash
# 获取文档列表
GET /admin/api/knowledge/documents

# 上传文档
POST /admin/api/knowledge/documents
Content-Type: multipart/form-data

# 删除文档
DELETE /admin/api/knowledge/documents/{doc_id}

# 重新处理文档
POST /admin/api/knowledge/documents/{doc_id}/reprocess
```

### 存储管理

```bash
# 获取存储信息
GET /admin/api/storage/info

# 执行 SQL 查询
POST /admin/api/storage/query
```

**请求体：**

```json
{
  "sql": "SELECT * FROM users LIMIT 10"
}
```

### 向量数据库管理

```bash
# 获取向量库状态
GET /admin/api/vector/stats

# 获取所有向量块
GET /admin/api/vector/chunks

# 清空向量库
DELETE /admin/api/vector/clear
```

### 系统管理

```bash
# 获取系统状态
GET /admin/api/system/status

# 获取系统配置
GET /admin/api/system/config

# 更新系统配置
PUT /admin/api/system/config
```

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息",
  "status_code": 400
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 / Token 无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 错误示例

```bash
# 模型未配置
POST /api/chat
```

```json
{
  "detail": "未配置有效的模型，请在admin管理端配置并启用模型"
}
```

## 数据格式

### 通用响应

所有列表接口支持分页：

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### 时间格式

所有时间字段使用 ISO 8601 格式：

```
2024-01-15T10:30:00.000000
```

### ID 格式

所有 ID 使用 UUID 字符串：

```
550e8400-e29b-41d4-a716-446655440000
```

## 相关文档

- [项目结构](/development/project-structure)
- [脚本使用指南](/development/scripts)
- [模型配置架构](/architecture/model-config)
