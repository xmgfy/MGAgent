---
title: 模型配置
description: MGAgent 大模型配置管理、动态加载与配置变更即时刷新机制，支持云端 API、本地 Ollama 和本地 Embedding 模型
slug: /architecture/model-config
---

# 模型配置

## 概述

MGAgent 的大模型配置采用三层协同架构，统一存储在数据库中，通过 Admin 端管理，支持动态切换和即时刷新，**配置变更无需重启服务即可生效**。

| 层级 | 组件 | 职责 |
|------|------|------|
| **元数据层** | Provider 厂商注册表 | 维护可用的 LLM 厂商信息，种子预置 + 用户自定义混合 |
| **配置层** | ModelConfig 模型配置 | 每条配置对应一个具体模型实例，支持多租户、多场景、多策略 |
| **路由层** | LLM Factory 工厂模式 | 根据 `tenant_id` + `scenario` 动态解析出正确的 ModelConfig，并路由到对应的 LangChain 实现 |

系统支持三种模型类型：

- **对话模型 (`chat`)**：用于用户对话的 LLM 模型
- **Embedding 模型 (`embedding`)**：用于知识库向量化的嵌入模型
- **重排序模型 (`reranker`)**：用于检索后重排序的 Cross-Encoder 模型

> **注意**：`chat` 和 `embedding` 是主流程必需的，同一时刻每种类型最多激活一条配置。`reranker` 为可选功能。

---

## Provider 厂商注册表

Provider 注册表定义了每个 LLM 厂商的元数据（API Base、是否支持 API Key、支持哪些模型类型、是否可动态发现等），是 ModelConfig 的"上游字典"。

### 表结构

`providers` 表字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | VARCHAR(64) | 主键，UUID |
| `code` | VARCHAR(50) | 厂商唯一编码（如 `openai`、`deepseek`） |
| `display_name` | VARCHAR(100) | 前端显示名称 |
| `favicon_domain` | VARCHAR(200) | 用于展示厂商图标域名 |
| `default_api_base` | VARCHAR(300) | 默认 API Base URL，创建 ModelConfig 时预填 |
| `supports_api_key` | BOOLEAN | 是否需要 API Key（Ollama / local 为 `False`） |
| `supports_local` | BOOLEAN | 是否为本地部署 |
| `supports_discover` | BOOLEAN | 是否支持通过 API 动态发现模型列表 |
| `supported_model_types` | TEXT (JSON) | 支持的模型类型数组，如 `["chat","embedding"]` |
| `fallback_models` | TEXT (JSON) | 兜底模型列表，按类型分组 |
| `description` | VARCHAR(500) | 厂商简介 |
| `api_key` | VARCHAR(500) | **Provider 级全局 API Key**，创建 ModelConfig 时自动预填 |
| `is_system` | BOOLEAN | 是否为内置种子 Provider（不可删除） |
| `is_active` | BOOLEAN | 是否启用该 Provider |
| `created_at` / `updated_at` | DATETIME | 时间戳 |

### 种子 upsert 机制

系统内置了一组种子 Provider（定义在 `mgagent-admin-backend/app/config/providers.py`），服务启动时通过 `seed_providers(db)` 函数将其 upsert 到 `providers` 表。

**upsert 策略（关键）**：

| 场景 | 行为 |
|------|------|
| DB 中不存在该 `code` | **插入新行**，完整使用种子元数据（`api_key` 为空），标记 `is_system=True` |
| DB 中已存在且 `is_system=True` | 更新 `display_name`、`default_api_base`、`supports_*` 等元数据列，**但不覆盖** `api_key`、`supported_model_types`、`fallback_models`、`is_active` |
| DB 中已存在且 `is_system=False` | **跳过**，不做任何修改 |

这样设计的好处：用户通过「探测类型」动态发现了新模型类型，或手动修改了 API Key 后，重启服务不会被种子重置。

### 已支持的种子厂商

