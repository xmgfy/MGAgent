"""
向量数据库管理接口 - 基于 Milvus
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from app.db.models import Admin
from .auth import get_current_admin
from app.config.settings import settings
from pymilvus import connections, Collection, utility

router = APIRouter()


class VectorDBStats(BaseModel):
    total_chunks: int
    host: str
    port: int
    collection_name: str


class VectorChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]


def get_milvus_collection():
    """获取 Milvus 集合"""
    connections.connect(
        alias="default",
        host=settings.MILVUS_HOST,
        port=str(settings.MILVUS_PORT)
    )
    
    collection_name = settings.MILVUS_COLLECTION
    
    if not utility.has_collection(collection_name):
        raise HTTPException(status_code=404, detail="向量数据库集合不存在，请先上传文档")
    
    collection = Collection(collection_name)
    collection.load()
    return collection


@router.get("/vector-db/stats", response_model=VectorDBStats)
async def get_vector_db_stats(admin: Admin = Depends(get_current_admin)):
    """获取向量数据库统计信息"""
    try:
        collection = get_milvus_collection()
        
        return VectorDBStats(
            total_chunks=collection.num_entities,
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION
        )
    except HTTPException:
        # 如果集合不存在，返回0
        return VectorDBStats(
            total_chunks=0,
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector-db/chunks", response_model=List[VectorChunk])
async def list_vector_chunks(
    limit: int = Query(50),
    offset: int = Query(0),
    admin: Admin = Depends(get_current_admin)
):
    """列出向量块"""
    try:
        collection = get_milvus_collection()
        
        results = collection.query(
            expr="",
            output_fields=["id", "content", "metadata"],
            limit=limit,
            offset=offset
        )
        
        chunks = []
        for result in results:
            chunks.append(VectorChunk(
                id=result["id"],
                content=result.get("content", ""),
                metadata=result.get("metadata", {})
            ))
        
        return chunks
    except HTTPException:
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector-db/search")
async def search_vector_db(
    query: str,
    k: int = Query(3),
    admin: Admin = Depends(get_current_admin)
):
    """搜索向量数据库"""
    try:
        from app.rag.milvus_service import MilvusService
        
        milvus_service = MilvusService(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION
        )
        
        # 生成查询嵌入
        from app.rag.retriever import vector_retriever
        query_embedding = vector_retriever.embeddings.embed_query(query)
        
        # 搜索
        results = milvus_service.similarity_search(query_embedding, k=k)
        
        search_results = []
        for result in results:
            search_results.append({
                "id": result["id"],
                "content": result["content"],
                "metadata": result["metadata"],
                "similarity": float(1 - result.get("score", 0))
            })
        
        if not search_results:
            return {"results": [], "message": "未找到匹配的结果"}
        
        return {"results": search_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/vector-db/chunks/{chunk_id}")
async def delete_vector_chunk(chunk_id: str, admin: Admin = Depends(get_current_admin)):
    """删除单个向量块"""
    try:
        collection = get_milvus_collection()
        
        expr = f'id == "{chunk_id}"'
        collection.delete(expr)
        collection.flush()
        
        return {"message": f"向量块 {chunk_id} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vector-db/clear")
async def clear_vector_db(admin: Admin = Depends(get_current_admin)):
    """清空向量数据库"""
    try:
        collection_name = settings.MILVUS_COLLECTION
        
        if utility.has_collection(collection_name):
            collection = Collection(collection_name)
            collection.drop()
        
        # 重新创建集合
        from pymilvus import CollectionSchema, FieldSchema, DataType
        
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536)
        ]
        
        schema = CollectionSchema(fields=fields, description="MGAgent 知识库向量集合")
        collection = Collection(name=collection_name, schema=schema)
        
        # 创建索引
        index_params = {"metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 1024}}
        collection.create_index(field_name="embedding", index_params=index_params)
        collection.load()
        
        return {"message": "向量数据库已清空并重新初始化"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
