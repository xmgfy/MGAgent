"""
模型提供商注册表 - 仅提供 Provider 元数据，模型列表通过动态发现获取

Supported model_types:
- chat       对话/生成模型
- embedding  向量嵌入模型
- reranker   重排序模型

混合架构说明：
- PROVIDERS 常量：内置种子（系统预置的提供商元数据）
- seed_providers(db)：启动时 upsert 到 DB，运行时以 DB 为唯一真相源
- 运行时 Provider 接口从 DB 读取，支持用户新增自定义 Provider
- DB 中 is_system=True 的行对应 PROVIDERS 常量内置项，不可删除但可修改 api_key
"""
import json
from typing import Dict, List, Any, Optional


PROVIDERS: List[Dict[str, Any]] = [
    {
        "code": "openai",
        "display_name": "OpenAI",
        "favicon_domain": "api.openai.com",
        "default_api_base": "https://api.openai.com/v1",
        "supports_api_key": True,
        "supports_local": False,
        "supports_discover": True,
        "supported_model_types": ["chat", "embedding"],
        "fallback_models": {
            "chat": ["gpt-4o-mini", "gpt-4o"],
            "embedding": ["text-embedding-3-small"],
        },
        "description": "OpenAI 官方 API，支持聊天和 Embedding 模型",
    },
    {
        "code": "deepseek",
        "display_name": "DeepSeek",
        "favicon_domain": "api.deepseek.com",
        "default_api_base": "https://api.deepseek.com/v1",
        "supports_api_key": True,
        "supports_local": False,
        "supports_discover": True,
        "supported_model_types": ["chat", "embedding"],
        "fallback_models": {
            "chat": ["deepseek-chat", "deepseek-reasoner"],
            "embedding": ["deepseek-embedding-v1"],
        },
        "description": "DeepSeek 深度求索，性价比高的推理和 Embedding 模型",
    },
    {
        "code": "dashscope",
        "display_name": "阿里云 DashScope",
        "favicon_domain": "dashscope.aliyuncs.com",
        "default_api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "supports_api_key": True,
        "supports_local": False,
        "supports_discover": True,
        "supported_model_types": ["chat", "embedding", "reranker"],
        "fallback_models": {
            "chat": ["qwen-plus", "qwen-turbo"],
            "embedding": ["text-embedding-v3"],
            "reranker": ["gte-rerank"],
        },
        "description": "阿里云百炼平台，通义千问系列模型",
    },
    {
        "code": "zhipu",
        "display_name": "智谱 AI",
        "favicon_domain": "open.bigmodel.cn",
        "default_api_base": "https://open.bigmodel.cn/api/paas/v4",
        "supports_api_key": True,
        "supports_local": False,
        "supports_discover": True,
        "supported_model_types": ["chat", "embedding"],
        "fallback_models": {
            "chat": ["glm-4-plus", "glm-4-flash"],
            "embedding": ["embedding-3"],
        },
        "description": "智谱 AI 大模型服务平台",
    },
    {
        "code": "minimax",
        "display_name": "MiniMax",
        "favicon_domain": "api.minimax.chat",
        "default_api_base": "https://api.minimax.chat/v1",
        "supports_api_key": True,
        "supports_local": False,
        "supports_discover": True,
        "supported_model_types": ["chat", "embedding", "reranker"],
        "fallback_models": {
            "chat": ["abab6.5s-chat", "abab6.5-chat"],
            "embedding": ["embo-01"],
            "reranker": ["rank-bge-large"],
        },
        "description": "MiniMax 海螺 AI，支持多模态和文本模型",
    },
    {
        "code": "moonshot",
        "display_name": "Moonshot AI (Kimi)",
        "favicon_domain": "api.moonshot.cn",
        "default_api_base": "https://api.moonshot.cn/v1",
        "supports_api_key": True,
        "supports_local": False,
        "supports_discover": True,
        "supported_model_types": ["chat", "embedding"],
        "fallback_models": {
            "chat": ["moonshot-v1-8k", "moonshot-v1-32k"],
            "embedding": ["moonshot-v1-8k"],
        },
        "description": "月之暗面 Kimi，长上下文模型",
    },
    {
        "code": "stepfun",
        "display_name": "阶跃星辰",
        "favicon_domain": "api.stepfun.com",
        "default_api_base": "https://api.stepfun.com/v1",
        "supports_api_key": True,
        "supports_local": False,
        "supports_discover": True,
        "supported_model_types": ["chat", "embedding"],
        "fallback_models": {
            "chat": ["step-2-16k", "step-1-256k"],
            "embedding": ["step-embedding"],
        },
        "description": "阶跃星辰 AI 服务平台",
    },
    {
        "code": "jina",
        "display_name": "Jina AI",
        "favicon_domain": "api.jina.ai",
        "default_api_base": "https://api.jina.ai/v1",
        "supports_api_key": True,
        "supports_local": False,
        "supports_discover": True,
        "supported_model_types": ["embedding", "reranker"],
        "fallback_models": {
            "embedding": ["jina-embeddings-v3"],
            "reranker": ["jina-reranker-v2-base-multilingual"],
        },
        "description": "专注 Embedding 和重排模型的 AI 服务商",
    },
    {
        "code": "ollama",
        "display_name": "Ollama",
        "favicon_domain": "ollama.com",
        "default_api_base": "http://localhost:11434/v1",
        "supports_api_key": False,
        "supports_local": True,
        "supports_discover": True,
        "discover_endpoint": "/api/tags",
        "supported_model_types": ["chat", "embedding"],
        "fallback_models": {
            "chat": ["qwen2.5:7b", "llama3.1:8b"],
            "embedding": ["nomic-embed-text"],
        },
        "description": "本地大模型运行框架，完全离线部署",
    },
    {
        "code": "local",
        "display_name": "本地 Embedding",
        "favicon_domain": "huggingface.co",
        "default_api_base": "",
        "supports_api_key": False,
        "supports_local": True,
        "supports_discover": False,
        "supported_model_types": ["embedding"],
        "fallback_models": {
            "embedding": [],
        },
        "description": "使用 HuggingFace sentence-transformers 本地运行（免 API Key）",
    },
    {
        "code": "custom",
        "display_name": "自定义 (OpenAI 兼容)",
        "favicon_domain": "openai.com",
        "default_api_base": "",
        "supports_api_key": True,
        "supports_local": False,
        "supports_discover": True,
        "supported_model_types": ["chat", "embedding", "reranker"],
        "fallback_models": {},
        "description": "接入任何 OpenAI 兼容 API（Dify/Coze/FastGPT/第三方网关/私有服务）",
    },
]