| code | 厂商 | 类型覆盖 | 默认 API Base | 特点 |
|------|------|----------|---------------|------|
| `openai` | OpenAI | chat, embedding | `https://api.openai.com/v1` | 标准 ChatOpenAI |
| `deepseek` | DeepSeek 深度求索 | chat, embedding | `https://api.deepseek.com/v1` | 性价比高，OpenAI 兼容 |
| `dashscope` | 阿里云 DashScope | chat, embedding, reranker | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 通义千问，OpenAI 兼容 |
| `zhipu` | 智谱 AI | chat, embedding | `https://open.bigmodel.cn/api/paas/v4` | GLM 系列 |
| `minimax` | MiniMax | chat, embedding, reranker | `https://api.minimax.chat/v1` | 海螺 AI |
| `moonshot` | Moonshot (Kimi) | chat, embedding | `https://api.moonshot.cn/v1` | 长上下文 |
| `stepfun` | 阶跃星辰 | chat, embedding | `https://api.stepfun.com/v1` | Step 系列 |
| `jina` | Jina AI | embedding, reranker | `https://api.jina.ai/v1` | 专注 Embedding / 重排 |
| `ollama` | Ollama | chat, embedding | `http://localhost:11434/v1` | 本地运行，不走 API Key |
| `local` | 本地 Embedding | embedding | （空） | sentence-transformers，免 Key |
| `custom` | 自定义 OpenAI 兼容 | chat, embedding, reranker | （空） | 接入任何 OpenAI 兼容 API |

### API Key 继承机制

```
Provider 级 api_key（全局默认）
        │
        ▼ 创建 ModelConfig 时自动预填
        │
   ModelConfig.api_key（用户可覆盖）
        │
        ▼ LLM Factory 构建 LangChain 实例时使用
   ChatOpenAI(api_key=config.api_key or "")
```

Provider 级 `api_key` 存的是厂商账号的全局 Key，创建 ModelConfig 时会自动填充到新建行的 `api_key` 字段。用户可以为每个 ModelConfig 单独覆盖，也可以留空（此时运行时会回退到 Provider 级 Key）。

### 动态模型发现

Admin 端提供了"🔍 探测可用模型"功能，后端端点为 `POST /admin/api/model/providers/discover-models`。

**发现流程**：

1. 前端传入 `provider_code` + `api_key`（可选，若未传则使用 Provider 级 Key）
2. 后端调用对应厂商的模型列表接口
   - OpenAI 兼容厂商：`GET {api_base}/models`
   - Ollama：`GET {api_base}/api/tags`
3. 对返回的模型列表自动分类（`classify_model_type`）：
   - 名称包含 `embed-`、`embedding`、`bge-`、`gte-` 等关键词 → `embedding`
   - 包含 `rerank`、`reranker`、`ranker`、`cross-encoder` → `reranker`
   - 排除 `whisper`、`tts`、`vision`、`dall` 等非对话模型关键词
   - 其余默认 → `chat`
4. 返回分类后的列表 + 每个模型的已知维度（`get_known_dimension`）

**已知 Embedding 维度**（部分）：

| 模型名 | 维度 |
|--------|------|
| `text-embedding-3-small` | 1536 |
| `text-embedding-3-large` | 3072 |
| `text-embedding-ada-002` | 1536 |
| `deepseek-embedding-v1` | 1024 |
| `text-embedding-v3` | 1024 |
| `embedding-3` / `embedding-2` | 1024 |
| `jina-embeddings-v3` | 1024 |
| `bge-m3` | 1024 |

---

## ModelConfig 模型配置

每条 `ModelConfig` 记录一个具体的 LLM 模型实例，包含租户隔离、场景隔离和高级参数。

### 完整表结构

