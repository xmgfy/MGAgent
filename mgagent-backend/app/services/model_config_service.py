"""
模型配置解析服务 — 多策略 + 多租户 + 多场景优先级

查询优先级（从最高到最低）：
  1. tenant_id + scenario + model_type + is_active
  2. tenant_id + model_type + is_active（该租户全局默认）
  3. scenario + model_type + tenant_id IS NULL + is_active（该场景全局默认）
  4. model_type + tenant_id IS NULL + scenario IS NULL + is_active（该类型全局默认）

无匹配时抛出 ValueError，让调用方（agent/rag 等）感知并处理。
"""
from typing import Optional, Any
from app.db import database as _db
from app.db.models import ModelConfig


def _get_session():
    """惰性初始化 SessionLocal（mgagent-backend 未在 import 时初始化 DB）"""
    if _db.SessionLocal is None:
        _db.init_engine()
    return _db.SessionLocal()


def get_active_model_config_row(
    model_type: str = "chat",
    tenant_id: Optional[str] = None,
    scenario: Optional[str] = None,
):
    """返回 DB ORM 行（ModelConfig），用于工厂构建 LLM 实例"""
    db = _get_session()
    try:
        row = (
            db.query(ModelConfig)
            .filter(ModelConfig.model_type == model_type)
            .filter(ModelConfig.is_active == True)  # noqa: E712
            .order_by(
                (ModelConfig.tenant_id == tenant_id).desc(),
                (ModelConfig.scenario == scenario).desc(),
                ModelConfig.created_at.desc(),
            )
            .first()
        )
        if row is None:
            raise ValueError(
                f"未找到有效的模型配置（model_type={model_type}, "
                f"tenant_id={tenant_id}, scenario={scenario}）"
            )
        return row
    finally:
        db.close()


def _row_to_dict(row: Any) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "model_type": row.model_type,
        "provider": row.provider,
        "api_key": row.api_key,
        "api_base": row.api_base,
        "model_name": row.model_name,
        "dimension": row.dimension,
        "tenant_id": row.tenant_id,
        "scenario": row.scenario,
        "temperature": row.temperature,
        "top_p": row.top_p,
        "max_tokens": row.max_tokens,
        "presence_penalty": row.presence_penalty,
        "frequency_penalty": row.frequency_penalty,
    }


def get_active_model_config_dict(
    model_type: str = "chat",
    tenant_id: Optional[str] = None,
    scenario: Optional[str] = None,
) -> dict:
    """返回 dict 形式，同样走优先级查询"""
    row = get_active_model_config_row(
        model_type=model_type, tenant_id=tenant_id, scenario=scenario
    )
    return _row_to_dict(row)


def get_embedding_model_config():
    """快捷方法：获取当前启用的 embedding 模型 ORM 行"""
    return get_active_model_config_row(model_type="embedding")


# ---- 向后兼容的别名（rag 模块在用） ----

def get_active_embedding_config() -> Optional[dict]:
    """rag/retriever.py 等使用：返回 embedding 配置 dict"""
    try:
        row = get_active_model_config_row(model_type="embedding")
        return _row_to_dict(row)
    except ValueError:
        return None


def create_embeddings_model(config_dict: dict):
    """rag/retriever.py 等使用：从 dict 创建 LangChain Embeddings"""
    from app.services.llm_factory import create_embedding, ModelConfig as FactoryConfig, build_llm_config

    class _RowAdapter:
        def __init__(self, d: dict):
            self.provider = d.get("provider", "openai")
            self.model_name = d["model_name"]
            self.api_key = d.get("api_key")
            self.api_base = d.get("api_base")
            self.model_type = d.get("model_type", "embedding")
            self.temperature = d.get("temperature")
            self.top_p = d.get("top_p")
            self.max_tokens = d.get("max_tokens")
            self.presence_penalty = d.get("presence_penalty")
            self.frequency_penalty = d.get("frequency_penalty")

    factory_cfg = build_llm_config(_RowAdapter(config_dict))
    provider_code = config_dict.get("provider", "openai")
    if provider_code == "ollama":
        from app.services.llm_factory import LocalOllamaProvider
        return LocalOllamaProvider().create_embedding_model(factory_cfg)
    from app.services.llm_factory import OpenAICompatibleProvider
    return OpenAICompatibleProvider().create_embedding_model(factory_cfg)