KNOWN_EMBEDDING_DIMENSIONS: Dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "deepseek-embedding-v1": 1024,
    "text-embedding-v3": 1024,
    "text-embedding-v2": 1536,
    "text-embedding-v1": 1536,
    "embedding-3": 1024,
    "embedding-2": 1024,
    "jina-embeddings-v3": 1024,
    "jina-embeddings-v2-base-zh": 768,
    "jina-embeddings-v2-base-en": 768,
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024,
    "bge-m3": 1024,
    "bge-large-zh": 1024,
    "bge-base-zh": 768,
    "gte-text-embedding": 1024,
}

MODEL_TYPE_LABELS: Dict[str, str] = {
    "chat": "对话模型",
    "embedding": "Embedding 模型",
    "reranker": "重排序模型",
}

EMBEDDING_KEYWORDS = [
    "embed", "embedding", "e5-", "bge-", "gte-",
    "nomic-embed", "mxbai-embed", "all-mpnet",
    "text-embedding", "text-embedd",
]

RERANKER_KEYWORDS = [
    "rerank", "reranker", "ranker", "cross-encoder",
    "colbert", "monot5", "bge-reranker",
]

CHAT_EXCLUDE_KEYWORDS = [
    "whisper", "audio", "speech", "tts", "transcribe",
    "vision-preview", "image-variation", "dall",
]


def get_providers(model_type: Optional[str] = None) -> List[Dict[str, Any]]:
    if model_type is None:
        return PROVIDERS
    return [p for p in PROVIDERS if model_type in p["supported_model_types"]]


def get_provider_by_code(code: str) -> Optional[Dict[str, Any]]:
    for p in PROVIDERS:
        if p["code"] == code:
            return p
    return None


def get_default_api_base(provider_code: str) -> str:
    provider = get_provider_by_code(provider_code)
    if provider:
        return provider["default_api_base"]
    return ""