`model_configs` 表字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | VARCHAR(64) | 主键，UUID |
| `name` | VARCHAR(100) | 配置名称（唯一） |
| `model_type` | VARCHAR(20) | `chat` / `embedding` / `reranker` |
| `provider` | VARCHAR(50) | Provider 的 `code` 外键 |
| `api_key` | VARCHAR(500) | API 密钥（本地模型可为空） |
| `api_base` | VARCHAR(300) | API Base URL（本地模型可为空） |
| `model_name` | VARCHAR(100) | 实际的模型名称，如 `gpt-4o-mini` |
| `dimension` | INTEGER | 向量维度（仅 Embedding 类型） |
| `is_local` | BOOLEAN | 是否本地部署 |
| `is_active` | BOOLEAN | 是否为当前活跃配置（同类型可有多条 active，通过 tenant+scenario 区分） |
| `tenant_id` | VARCHAR(64) | 租户 ID（`NULL` = 全局默认） |
| `scenario` | VARCHAR(50) | 场景标识，如 `chat`、`rag`、`code`、`default`（`NULL` = 该租户全局默认） |
| `temperature` | FLOAT | 采样温度（`chat` 默认 0.7，非 chat 默认 0.1） |
| `top_p` | FLOAT | Nucleus 采样参数 |
| `max_tokens` | INTEGER | 最大生成 token 数 |
| `presence_penalty` | FLOAT | 存在惩罚（-2.0 ~ 2.0） |
| `frequency_penalty` | FLOAT | 频率惩罚（-2.0 ~ 2.0） |
| `created_at` / `updated_at` | DATETIME | 时间戳 |

### 多租户 + 多场景优先级

系统支持多租户和多场景隔离。同一 `model_type` 可以存在多条 `is_active=True` 的配置，运行时通过**优先级排序**选出最合适的一条。

**查询优先级（从高到低）**：

| 优先级 | 条件 | 含义 |
|--------|------|------|
| 1（最高） | `tenant_id = 指定值` AND `scenario = 指定值` | 某租户 + 某场景专用 |
| 2 | `tenant_id = 指定值` AND `scenario IS NULL` | 某租户全局默认 |
| 3 | `tenant_id IS NULL` AND `scenario = 指定值` | 该场景全局默认 |
| 4（最低） | `tenant_id IS NULL` AND `scenario IS NULL` | 全局默认（兜底） |

同级内按 `created_at DESC` 取最新一条。

**SQL 等价表达**：

```sql
SELECT * FROM model_configs
WHERE model_type = :model_type AND is_active = TRUE
ORDER BY
  (tenant_id = :tenant_id) DESC,
  (scenario  = :scenario)  DESC,
  created_at DESC
LIMIT 1;
```

**典型场景示例**：

- 租户 `tenant_A` 的客服对话 → `tenant_id="tenant_A", scenario="chat"` 专用 GPT-4o
- 租户 `tenant_A` 的 RAG 检索 → `tenant_id="tenant_A", scenario="rag"` 专用 deepseek-chat
- 租户 `tenant_B` 未配置 → 回退到 `tenant_id=NULL, scenario=NULL` 的全局默认

### 高级参数含义

| 参数 | 类型 | 推荐范围 | 默认值 | 说明 |
|------|------|----------|--------|------|
| `temperature` | float | 0.0 ~ 2.0 | 对话 0.7 / RAG 0.1 | 采样温度。越高越有创造性，越低越确定。RAG 和代码生成场景建议 0.1 ~ 0.3 |
| `top_p` | float | 0.0 ~ 1.0 | 工厂默认不设 | Nucleus 采样的概率阈值，与 `temperature` 二选一使用 |
| `max_tokens` | int | 模型上限的 50% ~ 90% | 工厂默认不设 | 单次响应的最大 token 数，防止超长输出 |
| `presence_penalty` | float | -2.0 ~ 2.0 | 0.0 | 对已出现 token 增加惩罚，鼓励生成新话题。正值增强多样性 |
| `frequency_penalty` | float | -2.0 ~ 2.0 | 0.0 | 根据 token 出现频率增加惩罚，抑制重复。正值降低重复率 |

