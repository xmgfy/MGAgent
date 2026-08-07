"""
向量数据库工厂 - Admin Backend
支持 ChromaDB 和 Milvus
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.config.config import is_mysql_scheme, settings


class VectorDBInterface(ABC):
    """向量数据库抽象接口"""
    
    @abstractmethod
    def add_documents(self, documents: List, embeddings: List[List[float]], 
                      ids: Optional[List[str]] = None) -> List[str]:
        """添加文档到向量数据库"""
        pass
    
    @abstractmethod
    def similarity_search(self, query_embedding: List[float], k: int = 3) -> List[Dict[str, Any]]:
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
    
    @abstractmethod
    def clear_all(self) -> None:
        """清空所有文档"""
        pass


class ChromaDBService(VectorDBInterface):
    """ChromaDB 服务实现"""
    
    def __init__(self):
        self._client = None
        self._collection_name = "mgagent_knowledge"
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化 ChromaDB 客户端"""
        try:
            import chromadb
            from app.config.config import get_chroma_dir
            chroma_dir = get_chroma_dir()
            chroma_dir.mkdir(parents=True, exist_ok=True)
            
            self._client = chromadb.PersistentClient(path=str(chroma_dir))
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            raise Exception(f"ChromaDB 初始化失败: {str(e)}")
    
    def add_documents(self, documents: List, embeddings: List[List[float]], 
                      ids: Optional[List[str]] = None) -> List[str]:
        """添加文档到 ChromaDB"""
        try:
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # 处理文档对象
            texts = []
            metadatas = []
            for i, doc in enumerate(documents):
                if hasattr(doc, 'page_content'):
                    texts.append(doc.page_content)
                    metadatas.append(doc.metadata if hasattr(doc, 'metadata') else {})
                elif isinstance(doc, dict):
                    texts.append(doc.get('page_content', ''))
                    metadatas.append(doc.get('metadata', {}))
                else:
                    texts.append(str(doc))
                    metadatas.append({})
            
            self._collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            return ids
        except Exception as e:
            raise Exception(f"ChromaDB 添加文档失败: {str(e)}")
    
    def similarity_search(self, query_embedding: List[float], k: int = 3) -> List[Dict[str, Any]]:
        """在 ChromaDB 中进行相似度搜索"""
        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    search_results.append({
                        "id": doc_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0
                    })
            
            return search_results
        except Exception as e:
            raise Exception(f"ChromaDB 相似度搜索失败: {str(e)}")
    
    def get_total_count(self) -> int:
        """获取 ChromaDB 中的文档总数"""
        try:
            return self._collection.count()
        except Exception as e:
            raise Exception(f"ChromaDB 获取总数失败: {str(e)}")
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """获取所有文档块"""
        try:
            results = self._collection.get(include=["documents", "metadatas"])
            
            chunks = []
            if results["ids"]:
                for i, doc_id in enumerate(results["ids"]):
                    chunks.append({
                        "id": doc_id,
                        "content": results["documents"][i] if results["documents"] else "",
                        "metadata": results["metadatas"][i] if results["metadatas"] else {}
                    })
            
            return chunks
        except Exception as e:
            raise Exception(f"ChromaDB 获取所有文档失败: {str(e)}")
    
    def delete_by_ids(self, ids: List[str]) -> None:
        """根据ID删除文档"""
        try:
            self._collection.delete(ids=ids)
        except Exception as e:
            raise Exception(f"ChromaDB 删除文档失败: {str(e)}")
    
    def clear_all(self) -> None:
        """清空所有文档"""
        try:
            self._collection.delete(where={})
        except Exception as e:
            # 如果没有文档，删除可能会失败
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
            
            # 连接到 Milvus
            connections.connect(host=self._host, port=self._port, db_name="default")
            
            # 检查现有集合的维度
            if utility.has_collection(self._collection_name):
                existing_collection = Collection(self._collection_name)
                existing_dim = existing_collection.schema.fields[1].params.get('dim', 1536)
                
                if existing_dim != self._dimension:
                    # 维度不匹配，删除旧集合并重建
                    print(f"Embedding 维度变更: {existing_dim} -> {self._dimension}，重建集合...")
                    utility.drop_collection(self._collection_name)
                else:
                    self._collection = existing_collection
                    self._collection.load()
                    return
            
            # 创建新集合
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=256),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self._dimension),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]
            schema = CollectionSchema(fields, description="MGAgent 知识库集合")
            self._collection = Collection(self._collection_name, schema)
            
            # 创建索引
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
            
            # 处理文档
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
    
    def similarity_search(self, query_embedding: List[float], k: int = 3) -> List[Dict[str, Any]]:
        """在 Milvus 中进行相似度搜索"""
        try:
            from pymilvus import Collection
            self._collection = Collection(self._collection_name)
            
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = self._collection.search(
                data=[query_embedding],
                anns_field="embedding",
                search_params=search_params,
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
            
            # Milvus 要求非空的过滤表达式，使用 id != "" 匹配所有记录
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
    
    def clear_all(self) -> None:
        """清空所有文档"""
        try:
            from pymilvus import Collection, utility
            if utility.has_collection(self._collection_name):
                self._collection.drop()
                # 重新创建集合
                self._initialize_client()
        except Exception as e:
            raise Exception(f"Milvus 清空文档失败: {str(e)}")


def get_vector_db() -> VectorDBInterface:
    """获取向量数据库实例（根据当前配置方案）"""
    if is_mysql_scheme():
        return MilvusService()
    else:
        return ChromaDBService()


def create_vector_db() -> VectorDBInterface:
    """创建向量数据库实例（工厂函数）"""
    return get_vector_db()