def get_supported_model_types(provider_code: str) -> List[str]:
    provider = get_provider_by_code(provider_code)
    if provider:
        return provider["supported_model_types"]
    return []


def get_model_type_label(model_type: str) -> str:
    return MODEL_TYPE_LABELS.get(model_type, model_type)


def get_known_dimension(model_name: str) -> Optional[int]:
    return KNOWN_EMBEDDING_DIMENSIONS.get(model_name)


def classify_model_type(model_id: str) -> Optional[str]:
    model_lower = model_id.lower()

    for kw in CHAT_EXCLUDE_KEYWORDS:
        if kw in model_lower:
            return None

    for kw in RERANKER_KEYWORDS:
        if kw in model_lower:
            return "reranker"

    for kw in EMBEDDING_KEYWORDS:
        if kw in model_lower:
            return "embedding"

    return "chat"


def seed_providers(db_session) -> None:
    """
    将 PROVIDERS 种子注册表 upsert 到 providers 数据库表。
    - 新 code → 插入（从种子拿默认 supported_model_types / fallback_models）
    - 已存在 code → 仅更新元数据（display_name / api_base / supports_* 等），
      不覆盖用户在运行时通过"探测类型"或手动编辑设置的 supported_model_types / fallback_models / api_key
    - 所有种子行标记 is_system=True
    """
    import json
    import uuid
    from app.db.models import Provider as ProviderORM

    for p in PROVIDERS:
        existing = db_session.query(ProviderORM).filter(ProviderORM.code == p["code"]).first()
        if existing:
            if not existing.is_system:
                continue
            existing.display_name = p["display_name"]
            existing.favicon_domain = p.get("favicon_domain", "")
            existing.default_api_base = p.get("default_api_base", "")
            existing.supports_api_key = p.get("supports_api_key", True)
            existing.supports_local = p.get("supports_local", False)
            existing.supports_discover = p.get("supports_discover", True)
            # supported_model_types / fallback_models / api_key / is_active 不覆盖
            # —— 这些是用户运行时配置的（探测类型、手动编辑），seed 只负责兜底默认值
            existing.description = p.get("description", "")
            existing.is_system = True
        else:
            new_row = ProviderORM(
                id=str(uuid.uuid4()),
                code=p["code"],
                display_name=p["display_name"],
                favicon_domain=p.get("favicon_domain", ""),
                default_api_base=p.get("default_api_base", ""),
                supports_api_key=p.get("supports_api_key", True),
                supports_local=p.get("supports_local", False),
                supports_discover=p.get("supports_discover", True),
                supported_model_types=json.dumps(p["supported_model_types"]),
                fallback_models=json.dumps(p.get("fallback_models", {})),
                description=p.get("description", ""),
                is_system=True,
                is_active=True,
            )
            db_session.add(new_row)
    db_session.commit()


def provider_orm_to_dict(row, include_full_key: bool = False) -> Dict[str, Any]:
    """将 DB Provider ORM 行转为前端/API 使用的 dict
    
    include_full_key=True 时 api_key 返回明文（仅 admin 内部链路需要，
    比如创建模型时预填、调用 discover-models 后端 fallback）。
    """
    import json as _json

    try:
        supported_types = _json.loads(row.supported_model_types) if row.supported_model_types else []
    except (TypeError, _json.JSONDecodeError):
        supported_types = []

    try:
        fallback_models = _json.loads(row.fallback_models) if row.fallback_models else {}
    except (TypeError, _json.JSONDecodeError):
        fallback_models = {}

    return {
        "id": row.id,
        "code": row.code,
        "display_name": row.display_name,
        "favicon_domain": row.favicon_domain or "",
        "default_api_base": row.default_api_base or "",
        "supports_api_key": bool(row.supports_api_key),
        "supports_local": bool(row.supports_local),
        "supports_discover": bool(row.supports_discover),
        "supported_model_types": supported_types,
        "fallback_models": fallback_models,
        "description": row.description or "",
        "api_key": row.api_key if include_full_key else "",
        "api_key_masked": _mask_api_key(row.api_key),
        "has_api_key": bool(row.api_key),
        "is_system": bool(row.is_system),
        "is_active": bool(row.is_active),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _mask_api_key(api_key: Optional[str]) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "****"
    return api_key[:4] + "****" + api_key[-4:]