---

## LLM Factory 工厂路由

### 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        调用方                                │
│            (Agent / RAG Retriever / Code Executor)           │
└─────────┬───────────────────────────────────────────────────┘
          │ get_llm(tenant_id=..., scenario=..., model_type=...)
          ▼
┌─────────────────────────────────────────────────────────────┐
│            model_config_service.get_active_model_config_row  │
│  按 tenant_id + scenario + model_type + 优先级查询 DB        │
└─────────┬───────────────────────────────────────────────────┘
          │ 返回 ModelConfig ORM 行
          ▼
┌─────────────────────────────────────────────────────────────┐
│                      LLM Factory                             │
│                                                              │
│  BaseLLMProvider (ABC)                                       │
│     ├─ OpenAICompatibleProvider   ← openai, deepseek,        │
│     │                             dashscope, zhipu, minimax, │
│     │                             moonshot, stepfun, jina,   │
│     │                             custom                      │
│     └─ LocalOllamaProvider        ← ollama                   │
│                                                              │
│  local 模型（sentence-transformers）在工厂外独立处理          │
└─────────┬───────────────────────────────────────────────────┘
          │ 返回 LangChain Runnable
          ▼
┌─────────────────────────────────────────────────────────────┐
│              LangChain ChatOpenAI / ChatOllama /             │
│              HuggingFaceEmbeddings                           │
└─────────────────────────────────────────────────────────────┘
```

### 参数优先级

```
用户显式传入 get_llm(temperature=...)    ← 最高
         │
         ▼
DB ModelConfig.temperature / top_p / ...  ← 其次
         │
         ▼
工厂内部默认值                             ← 兜底
  chat 场景：temperature=0.7
  非 chat 场景（RAG 等）：temperature=0.1
```

### Provider 路由映射

| Provider code | 工厂实现类 | 底层 LangChain | 备注 |
|---------------|-----------|---------------|------|
| `ollama` | `LocalOllamaProvider` | `ChatOllama` | 去掉 `/v1` 后访问 Ollama 原生 HTTP |
| `openai` / `deepseek` / `dashscope` / `zhipu` / `minimax` / `moonshot` / `stepfun` / `jina` / `custom` | `OpenAICompatibleProvider` | `ChatOpenAI` | 通过 `base_url` 区分厂商 |
| `local` | 不走工厂 | `HuggingFaceEmbeddings` | sentence-transformers 本地加载 |

### Chat Model 与 Embedding Model 独立工厂

工厂提供两个独立入口：

```python
# 创建对话模型 LangChain Runnable
from app.services.llm_factory import create_llm
llm = create_llm(db_row, overrides={"temperature": 0.3})

