"""
向量数据库工厂 - Backend (Milvus only)
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
import uuid

from app.config.config import settings


class VectorDBInterface(ABC):
    """向量数据库抽象接口"""
    
    @abstractmethod
    def add_documents(self, documents: List[Document], embeddings: List[List[float]]) -> List[str]:
        """添加文档"""
        pass
    
    @abstractmethod
    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 3,
        knowledge_base_ids: Optional[List[str]] = None,
        similarity_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
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


class MilvusService(VectorDBInterface):
    """Milvus 服务实现"""
    
    def __init__(self, host: str = None, port: int = None, collection_name: str = None):
        self.host = host or settings.MILVUS_HOST
        self.port = port or settings.MILVUS_PORT
        self.collection_name = collection_name or settings.MILVUS_COLLECTION
        self.collection = None
        self._dimension = self._get_dimension()
        self._needs_revectorization = False
        self.connect()
    
    def _get_dimension(self) -> int:
        """从数据库获取当前 Embedding 模型的维度"""
        try:
            from app.services.model_config_service import get_active_embedding_config
            config = get_active_embedding_config()
            if config and config.get("dimension"):
                return config["dimension"]
        except Exception:
            pass
        return 1536
    
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
        """确保集合存在，检查维度是否匹配"""
        from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, utility
        
        if utility.has_collection(self.collection_name):
            existing_collection = Collection(self.collection_name)
            try:
                existing_dim = existing_collection.schema.fields[3].params.get('dim', 1536)
            except Exception:
                existing_dim = 1536
            
            if existing_dim != self._dimension:
                print(f"警告: Embedding 维度不匹配 (当前: {existing_dim}, 期望: {self._dimension})")
                print(f"请在管理后台重新向量化文档，或删除旧集合并重建")
                self.collection = existing_collection
                self.collection.load()
                self._needs_revectorization = True
            else:
                self.collection = existing_collection
                self.collection.load()
                self._needs_revectorization = False
        else:
            self._create_collection()
            self._needs_revectorization = False
    
    def _create_collection(self):
        """创建集合"""
        from pymilvus import Collection, CollectionSchema, FieldSchema, DataType
        
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self._dimension)
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
    
    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 3,
        knowledge_base_ids: Optional[List[str]] = None,
        similarity_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        search_params = {"metric_type": "L2", "params": {"nprobe": 16}}
        
        try:
            if self._needs_revectorization:
                print("警告: 向量维度不匹配，检索结果可能不准确。建议重新向量化文档。")

            expr = None
            if knowledge_base_ids:
                expr = f'metadata["knowledge_base_id"] in {knowledge_base_ids}'

            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=k,
                expr=expr,
                output_fields=["content", "metadata"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    if similarity_threshold is not None and hit.score > similarity_threshold:
                        continue
                    search_results.append({
                        "id": hit.id,
                        "content": hit.entity.get("content", ""),
                        "metadata": hit.entity.get("metadata", {}),
                        "score": hit.score
                    })
            
            return search_results
        except Exception as e:
            print(f"Milvus 搜索失败: {e}")
            return []
    
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
    
    def keyword_search(
        self,
        keywords: List[str],
        k: int = 5,
        knowledge_base_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """基于关键词的文本搜索"""
        try:
            if not keywords or self.get_total_count() == 0:
                return []
            
            expr_parts = []
            for kw in keywords:
                if kw.strip():
                    expr_parts.append(f'content like "%{kw}%"')
            
            if not expr_parts:
                return []
            
            expr = " or ".join(expr_parts)

            if knowledge_base_ids:
                expr = f'({expr}) and metadata["knowledge_base_id"] in {knowledge_base_ids}'

            results = self.collection.query(
                expr=expr,
                output_fields=["id", "content", "metadata"],
                limit=k
            )
            
            search_results = []
            for i, doc_id in enumerate(results.get("ids", [])):
                search_results.append({
                    "id": doc_id,
                    "content": results.get("content", [""])[i] if i < len(results.get("content", [])) else "",
                    "metadata": results.get("metadata", [])[i] if i < len(results.get("metadata", [])) else {},
                    "score": 0.0
                })
            
            return search_results
        except Exception as e:
            print(f"Milvus 关键词搜索失败: {e}")
            return []


def create_vector_db() -> VectorDBInterface:
    """创建 Milvus 向量数据库实例"""
    return MilvusService()


_vector_db_instance = None


def get_vector_db() -> VectorDBInterface:
    """获取全局向量数据库实例"""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = create_vector_db()
    return _vector_db_instance


def reset_vector_db() -> None:
    """重置全局实例"""
    global _vector_db_instance
    _vector_db_instance = None
