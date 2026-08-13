"""
向量检索器 - 基于向量数据库的检索器（粗召回 + 可选 Reranker 精排）
底层使用 Milvus
Embedding 模型从 model_configs 表读取，支持本地和云端模型
Reranker 从 model_configs 表读取 type='reranker' 的激活配置，无则自动跳过
"""
import hashlib
import time
import threading
from collections import OrderedDict
from langchain_core.documents import Document
from typing import List, Optional
from app.rag.vector_factory import get_vector_db
from app.services.model_config_service import get_active_embedding_config, create_embeddings_model
import uuid
import logging

logger = logging.getLogger(__name__)

# 粗召回参数：先拿更多候选，再交给 reranker 精排
DEFAULT_RECALL_TOP_K = 50
# RRF (Reciprocal Rank Fusion) 常数，越大排名差异影响越小
_RRF_CONSTANT = 60


class EmbeddingCache:
    """LRU + TTL Embedding 缓存

    Key: f"{model_config_id}:{query_hash}"
    Value: embedding vector (List[float])
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 300.0, enabled: bool = True):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.enabled = enabled
        self._cache: OrderedDict[str, tuple[float, List[float]]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _make_key(model_config_id: str, text: str) -> str:
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        return f"{model_config_id}:{h}"

    def get(self, model_config_id: str, text: str) -> Optional[List[float]]:
        if not self.enabled:
            return None
        key = self._make_key(model_config_id, text)
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            ts, value = self._cache[key]
            if time.time() - ts > self.ttl:
                del self._cache[key]
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def put(self, model_config_id: str, text: str, value: List[float]) -> None:
        if not self.enabled:
            return
        key = self._make_key(model_config_id, text)
        with self._lock:
            self._cache[key] = (time.time(), value)
            self._cache.move_to_end(key)
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def invalidate(self, model_config_id: Optional[str] = None) -> None:
        """清除缓存（可指定 model_config_id 清除单模型，或不传则全清）"""
        with self._lock:
            if model_config_id is None:
                self._cache.clear()
            else:
                prefix = f"{model_config_id}:"
                keys_to_del = [k for k in self._cache if k.startswith(prefix)]
                for k in keys_to_del:
                    del self._cache[k]

    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0.0,
                "enabled": self.enabled,
                "ttl": self.ttl,
            }


def _extract_keywords(text: str) -> List[str]:
    """轻量中英文分词，不依赖 jieba

    - 英文/数字: 按 whitespace 和标点切
    - 中文: 按 bigram 切分（每个连续中文字符串取滑动窗口 2-gram）
    """
    import re

    keywords: List[str] = []
    # 先按非中英文数字切 token
    tokens = re.split(r"[^\w\u4e00-\u9fff]+", text)
    for token in tokens:
        if not token:
            continue
        if re.search(r"[\u4e00-\u9fff]", token):
            # 中文 token → 2-gram 滑窗
            for i in range(len(token) - 1):
                keywords.append(token[i : i + 2])
        else:
            keywords.append(token.lower())
    return keywords


class VectorRetriever:
    """基于向量数据库的向量检索器"""

    def __init__(self):
        self._current_config_id = None
        self.embeddings = self._init_embeddings()
        self.vector_db = get_vector_db()
        self.cache = EmbeddingCache(max_size=1000, ttl_seconds=300.0, enabled=True)

    def _init_embeddings(self):
        """初始化嵌入模型，从 model_configs 表读取配置"""
        emb_config = get_active_embedding_config()

        if not emb_config:
            raise ValueError(
                "未配置 Embedding 模型，请在模型管理中添加 Embedding 类型的模型并启用"
            )

        self._current_config_id = emb_config.get("id")

        try:
            return create_embeddings_model(emb_config)
        except Exception as e:
            raise ValueError(f"初始化嵌入模型失败: {str(e)}")

    def _check_and_reload(self):
        """检查 Embedding 配置是否变更，若变更则重新加载 + invalidate cache"""
        try:
            emb_config = get_active_embedding_config()
            config_id = emb_config.get("id") if emb_config else None

            if config_id != self._current_config_id:
                self.cache.invalidate()
                self.embeddings = self._init_embeddings()
                self.vector_db = get_vector_db()
                logger.info(f"[EmbeddingCache] model config changed → cache invalidated, new config={config_id}")
        except ValueError:
            raise
        except Exception:
            pass

    def reload_embeddings(self):
        """重新加载嵌入模型配置"""
        self.cache.invalidate()
        self.embeddings = self._init_embeddings()

    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量数据库"""
        self._check_and_reload()

        if not documents:
            return []

        texts = [doc.page_content for doc in documents]
        embeddings = self.embeddings.embed_documents(texts)
        ids = self.vector_db.add_documents(documents, embeddings)
        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 3,
        knowledge_base_ids: Optional[List[str]] = None,
        similarity_threshold: Optional[float] = None,
        enable_rerank: Optional[bool] = None,
        rerank_top_n: Optional[int] = None,
        enable_hybrid: Optional[bool] = None,
        hybrid_alpha: Optional[float] = None,
    ) -> List[Document]:
        """相似度搜索 - 支持纯向量检索或混合检索（RRF 融合）+ 可选 Reranker 精排

        流程:
          1. 向量检索粗召回 Top DEFAULT_RECALL_TOP_K
          2. 如果 enable_hybrid=True 且向量库支持 keyword_search → 关键词检索并行跑 + RRF 融合
             否则向量结果不够时关键词补充（降级为弱融合）
          3. similarity_threshold 过滤
          4. 如果有激活的 Reranker 配置 → CrossEncoder 精排 → 取最终 Top k
          5. 结果转 LangChain Document

        Args:
            query: 查询文本
            k: 最终返回的文档数量
            knowledge_base_ids: 限定检索的知识库 ID 列表，None 表示不限制
            similarity_threshold: L2 距离阈值（越小越好），过滤掉 score > threshold 的结果；None 不过滤
            enable_rerank: 是否启用 Reranker，None 表示跟随全局配置
            rerank_top_n: Reranker 精排时取的候选数，None 表示用默认 max(DEFAULT_RECALL_TOP_K, k)
            enable_hybrid: 是否启用混合检索（向量+关键词 RRF 融合）；None 表示不启用
            hybrid_alpha: 混合检索中向量分数权重 [0,1]，默认 0.7（70% 向量 + 30% 关键词）
        """
        self._check_and_reload()

        recall_k = max(DEFAULT_RECALL_TOP_K, k)

        # 1. Query Embedding（带缓存）
        query_embedding = self.cache.get(self._current_config_id or "", query)
        if query_embedding is None:
            query_embedding = self.embeddings.embed_query(query)
            self.cache.put(self._current_config_id or "", query, query_embedding)
        else:
            logger.debug("[EmbeddingCache] hit for query")

        # 2. 向量粗召回
        vector_results = self.vector_db.similarity_search(
            query_embedding, k=recall_k, knowledge_base_ids=knowledge_base_ids
        )

        # 3. 混合检索：关键词并行 + RRF 融合
        use_hybrid = bool(enable_hybrid) and hasattr(self.vector_db, "keyword_search")
        if use_hybrid:
            keywords = _extract_keywords(query)
            keyword_results = self.vector_db.keyword_search(
                keywords, k=recall_k, knowledge_base_ids=knowledge_base_ids
            )
            alpha = hybrid_alpha if hybrid_alpha is not None else 0.7
            results = self._fuse_hybrid(vector_results, keyword_results, alpha)
            logger.info(
                f"[Hybrid] vector={len(vector_results)}, keyword={len(keyword_results)}, "
                f"alpha={alpha} → fused={len(results)}"
            )
        else:
            # 降级：向量结果不够才关键词补充
            results = list(vector_results)
            if len(results) < recall_k and hasattr(self.vector_db, "keyword_search"):
                keywords = _extract_keywords(query)
                keyword_results = self.vector_db.keyword_search(
                    keywords, k=recall_k - len(results)
                )
                existing_ids = {r["id"] for r in results}
                for kr in keyword_results:
                    if kr["id"] not in existing_ids:
                        kr["score"] = kr.get("score", 0) - 10
                        results.append(kr)
                        existing_ids.add(kr["id"])

        # 4. similarity_threshold 过滤（L2 距离：分数越低越相似，过滤 score > threshold）
        if similarity_threshold is not None:
            results = [r for r in results if r.get("score", 0) <= similarity_threshold]

        # 5. Reranker 精排（如果配置了）
        reranked = self._maybe_rerank(
            query, results, k, enable_rerank=enable_rerank, rerank_top_n=rerank_top_n
        )

        # 6. 转换为 LangChain Document
        documents = []
        for result in reranked:
            doc = Document(
                page_content=result["content"],
                metadata={
                    **result.get("metadata", {}),
                    "id": result["id"],
                    "score": result.get("score", 0),
                },
            )
            documents.append(doc)

        return documents

    @staticmethod
    def _fuse_hybrid(
        vector_results: List[dict],
        keyword_results: List[dict],
        alpha: float,
    ) -> List[dict]:
        """RRF + 加权融合向量检索和关键词检索结果

        RRF (Reciprocal Rank Fusion): score(d) = Σ 1/(k + rank_i(d))
        最终分数 = alpha * vector_rrf + (1 - alpha) * keyword_rrf
        """
        fused: dict[str, dict] = {}
        vector_rrf_sum = 0.0
        keyword_rrf_sum = 0.0

        for rank, r in enumerate(vector_results):
            doc_id = r["id"]
            rrf = 1.0 / (_RRF_CONSTANT + rank + 1)
            vector_rrf_sum += rrf
            if doc_id not in fused:
                fused[doc_id] = dict(r)
                fused[doc_id]["vector_score"] = r.get("score", 0)
                fused[doc_id]["keyword_score"] = None
                fused[doc_id]["vector_rank"] = rank + 1
                fused[doc_id]["keyword_rank"] = None
                fused[doc_id]["keyword_hit"] = False
            fused[doc_id]["_rrf_vector"] = rrf

        for rank, r in enumerate(keyword_results):
            doc_id = r["id"]
            rrf = 1.0 / (_RRF_CONSTANT + rank + 1)
            keyword_rrf_sum += rrf
            if doc_id not in fused:
                fused[doc_id] = dict(r)
                fused[doc_id]["vector_score"] = None
                fused[doc_id]["keyword_score"] = r.get("score", 0)
                fused[doc_id]["vector_rank"] = None
                fused[doc_id]["keyword_rank"] = rank + 1
                fused[doc_id]["keyword_hit"] = True
                fused[doc_id]["_rrf_vector"] = 0.0
            else:
                fused[doc_id]["keyword_score"] = r.get("score", 0)
                fused[doc_id]["keyword_rank"] = rank + 1
                fused[doc_id]["keyword_hit"] = True
            fused[doc_id]["_rrf_keyword"] = rrf

        # 归一化 RRF 分数后加权融合
        total = vector_rrf_sum + keyword_rrf_sum
        if total == 0:
            return []

        for doc_id, entry in fused.items():
            v_norm = entry.get("_rrf_vector", 0) / total if total > 0 else 0
            k_norm = entry.get("_rrf_keyword", 0) / total if total > 0 else 0
            entry["score"] = alpha * v_norm + (1 - alpha) * k_norm
            entry["_source"] = "hybrid"

        sorted_docs = sorted(fused.values(), key=lambda x: x["score"], reverse=True)
        return sorted_docs

    def _maybe_rerank(
        self,
        query: str,
        candidates: List[dict],
        top_k: int,
        enable_rerank: Optional[bool] = None,
        rerank_top_n: Optional[int] = None,
    ) -> List[dict]:
        """如果存在激活的 reranker 配置，对 candidates 精排；否则直接截断

        Args:
            query: 查询文本
            candidates: 候选文档列表
            top_k: 最终返回数量
            enable_rerank: 是否强制启用/禁用 rerank，None 表示跟随全局配置；False 时直接跳过
            rerank_top_n: rerank 阶段取的候选数上限（用于截断候选），None 表示不限
        """
        effective_top_k = rerank_top_n if rerank_top_n is not None else top_k

        if len(candidates) <= effective_top_k:
            return candidates[:top_k]

        if enable_rerank is False:
            return candidates[:top_k]

        try:
            from app.services.reranker_factory import get_reranker
            reranker = get_reranker()
        except Exception as e:
            logger.warning(f"[Reranker] 加载失败，跳过精排: {e}")
            return candidates[:top_k]

        if reranker is None:
            if enable_rerank is True:
                logger.warning("[Reranker] enable_rerank=True 但未配置 Reranker，降级为向量检索")
            return candidates[:top_k]

        try:
            docs_text = [c["content"] for c in candidates[:effective_top_k]]
            scores = reranker.score(query, docs_text)

            for c, s in zip(candidates[:effective_top_k], scores):
                c["score"] = s
            candidates[:effective_top_k] = sorted(
                candidates[:effective_top_k], key=lambda x: x["score"], reverse=True
            )
            logger.info(f"[Reranker] 精排完成: {min(len(candidates), effective_top_k)} 候选 → Top {top_k}")
            return candidates[:top_k]
        except Exception as e:
            logger.warning(f"[Reranker] 精排失败，降级为向量检索: {e}")
            return candidates[:top_k]

    def similarity_search_with_config(
        self, query: str, config: dict, k: Optional[int] = None
    ) -> List[Document]:
        """根据知识库配置 dict 执行检索

        Args:
            query: 查询文本
            config: 知识库配置 dict，可包含以下 key:
                - retrieve_limit: 最终返回数量（作为 k 的默认值）
                - similarity_threshold: L2 距离阈值
                - enable_rerank: 是否启用 rerank
                - rerank_top_n: rerank 候选数上限
                - enable_hybrid: 是否启用混合检索（RRF 融合）
                - hybrid_alpha: 混合检索中向量分数权重 [0,1]
                - knowledge_base_id: 限定检索的知识库 ID
            k: 显式指定返回数量，优先于 config['retrieve_limit']
        """
        effective_k = k if k is not None else config.get("retrieve_limit", 3)

        kb_id = config.get("knowledge_base_id") or config.get("id")
        knowledge_base_ids = [kb_id] if kb_id else None

        return self.similarity_search(
            query=query,
            k=effective_k,
            knowledge_base_ids=knowledge_base_ids,
            similarity_threshold=config.get("similarity_threshold"),
            enable_rerank=config.get("enable_rerank"),
            rerank_top_n=config.get("rerank_top_n"),
            enable_hybrid=config.get("enable_hybrid"),
            hybrid_alpha=config.get("hybrid_alpha"),
        )

    def get_retriever(self, k: int = 3, search_type: str = "similarity"):
        """获取检索器接口（兼容 LangChain 接口）"""
        class VectorDBRetriever:
            def __init__(self, retriever, k):
                self.retriever = retriever
                self.k = k
            
            def get_relevant_documents(self, query: str) -> List[Document]:
                return self.retriever.similarity_search(query, k=self.k)
            
            def invoke(self, input_data: str) -> List[Document]:
                return self.get_relevant_documents(input_data)
        
        return VectorDBRetriever(self, k)
    
    def search(self, query: str, k: int = 3) -> List[Document]:
        """搜索接口"""
        return self.similarity_search(query, k=k)
    
    def delete_by_ids(self, ids: List[str]) -> None:
        """根据 ID 删除向量"""
        self.vector_db.delete_by_ids(ids)
    
    def get_collection_stats(self) -> dict:
        """获取集合统计信息"""
        self._check_and_reload()
        stats = self.vector_db.get_stats()
        stats["embedding_model"] = type(self.embeddings).__name__
        return stats
    
    def clear_all(self) -> None:
        """清空所有数据"""
        self.vector_db.clear_all()
    
    def get_total_count(self) -> int:
        """获取总向量数"""
        return self.vector_db.get_total_count()


# 全局实例（惰性初始化）
_vector_retriever = None

def get_vector_retriever():
    """获取全局 VectorRetriever 实例（惰性初始化）"""
    global _vector_retriever
    if _vector_retriever is None:
        _vector_retriever = VectorRetriever()
    return _vector_retriever