# 创建 Embedding 模型 LangChain Runnable
from app.services.llm_factory import create_embedding
embeddings = create_embedding(db_row)
```

每个入口都先通过 `model_config_service` 按 `model_type` + `tenant_id` + `scenario` 查出对应 ORM 行，再走 Provider 路由。

---

## Admin 端使用手册

### Provider 管理

**API 端点汇总**：

| 操作 | 方法 | 端点 |
|------|------|------|
| 列出所有 Provider | `GET` | `/admin/api/model/providers` |
| 按类型过滤 | `GET` | `/admin/api/model/providers?model_type=chat` |
| 新增自定义 Provider | `POST` | `/admin/api/model/providers` |
| 编辑 Provider | `PUT` | `/admin/api/model/providers/{provider_id}` |
| 启用/禁用 | `POST` | `/admin/api/model/providers/{provider_id}/toggle` |
| 删除（仅非系统） | `DELETE` | `/admin/api/model/providers/{provider_id}` |

**新增自定义 Provider 示例**（接入 Dify / FastGPT 等 OpenAI 兼容服务）：

```json
POST /admin/api/model/providers
{
  "code": "my-gateway",
  "display_name": "内部网关",
  "default_api_base": "https://gateway.example.com/v1",
  "supports_api_key": true,
  "supports_local": false,
  "supports_discover": true,
  "supported_model_types": ["chat", "embedding"],
  "description": "内部统一 LLM 网关"
}
```

> **系统内置 Provider 不可删除**（`is_system=True`），但可以修改 `api_key`、`default_api_base` 等字段。

### 动态发现模型

**API**：`POST /admin/api/model/providers/discover-models`

```json
{
  "provider_code": "deepseek",
  "api_key": "sk-...",
  "model_type": "chat"
}
```

**前端典型流程**：

1. 选择 Provider → 自动预填 `default_api_base` 和 Provider 级 `api_key`
2. 点击「🔍 探测可用模型」按钮
3. 后端调用厂商 `/v1/models` 接口并自动分类
4. 前端展示探测到的模型列表（按 `chat` / `embedding` / `reranker` 分组）
5. 用户一键选择某模型 → 自动填入 `model_name`、`model_type`、`dimension`

### 模型配置管理

**API 端点汇总**：

| 操作 | 方法 | 端点 |
|------|------|------|
| 创建配置 | `POST` | `/admin/api/model/config` |
| 列表 | `GET` | `/admin/api/model/configs` |
| 详情 | `GET` | `/admin/api/model/config/{config_id}` |
| 更新 | `PUT` | `/admin/api/model/config/{config_id}` |
| 激活 | `POST` | `/admin/api/model/config/{config_id}/activate` |
| 停用 | `POST` | `/admin/api/model/config/{config_id}/deactivate` |
| 删除（需先停用） | `DELETE` | `/admin/api/model/config/{config_id}` |
| 测试连通性 | `GET` | `/admin/api/model/test` |

**创建配置请求体**：

```json
POST /admin/api/model/config
{
  "name": "GPT-4o 客服对话",
  "model_type": "chat",
  "provider": "openai",
  "api_key": "sk-...（留空则继承 Provider 级 Key）",
  "api_base": "https://api.openai.com/v1",
  "model_name": "gpt-4o-mini",
  "dimension": null,
  "is_local": false,
  "scenario": "chat",
  "tenant_id": "tenant_A",
  "temperature": 0.7,
  "top_p": null,
  "max_tokens": 4096,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0
}
```

**激活规则**：

- 每种 `model_type`（chat / embedding / reranker）在同一优先级维度下，**最多只有一条 active**
- Activate 时会自动将同类型、同 `tenant_id` + `scenario` 的其他配置置为 inactive
- 全局默认（`tenant_id=NULL, scenario=NULL`）只有一条 active

### 前端场景与租户选择

| 字段 | 选择方式 | 说明 |
|------|----------|------|
| `tenant_id` | 下拉选择或留空 | 留空 = 全局默认，不绑定特定租户 |
| `scenario` | 下拉选择或留空 | 预设值：`chat`（对话）、`rag`（检索增强）、`code`（代码生成）、`default`。留空 = 该租户全局默认 |

---

## 本地 Embedding 模型

### 支持的模型列表

通过 `sentence-transformers` 库加载，模型 ID → HuggingFace 名称映射：

| ID | HuggingFace 名称 | 维度 | 大小 | 语言 |
|----|-----------------|------|------|------|
| `bge-small-zh` | BAAI/bge-small-zh-v1.5 | 512 | ~100MB | 中文 |
| `bge-base-zh` | BAAI/bge-base-zh-v1.5 | 768 | ~400MB | 中文 |
| `bge-large-zh` | BAAI/bge-large-zh-v1.5 | 1024 | ~1.3GB | 中文 |
| `bge-m3` | BAAI/bge-m3 | 1024 | ~2.3GB | 中英 |
| `m3e-base` | moka-ai/m3e-base | 768 | ~400MB | 中文 |
| `m3e-large` | moka-ai/m3e-large | 1024 | ~1.3GB | 中文 |
| `gte-base-zh` | thenlper/gte-base-zh | 768 | ~400MB | 中文 |
| `gte-large-zh` | thenlper/gte-large-zh | 1024 | ~1.3GB | 中文 |
| `jina-embeddings-v2-base-zh` | jinaai/jina-embeddings-v2-base-zh | 768 | ~400MB | 中英 |
| `paraphrase-multilingual` | paraphrase-multilingual-MiniLM-L12-v2 | 384 | ~120MB | 多语言 |

### 推荐选择

| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| 调试开发 / 资源受限 | `bge-small-zh` 或 `paraphrase-multilingual` | 体积小、加载快 |
| 小规模知识库（<10万文档） | `bge-base-zh` | 效果与资源平衡 |
| 生产环境（10万+文档） | `bge-large-zh` | 中文效果最好 |
| 中英文混合 | `bge-m3` | 双语支持 |
| 多语言且资源有限 | `paraphrase-multilingual` | 仅 120MB |

### 下载方式

#### 命令行脚本（推荐部署时使用）

```bash
cd mgagent-admin-backend

