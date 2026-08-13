"""
向量数据库工厂 - Admin Backend (Milvus only)
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.config.config import settings


class VectorDBInterface(ABC):
    """向量数据库抽象接口"""
    
    @abstractmethod
    def add_documents(self, documents: List, embeddings: List[List[float]], 
                      ids: Optional[List[str]] = None) -> List[str]:
        """添加文档到向量数据库"""
        pass
    
    @abstractmethod
    def similarity_search(self, query_embedding: List[float], k: int = 3,
                          knowledge_base_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """相似度搜索"""
        pass
    
    @abstractmethod
    def get_total_count(self) -> int:
        """获取文档总数"""
        pass
    
    @abstractmethod
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """获取所有文档块"""
        pass
    
    @abstractmethod
    def delete_by_ids(self, ids: List[str]) -> None:
        """根据ID删除文档"""
        pass

    def delete_by_metadata(self, key: str, value: str) -> int:
        """根据 metadata 条件删除文档（返回删除数量）

        默认实现扫描后删除（fallback）；子类应覆盖以利用原生能力。
        """
        chunks = self.get_all_chunks()
        ids = [c["id"] for c in chunks if c.get("metadata", {}).get(key) == value]
        if ids:
            self.delete_by_ids(ids)
        return len(ids)

    def keyword_search(
        self,
        keywords: List[str],
        k: int = 10,
        knowledge_base_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """轻量关键词检索（fallback：get_all_chunks + 文本匹配）"""
        all_chunks = self.get_all_chunks()
        if knowledge_base_ids:
            all_chunks = [
                c for c in all_chunks
                if c.get("metadata", {}).get("knowledge_base_id") in knowledge_base_ids
            ]

        kw_lower = [kw.lower() for kw in keywords if kw.strip()]
        if not kw_lower:
            return []

        scored: List[Dict[str, Any]] = []
        for chunk in all_chunks:
            content_lower = chunk.get("content", "").lower()
            hits = sum(1 for kw in kw_lower if kw in content_lower)
            if hits > 0:
                entry = dict(chunk)
                entry["score"] = float(hits)
                scored.append(entry)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]

    @abstractmethod
    def clear_all(self) -> None:
        """清空所有文档"""
        pass


class MilvusService(VectorDBInterface):
    """Milvus 服务实现"""
    
    def __init__(self):
        self._collection_name = "mgagent_knowledge"
        self._host = settings.MILVUS_HOST
        self._port = settings.MILVUS_PORT
        self._dimension = self._get_dimension()
        self._initialize_client()
    
    def _get_dimension(self) -> int:
        """从数据库获取当前 Embedding 模型的维度"""
        try:
            from app.services.model_config_service import get_active_embedding_config
            config = get_active_embedding_config()
            if config and config.get("dimension"):
                return config["dimension"]
        except Exception:
            pass
        return 1536  # 默认维度
    
    def _initialize_client(self):
        """初始化 Milvus 客户端"""
        try:
            from pymilvus import (
                Collection, FieldSchema, CollectionSchema, DataType,
                connections, utility
            )
            
            connections.connect(host=self._host, port=self._port, db_name="default")
            
            if utility.has_collection(self._collection_name):
                existing_collection = Collection(self._collection_name)
                existing_dim = existing_collection.schema.fields[1].params.get('dim', 1536)
                
                if existing_dim != self._dimension:
                    print(f"Embedding 维度变更: {existing_dim} -> {self._dimension}，重建集合...")
                    utility.drop_collection(self._collection_name)
                else:
                    self._collection = existing_collection
                    self._collection.load()
                    return
            
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=256),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self._dimension),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]
            schema = CollectionSchema(fields, description="MGAgent 知识库集合")
            self._collection = Collection(self._collection_name, schema)
            
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            self._collection.create_index(field_name="embedding", index_params=index_params)
            
        except Exception as e:
            raise Exception(f"Milvus 初始化失败: {str(e)}")
    
    def add_documents(self, documents: List, embeddings: List[List[float]], 
                      ids: Optional[List[str]] = None) -> List[str]:
        """添加文档到 Milvus"""
        try:
            from pymilvus import Collection
            self._collection = Collection(self._collection_name)
            
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in documents]
            
            data = []
            for i, doc in enumerate(documents):
                if hasattr(doc, 'page_content'):
                    content = doc.page_content
                    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                elif isinstance(doc, dict):
                    content = doc.get('page_content', '')
                    metadata = doc.get('metadata', {})
                else:
                    content = str(doc)
                    metadata = {}
                
                data.append({
                    "id": ids[i],
                    "embedding": embeddings[i],
                    "content": content,
                    "metadata": metadata
                })
            
            self._collection.insert(data)
            self._collection.flush()
            return ids
        except Exception as e:
            raise Exception(f"Milvus 添加文档失败: {str(e)}")
    
    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 3,
        knowledge_base_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """在 Milvus 中进行相似度搜索"""
        try:
            from pymilvus import Collection
            self._collection = Collection(self._collection_name)
            
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }

            expr = None
            if knowledge_base_ids:
                expr = f'metadata["knowledge_base_id"] in {knowledge_base_ids}'
            
            results = self._collection.search(
                data=[query_embedding],
                anns_field="embedding",
                search_params=search_params,
                limit=k,
                output_fields=["content", "metadata"],
                expr=expr,
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        "id": hit.id,
                        "content": hit.entity.get("content", ""),
                        "metadata": hit.entity.get("metadata", {}),
                        "distance": hit.distance
                    })
            
            return search_results
        except Exception as e:
            raise Exception(f"Milvus 相似度搜索失败: {str(e)}")
    
    def get_total_count(self) -> int:
        """获取 Milvus 中的文档总数"""
        try:
            from pymilvus import Collection
            self._collection = Collection(self._collection_name)
            return self._collection.num_entities
        except Exception as e:
            raise Exception(f"Milvus 获取总数失败: {str(e)}")
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """获取所有文档块"""
        try:
            from pymilvus import Collection
            self._collection = Collection(self._collection_name)
            self._collection.load()
            
            results = self._collection.query(
                expr='id != ""',
                output_fields=["content", "metadata"],
                limit=16384
            )
            
            chunks = []
            for result in results:
                chunks.append({
                    "id": result.get("id", ""),
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {})
                })
            
            return chunks
        except Exception as e:
            raise Exception(f"Milvus 获取所有文档失败: {str(e)}")
    
    def delete_by_ids(self, ids: List[str]) -> None:
        """根据ID删除文档"""
        try:
            from pymilvus import Collection
            self._collection = Collection(self._collection_name)
            
            ids_str = '["' + '", "'.join(ids) + '"]'
            self._collection.delete(expr=f'id in {ids_str}')
            self._collection.flush()
        except Exception as e:
            raise Exception(f"Milvus 删除文档失败: {str(e)}")
    
    def delete_by_metadata(self, key: str, value: str) -> int:
        """Milvus 原生 metadata expression 删除"""
        try:
            from pymilvus import Collection
            self._collection = Collection(self._collection_name)
            self._collection.load()
            
            expr = f'metadata["{key}"] == "{value}"'
            results = self._collection.query(expr=expr, output_fields=["id"], limit=16384)
            ids = [r["id"] for r in results]
            count = len(ids)
            
            if count > 0:
                self._collection.delete(expr=expr)
                self._collection.flush()
            
            return count
        except Exception as e:
            raise Exception(f"Milvus delete_by_metadata 失败: {str(e)}")
    
    def clear_all(self) -> None:
        """清空所有文档"""
        try:
            from pymilvus import Collection, utility
            if utility.has_collection(self._collection_name):
                self._collection.drop()
                self._initialize_client()
        except Exception as e:
            raise Exception(f"Milvus 清空文档失败: {str(e)}")


_vector_db_instance = None


def get_vector_db() -> VectorDBInterface:
    """获取向量数据库实例（单例）"""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = MilvusService()
    return _vector_db_instance


def reset_vector_db() -> None:
    """重置单例"""
    global _vector_db_instance
    _vector_db_instance = None


def create_vector_db() -> VectorDBInterface:
    """创建新的向量数据库实例（不走单例）"""
    return MilvusService()
