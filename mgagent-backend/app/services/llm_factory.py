"""
LLM 服务工厂 — 按 Provider 路由到对应实现

架构：
  BaseLLMProvider    (抽象基类，定义统一接口)
      └─ OpenAICompatibleProvider  (ChatOpenAI 包装，所有 OpenAI 兼容厂商都走这里)

扩展点：未来新增原生 Anthropic/Google/Moonshot 等 Provider，只需新增一个
BaseLLMProvider 子类并在 PROVIDER_REGISTRY 注册，不改工厂逻辑。

参数优先级：
  用户显式传 get_llm(temperature=...)    — 最高
  DB ModelConfig.temperature / top_p ... — 其次（这次已经加了）
  工厂默认值                              — 兜底
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field


@dataclass
class LLMParameters:
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None

    def merge_overrides(self, **overrides: Optional[Any]) -> "LLMParameters":
        for key, val in overrides.items():
            if val is not None and hasattr(self, key):
                setattr(self, key, val)
        return self

    def to_kwargs(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for key in ("temperature", "top_p", "max_tokens", "presence_penalty", "frequency_penalty"):
            v = getattr(self, key)
            if v is not None:
                out[key] = v
        return out


@dataclass
class ModelConfig:
    """工厂内部使用的轻量配置 DTO — 从 DB ModelConfig ORM 提取"""
    provider: str
    model_name: str
    api_key: Optional[str]
    api_base: Optional[str]
    model_type: str = "chat"
    params: LLMParameters = field(default_factory=LLMParameters)


def build_llm_config(db_row: Any) -> ModelConfig:
    """从 DB ModelConfig ORM 行构建工厂 DTO"""
    params = LLMParameters(
        temperature=getattr(db_row, "temperature", None),
        top_p=getattr(db_row, "top_p", None),
        max_tokens=getattr(db_row, "max_tokens", None),
        presence_penalty=getattr(db_row, "presence_penalty", None),
        frequency_penalty=getattr(db_row, "frequency_penalty", None),
    )
    return ModelConfig(
        provider=db_row.provider,
        model_name=db_row.model_name,
        api_key=db_row.api_key,
        api_base=db_row.api_base,
        model_type=db_row.model_type or "chat",
        params=params,
    )


class BaseLLMProvider(ABC):
    """LLM Provider 抽象基类"""

    provider_code: str = ""

    @abstractmethod
    def create_chat_model(self, config: ModelConfig, overrides: Optional[Dict[str, Any]] = None) -> Any:
        """创建 LangChain Runnable（用于对话/工具调用）"""
        ...

    def create_embedding_model(self, config: ModelConfig) -> Any:
        """创建 Embedding 模型（默认实现，OpenAI-compatible）"""
        from langchain_openai import OpenAIEmbeddings
        kwargs = {
            "model": config.model_name,
            "api_key": config.api_key or "",
        }
        if config.api_base:
            kwargs["base_url"] = config.api_base
        return OpenAIEmbeddings(**kwargs)


class OpenAICompatibleProvider(BaseLLMProvider):
    """所有 OpenAI 兼容厂商都走这里 — 通过 base_url 区分"""

    provider_code = "openai_compatible"

    def create_chat_model(self, config: ModelConfig, overrides: Optional[Dict[str, Any]] = None) -> Any:
        from langchain_openai import ChatOpenAI

        params = LLMParameters()
        if config.model_type == "chat":
            params.temperature = 0.7
        else:
            params.temperature = 0.1
        params = config.params
        params.merge_overrides(**(overrides or {}))

        kwargs: Dict[str, Any] = {
            "model": config.model_name,
            "api_key": config.api_key or "",
        }
        if config.api_base:
            kwargs["base_url"] = config.api_base

        kwargs.update(params.to_kwargs())
        return ChatOpenAI(**kwargs)


class LocalOllamaProvider(BaseLLMProvider):
    """本地 Ollama — 不走 api_key"""

    provider_code = "ollama"

    def create_chat_model(self, config: ModelConfig, overrides: Optional[Dict[str, Any]] = None) -> Any:
        from langchain_ollama import ChatOllama

        params = config.params
        if config.model_type != "chat":
            params.temperature = params.temperature or 0.1
        params.merge_overrides(**(overrides or {}))

        base = (config.api_base or "http://localhost:11434").rstrip("/").replace("/v1", "")

        kwargs: Dict[str, Any] = {
            "model": config.model_name,
            "base_url": base,
        }
        kwargs.update(params.to_kwargs())
        return ChatOllama(**kwargs)


PROVIDER_REGISTRY: Dict[str, BaseLLMProvider] = {
    "ollama": LocalOllamaProvider(),
}


def _resolve_provider(provider_code: str) -> BaseLLMProvider:
    """
    按 provider code 路由到具体实现。

    - ollama → LocalOllamaProvider（不走 OpenAI-compatible）
    - 其他所有（openai, deepseek, dashscope, zhipu, minimax, moonshot, stepfun, jina, custom）
      → OpenAICompatibleProvider（LangChain ChatOpenAI，通过 base_url 区分厂商）
    """
    if provider_code in PROVIDER_REGISTRY:
        return PROVIDER_REGISTRY[provider_code]
    return OpenAICompatibleProvider()


# 便捷入口（mgagent-backend 主要使用）

def create_llm(
    db_row: Any,
    overrides: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    从 DB ModelConfig ORM 行创建 LLM 实例。
    """
    cfg = build_llm_config(db_row)
    provider_impl = _resolve_provider(cfg.provider)
    return provider_impl.create_chat_model(cfg, overrides)


def create_embedding(db_row: Any) -> Any:
    cfg = build_llm_config(db_row)
    provider_impl = _resolve_provider(cfg.provider)
    return provider_impl.create_embedding_model(cfg)