# 列出所有可用模型
python scripts/download_local_models.py --list

# 下载指定模型
python scripts/download_local_models.py --model bge-small-zh

# 下载多个模型
python scripts/download_local_models.py --models bge-small-zh,bge-large-zh

# 下载全部
python scripts/download_local_models.py --all

# 指定缓存目录
python scripts/download_local_models.py --model bge-base-zh --cache-dir /data/hf-cache
```

国内网络环境下，脚本会自动设置 `HF_ENDPOINT=https://hf-mirror.com` 镜像加速。

#### Admin 前端 API 下载

**API**：`POST /admin/api/model/local-models/download`

```python
import requests

resp = requests.post(
    "http://localhost:8001/admin/api/model/local-models/download",
    json={"model_id": "bge-small-zh"},
    headers={"Authorization": "Bearer <admin_token>"},
)
# 返回 {"status": "success", "model_id": "bge-small-zh", "dimension": 512, ...}
```

> **对比**：命令行脚本适合首次部署批量下载，不阻塞产品主流程；前端 API 适合运行中临时补充模型。

### Admin 端配置本地 Embedding

1. 进入 Admin → 「模型配置」
2. 点击「新增模型」
3. 选择 `model_type = embedding`
4. `provider` 选择 `local`
5. 勾选「使用本地模型」
6. 从下拉列表选择预设模型（自动填充 `model_name` 和 `dimension`）
7. 保存并激活

---

## 配置变更即时刷新

### 工作原理

MGAgent **不使用进程内缓存**模型配置。每次调用 LLM 时，都会通过 `model_config_service.get_active_model_config_row()` 实时查询数据库，然后由 LLM Factory 构建全新的 LangChain 实例。

```python
# mgagent-backend/app/services/model_config_service.py 核心逻辑
def get_active_model_config_row(model_type="chat", tenant_id=None, scenario=None):
    row = db.query(ModelConfig)\
        .filter(ModelConfig.model_type == model_type)\
        .filter(ModelConfig.is_active == True)\
        .order_by(
            (ModelConfig.tenant_id == tenant_id).desc(),
            (ModelConfig.scenario == scenario).desc(),
            ModelConfig.created_at.desc(),
        ).first()
    return row
```

**因此**：在 Admin 端修改、激活或停用配置后，**下一次 LLM 调用自动生效**，无需重启任何后端服务。

### 刷新链路

```
Admin 端修改 ModelConfig.is_active
    │
    ▼
mgagent-admin-backend 写 DB
    │
    ▼
mgagent-backend 下次 LLM 调用
    │
    ▼ model_config_service.get_active_model_config_row()
实时查询 DB → 取到新的 active 行
    │
    ▼ LLM Factory
构建新的 LangChain 实例（携带新的 api_key / model_name / temperature 等）
```

