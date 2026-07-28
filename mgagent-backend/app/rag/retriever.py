"""
向量检索器 - 基于向量数据库的检索器
支持 ChromaDB 和 Milvus
模型配置从数据库读取，无兜底逻辑
"""
from langchain_core.documents import Document
from typing import List, Optional
from app.rag.vector_factory import get_vector_db
from app.services.model_config_service import get_active_model_config
import uuid

try:
    from langchain_openai import OpenAIEmbeddings
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class VectorRetriever:
    """基于向量数据库的向量检索器"""
    
    def __init__(self):
        self._current_config_id = None
        self.embeddings = self._init_embeddings()
        self.vector_db = get_vector_db()
    
    def _init_embeddings(self):
        """初始化嵌入模型，从数据库读取配置，无兜底"""
        model_config = get_active_model_config()
        
        if not model_config:
            raise ValueError("未配置活跃的模型，请在admin管理端配置并启用模型")
        
        self._current_config_id = model_config.get("id")
        
        if not OPENAI_AVAILABLE:
            raise ImportError("langchain_openai 未安装，请执行: pip install langchain-openai")
        
        try:
            return OpenAIEmbeddings(
                api_key=model_config["api_key"],
                base_url=model_config["api_base"],
                model="text-embedding-3-small"
            )
        except Exception as e:
            raise ValueError(f"初始化嵌入模型失败: {str(e)}")
    
    def _check_and_reload(self):
        """检查模型配置是否变更，若变更则重新加载嵌入模型"""
        try:
            model_config = get_active_model_config()
            config_id = model_config.get("id") if model_config else None
            
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
        """相似度搜索"""
        self._check_and_reload()
        
        query_embedding = self.embeddings.embed_query(query)
        results = self.vector_db.similarity_search(query_embedding, k=k)
        
        documents = []
        for result in results:
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


# 创建全局实例
vector_retriever = VectorRetriever()
