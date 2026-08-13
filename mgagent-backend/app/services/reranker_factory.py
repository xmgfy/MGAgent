"""
Reranker 工厂 — 本地 CrossEncoder + 云端 API 统一接口

支持三种后端:
  1. "local"    — sentence-transformers CrossEncoder（私有化部署）
  2. "openai-compatible" — OpenAI 兼容端点走 /rerank（部分网关/硅基流动）
  3. "cohere"   — Cohere Rerank v3 API
  4. "jina"     — Jina Reranker API（/v1/rerank endpoint）

运行时自动从 model_configs 表读取 provider + model_name + api_key + api_base
"""
from __future__ import annotations
from typing import List, Tuple, Optional
import logging
import requests

logger = logging.getLogger(__name__)


class BaseReranker:
    def score(self, query: str, documents: List[str]) -> List[float]:
        """返回与 documents 等长的相关性分数列表"""
        raise NotImplementedError


class LocalCrossEncoderReranker(BaseReranker):
    """本地 sentence-transformers CrossEncoder（私有化部署路径）"""

    def __init__(self, model_name: str, max_length: int = 512):
        from sentence_transformers import CrossEncoder
        logger.info(f"[Reranker] 加载本地 CrossEncoder: {model_name} (max_length={max_length})")
        self._model = CrossEncoder(model_name, num_labels=1, max_length=max_length)

    def score(self, query: str, documents: List[str]) -> List[float]:
        pairs = [(query, doc) for doc in documents]
        return [float(s) for s in self._model.predict(pairs)]


class CohereReranker(BaseReranker):
    """Cohere Rerank v3 API"""

    def __init__(self, api_key: str, model_name: str = "rerank-v3.5",
                 base_url: str = "https://api.cohere.com/v1"):
        self._api_key = api_key
        self._model = model_name
        self._url = f"{base_url}/rerank"

    def score(self, query: str, documents: List[str]) -> List[float]:
        resp = requests.post(
            self._url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "query": query,
                "documents": documents,
                "return_documents": False,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        # results 已按 score 排序，需要按原始索引恢复顺序
        scores = [0.0] * len(documents)
        for r in results:
            scores[r["index"]] = float(r["relevance_score"])
        return scores


class JinaReranker(BaseReranker):
    """Jina Reranker API（/v1/rerank endpoint）"""

    def __init__(self, api_key: str, model_name: str = "jina-reranker-v2-base-multilingual",
                 base_url: str = "https://api.jina.ai/v1"):
        self._api_key = api_key
        self._model = model_name
        self._url = f"{base_url}/rerank"

    def score(self, query: str, documents: List[str]) -> List[float]:
        resp = requests.post(
            self._url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "query": query,
                "documents": documents,
                "top_n": len(documents),
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        scores = [0.0] * len(documents)
        for r in results:
            scores[r["index"]] = float(r["relevance_score"])
        return scores


class OpenAICompatibleReranker(BaseReranker):
    """通过 OpenAI 兼容 API 端点调用 reranker（硅基流动 / DashScope compatible-mode 等）

    约定: /v1/rerank endpoint 接收 {"model","query","documents"} 返回 {"results":[{"index","relevance_score"}]}
    如果端点走 /embeddings + rerank 计算则不在本类处理。
    """

    def __init__(self, api_key: str, model_name: str, base_url: str):
        self._api_key = api_key
        self._model = model_name
        # base_url 可能已带 /v1 或不带，统一处理
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        if not base_url.endswith("/v1"):
            base_url = base_url + "/v1"
        self._url = f"{base_url}/rerank"

    def score(self, query: str, documents: List[str]) -> List[float]:
        resp = requests.post(
            self._url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "query": query,
                "documents": documents,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # 兼容不同厂商返回格式
        if "results" in data:
            results = data["results"]
        elif "data" in data and isinstance(data["data"], list):
            results = data["data"]
        else:
            raise ValueError(f"Unknown rerank response format: {list(data.keys())}")

        scores = [0.0] * len(documents)
        for r in results:
            idx = r.get("index", 0)
            score = r.get("relevance_score", r.get("score", 0.0))
            scores[idx] = float(score)
        return scores


def create_reranker(config_dict: dict) -> BaseReranker:
    """
    从 model_configs dict 创建 Reranker 实例。

    provider 路由规则:
      - local           → LocalCrossEncoderReranker
      - cohere          → CohereReranker
      - jina            → JinaReranker
      - 其他            → OpenAICompatibleReranker（硅基流动 / DashScope / 千帆 / 自定义）
    """
    provider = config_dict.get("provider", "local")
    model_name = config_dict["model_name"]
    api_key = config_dict.get("api_key") or ""
    api_base = config_dict.get("api_base") or ""

    logger.info(f"[Reranker] factory: provider={provider} model={model_name}")

    if provider == "local":
        return LocalCrossEncoderReranker(model_name=model_name)
    elif provider == "cohere":
        return CohereReranker(api_key=api_key, model_name=model_name)
    elif provider == "jina":
        base = api_base or "https://api.jina.ai/v1"
        return JinaReranker(api_key=api_key, model_name=model_name, base_url=base)
    else:
        # 默认 OpenAI compatible rerank endpoint
        if not api_base:
            raise ValueError(f"Reranker provider='{provider}' 需要配置 api_base")
        if not api_key:
            raise ValueError(f"Reranker provider='{provider}' 需要配置 api_key")
        return OpenAICompatibleReranker(api_key=api_key, model_name=model_name, base_url=api_base)


# --- 全局单例 + 配置变更检测 ---
_reranker_instance: Optional[BaseReranker] = None
_reranker_config_id: Optional[str] = None


def get_reranker(config: Optional[dict] = None) -> Optional[BaseReranker]:
    """获取全局 Reranker，配置变更时自动重建"""
    global _reranker_instance, _reranker_config_id

    if config is None:
        from app.services.model_config_service import get_active_reranker_config
        config = get_active_reranker_config()

    if config is None:
        return None

    cfg_id = config.get("id")
    if _reranker_instance is not None and _reranker_config_id == cfg_id:
        return _reranker_instance

    _reranker_instance = create_reranker(config)
    _reranker_config_id = cfg_id
    return _reranker_instance