### tenant_id + scenario 动态路由

调用方（Agent / RAG / Code Executor）在请求 LLM 时可以显式传入租户和场景：

```python
from app.services.model_config_service import get_active_model_config_row
from app.services.llm_factory import create_llm

# 客服场景、租户 A
row = get_active_model_config_row(
    model_type="chat",
    tenant_id="tenant_A",
    scenario="chat",
)
llm = create_llm(row)

# RAG 场景、全局默认（不传 tenant_id）
row = get_active_model_config_row(
    model_type="chat",
    scenario="rag",
)
llm = create_llm(row, overrides={"temperature": 0.1})
```

---

## 最佳实践 + 常见问题

### 最佳实践

**1. 先配 Provider，再建 ModelConfig**

Provider 的 `default_api_base` 和 `api_key` 会在创建 ModelConfig 时自动预填，能减少手动输入错误。

**2. 使用动态发现代替手动输入**

几乎所有 OpenAI 兼容厂商都支持 `GET /v1/models`。先「探测可用模型」→ 一键选择，比手动输入 model_name 准确得多（还能自动拿到 embedding 维度）。

**3. 多租户按优先级建三层**

```
tenant_id=NULL, scenario=NULL  → 全局兜底（OpenAI GPT-4o）
tenant_id=租户A, scenario=NULL  → 租户A 默认（DeepSeek）
tenant_id=租户A, scenario=chat  → 租户A 客服场景专用（GPT-4o-mini，低 temperature）
```

**4. RAG 场景单独设 scenario**

RAG 检索增强对模型创造性要求低，建议单独创建一条 `scenario=rag` 的配置，`temperature=0.1`，减少推理时的幻觉。

**5. 本地模型部署时先下载**

把 `python scripts/download_local_models.py --model bge-base-zh` 加到部署脚本里，避免首次 RAG 索引时卡住下载。

**6. Ollama 模型名带 Tag**

Ollama 发现的模型名包含 tag（如 `qwen2.5:7b`），工厂会自动识别并去除 `/v1` 走原生 HTTP，不需要手动改 `api_base`。

### 常见问题

**Q：切换模型后 Agent 没有生效？**

A：确认 `model_type` 匹配。Chat 模型和 Embedding 模型是独立配置、独立激活的。切换对话模型改的是 `model_type=chat` 的 active 行，Embedding 不跟着变。

**Q："找不到有效的模型配置" 报错？**

A：检查调用时传入的 `tenant_id` 和 `scenario` 是否有对应的 active 配置。如果没有，需要补齐更高优先级的配置，或者去掉 `tenant_id` / `scenario` 让它回退到全局默认。

**Q：Provider 的 API Key 和 ModelConfig 的 API Key 都填了，用哪个？**

A：LLM Factory 读取的是 **ModelConfig.api_key**。Provider 级 Key 只在创建 ModelConfig 时用来预填；运行时两者独立，以 ModelConfig 上的为准。

**Q：如何在运行中加一个全新的自定义厂商？**

A：
1. 走「Provider 管理」新增一个 `code="my-gateway"` 的自定义 Provider，勾选 `supports_discover=true`
2. 保存后就能在「模型配置」里选到它
3. 如果 `supports_discover=true`，还可以用探测功能自动发现该网关下的模型

**Q：本地 Embedding 模型首次使用很慢？**

A：是的，`sentence-transformers` 加载大模型（`bge-large-zh` 1.3GB）首次需要 10~30 秒。建议在部署阶段用脚本预热下载，或启动时预加载。

**Q：如何删除系统内置 Provider（如 Ollama）？**

A：无法删除（`is_system=True`），但可以设为 `is_active=false` 让它不出现在前端下拉列表中。

---

## 相关文档

- [双技术栈架构](/architecture/dual-stack)
- [数据库设计](/architecture/database)
