"""
Milvus 向量数据库服务
基于 pymilvus 实现的向量存储服务
"""
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
import uuid
from app.config.settings import settings


class MilvusService:
    """Milvus 向量数据库服务"""
    
    def __init__(self, host: str = None, port: int = None, collection_name: str = None):
        self.host = host or settings.MILVUS_HOST
        self.port = port or settings.MILVUS_PORT
        self.collection_name = collection_name or settings.MILVUS_COLLECTION
        self.collection = None
        self.connect()
    
    def connect(self):
        """连接到 Milvus 服务"""
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
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self.collection.load()
        else:
            self._create_collection()
    
    def _create_collection(self):
        """创建集合"""
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=64
            ),
            FieldSchema(
                name="content",
                dtype=DataType.VARCHAR,
                max_length=65535
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.JSON
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=1536  # 默认向量维度
            )
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="MGAgent 知识库向量集合"
        )
        
        self.collection = Collection(
            name=self.collection_name,
            schema=schema
        )
        
        # 创建索引
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        self.collection.load()
    
    def add_documents(self, documents: List[Document], embeddings: List[List[float]]) -> List[str]:
        """添加文档到向量数据库"""
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
            print(f"添加文档失败: {e}")
            raise
    
    def similarity_search(
        self, 
        query_embedding: List[float], 
        k: int = 3,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """相似度搜索"""
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 16}
        }
        
        expr = filters or None
        
        try:
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
                    search_results.append({
                        "id": hit.id,
                        "content": hit.entity.get("content", ""),
                        "metadata": hit.entity.get("metadata", {}),
                        "score": hit.score
                    })
            
            return search_results
        except Exception as e:
            print(f"搜索失败: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            stats = {
                "collection_name": self.collection_name,
                "total_vectors": self.collection.num_entities,
                "host": self.host,
                "port": self.port
            }
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """获取所有向量块"""
        try:
            results = self.collection.query(
                expr="",
                output_fields=["id", "content", "metadata"],
                limit=10000
            )
            return results
        except Exception as e:
            print(f"获取所有块失败: {e}")
            return []
    
    def delete_by_ids(self, ids: List[str]) -> None:
        """根据 ID 删除向量"""
        if not ids:
            return
        
        try:
            expr = f'id in {ids}'
            self.collection.delete(expr)
        except Exception as e:
            print(f"删除失败: {e}")
            raise
    
    def clear_all(self) -> None:
        """清空所有数据"""
        try:
            if self.collection.num_entities > 0:
                self.collection.drop()
                self._ensure_collection()
        except Exception as e:
            print(f"清空失败: {e}")
            raise
    
    def get_total_count(self) -> int:
        """获取总向量数"""
        try:
            return self.collection.num_entities
        except Exception:
            return 0


# 创建全局实例
milvus_service = MilvusService()
