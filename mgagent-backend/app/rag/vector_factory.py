"""
向量数据库工厂 - 根据方案创建对应的向量数据库连接
支持 ChromaDB 和 Milvus
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
import uuid

from app.config.config import (
    settings,
    is_sqlite_scheme,
    is_mysql_scheme,
    get_chroma_dir
)

class VectorDBInterface(ABC):
    """向量数据库抽象接口"""
    
    @abstractmethod
    def add_documents(self, documents: List[Document], embeddings: List[List[float]]) -> List[str]:
        """添加文档"""
        pass
    
    @abstractmethod
    def similarity_search(self, query_embedding: List[float], k: int = 3) -> List[Dict[str, Any]]:
        """相似度搜索"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
    
    @abstractmethod
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """获取所有向量块"""
        pass
    
    @abstractmethod
    def delete_by_ids(self, ids: List[str]) -> None:
        """根据ID删除"""
        pass
    
    @abstractmethod
    def clear_all(self) -> None:
        """清空所有数据"""
        pass
    
    @abstractmethod
    def get_total_count(self) -> int:
        """获取总数"""
        pass


class ChromaDBService(VectorDBInterface):
    """ChromaDB 服务实现"""
    
    def __init__(self):
        from langchain_chroma import Chroma
        self.persist_directory = str(get_chroma_dir())
        self._client = None
        self.connect()
    
    def connect(self):
        """连接 ChromaDB"""
        from langchain_chroma import Chroma
        try:
            self._client = Chroma(
                persist_directory=self.persist_directory,
                collection_name="mgagent_knowledge"
            )
        except Exception as e:
            print(f"ChromaDB 连接失败: {e}")
            raise
    
    def add_documents(self, documents: List[Document], embeddings: List[List[float]]) -> List[str]:
        if not documents:
            return []
        
        ids = [str(uuid.uuid4()) for _ in documents]
        
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        try:
            self._client.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            return ids
        except Exception as e:
            print(f"ChromaDB 添加文档失败: {e}")
            raise
    
    def similarity_search(self, query_embedding: List[float], k: int = 3) -> List[Dict[str, Any]]:
        try:
            results = self._client.similarity_search_by_vector(
                embedding=query_embedding,
                k=k
            )
            return [
                {
                    "id": doc.metadata.get("id", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": 0.0
                }
                for doc in results
            ]
        except Exception as e:
            print(f"ChromaDB 搜索失败: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        try:
            count = self.get_total_count()
            return {
                "type": "chromadb",
                "name": "ChromaDB",
                "total_chunks": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        try:
            results = self._client.get()
            chunks = []
            for i, doc_id in enumerate(results.get("ids", [])):
                chunks.append({
                    "id": doc_id,
                    "content": results.get("documents", [])[i] if i < len(results.get("documents", [])) else "",
                    "metadata": results.get("metadatas", [])[i] if i < len(results.get("metadatas", [])) else {}
                })
            return chunks
        except Exception as e:
            print(f"ChromaDB 获取所有块失败: {e}")
            return []
    
    def delete_by_ids(self, ids: List[str]) -> None:
        if not ids:
            return
        try:
            self._client.delete(ids=ids)
        except Exception as e:
            print(f"ChromaDB 删除失败: {e}")
            raise
    
    def clear_all(self) -> None:
        try:
            count = self.get_total_count()
            if count > 0:
                all_data = self._client.get()
                ids = all_data.get("ids", [])
                if ids:
                    self._client.delete(ids=ids)
        except Exception as e:
            print(f"ChromaDB 清空失败: {e}")
            raise
    
    def get_total_count(self) -> int:
        try:
            results = self._client.get()
            return len(results.get("ids", []))
        except Exception:
            return 0


class MilvusService(VectorDBInterface):
    """Milvus 服务实现"""
    
    def __init__(self, host: str = None, port: int = None, collection_name: str = None):
        self.host = host or settings.MILVUS_HOST
        self.port = port or settings.MILVUS_PORT
        self.collection_name = collection_name or settings.MILVUS_COLLECTION
        self.collection = None
        self.connect()
    
    def connect(self):
        """连接到 Milvus 服务"""
        from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
        
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=str(self.port)
            )
            self._ensure_collection()
        except Exception as e:
            print(f"Milvus 连接失败: {e}")
            raise
    
    def _ensure_collection(self):
        """确保集合存在"""
        from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, utility
        
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self.collection.load()
        else:
            self._create_collection()
    
    def _create_collection(self):
        """创建集合"""
        from pymilvus import Collection, CollectionSchema, FieldSchema, DataType
        
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536)
        ]
        
        schema = CollectionSchema(fields=fields, description="MGAgent 知识库向量集合")
        self.collection = Collection(name=self.collection_name, schema=schema)
        
        index_params = {"metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 1024}}
        self.collection.create_index(field_name="embedding", index_params=index_params)
        self.collection.load()
    
    def add_documents(self, documents: List[Document], embeddings: List[List[float]]) -> List[str]:
        if not documents or not embeddings:
            return []
        
        ids = [str(uuid.uuid4()) for _ in documents]
        
        data = [
            ids,
            [doc.page_content[:65535] for doc in documents],
            [doc.metadata for doc in documents],
            embeddings
        ]
        
        try:
            self.collection.insert(data)
            self.collection.flush()
            return ids
        except Exception as e:
            print(f"Milvus 添加文档失败: {e}")
            raise
    
    def similarity_search(self, query_embedding: List[float], k: int = 3) -> List[Dict[str, Any]]:
        search_params = {"metric_type": "L2", "params": {"nprobe": 16}}
        
        try:
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=k,
                output_fields=["content", "metadata"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        "id": hit.id,
                        "content": hit.entity.get("content", ""),
                        "metadata": hit.entity.get("metadata", {}),
                        "score": hit.score
                    })
            
            return search_results
        except Exception as e:
            print(f"Milvus 搜索失败: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        try:
            return {
                "type": "milvus",
                "name": "Milvus",
                "total_chunks": self.get_total_count(),
                "host": self.host,
                "port": self.port,
                "collection": self.collection_name
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        try:
            results = self.collection.query(
                expr="",
                output_fields=["id", "content", "metadata"],
                limit=10000
            )
            return results
        except Exception as e:
            print(f"Milvus 获取所有块失败: {e}")
            return []
    
    def delete_by_ids(self, ids: List[str]) -> None:
        if not ids:
            return
        try:
            expr = f'id in {ids}'
            self.collection.delete(expr)
        except Exception as e:
            print(f"Milvus 删除失败: {e}")
            raise
    
    def clear_all(self) -> None:
        try:
            if self.get_total_count() > 0:
                self.collection.drop()
                self._ensure_collection()
        except Exception as e:
            print(f"Milvus 清空失败: {e}")
            raise
    
    def get_total_count(self) -> int:
        try:
            return self.collection.num_entities
        except Exception:
            return 0


def create_vector_db() -> VectorDBInterface:
    """根据当前方案创建向量数据库实例"""
    if is_mysql_scheme():
        return MilvusService()
    else:
        return ChromaDBService()


# 全局实例
_vector_db_instance = None

def get_vector_db() -> VectorDBInterface:
    """获取全局向量数据库实例"""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = create_vector_db()
    return _vector_db_instance

def reset_vector_db() -> None:
    """重置全局实例（用于切换方案时）"""
    global _vector_db_instance
    _vector_db_instance = None
