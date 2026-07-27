"""
向量检索器 - 使用 Milvus 向量数据库
"""
from langchain_core.documents import Document
from typing import List, Optional
from app.config.settings import settings
from app.rag.milvus_service import MilvusService
import uuid

try:
    from langchain_openai import OpenAIEmbeddings
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain.embeddings.base import Embeddings
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class TfidfEmbeddings(Embeddings):
    """本地 TF-IDF 嵌入"""
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1536,  # 与 Milvus 集合维度匹配
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b\w+\b"
        )
        self.fitted = False
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.fitted:
            self.vectorizer.fit(texts)
            self.fitted = True
        # 确保维度为 1536
        vectors = self.vectorizer.transform(texts).toarray()
        # 如果维度不够，进行填充
        if vectors.shape[1] < 1536:
            padded = np.zeros((len(texts), 1536))
            padded[:, :vectors.shape[1]] = vectors
            return padded.tolist()
        return vectors[:, :1536].tolist()
    
    def embed_query(self, text: str) -> List[float]:
        if not self.fitted:
            self.vectorizer.fit([text])
            self.fitted = True
        vectors = self.vectorizer.transform([text]).toarray()
        # 确保维度为 1536
        if vectors.shape[1] < 1536:
            padded = np.zeros((1, 1536))
            padded[:, :vectors.shape[1]] = vectors
            return padded[0].tolist()
        return vectors[0, :1536].tolist()


class VectorRetriever:
    """基于 Milvus 的向量检索器"""
    
    def __init__(self):
        # 初始化嵌入模型
        use_local_embedding = settings.OPENAI_API_BASE and "deepseek" in settings.OPENAI_API_BASE.lower()
        
        if use_local_embedding or not OPENAI_AVAILABLE:
            if SKLEARN_AVAILABLE:
                self.embeddings = TfidfEmbeddings()
            else:
                raise ImportError("请安装 scikit-learn: pip install scikit-learn")
        else:
            try:
                self.embeddings = OpenAIEmbeddings(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_API_BASE,
                    model="text-embedding-3-small"
                )
            except Exception:
                if SKLEARN_AVAILABLE:
                    self.embeddings = TfidfEmbeddings()
                else:
                    raise ImportError("请安装 scikit-learn: pip install scikit-learn")
        
        # 初始化 Milvus 服务
        self.milvus_service = MilvusService(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION
        )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量数据库"""
        if not documents:
            return []
        
        # 生成嵌入
        texts = [doc.page_content for doc in documents]
        embeddings = self.embeddings.embed_documents(texts)
        
        # 添加到 Milvus
        ids = self.milvus_service.add_documents(documents, embeddings)
        return ids
    
    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """相似度搜索"""
        # 生成查询嵌入
        query_embedding = self.embeddings.embed_query(query)
        
        # 在 Milvus 中搜索
        results = self.milvus_service.similarity_search(query_embedding, k=k)
        
        # 转换为 Document 对象
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
        class MilvusRetriever:
            def __init__(self, retriever, k):
                self.retriever = retriever
                self.k = k
            
            def get_relevant_documents(self, query: str) -> List[Document]:
                return self.retriever.similarity_search(query, k=self.k)
            
            def invoke(self, input_data: str) -> List[Document]:
                return self.get_relevant_documents(input_data)
        
        return MilvusRetriever(self, k)
    
    def search(self, query: str, k: int = 3) -> List[Document]:
        """搜索接口"""
        return self.similarity_search(query, k=k)
    
    def delete_by_ids(self, ids: List[str]) -> None:
        """根据 ID 删除向量"""
        self.milvus_service.delete_by_ids(ids)
    
    def get_collection_stats(self) -> dict:
        """获取集合统计信息"""
        stats = self.milvus_service.get_collection_stats()
        stats["embedding_model"] = type(self.embeddings).__name__
        return stats
    
    def clear_all(self) -> None:
        """清空所有数据"""
        self.milvus_service.clear_all()
    
    def get_total_count(self) -> int:
        """获取总向量数"""
        return self.milvus_service.get_total_count()


# 创建全局实例
vector_retriever = VectorRetriever()
