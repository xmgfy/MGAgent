"""
向量检索器 - 基于向量数据库的检索器
支持 ChromaDB 和 Milvus
Embedding 模型从 model_configs 表读取，支持本地和云端模型
"""
from langchain_core.documents import Document
from typing import List, Optional
from app.rag.vector_factory import get_vector_db
from app.services.model_config_service import get_active_embedding_config, create_embeddings_model
import uuid


class VectorRetriever:
    """基于向量数据库的向量检索器"""

    def __init__(self):
        self._current_config_id = None
        self.embeddings = self._init_embeddings()
        self.vector_db = get_vector_db()

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
        """检查 Embedding 配置是否变更，若变更则重新加载"""
        try:
            emb_config = get_active_embedding_config()
            config_id = emb_config.get("id") if emb_config else None

            if config_id != self._current_config_id:
                self.embeddings = self._init_embeddings()
                self.vector_db = get_vector_db()
        except ValueError:
            raise
        except Exception:
            pass

    def reload_embeddings(self):
        """重新加载嵌入模型配置"""
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

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """相似度搜索 - 使用混合检索策略"""
        self._check_and_reload()

        # 1. 向量检索
        query_embedding = self.embeddings.embed_query(query)
        results = self.vector_db.similarity_search(query_embedding, k=k)
        
        # 2. 如果向量检索结果不够，尝试关键词搜索作为补充
        if len(results) < k and hasattr(self.vector_db, 'keyword_search'):
            # 提取关键词（简单分词）
            keywords = [w for w in query if w.strip()]
            keyword_results = self.vector_db.keyword_search(keywords, k=k - len(results))
            
            # 合并结果（去重）
            existing_ids = {r["id"] for r in results}
            for kr in keyword_results:
                if kr["id"] not in existing_ids:
                    # 为关键词搜索结果设置一个较高的相关性分数
                    kr["score"] = kr.get("score", 0) - 10  # 降低关键词搜索的优先级
                    results.append(kr)
                    existing_ids.add(kr["id"])
        
        # 3. 转换为 LangChain Document 格式
        documents = []
        for result in results[:k]:
            doc = Document(
                page_content=result["content"],
                metadata={
                    **result.get("metadata", {}),
                    "id": result["id"],
                    "score": result.get("score", 0)
                }
            )
            documents.append(doc)

        return documents
    
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
