---
title: 模型配置
description: MGAgent 大模型配置管理、动态加载与配置变更即时刷新机制
slug: /architecture/model-config
---

# 模型配置

## 概述

MGAgent 的大模型配置统一存储在数据库中，通过 Admin 端管理，支持动态切换和即时刷新。

## 配置表设计

`model_configs` 表存储 LLM 模型配置信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | 主键，UUID |
| name | VARCHAR(255) | 配置名称，唯一 |
| api_key | VARCHAR(500) | API 密钥 |
| api_base | VARCHAR(200) | API 基础 URL |
| model_name | VARCHAR(100) | 模型名称 |
| is_active | BOOLEAN | 是否为当前活跃配置 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 配置加载机制

### 启动时加载

系统启动时从数据库加载当前活跃的模型配置：

```python
from app.db.database import get_session
from app.models.model_config import ModelConfig

def load_active_config():
    """加载当前活跃的模型配置"""
    with get_session() as session:
        config = session.query(ModelConfig).filter(
            ModelConfig.is_active == True
        ).first()
        return config
```

### 配置变更即时刷新

系统运行时通过定时检查机制自动感知配置变更：

```python
import asyncio
from datetime import datetime

async def config_refresh_loop():
    """配置刷新循环"""
    while True:
        await asyncio.sleep(60)  # 每 60 秒检查一次
        current_config = get_current_config()
        if current_config != cached_config:
            reload_model_config(current_config)
            cached_config = current_config
```

## 动态切换示例

### 添加新模型配置

```python
# Admin 端 API
POST /admin/api/model-configs
{
    "name": "GPT-4 配置",
    "api_key": "sk-...",
    "api_base": "https://api.openai.com/v1",
    "model_name": "gpt-4",
    "is_active": false
}
```

### 切换当前模型

```python
# 激活指定配置
PUT /admin/api/model-configs/{config_id}/activate
```

## 与其他模块的集成

### 向量检索器

向量检索器在初始化时获取当前模型配置：

```python
class VectorRetriever:
    def __init__(self):
        self.model_config = self._get_active_config()
        self.embedding_model = self._create_embedding_model()
    
    def _get_active_config(self):
        """获取当前活跃的模型配置"""
        config = load_active_config()
        if not config:
            raise Exception("未配置模型，请先在 Admin 端配置")
        return config
    
    def _create_embedding_model(self):
        """创建嵌入模型实例"""
        return EmbeddingModel(
            api_key=self.model_config.api_key,
            api_base=self.model_config.api_base,
            model_name=self.model_config.model_name
        )
```

### 对话引擎

对话引擎使用模型配置进行 LLM 调用：

```python
class ConversationEngine:
    async def chat(self, messages):
        config = self._get_active_config()
        llm = ChatModel(
            api_key=config.api_key,
            api_base=config.api_base,
            model=config.model_name
        )
        response = await llm.ainvoke(messages)
        return response
```

## 配置校验

Admin 端保存配置时进行以下校验：

1. **必填字段校验**：`api_key`、`api_base`、`model_name` 为必填项
2. **URL 格式校验**：`api_base` 必须为合法的 URL
3. **重复名称校验**：配置名称不能重复
4. **API 连通性测试**：保存前测试 API 是否可用

## 最佳实践

1. **多环境配置**：为开发、测试、生产环境分别创建配置
2. **密钥管理**：API Key 加密存储，前端脱敏显示
3. **配置备份**：定期备份模型配置
4. **日志审计**：记录配置变更历史

## 相关文档

- [双技术栈架构](/architecture/dual-stack)
- [数据库设计](/architecture/database)
- [Admin 端使用](/development/api-reference)
